from rest_framework import serializers
from apps.catalog.models import Course
from apps.catalog.serializers import CourseListSerializer
from .models import Enrollment, LessonProgress, Certificate, WishlistItem, StudyStreak


class EnrolledCourseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'category_name')


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = LessonProgress
        fields = ('id', 'lesson', 'lesson_title', 'is_completed', 'watch_percentage', 'completed_at')
        read_only_fields = ('completed_at',)


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = (
            'issued_at', 'verification_code',
            'student_name', 'course_title', 'course_duration_hours', 'completed_at',
        )
        read_only_fields = fields


class EnrollmentSerializer(serializers.ModelSerializer):
    course = EnrolledCourseSerializer(read_only=True)
    lesson_progresses = LessonProgressSerializer(many=True, read_only=True)
    certificate = CertificateSerializer(read_only=True)
    activities = serializers.SerializerMethodField()
    can_certify = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = (
            'id', 'course', 'enrollment_type',
            'enrolled_at', 'progress_percentage',
            'is_completed', 'lesson_progresses', 'certificate',
            'activities', 'can_certify',
        )
        read_only_fields = ('enrolled_at', 'progress_percentage', 'is_completed')

    def get_activities(self, obj):
        """
        Estado de las dos actividades del curso (cuestionario y trabajo).
        El frontend lo usa para saber qué botón mostrar en cada tarjeta.
        """
        from .actividades import estado_actividades
        return estado_actividades(obj)

    def get_can_certify(self, obj):
        from .actividades import curso_terminado
        return curso_terminado(obj)


class WishlistItemSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'course', 'added_at')
        read_only_fields = ('id', 'added_at')


class StudyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyStreak
        fields = ('current_streak', 'longest_streak', 'last_activity_date')
        read_only_fields = fields
