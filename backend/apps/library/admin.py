from django.contrib import admin

from .models import (
    AssignmentSubmission, EnrollmentType, Enrollment, LessonProgress, Certificate,
    WishlistItem, StudyStreak, Achievement, UserAchievement,
)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    """
    Entregas de los alumnos. Se consultan y se descargan; no se crean a mano,
    las sube el alumno desde su curso.
    """
    list_display = ('enrollment', 'assignment', 'is_auto', 'submitted_at')
    list_filter = ('is_auto', 'assignment__course__category')
    search_fields = ('enrollment__user__email', 'assignment__title')
    ordering = ('-submitted_at',)
    readonly_fields = ('enrollment', 'assignment', 'file', 'comment', 'submitted_at', 'is_auto')

    def has_add_permission(self, request):
        return False


@admin.register(EnrollmentType)
class EnrollmentTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')


class LessonProgressInline(admin.TabularInline):
    model = LessonProgress
    extra = 0
    readonly_fields = ('lesson', 'is_completed', 'watch_percentage', 'completed_at')
    can_delete = False


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrollment_type', 'progress_percentage', 'is_completed', 'enrolled_at')
    list_filter = ('enrollment_type', 'is_completed')
    search_fields = ('user__email', 'course__title')
    ordering = ('-enrolled_at',)
    inlines = [LessonProgressInline]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """
    Los certificados son documentos históricos emitidos por el sistema:
    se pueden consultar y anular (borrar), pero no crear ni editar a mano.
    """
    list_display = ('verification_code', 'student_name', 'course_title', 'course_duration_hours', 'issued_at')
    search_fields = ('student_name', 'course_title', 'verification_code')
    ordering = ('-issued_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'added_at')
    search_fields = ('user__email', 'course__title')


@admin.register(StudyStreak)
class StudyStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_activity_date')
    search_fields = ('user__email',)
    ordering = ('-current_streak',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Catálogo de medallas: el admin puede ajustar nombre/ícono/orden sin deploy."""
    list_display = ('code', 'icon', 'name', 'description', 'sort_order')
    list_editable = ('icon', 'sort_order')
    ordering = ('sort_order',)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Las medallas las otorga el sistema: aquí solo se consultan o anulan."""
    list_display = ('user', 'achievement', 'earned_at')
    search_fields = ('user__email', 'achievement__name')
    ordering = ('-earned_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
