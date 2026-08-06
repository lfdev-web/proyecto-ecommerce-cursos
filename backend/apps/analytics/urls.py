from django.urls import path
from .views import LogEventView, AnalyticsDashboardView

urlpatterns = [
    path('log-event/', LogEventView.as_view(), name='analytics_log_event'),
    path('dashboard/', AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
]
