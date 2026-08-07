import secrets
import uuid
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

# Saldo simulado inicial que recibe cada usuario nuevo (wallet de demo).
INITIAL_WALLET_BALANCE = Decimal('500.00')
# Bono simulado que reciben referidor y referido cuando un registro usa un código de referido válido.
REFERRAL_BONUS = Decimal('10.00')


def generate_referral_code():
    return secrets.token_hex(4).upper()


class Role(models.Model):
    """
    Tabla catálogo de roles del sistema (lookup table).
    Los roles viven en la BD con FK real desde usuarios, en lugar de
    texto suelto con choices — el dominio puede crecer sin migraciones.
    """
    ADMIN = 'ADMIN'
    DOCENTE = 'DOCENTE'
    ALUMNO = 'ALUMNO'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name


class WalletTransactionType(models.Model):
    """
    Tabla catálogo de tipos de movimiento del saldo simulado (lookup table).
    """
    WELCOME = 'WELCOME'
    PURCHASE = 'PURCHASE'
    MEMBERSHIP = 'MEMBERSHIP'
    REFERRAL_BONUS = 'REFERRAL_BONUS'
    RECHARGE = 'RECHARGE'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Tipo de movimiento de saldo'
        verbose_name_plural = 'Tipos de movimiento de saldo'

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)

    # FK a la tabla catálogo de roles (la columna en la BD sigue llamándose 'role')
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        db_column='role',
        default=Role.ALUMNO,
        related_name='users'
    )

    # Extra fields
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Wallet simulado para checkout (Luhn valida la tarjeta, balance valida fondos).
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=INITIAL_WALLET_BALANCE,
        help_text="Saldo simulado disponible para compras (demo, no es dinero real)."
    )

    # Atajo de demostración: permite dar por completado un curso entero de un
    # clic (lecciones, cuestionario y entrega) para poder mostrar el
    # certificado sin recorrer las 7 lecciones una por una.
    #
    # Es una puerta trasera deliberada y por eso está apagada por defecto y
    # atada al usuario, no al entorno: quien la tenga solo puede completar SUS
    # propias inscripciones. En una plataforma real este campo no existiría.
    can_autocomplete_demo = models.BooleanField(
        default=False,
        verbose_name='Puede completar cursos de un clic (demo)',
        help_text='Solo para la cuenta de revisión. Salta las actividades del curso.'
    )

    # Programa de referidos: cada usuario tiene un código único para compartir.
    referral_code = models.CharField(max_length=12, unique=True, default=generate_referral_code, editable=False)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class WalletTransaction(models.Model):
    """
    Libro mayor (ledger) del saldo simulado: cada cambio del balance queda
    registrado con su tipo, monto con signo y saldo resultante, para que
    el wallet tenga historial auditable en lugar de un número mutable.
    """
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='wallet_transactions'
    )
    transaction_type = models.ForeignKey(
        WalletTransactionType,
        on_delete=models.PROTECT,
        db_column='transaction_type',
        related_name='+'
    )
    # Positivo = ingreso (bono), negativo = egreso (compra)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.user.email} — {self.transaction_type_id} — {sign}{self.amount} (saldo: {self.balance_after})"


def record_wallet_transaction(user, transaction_type_code, amount, description=''):
    """
    Registra un movimiento en el libro mayor del saldo simulado.
    Debe llamarse DESPUÉS de actualizar user.balance, dentro de la misma
    transacción atómica, para que balance_after refleje el saldo real resultante.
    """
    return WalletTransaction.objects.create(
        user=user,
        transaction_type_id=transaction_type_code,
        amount=amount,
        balance_after=user.balance,
        description=description,
    )


# Límites de una recarga individual. No hay tope de saldo acumulado.
RECHARGE_MIN = Decimal('5.00')
RECHARGE_MAX = Decimal('500.00')


