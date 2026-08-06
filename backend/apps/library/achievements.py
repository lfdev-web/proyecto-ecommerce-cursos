"""
Reglas de otorgamiento de medallas (gamificación tipo Duolingo/Platzi).

Cada regla es una función (user) -> bool sobre datos que ya existen en el
sistema: no se guarda estado nuevo aparte de UserAchievement, así la
evaluación es idempotente y puede re-ejecutarse en cualquier momento
(se usa también como auto-reparación al abrir el perfil, lo que cubre a
los usuarios históricos creados por el seed con bulk_create sin señales).
"""
from .models import Achievement, UserAchievement


def _completed_courses(user):
    from .models import Enrollment
    return Enrollment.objects.filter(user=user, is_completed=True).count()


RULES = {
    'FIRST_ENROLLMENT': lambda user: user.enrollments.exists(),
    'FIRST_COURSE': lambda user: _completed_courses(user) >= 1,
    'THREE_COURSES': lambda user: _completed_courses(user) >= 3,
    'FIVE_COURSES': lambda user: _completed_courses(user) >= 5,
    'FIRST_CERTIFICATE': lambda user: _has_certificate(user),
    'EXAM_PASSED': lambda user: _exam_passed(user),
    'PERFECT_EXAM': lambda user: _perfect_exam(user),
    'STREAK_7': lambda user: _longest_streak(user) >= 7,
    'STREAK_30': lambda user: _longest_streak(user) >= 30,
    'FIRST_REVIEW': lambda user: _has_review(user),
}


def _has_certificate(user):
    from .models import Certificate
    return Certificate.objects.filter(enrollment__user=user).exists()


def _exam_passed(user):
    from apps.exams.models import ExamAttempt
    return ExamAttempt.objects.filter(enrollment__user=user, passed=True).exists()


def _perfect_exam(user):
    from apps.exams.models import ExamAttempt
    return ExamAttempt.objects.filter(enrollment__user=user, passed=True, score__gte=100).exists()


def _longest_streak(user):
    from .models import StudyStreak
    streak = StudyStreak.objects.filter(user=user).first()
    return streak.longest_streak if streak else 0


def _has_review(user):
    from apps.catalog.models import Review
    return Review.objects.filter(user=user).exists()


def evaluate_achievements(user):
    """
    Revisa las medallas que el usuario aún no tiene y otorga las que ahora
    cumple. Devuelve la lista de códigos recién otorgados. Idempotente.
    """
    earned = set(
        UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    )
    # Solo se otorgan medallas que existen en el catálogo (por si el admin retira alguna)
    catalog = set(Achievement.objects.values_list('code', flat=True))

    newly_earned = []
    for code, check in RULES.items():
        if code in earned or code not in catalog:
            continue
        try:
            if check(user):
                _, created = UserAchievement.objects.get_or_create(user=user, achievement_id=code)
                if created:
                    newly_earned.append(code)
        except Exception:
            # Una regla rota nunca debe tumbar el flujo que la disparó (progreso, checkout)
            import logging
            logging.getLogger(__name__).exception(f'Error evaluando la medalla {code}')
    return newly_earned
