from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.library.models import Enrollment
from .models import Exam, ExamAttempt, AttemptAnswer
from .serializers import (
    ExamPublicSerializer,
    QuestionPublicSerializer,
    ExamAttemptSummarySerializer,
    SubmitAttemptSerializer,
)


def _get_enrollment_or_403(user, course_id):
    """El examen solo es accesible para alumnos inscritos en el curso."""
    return get_object_or_404(Enrollment, user=user, course_id=course_id)


def _close_expired_attempt(attempt, exam):
    """Cierra un intento abierto cuyo tiempo ya venció (calificación 0)."""
    attempt.submitted_at = timezone.now()
    attempt.score = Decimal('0.00')
    attempt.passed = False
    attempt.save(update_fields=['submitted_at', 'score', 'passed'])


class CourseExamInfoView(APIView):
    """
    GET /api/exams/course/<course_id>/
    Estado del examen final del curso para el alumno: si existe, intentos usados,
    si ya lo aprobó y su mejor puntaje. El frontend decide qué botón mostrar.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        enrollment = _get_enrollment_or_403(request.user, course_id)
        exam = Exam.objects.filter(course_id=course_id, is_active=True).first()
        if not exam:
            return Response({'has_exam': False})

        attempts = ExamAttempt.objects.filter(enrollment=enrollment)
        finished = attempts.exclude(submitted_at=None)
        best = max((a.score for a in finished), default=None)
        attempts_used = finished.count()
        attempts_left = None if exam.max_attempts == 0 else max(exam.max_attempts - attempts_used, 0)

        return Response({
            'has_exam': True,
            'exam': ExamPublicSerializer(exam).data,
            'passed': attempts.filter(passed=True).exists(),
            'best_score': best,
            'attempts_used': attempts_used,
            'attempts_left': attempts_left,
            'attempts': ExamAttemptSummarySerializer(finished, many=True).data,
        })


class StartAttemptView(APIView):
    """
    POST /api/exams/course/<course_id>/start/
    Inicia (o retoma) un intento. Devuelve las preguntas SIN las respuestas
    correctas y los segundos restantes calculados por el servidor.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, course_id):
        enrollment = _get_enrollment_or_403(request.user, course_id)
        exam = Exam.objects.filter(course_id=course_id, is_active=True).first()
        if not exam:
            return Response({'detail': 'Este curso no tiene examen final.'}, status=status.HTTP_404_NOT_FOUND)

        if enrollment.progress_percentage < 100.0:
            return Response(
                {'detail': 'Debes completar el 100% de las lecciones antes de rendir el examen final.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if ExamAttempt.objects.filter(enrollment=enrollment, passed=True).exists():
            return Response({'detail': 'Ya aprobaste este examen.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retomar el intento abierto si sigue dentro del tiempo; cerrarlo si expiró
        open_attempt = ExamAttempt.objects.filter(enrollment=enrollment, submitted_at=None).first()
        if open_attempt:
            if open_attempt.is_expired(exam):
                _close_expired_attempt(open_attempt, exam)
                open_attempt = None
            else:
                return self._attempt_payload(open_attempt, exam)

        finished_count = ExamAttempt.objects.filter(enrollment=enrollment).exclude(submitted_at=None).count()
        if exam.max_attempts and finished_count >= exam.max_attempts:
            return Response(
                {'detail': f'Agotaste los {exam.max_attempts} intentos permitidos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt = ExamAttempt.objects.create(
            enrollment=enrollment,
            attempt_number=ExamAttempt.objects.filter(enrollment=enrollment).count() + 1,
        )
        return self._attempt_payload(attempt, exam)

    def _attempt_payload(self, attempt, exam):
        remaining = (attempt.deadline(exam) - timezone.now()).total_seconds()
        questions = exam.questions.prefetch_related('options').all()
        return Response({
            'attempt_id': attempt.id,
            'attempt_number': attempt.attempt_number,
            'time_remaining_seconds': max(int(remaining), 0),
            'exam': ExamPublicSerializer(exam).data,
            'questions': QuestionPublicSerializer(questions, many=True).data,
        }, status=status.HTTP_201_CREATED)


class SubmitAttemptView(APIView):
    """
    POST /api/exams/attempts/<attempt_id>/submit/
    Body: {"answers": [{"question": <id>, "option": <id|null>}, ...]}
    Califica el intento. El límite de tiempo se valida contra el reloj del
    servidor (started_at + time_limit + gracia); vencido = intento en 0.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            ExamAttempt.objects.select_related('enrollment__course', 'enrollment__user'),
            id=attempt_id,
            enrollment__user=request.user,
        )
        if not attempt.is_open:
            return Response({'detail': 'Este intento ya fue enviado.'}, status=status.HTTP_400_BAD_REQUEST)

        exam = Exam.objects.filter(course=attempt.enrollment.course, is_active=True).first()
        if not exam:
            return Response({'detail': 'El examen ya no está disponible.'}, status=status.HTTP_400_BAD_REQUEST)

        if attempt.is_expired(exam):
            _close_expired_attempt(attempt, exam)
            return Response({
                'detail': 'Tiempo agotado: el intento se cerró con calificación 0.',
                'score': attempt.score,
                'passed': False,
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubmitAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = {a['question']: a.get('option') for a in serializer.validated_data['answers']}

        questions = list(exam.questions.prefetch_related('options').all())
        total_points = sum(q.points for q in questions) or 1
        earned_points = 0

        for question in questions:
            option_id = answers.get(question.id)
            selected = None
            if option_id is not None:
                selected = next((o for o in question.options.all() if o.id == option_id), None)
            is_correct = bool(selected and selected.is_correct)
            if is_correct:
                earned_points += question.points
            AttemptAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_option=selected,
                is_correct=is_correct,
            )

        score = (Decimal(earned_points) / Decimal(total_points) * Decimal('100')).quantize(Decimal('0.01'))
        attempt.submitted_at = timezone.now()
        attempt.score = score
        attempt.passed = score >= exam.passing_score
        attempt.save(update_fields=['submitted_at', 'score', 'passed'])

        # Si aprobó y ya tiene el 100% de progreso, emitir el certificado
        if attempt.passed:
            from apps.library.signals import _issue_certificate_if_needed
            _issue_certificate_if_needed(attempt.enrollment)

        finished_count = ExamAttempt.objects.filter(enrollment=attempt.enrollment).exclude(submitted_at=None).count()
        attempts_left = None if exam.max_attempts == 0 else max(exam.max_attempts - finished_count, 0)

        return Response({
            'score': attempt.score,
            'passed': attempt.passed,
            'passing_score': exam.passing_score,
            'correct_answers': sum(1 for a in attempt.answers.all() if a.is_correct),
            'total_questions': len(questions),
            'attempts_left': attempts_left,
            'certificate_issued': attempt.passed and attempt.enrollment.is_completed,
        })
