from django.contrib import admin
from .models import NavigationLog, ConversionFunnel


@admin.register(NavigationLog)
class NavigationLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'session_id', 'ip_address', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('user__email', 'session_id')
    readonly_fields = ('timestamp',)


@admin.register(ConversionFunnel)
class ConversionFunnelAdmin(admin.ModelAdmin):
    list_display = ('stage', 'user', 'session_id', 'course_id', 'reached_at')
    list_filter = ('stage',)
    readonly_fields = ('reached_at',)
