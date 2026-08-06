from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import LessonProgress, Certificate, StudyStreak, Enrollment
from .achievements import evaluate_achievements

# Umbral de progreso que activa el trigger de interacción en recomendaciones
ENGAGEMENT_TRIGGER_THRESHOLD = 20.0


@receiver(post_save, sender=LessonProgress)
def handle_lesson_completion(sender, instance, **kwargs):
    """
    Signal que se activa cada vez que se actualiza el progreso de una lección.
    1. Recalcula el progreso total del Enrollment.
    2. Si el progreso supera el 20%, registra una interacción tipo REVIEW
       en el sistema de recomendaciones (el alumno está comprometido con el curso).
    3. Si el curso llega al 100%, emite el certificado (simulado) del alumno.
    """
    enrollment = instance.enrollment

    # Marcar timestamp de completado si el alumno terminó la lección
    if instance.is_completed and not instance.completed_at:
        LessonProgress.objects.filter(pk=instance.pk).update(
            completed_at=timezone.now()
        )

    # Recalcular el progreso del curso completo
    new_progress = enrollment.recalculate_progress()

    # Trigger al 20%: registrar señal de compromiso en el motor de recomendaciones
    _trigger_engagement_interaction_if_needed(enrollment, new_progress)

    # Trigger al 100%: emitir certificado
    if enrollment.is_completed:
        _issue_certificate_if_needed(enrollment)

    # Actualizar la racha de estudio del usuario cuando completa una lección
    if instance.is_completed:
        _update_study_streak(enrollment.user)

    # Revisar medallas (curso completado, rachas, etc.) — idempotente y a prueba de fallos
    evaluate_achievements(enrollment.user)


def _trigger_engagement_interaction_if_needed(enrollment, progress_percentage):
    """
    Registra una interacción de tipo REVIEW en el sistema de recomendaciones
    cuando el alumno alcanza el umbral del 20% de progreso en el curso.
    Esto indica que el alumno está activamente comprometido con el contenido.
    """
    if progress_percentage < ENGAGEMENT_TRIGGER_THRESHOLD:
        return

    # Evitar registrar la interacción más de una vez (idempotente)
    try:
        from apps.recommendations.models import UserCourseInteraction

        interaction, created = UserCourseInteraction.objects.get_or_create(
            user=enrollment.user,
            course=enrollment.course,
            interaction_type_id='REVIEW'
        )

        if created:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Trigger al {ENGAGEMENT_TRIGGER_THRESHOLD}%: Interacción REVIEW registrada "
                f"para {enrollment.user.email} en {enrollment.course.title}"
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error al registrar interacción de engagement: {e}")


def _issue_certificate_if_needed(enrollment):
    """
    Crea el Certificate del enrollment si aún no existe (idempotente vía get_or_create).
    Requisitos: 100% de progreso Y, si el curso tiene examen final activo, haberlo aprobado.
    Al emitir se guarda un snapshot histórico (nombre, título, horas): el certificado
    es un documento y debe conservar los datos de ese momento aunque cambien después.
    """
    if not enrollment.is_completed:
        return

    # Si el curso tiene examen final activo, el certificado exige haberlo aprobado
    from apps.exams.models import Exam, ExamAttempt
    exam = Exam.objects.filter(course=enrollment.course, is_active=True).first()
    if exam and not ExamAttempt.objects.filter(enrollment=enrollment, passed=True).exists():
        return

    user = enrollment.user
    course = enrollment.course
    from decimal import Decimal
    total_minutes = sum(course.lessons.values_list('duration_minutes', flat=True))
    Certificate.objects.get_or_create(
        enrollment=enrollment,
        defaults={
            'student_name': user.get_full_name() or user.email,
            'course_title': course.title,
            'course_duration_hours': (Decimal(total_minutes) / Decimal('60')).quantize(Decimal('0.01')),
            'completed_at': timezone.now(),
        }
    )


@receiver(post_save, sender=Enrollment)
def handle_enrollment_created(sender, instance, created, **kwargs):
    """Al inscribirse (compra o membresía) puede ganar la medalla de primera inscripción."""
    if created:
        evaluate_achievements(instance.user)


@receiver(post_save, sender=Certificate)
def handle_certificate_issued(sender, instance, created, **kwargs):
    """Al emitirse un certificado puede ganar la medalla correspondiente."""
    if created:
        evaluate_achievements(instance.enrollment.user)


def _connect_cross_app_achievement_signals():
    """
    Medallas que dependen de modelos de otras apps (examen aprobado, primera
    reseña). Se conectan aquí para mantener toda la gamificación en library.
    """
    from apps.exams.models import ExamAttempt
    from apps.catalog.models import Review

    @receiver(post_save, sender=ExamAttempt, weak=False)
    def _on_exam_attempt(sender, instance, **kwargs):
        if instance.passed:
            evaluate_achievements(instance.enrollment.user)

    @receiver(post_save, sender=Review, weak=False)
    def _on_review(sender, instance, created, **kwargs):
        if created:
            evaluate_achievements(instance.user)


_connect_cross_app_achievement_signals()


def _update_study_streak(user):
    """
    Actualiza la racha de días consecutivos de estudio del usuario.
    - Misma fecha que la última actividad: no cambia nada (ya contabilizado hoy).
    - Día siguiente consecutivo: incrementa la racha.
    - Cualquier otro caso (brecha o primera actividad): reinicia la racha en 1.
    """
    today = timezone.localdate()
    streak, _ = StudyStreak.objects.get_or_create(user=user)

    if streak.last_activity_date == today:
        return

    if streak.last_activity_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_activity_date = today
    streak.save(update_fields=['current_streak', 'longest_streak', 'last_activity_date'])
