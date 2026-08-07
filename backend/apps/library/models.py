import uuid
from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings
from apps.catalog.models import Assignment, Course, Lesson

# Extensiones aceptadas en la entrega del trabajo práctico.
#
# La lista es corta a propósito: nginx sirve /media/ desde el MISMO origen que
# la aplicación, así que un .html o un .svg subido por un alumno se ejecutaría
# como si fuera código nuestro (XSS almacenado). Formatos que el navegador no
# ejecuta, únicamente.
EXTENSIONES_ENTREGA = ['pdf', 'zip', 'png', 'jpg', 'jpeg', 'txt', 'md', 'docx', 'ipynb']
# Tope por archivo (bytes). DATA_UPLOAD_MAX_MEMORY_SIZE ya limita la petición
# completa; esto da además un mensaje de error entendible.
TAMANO_MAX_ENTREGA = 5 * 1024 * 1024


class EnrollmentType(models.Model):
    """
    Tabla catálogo de tipos de inscripción (lookup table).
    """
    PURCHASED = 'PURCHASED'
    MEMBERSHIP = 'MEMBERSHIP'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Tipo de inscripción'
        verbose_name_plural = 'Tipos de inscripción'

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    """
    Representa el acceso de un usuario a un curso.
    Puede ser por compra directa (PURCHASED) o mediante membresía activa (MEMBERSHIP).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,  # No borrar un curso si tiene alumnos inscritos
        related_name='enrollments'
    )
    enrollment_type = models.ForeignKey(
        EnrollmentType,
        on_delete=models.PROTECT,
        db_column='enrollment_type',
        default=EnrollmentType.PURCHASED,
        related_name='+'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    # Progreso calculado como porcentaje de lecciones completadas (0-100)
    progress_percentage = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')  # Un alumno solo puede inscribirse una vez

    def recalculate_progress(self):
        """
        Recalcula y actualiza el progreso del alumno en el curso.
        Se llama automáticamente cuando el alumno marca una lección como completada.
        """
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            self.progress_percentage = 0.0
            self.is_completed = False
        else:
            completed = LessonProgress.objects.filter(
                enrollment=self,
                is_completed=True
            ).count()
            self.progress_percentage = round((completed / total_lessons) * 100, 2)
            self.is_completed = (self.progress_percentage >= 100.0)

        self.save(update_fields=['progress_percentage', 'is_completed'])
        return self.progress_percentage

    def __str__(self):
        return f"{self.user.email} → {self.course.title} ({self.enrollment_type_id})"


class LessonProgress(models.Model):
    """
    Registra si el alumno ha completado una lección específica dentro de su inscripción.
    Al alcanzar el 20% de progreso en el curso, se activa el trigger para
    registrar la interacción de tipo REVIEW en el sistema de recomendaciones.
    """
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='lesson_progresses'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progresses'
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    watch_percentage = models.FloatField(default=0.0)  # Porcentaje visto del video (0-100)

    class Meta:
        unique_together = ('enrollment', 'lesson')

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.enrollment.user.email} — {self.lesson.title}"


def ruta_entrega(instance, filename):
    """Cada inscripción guarda su entrega en su propia carpeta."""
    return f'entregas/{instance.enrollment_id}/{filename}'


class AssignmentSubmission(models.Model):
    """
    Entrega del alumno para el trabajo práctico de su curso (Actividad 2).

    Se acepta automáticamente al subirla: esta es una plataforma de
    demostración y si la entrega quedara esperando la corrección de un docente,
    el recorrido hasta el certificado se cortaría ahí y no habría nada que
    mostrar. En una plataforma real aquí iría un estado (entregada / aprobada /
    devuelta) y la calificación del docente.
    """
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='assignment_submission'
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    file = models.FileField(
        upload_to=ruta_entrega,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=EXTENSIONES_ENTREGA)],
    )
    comment = models.TextField(blank=True, default='', help_text='Nota del alumno al docente')
    submitted_at = models.DateTimeField(auto_now_add=True)
    # Marca las entregas que generó el botón de recorrido rápido, para que no
    # se confundan con el trabajo real de un alumno.
    is_auto = models.BooleanField(
        default=False,
        help_text='Generada por el atajo de demostración, no subida por el alumno.'
    )

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Entrega de trabajo'
        verbose_name_plural = 'Entregas de trabajo'

    def __str__(self):
        return f'{self.enrollment.user.email} → {self.assignment.title}'


class Certificate(models.Model):
    """
    Certificado (simulado) emitido cuando un alumno completa el 100% de un curso.
    Se genera automáticamente vía señal cuando Enrollment.is_completed pasa a True.
    """
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='certificate'
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    # Código público para "verificar" la autenticidad del certificado (simulado)
    verification_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Snapshot histórico al momento de la emisión: el certificado es un documento
    # y debe conservar los datos de ese instante aunque el curso o el usuario cambien después.
    student_name = models.CharField(max_length=200, blank=True, default='')
    course_title = models.CharField(max_length=200, blank=True, default='')
    course_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Certificado {self.verification_code} — {self.enrollment.user.email} — {self.enrollment.course.title}"


class WishlistItem(models.Model):
    """
    Curso guardado por el usuario para comprarlo más adelante.
    Al agregarse, registra también una interacción tipo WISHLIST en
    apps.recommendations para alimentar el motor de recomendaciones SVD.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.email} ♥ {self.course.title}"


class StudyStreak(models.Model):
    """
    Racha de días consecutivos de estudio del usuario.
    Se actualiza vía señal cada vez que completa una lección (ver signals.py).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_streak'
    )
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} — racha actual: {self.current_streak} días"


class Achievement(models.Model):
    """
    Tabla catálogo de medallas/logros (lookup table).
    Las reglas que otorgan cada medalla viven en achievements.py; aquí solo
    se define el catálogo (código, nombre, ícono) para que el dominio pueda
    crecer o corregirse desde el admin sin tocar el esquema.
    """
    code = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=8, default='🏅', help_text='Emoji mostrado en el perfil')
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'code']
        verbose_name = 'Medalla'
        verbose_name_plural = 'Medallas'

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserAchievement(models.Model):
    """
    Medalla ganada por un usuario. La otorga el sistema (achievements.py)
    de forma idempotente; nunca se crea a mano.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.PROTECT,
        db_column='achievement',
        related_name='earned_by'
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')
        ordering = ['-earned_at']
        verbose_name = 'Medalla de usuario'
        verbose_name_plural = 'Medallas de usuario'

    def __str__(self):
        return f"{self.user.email} — {self.achievement_id}"
