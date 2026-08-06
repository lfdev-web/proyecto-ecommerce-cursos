from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class CourseLevel(models.Model):
    """
    Tabla catálogo de niveles de dificultad de los cursos (lookup table).
    """
    BASICO = 'BASICO'
    INTERMEDIO = 'INTERMEDIO'
    AVANZADO = 'AVANZADO'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Nivel de curso'
        verbose_name_plural = 'Niveles de curso'

    def __str__(self):
        return self.name


class CourseStatus(models.Model):
    """
    Tabla catálogo del estado de publicación de un curso (lookup table).
    Flujo: el docente arma el curso en BORRADOR, lo envía a revisión, y el
    administrador lo publica o lo devuelve con observaciones.
    """
    DRAFT = 'DRAFT'
    IN_REVIEW = 'IN_REVIEW'
    PUBLISHED = 'PUBLISHED'
    REJECTED = 'REJECTED'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Estado de curso'
        verbose_name_plural = 'Estados de curso'

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Docente que imparte el curso
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='courses_taught',
        limit_choices_to={'role': 'DOCENTE'}
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    
    is_active = models.BooleanField(default=True)

    # Estado de publicación: solo los PUBLISHED aparecen en el catálogo público.
    status = models.ForeignKey(
        CourseStatus,
        on_delete=models.PROTECT,
        db_column='status',
        default=CourseStatus.DRAFT,
        related_name='courses',
    )
    # Observaciones del administrador cuando devuelve un curso al docente
    review_notes = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Buy Box indicator (calculado de forma asíncrona vía Celery)
    is_best_seller = models.BooleanField(default=False)

    # Ficha completa del catálogo
    level = models.ForeignKey(
        CourseLevel,
        on_delete=models.PROTECT,
        db_column='level',
        default=CourseLevel.BASICO,
        related_name='+'
    )
    language = models.CharField(max_length=30, default='Español')
    cover_image = models.URLField(blank=True, default='')
    requirements = models.TextField(blank=True, default='')
    learning_outcomes = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()
    video_url = models.URLField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class SlotRequestStatus(models.Model):
    """
    Tabla catálogo de estados de una solicitud de espacio de curso (lookup table).
    """
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'

    code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Estado de solicitud de espacio'
        verbose_name_plural = 'Estados de solicitud de espacio'

    def __str__(self):
        return self.name


class CourseSlotRequest(models.Model):
    """
    Solicitud del docente para que se le habilite el espacio de un curso nuevo.
    El plan de docente define cuántos espacios puede tener en total; el
    administrador aprueba cada solicitud antes de que el docente pueda crear
    el curso. Una solicitud aprobada se "consume" al crear el curso.
    """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='slot_requests',
        limit_choices_to={'role': 'DOCENTE'},
    )
    proposed_title = models.CharField(max_length=200, help_text='Título tentativo del curso')
    proposed_category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='slot_requests'
    )
    justification = models.TextField(help_text='De qué trata el curso y por qué aporta al catálogo')

    status = models.ForeignKey(
        SlotRequestStatus,
        on_delete=models.PROTECT,
        db_column='status',
        default=SlotRequestStatus.PENDING,
        related_name='+',
    )
    rejection_reason = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_slot_requests',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Se marca cuando el docente usa el espacio aprobado para crear su curso
    is_consumed = models.BooleanField(default=False)
    created_course = models.OneToOneField(
        'catalog.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='slot_request'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de espacio de curso'
        verbose_name_plural = 'Solicitudes de espacio de curso'

    def __str__(self):
        return f'{self.teacher.email} — {self.proposed_title} [{self.status_id}]'

    @staticmethod
    def slot_summary(teacher):
        """
        Resumen de cupos del docente: cuántos le da su plan, cuántos ya usó
        (cursos creados), cuántos tiene aprobados sin usar y cuántos le quedan.
        """
        from apps.memberships.models import PlanAudience, UserMembership

        membership = (
            UserMembership.objects
            .filter(user=teacher, audience_id=PlanAudience.DOCENTE)
            .select_related('plan', 'plan__tier')
            .first()
        )
        active = bool(membership and membership.is_currently_active)
        plan_slots = membership.plan.course_slots if active else 0
        plan_name = membership.plan.name if active else None

        used = Course.objects.filter(instructor=teacher).count()
        approved_unused = CourseSlotRequest.objects.filter(
            teacher=teacher, status_id=SlotRequestStatus.APPROVED, is_consumed=False
        ).count()
        pending = CourseSlotRequest.objects.filter(
            teacher=teacher, status_id=SlotRequestStatus.PENDING
        ).count()

        return {
            'has_active_plan': active,
            'plan_name': plan_name,
            'plan_slots': plan_slots,
            'courses_created': used,
            'approved_unused': approved_unused,
            'pending_requests': pending,
            'available': max(plan_slots - used - approved_unused, 0),
        }


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'user') # Un usuario solo puede dejar una review por curso
        constraints = [
            # Refuerzo a nivel de BD de los validators (1-5), no solo en la app
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='ck_review_rating_1_5',
            ),
        ]

    def __str__(self):
        return f"{self.rating} stars by {self.user.email} for {self.course.title}"
