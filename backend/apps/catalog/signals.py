from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review
from .tasks import update_best_seller_status

@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def trigger_buy_box_update(sender, instance, **kwargs):
    """
    Cuando se crea, actualiza o elimina una reseña, se dispara de forma
    asíncrona el recálculo del Buy Box (is_best_seller) mediante Celery.
    """
    # Enviar la tarea a Celery de forma asíncrona para no bloquear la request HTTP
    update_best_seller_status.delay(instance.course.id)
