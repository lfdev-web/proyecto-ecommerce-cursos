from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.catalog.models import Course
from apps.library.models import Enrollment

# Margen de tolerancia sobre el límite de tiempo para absorber latencia de red
SUBMIT_GRACE_SECONDS = 30


class Exam(models.Model):
    """
    Examen final de un curso (1:1). Completar el 100% de las lecciones ya no
    basta para certificarse: si el curso tiene examen activo, hay que aprobarlo.
    """
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='exam')
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True, default='')
    time_limit_minutes = models.PositiveIntegerField(default=30)
    # Porcentaje mínimo (0-100) para aprobar
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('70.00'))
    max_attempts = models.PositiveIntegerField(default=3, help_text='0 = intentos ilimitados')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Examen'
        verbose_name_plural = 'Exámenes'

    def __str__(self):
        return f"Examen: {self.title} — {self.course.title}"


class Question(models.Model):
    """
    Pregunta de opción múltiple dentro de un examen.
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f"P{self.order}: {self.text[:60]}"


class AnswerOption(models.Model):
    """
    Opción de respuesta de una pregunta. is_correct nunca se expone por la API pública.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Opción de respuesta'
        verbose_name_plural = 'Opciones de respuesta'

    def __str__(self):
        marker = '✓' if self.is_correct else '✗'
        return f"[{marker}] {self.text[:60]}"


class ExamAttempt(models.Model):
    """
    Intento de un alumno sobre el examen de su inscripción. El tiempo se valida
    del lado del servidor: started_at + time_limit define la fecha límite real.
    """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='exam_attempts')
    attempt_number = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    # Porcentaje obtenido (0-100); null mientras el intento sigue abierto
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('enrollment', 'attempt_number')
        ordering = ['-started_at']
        verbose_name = 'Intento de examen'
        verbose_name_plural = 'Intentos de examen'

    @property
    def is_open(self):
        return self.submitted_at is None

    def deadline(self, exam):
        return self.started_at + timedelta(minutes=exam.time_limit_minutes)

    def is_expired(self, exam):
        return timezone.now() > self.deadline(exam) + timedelta(seconds=SUBMIT_GRACE_SECONDS)

    def __str__(self):
        state = 'abierto' if self.is_open else f"{self.score}% {'APROBADO' if self.passed else 'reprobado'}"
        return f"Intento {self.attempt_number} — {self.enrollment} — {state}"


class AttemptAnswer(models.Model):
    """
    Respuesta dada en un intento. is_correct es snapshot al momento de calificar.
    """
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='+')
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')
        verbose_name = 'Respuesta de intento'
        verbose_name_plural = 'Respuestas de intento'

    def __str__(self):
        return f"{self.attempt_id} — Q{self.question_id} — {'✓' if self.is_correct else '✗'}"
