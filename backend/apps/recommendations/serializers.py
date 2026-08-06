from rest_framework import serializers
from apps.catalog.models import Course
from .models import UserCourseInteraction


class CourseRecommendationSerializer(serializers.ModelSerializer):
    """
    Versión ligera del curso para las tarjetas de recomendación. Incluye
    portada y nivel porque el frontend reutiliza el mismo componente de
    tarjeta que el catálogo: sin estos campos las recomendaciones se veían
    con el icono de relleno en vez de su portada.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    level_name = serializers.CharField(source='level.name', read_only=True)
    instructor_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'price', 'is_best_seller', 'category_name',
            'cover_image', 'level', 'level_name', 'instructor_name',
        )

    def get_instructor_name(self, obj):
        if obj.instructor is None:
            return None
        return f'{obj.instructor.first_name} {obj.instructor.last_name}'.strip() or obj.instructor.email


class InteractionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCourseInteraction
        fields = ('course', 'interaction_type')
        # interaction_type es FK a la tabla catálogo: DRF valida automáticamente
        # que el código exista (PrimaryKeyRelatedField)
