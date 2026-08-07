from rest_framework import serializers
from .models import Category, Course, Lesson, Review, CourseSlotRequest


class CourseSlotRequestSerializer(serializers.ModelSerializer):
    """
    Solicitud de espacio de curso. El docente solo escribe el título propuesto,
    la categoría y la justificación; el estado y la revisión los maneja el admin.
    """
    status_name = serializers.CharField(source='status.name', read_only=True)
    category_name = serializers.CharField(source='proposed_category.name', read_only=True)

    class Meta:
        model = CourseSlotRequest
        fields = (
            'id', 'proposed_title', 'proposed_category', 'category_name', 'justification',
            'status', 'status_name', 'rejection_reason', 'is_consumed',
            'created_course', 'created_at', 'reviewed_at',
        )
        read_only_fields = (
            'id', 'status', 'status_name', 'rejection_reason', 'is_consumed',
            'created_course', 'created_at', 'reviewed_at',
        )


class TeacherCourseSerializer(serializers.ModelSerializer):
    """
    Curso visto/editado por su propio docente. El estado, el instructor y las
    fechas de revisión son de solo lectura: los controla el flujo de aprobación.
    """
    status_name = serializers.CharField(source='status.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    level_name = serializers.CharField(source='level.name', read_only=True)
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'price', 'category', 'category_name',
            'level', 'level_name', 'language', 'cover_image', 'requirements', 'learning_outcomes',
            'status', 'status_name', 'review_notes', 'submitted_at', 'published_at',
            'is_active', 'is_best_seller', 'lessons_count', 'created_at',
        )
        read_only_fields = (
            'id', 'slug', 'status', 'status_name', 'review_notes', 'submitted_at',
            'published_at', 'is_best_seller', 'created_at',
        )

    def get_lessons_count(self, obj):
        return obj.lessons.count()


class TeacherLessonSerializer(serializers.ModelSerializer):
    """Lección editable por el docente dueño del curso (incluye el contenido)."""
    # Opcional: si el docente no manda orden, la vista la coloca al final del temario
    order = serializers.IntegerField(required=False, min_value=1)

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'order', 'video_url', 'content', 'duration_minutes')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class LessonSerializer(serializers.ModelSerializer):
    """
    Versión pública de la lección (detalle del curso, visible sin comprar):
    solo el temario. El contenido real (video_url, content) se sirve únicamente
    por el endpoint protegido de library que verifica la inscripción.
    """
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'duration_minutes', 'order')


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user_name', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'created_at')


class CourseListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    instructor_name = serializers.SerializerMethodField()

    level_name = serializers.CharField(source='level.name', read_only=True)
    # cover_image es un URLField: guarda la URL tal cual (puede ser externa, o
    # una ruta /media/... servida por el propio proyecto). No necesita
    # transformación en el serializer.
    #
    # Anotados en la vista del catálogo (Avg/Count). Si el serializer se reutiliza
    # sin la anotación (wishlist, recomendaciones), se devuelven vacíos sin consulta extra.
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    # Promoción: el frontend necesita los tres datos para pintar la tarjeta con
    # el precio tachado, el nuevo y la etiqueta de descuento.
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_on_promo = serializers.BooleanField(read_only=True)
    promo_discount_pct = serializers.IntegerField(read_only=True)

    def get_avg_rating(self, obj):
        value = getattr(obj, 'avg_rating', None)
        return round(value, 1) if value is not None else None

    def get_review_count(self, obj):
        return getattr(obj, 'review_count', 0)

    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'instructor_name', 'category', 'price',
            'is_best_seller', 'level', 'level_name', 'language', 'cover_image',
            'avg_rating', 'review_count', 'created_at',
            'effective_price', 'is_on_promo', 'promo_discount_pct', 'promo_until',
        )

    def get_instructor_name(self, obj):
        # instructor es SET_NULL en el modelo (docente eliminado o no asignado aún)
        if obj.instructor is None:
            return None
        return f"{obj.instructor.first_name} {obj.instructor.last_name}".strip()


class CourseDetailSerializer(CourseListSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + (
            'description', 'requirements', 'learning_outcomes', 'lessons', 'reviews',
            'is_enrolled',
        )

    def get_is_enrolled(self, obj):
        """True solo si el usuario autenticado está inscrito (para habilitar la reseña)."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        from apps.library.models import Enrollment
        return Enrollment.objects.filter(user=request.user, course=obj).exists()
