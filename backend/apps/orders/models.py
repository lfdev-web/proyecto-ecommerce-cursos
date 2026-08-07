from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.catalog.models import Course

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

    def get_total_price(self):
        # effective_price respeta la promoción vigente: si el curso está en
        # oferta, el carrito muestra el precio rebajado, no el de lista.
        return sum(item.course.effective_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'course') # Un mismo curso no puede estar dos veces en el carrito

    def __str__(self):
        return f"{self.course.title} in {self.cart}"

class OrderStatus(models.Model):
    """
    Tabla catálogo de estados de una orden (lookup table).
    """
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Estado de orden'
        verbose_name_plural = 'Estados de orden'

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    # FK a la tabla catálogo de estados (la columna en la BD sigue llamándose 'status')
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        db_column='status',
        default=OrderStatus.PENDING,
        related_name='+'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Auditoría del pago simulado (mismo criterio que MembershipPayment)
    coupon = models.ForeignKey(
        'orders.Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    # Solo los últimos 4 dígitos (PCI-DSS compliance)
    card_last4 = models.CharField(max_length=4, blank=True, default='')
    transaction_reference = models.CharField(max_length=200, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # El dashboard suma ingresos/órdenes por estado dentro de una ventana de fechas.
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Order {self.id} by {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey(Course, on_delete=models.PROTECT) # Evitar borrar cursos que han sido comprados
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.course.title} in Order {self.order.id}"


class InstructorEarning(models.Model):
    """
    Ingreso del docente por cada venta de uno de sus cursos (comisión estilo
    Udemy: 70% instructor / 30% plataforma). Se genera en el checkout y es el
    insumo del panel Docente. El monto queda congelado con la tasa del momento.
    """
    INSTRUCTOR_RATE = Decimal('0.70')

    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='earning')
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earnings'
    )
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='earnings')
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=4, decimal_places=2, default=INSTRUCTOR_RATE)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # El panel docente suma ingresos por instructor dentro de una ventana de fechas.
            models.Index(fields=['instructor', 'created_at']),
        ]

    @classmethod
    def get_commission_rate_for(cls, instructor):
        """
        La comisión del docente depende de su plan: los niveles altos se llevan
        un porcentaje mayor de cada venta. Sin plan activo se usa la tasa base.
        """
        from apps.memberships.models import PlanAudience, UserMembership

        membership = (
            UserMembership.objects
            .filter(user=instructor, audience_id=PlanAudience.DOCENTE)
            .select_related('plan')
            .first()
        )
        if membership and membership.is_currently_active:
            return membership.plan.instructor_commission_pct
        return cls.INSTRUCTOR_RATE

    @classmethod
    def create_for_order_item(cls, order_item):
        """Crea el ingreso si el curso tiene instructor asignado (si no, no hay a quién pagar)."""
        instructor = order_item.course.instructor
        if instructor is None:
            return None
        gross = order_item.price_at_purchase
        rate = cls.get_commission_rate_for(instructor)
        return cls.objects.create(
            order_item=order_item,
            instructor=instructor,
            course=order_item.course,
            gross_amount=gross,
            commission_rate=rate,
            net_amount=(gross * rate).quantize(Decimal('0.01')),
        )

    def __str__(self):
        return f"{self.instructor.email} — {self.course.title} — ${self.net_amount}"


class Coupon(models.Model):
    """
    Código de descuento aplicable en el checkout de cursos.
    """
    code = models.CharField(max_length=30, unique=True)
    discount_pct = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Porcentaje de descuento sobre el total (0-100)"
    )
    is_active = models.BooleanField(default=True)
    valid_until = models.DateTimeField(null=True, blank=True, help_text="Vacío = sin fecha de expiración")
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = usos ilimitados")
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.valid_until and self.valid_until < timezone.now():
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        return True

    # Nota: el descuento NO se calcula aquí. El checkout elige el mejor porcentaje
    # entre el del cupón y el de la membresía del usuario, así que aplica ese
    # porcentaje ganador sobre el total (apps/orders/views.py). Un método que
    # asumiera siempre self.discount_pct daría un descuento incorrecto.

    def __str__(self):
        return f"{self.code} (-{self.discount_pct}%)"
