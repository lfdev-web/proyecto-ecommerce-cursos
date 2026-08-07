"""
Estado de las dos actividades evaluadas de un curso.

Un curso ya no se da por terminado con el 100% de las lecciones: hacen falta
también el cuestionario aprobado (Actividad 1) y el trabajo práctico entregado
(Actividad 2). Esa regla se define UNA sola vez aquí porque la consultan tres
lugares distintos — el serializer de la biblioteca, la vista de actividades y
la señal que emite el certificado — y si cada uno la reimplementara, bastaría
tocar uno para que el certificado y la interfaz dejaran de coincidir.
"""


def estado_actividades(enrollment):
    """
    Devuelve el estado de las actividades del curso de esta inscripción.

    Un curso puede no tener alguna de las dos (los cursos viejos o los que crea
    un docente a mano): lo que no existe no bloquea el certificado.
    """
    from apps.catalog.models import Assignment
    from apps.exams.models import Exam
    from .models import AssignmentSubmission

    course = enrollment.course

    exam = Exam.objects.filter(course=course, is_active=True).first()
    quiz_passed = bool(
        exam and enrollment.exam_attempts.filter(passed=True).exists()
    )

    assignment = Assignment.objects.filter(course=course, is_active=True).first()
    submission = None
    if assignment:
        submission = AssignmentSubmission.objects.filter(enrollment=enrollment).first()

    lecciones_ok = enrollment.progress_percentage >= 100.0

    return {
        'lessons': {
            'done': lecciones_ok,
            'progress_percentage': enrollment.progress_percentage,
        },
        'quiz': {
            'exists': exam is not None,
            'exam_id': exam.id if exam else None,
            'title': exam.title if exam else '',
            'passing_score': exam.passing_score if exam else None,
            'done': quiz_passed,
            # Solo se habilita después de ver todas las lecciones (lo valida
            # también el backend en StartAttemptView).
            'unlocked': lecciones_ok,
        },
        'assignment': {
            'exists': assignment is not None,
            'assignment_id': assignment.id if assignment else None,
            'title': assignment.title if assignment else '',
            'instructions': assignment.instructions if assignment else '',
            'resource_label': assignment.resource_label if assignment else '',
            'resource_url': assignment.resource_url if assignment else '',
            'done': submission is not None,
            'unlocked': lecciones_ok,
            'submitted_at': submission.submitted_at if submission else None,
            'file_url': (
                submission.file.url if submission and submission.file else None
            ),
            'comment': submission.comment if submission else '',
            'is_auto': submission.is_auto if submission else False,
        },
    }


def curso_terminado(enrollment, estado=None):
    """
    ¿Puede emitirse el certificado? Las lecciones al 100% y las actividades que
    el curso realmente tenga, completadas.
    """
    estado = estado or estado_actividades(enrollment)
    if not estado['lessons']['done']:
        return False
    if estado['quiz']['exists'] and not estado['quiz']['done']:
        return False
    if estado['assignment']['exists'] and not estado['assignment']['done']:
        return False
    return True
