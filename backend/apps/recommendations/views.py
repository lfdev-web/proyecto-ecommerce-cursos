from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Course
from .models import RecommendationCache
from .serializers import CourseRecommendationSerializer, InteractionCreateSerializer


class RecommendationsForUserView(APIView):
    """
    Endpoint personalizado de recomendaciones.
    Si el usuario tiene historial de interacciones con el modelo SVD entrenado,
    devuelve su caché de recomendaciones personalizadas.
    En caso contrario, hace un FALLBACK a los cursos Best Sellers globales.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Intentar devolver recomendaciones personalizadas desde el caché SVD
        cache = RecommendationCache.objects.filter(user=user).first()
        if cache and cache.recommended_course_ids:
            # Preservar el orden de scoring del SVD usando Case/When
            from django.db.models import Case, When, IntegerField
            preserved_order = Case(
                *[When(id=pk, then=pos) for pos, pk in enumerate(cache.recommended_course_ids)],
                output_field=IntegerField()
            )
            # select_related evita una consulta por curso al leer categoría,
            # nivel e instructor en el serializer (problema N+1).
            courses = Course.objects.filter(
                id__in=cache.recommended_course_ids,
                is_active=True, status_id='PUBLISHED'
            ).select_related('category', 'level', 'instructor').order_by(preserved_order)

            serializer = CourseRecommendationSerializer(courses, many=True)
            return Response({
                'source': 'personalized',
                'results': serializer.data
            })

        # Fallback: Best Sellers si no hay historial suficiente
        best_sellers = Course.objects.filter(
            is_active=True, status_id='PUBLISHED',
            is_best_seller=True
        ).select_related('category', 'level', 'instructor').order_by('-created_at')[:10]

        serializer = CourseRecommendationSerializer(best_sellers, many=True)
        return Response({
            'source': 'best_sellers_fallback',
            'results': serializer.data
        })


class SimilarCoursesView(APIView):
    """
    Cross-selling: devuelve cursos de la misma categoría del curso visto,
    excluyendo los cursos que el usuario ya tiene (ya compró o está en biblioteca).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id, is_active=True, status_id='PUBLISHED')
        except Course.DoesNotExist:
            return Response({'detail': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Obtener cursos ya adquiridos del usuario para excluirlos
        from apps.orders.models import OrderItem
        purchased_ids = list(
            OrderItem.objects.filter(
                order__user=request.user,
                order__status='COMPLETED'
            ).values_list('course_id', flat=True)
        )

        similar = Course.objects.select_related(
            'category', 'level', 'instructor'
        ).filter(
            category=course.category,
            is_active=True, status_id='PUBLISHED'
        ).exclude(
            id=course.id
        ).exclude(
            id__in=purchased_ids
        ).order_by('-is_best_seller', '-created_at')[:6]

        serializer = CourseRecommendationSerializer(similar, many=True)
        return Response({
            'source': 'similar_courses',
            'results': serializer.data
        })


class TrackInteractionView(generics.CreateAPIView):
    """
    Registra una interacción del usuario con un curso.
    Los pesos se asignan automáticamente en el modelo según el tipo de interacción.
    """
    serializer_class = InteractionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
