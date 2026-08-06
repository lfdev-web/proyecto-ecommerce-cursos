from django.contrib import admin

from .models import InteractionType, UserCourseInteraction, RecommendationCache


@admin.register(InteractionType)
class InteractionTypeAdmin(admin.ModelAdmin):
    """
    El peso de cada tipo alimenta la matriz del modelo SVD: ajustarlo aquí
    cambia la señal del recomendador sin tocar código (aplica a interacciones nuevas).
    """
    list_display = ('code', 'name', 'weight', 'description')


@admin.register(UserCourseInteraction)
class UserCourseInteractionAdmin(admin.ModelAdmin):
    """Las interacciones las registra el sistema; aquí solo se consultan."""
    list_display = ('user', 'course', 'interaction_type', 'weight', 'created_at')
    list_filter = ('interaction_type',)
    search_fields = ('user__email', 'course__title')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    """Resultado nocturno del modelo SVD (solo consulta)."""
    list_display = ('user', 'recommended_course_ids', 'last_updated')
    search_fields = ('user__email',)
    ordering = ('-last_updated',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
