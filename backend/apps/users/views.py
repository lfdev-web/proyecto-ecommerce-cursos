from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from . import gateway
from .models import (
    RechargeStatus, Role, TeacherApplicationStatus,
    WalletRecharge, WalletTransactionType, record_wallet_transaction,
)
from .serializers import (
    CustomUserSerializer,
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    RechargeAuthorizeSerializer,
    RechargeStartSerializer,
    TeacherApplicationSerializer,
    WalletRechargeSerializer,
    WalletTransactionSerializer,
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    # Sin este límite el login aceptaba intentos ilimitados: con un diccionario
    # básico una cuenta se abría en minutos. 8 intentos/minuto por IP.
    throttle_scope = 'login'

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_scope = 'registro'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Auto-login: Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': CustomUserSerializer(user, context=self.get_serializer_context()).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class WalletTransactionsView(generics.ListAPIView):
    """
    Historial de movimientos del saldo simulado del usuario (libro mayor),
    del más reciente al más antiguo.
    """
    serializer_class = WalletTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            self.request.user.wallet_transactions
            .select_related('transaction_type')
            .order_by('-created_at')
        )


class RechargeStartView(APIView):
    """
    Paso 1 — el usuario elige cuánto recargar.

    Crea la intención en estado PENDIENTE y devuelve su token. El frontend
    redirige con ese token a la pantalla de la pasarela simulada.
    """
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'recarga'

    def post(self, request):
        serializer = RechargeStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recarga = WalletRecharge.objects.create(
            user=request.user,
            amount=serializer.validated_data['amount'],
            status_id=RechargeStatus.PENDING,
        )
        return Response(WalletRechargeSerializer(recarga).data, status=status.HTTP_201_CREATED)


class RechargeDetailView(APIView):
    """
    Datos de la intención, para que la pantalla de la pasarela sepa cuánto
    está cobrando y a quién. Solo la ve su propio dueño.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, token):
        recarga = get_object_or_404(WalletRecharge, token=token, user=request.user)
        datos = WalletRechargeSerializer(recarga).data
        # La pasarela muestra estos números de prueba como ayuda
        datos['test_cards'] = {
            'aprobadas': gateway.TARJETAS_APROBADAS,
            'rechazadas': [
                {'numero': n, 'motivo': motivo}
                for n, (_, motivo) in gateway.TARJETAS_DE_PRUEBA.items()
            ],
        }
        return Response(datos)


class RechargeAuthorizeView(APIView):
    """
    Paso 2 — el usuario autoriza el cobro en la pasarela.

    Es el punto crítico: si esta petición se procesa dos veces, el saldo se
    acredita dos veces. Por eso la fila se bloquea con select_for_update() y
    se verifica que siga PENDIENTE antes de tocar el saldo.
    """
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'recarga'

    def post(self, request, token):
        serializer = RechargeAuthorizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # select_for_update bloquea la fila hasta el fin de la transacción:
            # dos peticiones simultáneas se serializan y la segunda encuentra
            # el estado ya cambiado.
            recarga = get_object_or_404(
                WalletRecharge.objects.select_for_update(),
                token=token, user=request.user,
            )

            if recarga.status_id != RechargeStatus.PENDING:
                return Response(
                    {'detail': f'Esta recarga ya fue procesada ({recarga.status_id}).',
                     'recharge': WalletRechargeSerializer(recarga).data},
                    status=status.HTTP_409_CONFLICT,
                )

            if recarga.is_expired:
                recarga.status_id = RechargeStatus.EXPIRED
                recarga.completed_at = timezone.now()
                recarga.save(update_fields=['status', 'completed_at'])
                return Response(
                    {'detail': 'La sesión de pago expiró. Inicia una recarga nueva.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            aprobada, motivo, ultimos4 = gateway.autorizar(
                serializer.validated_data['card_number']
            )
            recarga.card_last4 = ultimos4
            recarga.completed_at = timezone.now()

            if not aprobada:
                recarga.status_id = RechargeStatus.DECLINED
                recarga.decline_reason = motivo
                recarga.save(update_fields=['status', 'card_last4', 'decline_reason', 'completed_at'])
                return Response(
                    {'detail': motivo, 'recharge': WalletRechargeSerializer(recarga).data},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

            # Aprobada: se acredita el saldo y se deja constancia en el libro mayor.
            # El monto sale de la BD, nunca de la petición.
            usuario = User.objects.select_for_update().get(pk=request.user.pk)
            usuario.balance = usuario.balance + recarga.amount
            usuario.save(update_fields=['balance'])

            recarga.status_id = RechargeStatus.APPROVED
            recarga.reference = gateway.generar_referencia()
            recarga.save(update_fields=['status', 'card_last4', 'reference', 'completed_at'])

            record_wallet_transaction(
                usuario, WalletTransactionType.RECHARGE, recarga.amount,
                description=f'Recarga de saldo — {recarga.reference}',
            )

        return Response({
            'recharge': WalletRechargeSerializer(recarga).data,
            'balance': str(usuario.balance),
        })


class RechargeCancelView(APIView):
    """El usuario abandona el pago desde la pantalla de la pasarela."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, token):
        with transaction.atomic():
            recarga = get_object_or_404(
                WalletRecharge.objects.select_for_update(),
                token=token, user=request.user,
            )
            if recarga.status_id != RechargeStatus.PENDING:
                return Response(
                    {'detail': f'Esta recarga ya fue procesada ({recarga.status_id}).'},
                    status=status.HTTP_409_CONFLICT,
                )
            recarga.status_id = RechargeStatus.CANCELLED
            recarga.completed_at = timezone.now()
            recarga.save(update_fields=['status', 'completed_at'])
        return Response(WalletRechargeSerializer(recarga).data)


class RechargeHistoryView(generics.ListAPIView):
    """Historial de recargas del usuario, incluidas las rechazadas."""
    serializer_class = WalletRechargeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.recharges.select_related('status')


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class TeacherApplicationView(APIView):
    """
    Onboarding de docente (modelo marketplace).
    GET  -> estado de la última solicitud del usuario (para pintar la pantalla).
    POST -> crea una solicitud nueva (multipart, con cédula obligatoria).
    Reglas: no puede aplicar quien ya es DOCENTE/ADMIN, ni quien tiene una
    solicitud PENDING abierta. Tras un rechazo sí puede volver a aplicar.
    """
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        application = request.user.teacher_applications.order_by('-created_at').first()
        if not application:
            return Response({'has_application': False})
        data = TeacherApplicationSerializer(application, context={'request': request}).data
        return Response({'has_application': True, **data})

    def post(self, request):
        user = request.user
        if user.role_id in (Role.DOCENTE, Role.ADMIN):
            return Response(
                {'detail': 'Ya eres docente o administrador; no necesitas postular.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.teacher_applications.filter(status_id=TeacherApplicationStatus.PENDING).exists():
            return Response(
                {'detail': 'Ya tienes una solicitud pendiente de revisión.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TeacherApplicationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, status_id=TeacherApplicationStatus.PENDING)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
