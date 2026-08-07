from django.contrib import admin
from django.utils import timezone
from .models import (
    Category, Course, Lesson, Review,
    CourseSlotRequest, SlotRequestStatus, CourseStatus,
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CourseStatus)
class CourseStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')


class LessonInline(admin.TabularInline):
    """Para revisar el temario sin salir de la ficha del curso."""
    model = Lesson
    extra = 0
    fields = ('order', 'title', 'duration_minutes', 'video_url')
    ordering = ('order',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Bandeja de revisión de cursos. Los cursos que el docente envía llegan en
    estado "En revisión"; desde aquí se publican o se devuelven con observaciones.
    """
    list_display = (
        'title', 'instructor', 'category', 'price', 'promo_price', 'en_oferta',
        'status', 'is_active', 'is_best_seller', 'created_at',
    )
    list_filter = ('status', 'is_active', 'is_best_seller', 'category')
    list_editable = ('promo_price',)
    search_fields = ('title', 'description', 'instructor__email')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('is_best_seller', 'submitted_at', 'published_at')
    inlines = [LessonInline]
    actions = ['publicar_cursos', 'devolver_cursos', 'quitar_promocion']

    @admin.display(description='En oferta', boolean=True)
    def en_oferta(self, obj):
        """Muestra si la promoción está VIGENTE, no solo si tiene precio puesto."""
        return obj.is_on_promo

    @admin.action(description='Quitar la promoción de los cursos seleccionados')
    def quitar_promocion(self, request, queryset):
        total = queryset.filter(promo_price__isnull=False).update(
            promo_price=None, promo_until=None)
        self.message_user(request, f'{total} curso(s) vuelven a su precio de lista.')

    @admin.action(description='Publicar cursos seleccionados')
    def publicar_cursos(self, request, queryset):
        total = 0
        for course in queryset.exclude(status_id=CourseStatus.PUBLISHED):
            course.status_id = CourseStatus.PUBLISHED
            course.published_at = timezone.now()
            course.review_notes = ''
            course.is_active = True
            course.save(update_fields=['status', 'published_at', 'review_notes', 'is_active'])
            total += 1
        self.message_user(request, f'{total} curso(s) publicado(s) y visibles en el catálogo.')

    @admin.action(description='Devolver cursos al docente (con observaciones)')
    def devolver_cursos(self, request, queryset):
        total = queryset.exclude(status_id=CourseStatus.DRAFT).count()
        for course in queryset.exclude(status_id=CourseStatus.DRAFT):
            course.status_id = CourseStatus.REJECTED
            course.save(update_fields=['status'])
        self.message_user(
            request,
            f'{total} curso(s) devuelto(s). Escribe las observaciones en el campo '
            f'"review notes" de cada curso para que el docente las vea.'
        )

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'order', 'duration_minutes')
    list_filter = ('course',)
    search_fields = ('title', 'content')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('course', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'course')
    search_fields = ('comment',)


@admin.register(SlotRequestStatus)
class SlotRequestStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')


@admin.register(CourseSlotRequest)
class CourseSlotRequestAdmin(admin.ModelAdmin):
    """
    Aquí el administrador habilita (o niega) el espacio para que un docente
    cree un curso nuevo. Aprobar no crea el curso: habilita el cupo para que
    el docente lo arme y después lo envíe a revisión.
    """
    list_display = ('teacher', 'proposed_title', 'proposed_category', 'status', 'is_consumed', 'created_at')
    list_filter = ('status', 'is_consumed')
    search_fields = ('teacher__email', 'proposed_title')
    ordering = ('-created_at',)
    readonly_fields = (
        'teacher', 'proposed_title', 'proposed_category', 'justification',
        'is_consumed', 'created_course', 'created_at', 'reviewed_at', 'reviewed_by',
    )
    fieldsets = (
        ('Solicitud', {'fields': ('teacher', 'proposed_title', 'proposed_category', 'justification', 'created_at')}),
        ('Revisión', {'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at')}),
        ('Uso del espacio', {'fields': ('is_consumed', 'created_course')}),
    )
    actions = ['aprobar_espacios', 'rechazar_espacios']

    def _stamp(self, obj, request):
        obj.reviewed_by = request.user
        obj.reviewed_at = timezone.now()

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data and obj.status_id in (
            SlotRequestStatus.APPROVED, SlotRequestStatus.REJECTED
        ):
            self._stamp(obj, request)
        super().save_model(request, obj, form, change)

    @admin.action(description='Aprobar espacios seleccionados')
    def aprobar_espacios(self, request, queryset):
        pendientes = queryset.filter(status_id=SlotRequestStatus.PENDING)
        total = pendientes.count()
        for solicitud in pendientes:
            solicitud.status_id = SlotRequestStatus.APPROVED
            self._stamp(solicitud, request)
            solicitud.save()
        self.message_user(request, f'{total} espacio(s) habilitado(s). El docente ya puede crear su curso.')

    @admin.action(description='Rechazar espacios seleccionados')
    def rechazar_espacios(self, request, queryset):
        pendientes = queryset.filter(status_id=SlotRequestStatus.PENDING)
        total = pendientes.count()
        for solicitud in pendientes:
            solicitud.status_id = SlotRequestStatus.REJECTED
            self._stamp(solicitud, request)
            solicitud.save()
        self.message_user(request, f'{total} solicitud(es) rechazada(s).')
