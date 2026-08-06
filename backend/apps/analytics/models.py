from django.db import models
from django.conf import settings
from django.utils import timezone


class NavigationLog(models.Model):
    """
    Registra cada evento de navegación del usuario en la plataforma.
    Funciona tanto para usuarios autenticados como anónimos (via session_id).
    Los datos son insumo para el ConversionFunnel y el análisis de KPIs.
    """
    class EventType(models.TextChoices):
        COURSE_VIEW = 'COURSE_VIEW', 'Vista de Curso'
        CATEGORY_VIEW = 'CATEGORY_VIEW', 'Vista de Categoría'
        SEARCH = 'SEARCH', 'Búsqueda'
        CART_ADD = 'CART_ADD', 'Agregado al Carrito'
        CART_REMOVE = 'CART_REMOVE', 'Eliminado del Carrito'
        CHECKOUT_START = 'CHECKOUT_START', 'Inicio de Checkout'
        PURCHASE = 'PURCHASE', 'Compra Completada'
        WISHLIST_ADD = 'WISHLIST_ADD', 'Agregado a Lista de Deseos'
        VIDEO_PLAY = 'VIDEO_PLAY', 'Video Reproducido'
        VIDEO_PAUSE = 'VIDEO_PAUSE', 'Video Pausado'

    # Usuario autenticado (NULL si es anónimo)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='navigation_logs'
    )
    # Identificador de sesión para usuarios anónimos
    session_id = models.CharField(max_length=255, blank=True, db_index=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    # Datos contextuales del evento (course_id, search_term, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        who = self.user.email if self.user else f"anon:{self.session_id[:8]}"
        return f"{self.event_type} — {who} — {self.timestamp}"


class ConversionFunnel(models.Model):
    """
    Agrega los eventos de navegación en etapas del funnel de conversión.
    Permite calcular la tasa de conversión entre cada etapa:
    VIEW → CART → CHECKOUT → PURCHASE
    """
    class FunnelStage(models.TextChoices):
        VIEW = 'VIEW', 'Vista de Producto'
        CART = 'CART', 'Carrito'
        CHECKOUT = 'CHECKOUT', 'Checkout Iniciado'
        PURCHASE = 'PURCHASE', 'Compra Completada'

    session_id = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='funnel_entries'
    )
    stage = models.CharField(max_length=15, choices=FunnelStage.choices)
    # ID del curso involucrado en este paso del funnel
    course_id = models.IntegerField(null=True, blank=True)
    reached_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-reached_at']
        indexes = [
            models.Index(fields=['session_id', 'stage']),
            # El dashboard cuenta sesiones por etapa dentro de una ventana de fechas.
            models.Index(fields=['stage', 'reached_at']),
        ]

    def __str__(self):
        return f"Funnel [{self.stage}] — session:{self.session_id[:8]} — {self.reached_at}"
