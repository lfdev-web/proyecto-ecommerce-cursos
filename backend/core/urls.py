from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # OpenAPI Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/catalog/', include('apps.catalog.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/library/', include('apps.library.urls')),
    path('api/memberships/', include('apps.memberships.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/exams/', include('apps.exams.urls')),
    path('api/teacher/', include('apps.catalog.teacher_urls')),
]

# En desarrollo, Django sirve los archivos subidos (documentos de solicitudes,
# avatares). En producción esto lo sirve nginx (ver configuración de deploy).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