class RechargeStatus(models.Model):
    """
    Tabla catálogo de estados de una recarga (lookup table).
    """
    PENDING = 'PENDING'      # creada, esperando que el usuario autorice en la pasarela
    APPROVED = 'APPROVED'    # autorizada y acreditada al saldo
    DECLINED = 'DECLINED'    # la pasarela la rechazó (tarjeta de prueba que falla)
    CANCELLED = 'CANCELLED'  # el usuario canceló en la pasarela
    EXPIRED = 'EXPIRED'      # pasaron más de 15 minutos sin autorizar

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Estado de recarga'
        verbose_name_plural = 'Estados de recarga'

    def __str__(self):
        return self.name


class WalletRecharge(models.Model):
    """
    Intento de recarga del saldo simulado a través de la pasarela de pago.

    Existe como registro propio (en vez de acreditar el saldo directamente)
    porque el flujo tiene dos pasos separados en el tiempo: primero se crea la
    intención con el monto, después el usuario autoriza en la pantalla de la
    pasarela. Guardar el estado permite que:

      - el monto NO viaje desde el navegador al confirmar (se lee de aquí),
        así nadie puede pedir $50 y acreditarse $5000;
      - una autorización reenviada no acredite dos veces (idempotencia);
      - quede historial de los intentos fallidos, no solo de los exitosos.

    El número de tarjeta nunca se guarda: solo los 4 últimos dígitos.
    """
    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE, related_name='recharges'
    )
    # Identificador público que viaja en la URL de la pasarela. UUID para que
    # no se pueda adivinar el de otro usuario probando números consecutivos.
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.ForeignKey(
        RechargeStatus, on_delete=models.PROTECT, db_column='status', related_name='+'
    )
    card_last4 = models.CharField(max_length=4, blank=True, default='')
    # Motivo del rechazo devuelto por la pasarela simulada
    decline_reason = models.CharField(max_length=120, blank=True, default='')
    reference = models.CharField(max_length=40, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recarga de saldo'
        verbose_name_plural = 'Recargas de saldo'
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f'{self.user.email} — ${self.amount} [{self.status_id}]'

    @property
    def is_expired(self):
        """Una intención sin autorizar caduca a los 15 minutos."""
        return (timezone.now() - self.created_at) > timedelta(minutes=15)


class TeacherApplicationStatus(models.Model):
    """
    Tabla catálogo de estados de una solicitud para ser docente (lookup table).
    """
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Estado de solicitud de docente'
        verbose_name_plural = 'Estados de solicitud de docente'

    def __str__(self):
        return self.name


class TeacherApplication(models.Model):
    """
    Solicitud de un usuario (ALUMNO) para convertirse en docente.
    Flujo tipo marketplace (Udemy): el usuario aplica con sus datos y documentos,
    la solicitud queda PENDING y un administrador la revisa en el admin. Al aprobar,
    una señal (signals.py) cambia el rol del usuario a DOCENTE de forma automática.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_applications',
    )
    status = models.ForeignKey(
        TeacherApplicationStatus,
        on_delete=models.PROTECT,
        db_column='status',
        default=TeacherApplicationStatus.PENDING,
        related_name='+',
    )
    # Datos que escribe el postulante
    headline = models.CharField(max_length=150, help_text='Especialidad o titular profesional')
    bio = models.TextField(help_text='Experiencia y motivación para enseñar')
    # Documentos: la cédula es obligatoria; los certificados son opcionales
    id_document = models.FileField(upload_to='teacher_applications/id/')
    credentials_document = models.FileField(
        upload_to='teacher_applications/credentials/', blank=True, null=True
    )
    # Auditoría de la revisión del administrador
    rejection_reason = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_teacher_applications',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de docente'
        verbose_name_plural = 'Solicitudes de docente'
        constraints = [
            # Un usuario no puede tener dos solicitudes PENDING a la vez
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status='PENDING'),
                name='uq_one_pending_application_per_user',
            ),
        ]

    def __str__(self):
        return f'{self.user.email} — {self.status_id}'
