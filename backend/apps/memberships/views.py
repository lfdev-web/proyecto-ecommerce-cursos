from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from .models import (
    MembershipPlan, UserMembership, MembershipPayment,
    BillingCycle, MembershipStatus, PlanAudience,
)
from .serializers import (
    MembershipPlanSerializer,
    UserMembershipSerializer,
    SubscribeSerializer,
)


class MembershipPlanListView(generics.ListAPIView):
    """
    Lista pública de los planes disponibles, ordenados por nivel.
    Acepta ?audience=ALUMNO|DOCENTE para pedir solo una familia de planes.
    """
    serializer_class = MembershipPlanSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = (
            MembershipPlan.objects
            .filter(is_active=True)
            .select_related('audience', 'tier')
            .order_by('audience_id', 'tier__rank', 'price')
        )
        audience = self.request.query_params.get('audience')
        if audience:
            queryset = queryset.filter(audience_id=audience.upper())
        return queryset


class SubscribeView(APIView):
    """
    Permite al usuario suscribirse a un plan de membresía.
    FLUJO CRÍTICO:
    1. Valida el número de tarjeta con el Algoritmo de Luhn (en memoria, sin persistir).
    2. Verifica que el wallet simulado del usuario tenga saldo suficiente y lo descuenta.
    3. Calcula la fecha de expiración según el ciclo de facturación del plan.
    4. Crea o actualiza el UserMembership del usuario.
    5. Registra el pago en MembershipPayment con solo los últimos 4 dígitos.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data['plan_id']
        card_number = serializer.validated_data['card_number']
        # Extraer solo los últimos 4 dígitos (nunca almacenar el número completo — PCI-DSS)
        card_last4 = card_number.replace(' ', '').replace('-', '')[-4:]

        plan = MembershipPlan.objects.select_related('audience').get(id=plan_id)

        # Los planes de docente solo los puede contratar quien ya es docente.
        if plan.audience_id == PlanAudience.DOCENTE and request.user.role_id not in ('DOCENTE', 'ADMIN'):
            return Response(
                {'detail': 'Los planes de docente son solo para instructores aprobados. '
                           'Postula primero desde "Enseña con nosotros".'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Bloquear la fila del usuario para evitar condiciones de carrera sobre el saldo
        user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
        if user.balance < plan.price:
            return Response({
                'detail': 'Saldo insuficiente para suscribirte a este plan.',
                'balance': user.balance,
                'plan_price': plan.price,
            }, status=status.HTTP_400_BAD_REQUEST)

        user.balance -= plan.price
        user.save(update_fields=['balance'])

        # Registrar el egreso en el libro mayor del saldo simulado
        from apps.users.models import WalletTransactionType, record_wallet_transaction
        record_wallet_transaction(
            user, WalletTransactionType.MEMBERSHIP, -plan.price,
            description=f'Suscripción al plan {plan.name}'
        )

        # Calcular fecha de expiración según el ciclo de facturación
        now = timezone.now()
        if plan.billing_cycle_id == BillingCycle.MONTHLY:
            expires_at = now + relativedelta(months=1)
        else:  # ANNUAL
            expires_at = now + relativedelta(years=1)

        # Crear o renovar la membresía del usuario en esa familia de planes
        # (puede tener a la vez una de alumno y una de docente).
        membership, created = UserMembership.objects.update_or_create(
            user=request.user,
            audience_id=plan.audience_id,
            defaults={
                'plan': plan,
                'status_id': MembershipStatus.ACTIVE,
                'expires_at': expires_at,
                'auto_renew': True,
                'cancelled_at': None,
            }
        )

        # Registrar pago con solo los últimos 4 dígitos (PCI-DSS)
        payment = MembershipPayment.objects.create(
            membership=membership,
            amount=plan.price,
            card_last4=card_last4,
            transaction_reference=f"DEMO-{timezone.now().timestamp():.0f}",
            is_successful=True,
        )

        return Response({
            'detail': f"Membresía '{plan.name}' activada correctamente.",
            'expires_at': expires_at,
            'membership': UserMembershipSerializer(membership).data,
        }, status=status.HTTP_201_CREATED)


class MyMembershipView(generics.RetrieveAPIView):
    """
    Estado de la membresía del usuario en una familia de planes.
    Acepta ?audience=ALUMNO|DOCENTE (por defecto ALUMNO).
    """
    serializer_class = UserMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        audience = self.request.query_params.get('audience', PlanAudience.ALUMNO).upper()
        membership = (
            UserMembership.objects
            .filter(user=self.request.user, audience_id=audience)
            .select_related('plan', 'plan__tier', 'plan__audience')
            .first()
        )
        if not membership:
            from rest_framework.exceptions import NotFound
            raise NotFound("No tienes ninguna membresía en esta categoría.")
        return membership


class CancelMembershipView(APIView):
    """
    Cancela la membresía del usuario en una familia de planes.
    El acceso continúa hasta la fecha de expiración ya pagada (no se hace refund automático).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        audience = (request.data.get('audience') or PlanAudience.ALUMNO).upper()
        membership = UserMembership.objects.filter(user=request.user, audience_id=audience).first()
        if not membership:
            return Response({'detail': 'No tienes ninguna membresía en esta categoría.'},
                            status=status.HTTP_404_NOT_FOUND)

        if membership.status_id == MembershipStatus.CANCELLED:
            return Response({'detail': 'Tu membresía ya está cancelada.'}, status=status.HTTP_400_BAD_REQUEST)

        membership.status_id = MembershipStatus.CANCELLED
        membership.auto_renew = False
        membership.cancelled_at = timezone.now()
        membership.save(update_fields=['status', 'auto_renew', 'cancelled_at'])

        return Response({
            'detail': 'Membresía cancelada. Mantendrás el acceso hasta el fin del período pagado.',
            'access_until': membership.expires_at,
        })
