"""
Atajo de recorrido rápido para la cuenta de revisión.

Completar un curso a mano son siete lecciones, un cuestionario y una entrega.
Eso está bien para el alumno, pero quien viene a revisar la plataforma necesita
ver el certificado y el correo, no repetir el trámite treinta veces.

Este módulo hace ese recorrido de una vez, y lo hace generando los MISMOS
registros que generaría el alumno: progreso por lección, un intento de examen
con sus respuestas marcadas y una entrega. No se falsifica el certificado ni se
saltan las validaciones — se cumplen los requisitos de verdad y el certificado
lo emite la señal de siempre.

Solo lo puede usar quien tenga `CustomUser.can_autocomplete_demo`, y solo sobre
sus propias inscripciones.
"""
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Assignment
from apps.exams.models import AttemptAnswer, Exam, ExamAttempt

from .actividades import estado_actividades
from .models import AssignmentSubmission, Certificate, LessonProgress
from .signals import _issue_certificate_if_needed

COMENTARIO_AUTO = (
    'Entrega generada por el atajo de demostración de la plataforma. '
    'No corresponde a un trabajo real del alumno.'
)


def _completar_lecciones(enrollment):
    """Marca como vistas todas las lecciones que falten."""
    hechas = set(
        LessonProgress.objects
        .filter(enrollment=enrollment, is_completed=True)
        .values_list('lesson_id', flat=True)
    )
    creadas = 0
    for lesson in enrollment.course.lessons.order_by('order'):
        if lesson.id in hechas:
            continue
        progreso, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment, lesson=lesson,
            defaults={'is_completed': True, 'watch_percentage': 100.0},
        )
        if not progreso.is_completed:
            progreso.is_completed = True
            progreso.watch_percentage = 100.0
        # save() siempre: dispara la señal que recalcula el progreso del curso.
        progreso.save()
        creadas += 1
    return creadas


def _aprobar_cuestionario(enrollment):
    """
    Crea un intento aprobado marcando la opción correcta de cada pregunta.

    Se guardan las respuestas una por una en lugar de escribir score=100 a
    secas: así el intento se puede abrir en el admin y se ve coherente, con la
    misma forma que tendría el de un alumno que respondió bien.
    """
    exam = Exam.objects.filter(course=enrollment.course, is_active=True).first()
    if not exam:
        return False
    if ExamAttempt.objects.filter(enrollment=enrollment, passed=True).exists():
        return False

    # Cerrar cualquier intento a medias para no romper el unique de la app
    ExamAttempt.objects.filter(enrollment=enrollment, submitted_at=None).update(
        submitted_at=timezone.now(), score=0, passed=False
    )

    intento = ExamAttempt.objects.create(
        enrollment=enrollment,
        attempt_number=ExamAttempt.objects.filter(enrollment=enrollment).count() + 1,
    )
    respuestas = []
    for pregunta in exam.questions.prefetch_related('options').all():
        correcta = next((o for o in pregunta.options.all() if o.is_correct), None)
        respuestas.append(AttemptAnswer(
            attempt=intento, question=pregunta,
            selected_option=correcta, is_correct=correcta is not None,
        ))
    AttemptAnswer.objects.bulk_create(respuestas)

    intento.submitted_at = timezone.now()
    intento.score = 100
    intento.passed = True
    intento.save(update_fields=['submitted_at', 'score', 'passed'])
    return True


def _entregar_trabajo(enrollment):
    """Registra la entrega del trabajo práctico, marcada como automática."""
    assignment = Assignment.objects.filter(course=enrollment.course, is_active=True).first()
    if not assignment:
        return False
    _, creada = AssignmentSubmission.objects.get_or_create(
        enrollment=enrollment,
        defaults={'assignment': assignment, 'comment': COMENTARIO_AUTO, 'is_auto': True},
    )
    return creada


@transaction.atomic
def completar_inscripcion(enrollment):
    """
    Deja una inscripción lista para certificarse y devuelve qué hizo.

    El certificado NO se crea aquí: se pide la emisión por el camino normal
    (_issue_certificate_if_needed), que vuelve a comprobar los requisitos. Si
    algún día se agrega una tercera actividad, este atajo se quedará corto y el
    certificado no saldrá — que es exactamente lo que debe pasar.
    """
    lecciones = _completar_lecciones(enrollment)
    cuestionario = _aprobar_cuestionario(enrollment)
    entrega = _entregar_trabajo(enrollment)

    enrollment.refresh_from_db()
    _issue_certificate_if_needed(enrollment)
    enrollment.refresh_from_db()

    return {
        'enrollment_id': enrollment.id,
        'course': enrollment.course.title,
        'lecciones_completadas': lecciones,
        'cuestionario_aprobado': cuestionario,
        'trabajo_entregado': entrega,
        'certificado': Certificate.objects.filter(enrollment=enrollment).exists(),
        'actividades': estado_actividades(enrollment),
    }
