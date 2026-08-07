from django.db.models import Q, Avg, Count, Prefetch, F
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Category, Course, CourseStatus, Review, con_precio_efectivo
from .serializers import CategorySerializer, CourseListSerializer, CourseDetailSerializer, ReviewSerializer


def _course_queryset_with_stats():
    """
    Base del catálogo público: solo cursos activos YA PUBLICADOS (los borradores
    y los que están en revisión no se ven). Trae calificación y nº de reseñas
    anotados en una sola consulta, con los FK precargados (evita N+1).

    `precio_efectivo` se anota para que filtrar y ordenar por precio tenga en
    cuenta las promociones vigentes: un curso rebajado de $39 a $27 debe
    aparecer al filtrar "hasta $30".
    """
    return con_precio_efectivo(
        Course.objects.filter(is_active=True, status_id=CourseStatus.PUBLISHED)
        .select_related('category', 'instructor', 'level')
        .annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', distinct=True),
        )
    )


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class CourseListView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]

    # Órdenes permitidos (whitelist: el query param nunca llega crudo al ORM).
    # El orden por precio usa el efectivo, no el de lista: si no, un curso en
    # oferta aparecería en la posición de su precio original.
    ORDERINGS = {
        'price': 'precio_efectivo',
        '-price': '-precio_efectivo',
        '-rating': '-avg_rating',
        '-created': '-created_at',
    }

    def get_queryset(self):
        queryset = _course_queryset_with_stats()
        params = self.request.query_params

        category_slug = params.get('category', None)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        search = params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Filtro por nivel (código del catálogo CourseLevel: BEGINNER/INTERMEDIATE/ADVANCED)
        level = params.get('level', None)
        if level:
            queryset = queryset.filter(level_id=level.upper())

        # Filtro por rango de precio (se ignoran valores no numéricos)
        # El rango de precio filtra por el efectivo: quien busca "hasta $30"
        # espera ver un curso de $39 rebajado a $27.
        for param, lookup in (('price_min', 'precio_efectivo__gte'),
                              ('price_max', 'precio_efectivo__lte')):
            raw = params.get(param, None)
            if raw:
                try:
                    queryset = queryset.filter(**{lookup: float(raw)})
                except ValueError:
                    pass

        ordering = self.ORDERINGS.get(params.get('ordering', ''))
        if ordering == '-avg_rating':
            # Los cursos sin reseñas (avg NULL) van al final, no al inicio (Postgres
            # pone NULL primero en DESC por defecto)
            queryset = queryset.order_by(F('avg_rating').desc(nulls_last=True))
        elif ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class PromotedCoursesView(generics.ListAPIView):
    """
    Cursos con promoción VIGENTE, para el carrete de ofertas de la portada.

    Se ordenan por el mayor descuento primero: lo que se quiere destacar es la
    oferta más atractiva, no el curso más caro ni el más nuevo.
    """
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        ahora = timezone.now()
        queryset = (
            _course_queryset_with_stats()
            .filter(promo_price__isnull=False, promo_price__lt=F('price'))
            .filter(Q(promo_until__isnull=True) | Q(promo_until__gt=ahora))
        )
        # Se ordena en Python por el porcentaje real de descuento: expresarlo
        # en SQL exigiría una división que complica la consulta sin ganar nada,
        # porque el carrete muestra a lo sumo una docena de cursos.
        return sorted(queryset, key=lambda c: c.promo_discount_pct, reverse=True)[:12]


class CourseDetailView(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        # Mismas estadísticas que el listado + lecciones y reseñas (con su autor)
        # precargadas para no disparar consultas por cada una en el detalle.
        return _course_queryset_with_stats().prefetch_related(
            'lessons',
            Prefetch('reviews', queryset=Review.objects.select_related('user').order_by('-created_at')),
        )


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Solo puede reseñar quien está inscrito en el curso (lo compró o lo tiene
        # por membresía). Igual que en Udemy: no se reseña un curso que no cursaste.
        from apps.library.models import Enrollment
        course_id = self.kwargs.get('course_id')
        if not Enrollment.objects.filter(user=self.request.user, course_id=course_id).exists():
            raise PermissionDenied('Debes estar inscrito en el curso para dejar una reseña.')

        # La señal de Review dispara el cálculo del Buy Box automáticamente
        serializer.save(user=self.request.user, course_id=course_id)
