from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(queue='default')
def update_best_seller_status(course_id):
    """
    Tarea asíncrona que recalcula si un curso merece el 'Buy Box' (is_best_seller).
    Se activa mediante un signal cada vez que el curso recibe una nueva Review
    o un nuevo pedido (se integrará con la app orders más adelante).
    """
    from .models import Course
    try:
        course = Course.objects.get(id=course_id)
        
        # Lógica dummy inicial para el Buy Box (luego se ampliará)
        # Ejemplo: Si tiene más de 5 reviews y el rating promedio es mayor a 4.5
        reviews = course.reviews.all()
        if reviews.count() >= 5:
            avg_rating = sum(r.rating for r in reviews) / reviews.count()
            course.is_best_seller = avg_rating >= 4.5
        else:
            course.is_best_seller = False
            
        course.save(update_fields=['is_best_seller'])
        logger.info(f"Updated Buy Box for course {course_id}. is_best_seller={course.is_best_seller}")
        
    except Course.DoesNotExist:
        logger.warning(f"Course {course_id} does not exist for best seller update.")
