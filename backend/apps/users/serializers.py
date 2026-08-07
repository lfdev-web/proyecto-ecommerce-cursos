from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    RECHARGE_MAX, RECHARGE_MIN, TeacherApplication, WalletRecharge, WalletTransaction,
)

User = get_user_model()

# Topes de la foto de perfil. Pillow ya garantiza que el archivo sea una imagen
# real (no se puede subir un .php renombrado), pero sin límite de tamaño un
# usuario podía subir imágenes de 50 MB repetidamente hasta llenar el disco.
AVATAR_MAX_BYTES = 2 * 1024 * 1024   # 2 MB
AVATAR_MAX_LADO = 2000               # píxeles


class CustomUserSerializer(serializers.ModelSerializer):
    # El avatar se escribe como archivo (multipart) pero se lee como URL RELATIVA
    # (/media/...): así funciona igual detrás del proxy de Vite en dev y de nginx
    # en producción, sin depender del header Host que reescribe el proxy.
    avatar = serializers.ImageField(write_only=True, required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'role', 'avatar', 'avatar_url',
            'bio', 'phone', 'is_email_verified', 'balance', 'referral_code',
            'can_autocomplete_demo',
        )
        read_only_fields = (
            'id', 'role', 'is_email_verified', 'balance', 'referral_code',
            # Solo de lectura: si fuera escribible, cualquiera podría darse
            # permiso para certificarse sin hacer los cursos.
            'can_autocomplete_demo',
        )

    def get_avatar_url(self, obj):
        return obj.avatar.url if obj.avatar else None

    def validate_avatar(self, imagen):
        if imagen is None:
            return imagen
        if imagen.size > AVATAR_MAX_BYTES:
            mb = imagen.size / (1024 * 1024)
            raise serializers.ValidationError(
                f'La imagen pesa {mb:.1f} MB. El máximo permitido es 2 MB.'
            )
        # image.width/height los expone DRF tras validar el archivo con Pillow
        ancho, alto = getattr(imagen, 'image', imagen).size
        if ancho > AVATAR_MAX_LADO or alto > AVATAR_MAX_LADO:
            raise serializers.ValidationError(
                f'La imagen mide {ancho}x{alto} px. El máximo permitido es '
                f'{AVATAR_MAX_LADO}x{AVATAR_MAX_LADO} px.'
            )
        return imagen


class WalletTransactionSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source='transaction_type.name', read_only=True)

    class Meta:
        model = WalletTransaction
        fields = ('id', 'transaction_type', 'type_name', 'amount', 'balance_after', 'description', 'created_at')


class RechargeStartSerializer(serializers.Serializer):
    """Paso 1: solo el monto. Los datos de la tarjeta llegan en la pasarela."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_amount(self, value):
        if value < RECHARGE_MIN or value > RECHARGE_MAX:
            raise serializers.ValidationError(
                f'El monto debe estar entre ${RECHARGE_MIN} y ${RECHARGE_MAX}.'
            )
        return value


class RechargeAuthorizeSerializer(serializers.Serializer):
    """
    Paso 2: datos de la tarjeta en la pantalla de la pasarela.

    Aquí NO se pide el monto: se lee de la intención guardada en la base. Si
    el monto viajara desde el navegador, cualquiera podría iniciar una recarga
    de $5 y autorizar $5000 modificando la petición.
    """
    card_number = serializers.CharField(max_length=19, write_only=True)
    card_holder = serializers.CharField(max_length=100, write_only=True)
    expiry_date = serializers.CharField(max_length=5, write_only=True)
    cvv = serializers.CharField(max_length=4, write_only=True)

    def validate_expiry_date(self, value):
        import re
        if not re.fullmatch(r'(0[1-9]|1[0-2])/\d{2}', value or ''):
            raise serializers.ValidationError('Usa el formato MM/AA (por ejemplo 12/28).')
        return value

    def validate_cvv(self, value):
        if not (value or '').isdigit() or not 3 <= len(value) <= 4:
            raise serializers.ValidationError('El CVV debe tener 3 o 4 dígitos.')
        return value


class WalletRechargeSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = WalletRecharge
        fields = (
            'token', 'amount', 'status', 'status_name', 'card_last4',
            'decline_reason', 'reference', 'created_at', 'completed_at',
        )
        read_only_fields = fields

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'referral_code')

    def create(self, validated_data):
        from django.db import transaction
        from .models import (
            REFERRAL_BONUS, INITIAL_WALLET_BALANCE,
            WalletTransactionType, record_wallet_transaction,
        )

        referral_code = validated_data.pop('referral_code', '') or ''
        referrer = User.objects.filter(referral_code__iexact=referral_code).first() if referral_code else None

        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', '')
            )
            record_wallet_transaction(
                user, WalletTransactionType.WELCOME, INITIAL_WALLET_BALANCE,
                description='Saldo simulado de bienvenida'
            )
            if referrer:
                user.referred_by = referrer
                user.balance += REFERRAL_BONUS
                user.save(update_fields=['referred_by', 'balance'])
                record_wallet_transaction(
                    user, WalletTransactionType.REFERRAL_BONUS, REFERRAL_BONUS,
                    description=f'Bono por registrarte con el código de {referrer.email}'
                )
                referrer.balance += REFERRAL_BONUS
                referrer.save(update_fields=['balance'])
                record_wallet_transaction(
                    referrer, WalletTransactionType.REFERRAL_BONUS, REFERRAL_BONUS,
                    description=f'Bono por referir a {user.email}'
                )

        return user

class TeacherApplicationSerializer(serializers.ModelSerializer):
    """
    Solicitud para ser docente. En creación solo se aceptan los campos que
    escribe el postulante; el estado, la revisión y el motivo de rechazo son
    de solo lectura (los gestiona el administrador desde el admin).
    """
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = TeacherApplication
        fields = (
            'id', 'headline', 'bio', 'id_document', 'credentials_document',
            'status', 'status_name', 'rejection_reason', 'created_at', 'reviewed_at',
        )
        read_only_fields = (
            'id', 'status', 'status_name', 'rejection_reason', 'created_at', 'reviewed_at',
        )

    def validate_id_document(self, value):
        # La cédula es obligatoria (los certificados son opcionales)
        if not value:
            raise serializers.ValidationError('La cédula es obligatoria.')
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Registrar IP de acceso
        request = self.context.get('request')
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            self.user.last_login_ip = ip
            self.user.save(update_fields=['last_login_ip'])

        # Add custom claims
        data['role'] = self.user.role_id
        data['email'] = self.user.email
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Solo pide el correo. La respuesta es la misma exista o no (ver la vista)."""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Datos del enlace del correo más la contraseña nueva.

    uid y token viajan en la URL que se le manda al usuario; aquí llegan en el
    cuerpo porque el frontend es una SPA y los lee de su propia ruta.
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value):
        # Las mismas reglas que en el registro: sin esto se podría usar el
        # enlace de recuperación para poner una contraseña que el formulario
        # de registro habría rechazado.
        validate_password(value)
        return value
