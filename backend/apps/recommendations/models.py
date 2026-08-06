from django.db import models
from django.conf import settings
from apps.catalog.models import Course


class InteractionType(models.Model):
    """
    Tabla catálogo de tipos de interacción (lookup table).
    El peso de cada tipo para la matriz de utilidad del modelo SVD vive
    aquí como dato — ajustar la señal del recomendador no requiere deploy.
    """
    VIEW = 'VIEW'
    CART_ADD = 'CART_ADD'
    WISHLIST = 'WISHLIST'
    REVIEW = 'REVIEW'
    PURCHASE = 'PURCHASE'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    # Intensidad de interés que aporta al modelo SVD (comprar pesa más que mirar)
    weight = models.FloatField(default=0.5)

    class Meta:
        verbose_name = 'Tipo de interacción'
        verbose_name_plural = 'Tipos de interacción'

    def __str__(self):
        return f"{self.name} (peso {self.weight})"


class UserCourseInteraction(models.Model):
    """
    Registra las interacciones del usuario con los cursos.
    Los pesos definen la 'intensidad de interés' para el modelo SVD.
    Cuanto mayor el peso, mayor la señal para el sistema de recomendaciones.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_interactions'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='user_interactions'
    )
    interaction_type = models.ForeignKey(
        InteractionType,
        on_delete=models.PROTECT,
        db_column='interaction_type',
        related_name='+'
    )
    weight = models.FloatField(editable=False)  # Se copia desde la tabla catálogo al guardar
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Permitir múltiples tipos de interacción por usuario/curso (ej: VIEW + PURCHASE)
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['interaction_type']),
        ]

    def save(self, *args, **kwargs):
        # Copiar el peso definido en la tabla catálogo antes de guardar
        # (snapshot: si el peso cambia después, las interacciones pasadas no se reescriben)
        self.weight = self.interaction_type.weight
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} — {self.interaction_type_id} — {self.course.title}"


class RecommendationCache(models.Model):
    """
    Almacena los resultados pre-calculados del modelo SVD.
    Se actualiza de forma asíncrona por Celery cada noche para evitar
    recalcular en tiempo real durante las requests del usuario.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations_cache'
    )
    # IDs de cursos recomendados almacenados como JSON (lista ordenada por score)
    recommended_course_ids = models.JSONField(default=list)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendations for {self.user.email} (updated: {self.last_updated})"
