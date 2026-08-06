from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class BillingCycle(models.Model):
    """
    Tabla catálogo de ciclos de facturación (lookup table).
    """
    MONTHLY = 'MONTHLY'
    ANNUAL = 'ANNUAL'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ciclo de facturación'
        verbose_name_plural = 'Ciclos de facturación'

    def __str__(self):
        return self.name


class MembershipStatus(models.Model):
    """
    Tabla catálogo de estados de una membresía (lookup table).
    """
    ACTIVE = 'ACTIVE'
    CANCELLED = 'CANCELLED'
    EXPIRED = 'EXPIRED'
    PENDING = 'PENDING'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Estado de membresía'
        verbose_name_plural = 'Estados de membresía'

    def __str__(self):
        return self.name


class PlanAudience(models.Model):
    """
    Tabla catálogo del público al que aplica un plan (lookup table).
    Las membresías se dividen en dos familias porque los beneficios no se parecen:
    el alumno compra descuento, el docente compra capacidad de publicar.
    """
    ALUMNO = 'ALUMNO'
    DOCENTE = 'DOCENTE'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Público del plan'
        verbose_name_plural = 'Públicos de plan'

    def __str__(self):
        return self.name


class PlanTier(models.Model):
    """
    Tabla catálogo de niveles de plan (lookup table): Bronce, Plata, Oro, VIP.
    El campo rank ordena los niveles de menor a mayor.
    """
    BRONCE = 'BRONCE'
    PLATA = 'PLATA'
    ORO = 'ORO'
    VIP = 'VIP'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    rank = models.PositiveIntegerField(default=0, help_text='Orden del nivel (mayor = mejor)')
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['rank']
        verbose_name = 'Nivel de plan'
        verbose_name_plural = 'Niveles de plan'

    def __str__(self):
        return self.name


class MembershipPlan(models.Model):
    """
    Define los planes de membresía disponibles en la plataforma.
    El campo discount_pct permite ofrecer un descuento sobre el precio
    mensual cuando el usuario elige el ciclo anual.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    billing_cycle = models.ForeignKey(
        BillingCycle,
        on_delete=models.PROTECT,
        db_column='billing_cycle',
        default=BillingCycle.MONTHLY,
        related_name='+'
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)
    # Porcentaje de descuento aplicado (ej: 20 = 20% de descuento)
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Porcentaje de descuento vs. precio mensual equivalente (0-100)"
    )
    is_active = models.BooleanField(default=True)
    # Número de cursos accesibles por mes con esta membresía (0 = ilimitado)
    courses_limit = models.PositiveIntegerField(
        default=0,
        help_text="0 = acceso ilimitado"
    )
    # Beneficio real de la membresía: descuento que obtiene el miembro en TODAS
    # las compras de cursos mientras la suscripción esté activa (modelo "club").
    member_discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Descuento (%) aplicado a todas las compras de cursos del miembro activo (0-100)"
    )

    # --- Familia y nivel del plan ---
    audience = models.ForeignKey(
        PlanAudience,
        on_delete=models.PROTECT,
        db_column='audience',
        default=PlanAudience.ALUMNO,
        related_name='plans',
    )
    tier = models.ForeignKey(
        PlanTier,
        on_delete=models.PROTECT,
        db_column='tier',
        default=PlanTier.BRONCE,
        related_name='plans',
    )

    # --- Beneficios exclusivos de los planes de DOCENTE ---
    course_slots = models.PositiveIntegerField(
        default=0,
        help_text="Cupos de curso incluidos en el plan (solo planes de docente). 0 = ninguno"
    )
    instructor_commission_pct = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.70'),
        help_text="Porcentaje de cada venta que se lleva el docente con este plan (ej. 0.80 = 80%)"
    )

    def __str__(self):
        discount_label = f" ({self.discount_pct}% off)" if self.discount_pct else ""
        return f"{self.name} — {self.billing_cycle_id}{discount_label} — ${self.price}"


class UserMembership(models.Model):
    """
    Representa la membresía activa de un usuario.
    La propiedad is_currently_active verifica en tiempo real si la membresía
    no ha expirado, evitando depender de un campo booleano que podría
    quedar desactualizado si falla algún job de expiración.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    # Familia del plan, denormalizada para poder exigir "una membresía por familia":
    # un docente puede tener a la vez su plan de docente y su membresía de alumno.
    audience = models.ForeignKey(
        PlanAudience,
        on_delete=models.PROTECT,
        db_column='audience',
        default=PlanAudience.ALUMNO,
        related_name='memberships',
    )
    status = models.ForeignKey(
        MembershipStatus,
        on_delete=models.PROTECT,
        db_column='status',
        default=MembershipStatus.PENDING,
        related_name='+'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)

    class Meta:
        # Una membresía por familia: como máximo un plan de alumno y uno de docente.
        unique_together = ('user', 'audience')

    @property
    def is_currently_active(self) -> bool:
        """
        Verifica en tiempo real si la membresía sigue vigente.
        Se compara contra timezone.now() para respetar el huso horario
        configurado (America/Guayaquil, UTC-5).
        """
        return (
            self.status_id == MembershipStatus.ACTIVE and
            self.expires_at > timezone.now()
        )

    def __str__(self):
        active = "✓ ACTIVA" if self.is_currently_active else "✗ INACTIVA"
        return f"{self.user.email} — {self.plan.name} [{active}]"


class MembershipPayment(models.Model):
    """
    Historial de pagos asociados a una membresía.
    El PAN nunca se almacena completo — solo los últimos 4 dígitos
    para mostrar al usuario qué tarjeta usó (cumplimiento PCI-DSS).
    """
    membership = models.ForeignKey(
        UserMembership,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    # Solo se almacenan los últimos 4 dígitos (PCI-DSS compliance)
    card_last4 = models.CharField(max_length=4)
    paid_at = models.DateTimeField(auto_now_add=True)
    # Referencia de transacción de la pasarela de pago (Stripe/Kushki token ID)
    transaction_reference = models.CharField(max_length=200, blank=True)
    is_successful = models.BooleanField(default=False)

    def __str__(self):
        status = "OK" if self.is_successful else "FAILED"
        return f"Pago {status} — {self.membership.user.email} — ${self.amount}"
