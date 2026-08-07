from django.db import models
from django.db.models import Case, DecimalField, F, When
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

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
    
    # --- Promoción por tiempo limitado ---
    # El precio de lista NUNCA se modifica: la oferta vive en estos dos campos.
    # Así se puede mostrar el precio tachado, y al terminar la promoción el
    # curso vuelve solo a su precio original sin tener que restaurar nada.
    promo_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Precio rebajado. Déjalo vacío si el curso no está en oferta.',
    )
    promo_until = models.DateTimeField(
        null=True, blank=True,
        help_text='Fin de la oferta. Vacío = sin fecha de término.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # ------------------------------------------------------------------
    @property
    def is_on_promo(self):
        """
        La oferta cuenta solo si hay precio rebajado, es MENOR al de lista y
        no ha vencido. Comprobar que sea menor evita que una promoción mal
        cargada termine cobrando de más.
        """
        if self.promo_price is None or self.promo_price >= self.price:
            return False
        return self.promo_until is None or self.promo_until > timezone.now()

    @property
    def effective_price(self):
        """El precio que se le cobra realmente al alumno."""
        return self.promo_price if self.is_on_promo else self.price

    @property
    def promo_discount_pct(self):
        """Porcentaje de descuento, para la etiqueta del carrete."""
        if not self.is_on_promo:
            return 0
        return int(round((1 - (self.promo_price / self.price)) * 100))


def con_precio_efectivo(queryset):
    """
    Anota `precio_efectivo` en la consulta.

    Hace falta porque `effective_price` es una propiedad de Python y la base de
    datos no la conoce: sin esto, filtrar por rango de precio u ordenar por
    precio usaría el de lista e ignoraría las ofertas — un curso rebajado a $27
    no aparecería al filtrar "hasta $30".
    """
    ahora = timezone.now()
    return queryset.annotate(
        precio_efectivo=Case(
            When(
                promo_price__isnull=False,
                promo_price__lt=F('price'),
                then=Case(
                    When(promo_until__isnull=True, then=F('promo_price')),
                    When(promo_until__gt=ahora, then=F('promo_price')),
                    default=F('price'),
                ),
            ),
            default=F('price'),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )


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

class Assignment(models.Model):
    """
    Actividad 2 del curso: el trabajo práctico que el alumno debe entregar.

    Es contenido del curso, igual que Lesson, por eso vive en catalog; la
    entrega del alumno vive en library (AssignmentSubmission), del mismo modo
    que Lesson vive aquí y LessonProgress allá.

    Existe porque terminar un curso era pulsar "completada" en cada lección:
    nada verificaba que el alumno hubiera hecho algo. Ahora el certificado
    exige, además del 100% de las lecciones, aprobar el cuestionario y entregar
    este trabajo.
    """
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='assignment')
    title = models.CharField(max_length=200)
    instructions = models.TextField(help_text='Consigna: qué debe hacer y entregar el alumno')
    # Material de apoyo del tema (documentación oficial, libro de acceso libre)
    resource_label = models.CharField(max_length=200, blank=True, default='')
    resource_url = models.URLField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trabajo práctico'
        verbose_name_plural = 'Trabajos prácticos'

    def __str__(self):
        return f'Trabajo: {self.title} — {self.course.title}'


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
