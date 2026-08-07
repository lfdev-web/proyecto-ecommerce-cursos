from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from django.utils import timezone

from apps.common.red import ip_cliente as _ip_del_cliente

from .models import NavigationLog, ConversionFunnel
from .serializers import LogEventSerializer


class LogEventView(APIView):
    """
    Endpoint POST para registrar eventos de navegación desde el frontend.
    Funciona tanto para usuarios autenticados (JWT) como anónimos (session_id).
    """
    permission_classes = [permissions.AllowAny]
    # El endpoint debe seguir siendo público (rastrea visitantes anónimos), pero
    # sin límite cualquiera podía inundar NavigationLog/ConversionFunnel con
    # eventos falsos, que además alimentan el entrenamiento SVD del recomendador.
    throttle_scope = 'analitica'

    def post(self, request):
        serializer = LogEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = _ip_del_cliente(request)

        event_type = serializer.validated_data['event_type']
        metadata = serializer.validated_data.get('metadata', {})
        session_id = serializer.validated_data.get('session_id', '')

        # Guardar el log de navegación
        log = NavigationLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id,
            event_type=event_type,
            metadata=metadata,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        # Actualizar el ConversionFunnel según el tipo de evento
        _update_conversion_funnel(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
            event_type=event_type,
            metadata=metadata,
        )

        return Response({'detail': 'Evento registrado.', 'event_id': log.id}, status=status.HTTP_201_CREATED)


def _update_conversion_funnel(session_id, user, event_type, metadata):
    """
    Mapea los tipos de eventos a las etapas del funnel de conversión y las persiste.
    """
    FUNNEL_MAP = {
        NavigationLog.EventType.COURSE_VIEW: ConversionFunnel.FunnelStage.VIEW,
        NavigationLog.EventType.CART_ADD: ConversionFunnel.FunnelStage.CART,
        NavigationLog.EventType.CHECKOUT_START: ConversionFunnel.FunnelStage.CHECKOUT,
        NavigationLog.EventType.PURCHASE: ConversionFunnel.FunnelStage.PURCHASE,
    }
    stage = FUNNEL_MAP.get(event_type)
    if stage and session_id:
        ConversionFunnel.objects.create(
            session_id=session_id,
            user=user,
            stage=stage,
            course_id=metadata.get('course_id'),
        )


class AnalyticsDashboardView(APIView):
    """
    KPIs del negocio — solo accesible para el rol ADMIN.
    Devuelve métricas clave de los últimos 30 días:
    - Eventos totales por tipo.
    - Tasa de conversión de cada etapa del funnel.
    - Top 10 cursos más vistos.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Solo el rol ADMIN puede ver el dashboard
        if request.user.role_id != 'ADMIN':
            return Response(
                {'detail': 'No tienes permisos para acceder a este dashboard.'},
                status=status.HTTP_403_FORBIDDEN
            )

        since = timezone.now() - timezone.timedelta(days=30)

        # --- KPI 1: Eventos totales por tipo ---
        events_by_type = (
            NavigationLog.objects
            .filter(timestamp__gte=since)
            .values('event_type')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        # --- KPI 2: Tasa de conversión del funnel ---
        funnel_counts = {}
        for stage in ConversionFunnel.FunnelStage:
            funnel_counts[stage.value] = (
                ConversionFunnel.objects
                .filter(stage=stage, reached_at__gte=since)
                .values('session_id')
                .distinct()
                .count()
            )

        # Calcular tasas de conversión entre etapas
        conversion_rates = {}
        stages = [s.value for s in ConversionFunnel.FunnelStage]
        for i in range(1, len(stages)):
            prev_stage = stages[i - 1]
            curr_stage = stages[i]
            prev_count = funnel_counts.get(prev_stage, 0)
            curr_count = funnel_counts.get(curr_stage, 0)
            rate = round((curr_count / prev_count * 100), 2) if prev_count > 0 else 0.0
            conversion_rates[f"{prev_stage}_to_{curr_stage}"] = f"{rate}%"

        # --- KPI 3: Top 10 cursos más vistos (con título para el frontend) ---
        top_courses_raw = (
            NavigationLog.objects
            .filter(event_type=NavigationLog.EventType.COURSE_VIEW, timestamp__gte=since)
            .values('metadata__course_id')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        from apps.catalog.models import Course
        course_ids = [r['metadata__course_id'] for r in top_courses_raw if r['metadata__course_id']]
        titles = {c.id: c.title for c in Course.objects.filter(id__in=course_ids)}
        top_courses = [
            {
                'course_id': r['metadata__course_id'],
                'title': titles.get(r['metadata__course_id'], f"Curso #{r['metadata__course_id']}"),
                'views': r['views'],
            }
            for r in top_courses_raw
        ]

        # --- KPI 4: métricas de negocio ---
        from django.db.models import Sum
        from apps.users.models import CustomUser
        from apps.orders.models import Order
        from apps.library.models import Certificate

        orders_30d = Order.objects.filter(status_id='COMPLETED', created_at__gte=since)
        business_kpis = {
            'total_students': CustomUser.objects.filter(role_id='ALUMNO').count(),
            'new_students_30d': CustomUser.objects.filter(role_id='ALUMNO', date_joined__gte=since).count(),
            'orders_30d': orders_30d.count(),
            'revenue_30d': orders_30d.aggregate(t=Sum('total_amount'))['t'] or 0,
            'total_revenue': Order.objects.filter(status_id='COMPLETED').aggregate(t=Sum('total_amount'))['t'] or 0,
            'certificates_issued': Certificate.objects.count(),
        }

        return Response({
            'period': 'last_30_days',
            'kpis': business_kpis,
            'events_by_type': list(events_by_type),
            'funnel_counts': funnel_counts,
            'conversion_rates': conversion_rates,
            'top_viewed_courses': top_courses,
        })
