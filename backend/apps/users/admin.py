from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUser, Role, WalletTransactionType, WalletTransaction,
    TeacherApplicationStatus, TeacherApplication,
)

class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'avatar', 'bio', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'role'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Extra info'), {'fields': ('last_login_ip', 'is_email_verified', 'balance', 'referral_code')}),
        (_('Demostración'), {
            'fields': ('notification_email', 'can_autocomplete_demo'),
            'description': (
                'Deja completar un curso entero de un clic, saltándose las '
                'actividades. Solo para la cuenta de revisión: no lo actives '
                'en cuentas reales.'
            ),
        }),
    )
    readonly_fields = ('balance', 'referral_code')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'role'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')


@admin.register(WalletTransactionType)
class WalletTransactionTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """Libro mayor del saldo: solo lectura, se registra desde el código de negocio."""
    list_display = ('user', 'transaction_type', 'amount', 'balance_after', 'description', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('user__email', 'description')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TeacherApplicationStatus)
class TeacherApplicationStatusAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')


@admin.register(TeacherApplication)
class TeacherApplicationAdmin(admin.ModelAdmin):
    """
    Revisión de solicitudes para ser docente. El admin ve los datos y documentos
    (solo lectura) y decide el estado. Aprobar convierte al usuario en DOCENTE
    (vía la señal en signals.py); rechazar permite escribir un motivo.
    """
    list_display = ('user', 'headline', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'headline')
    ordering = ('-created_at',)
    readonly_fields = (
        'user', 'headline', 'bio', 'id_document', 'credentials_document',
        'created_at', 'reviewed_at', 'reviewed_by',
    )
    fieldsets = (
        ('Postulante', {'fields': ('user', 'headline', 'bio')}),
        ('Documentos', {'fields': ('id_document', 'credentials_document')}),
        ('Revisión', {'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'created_at')}),
    )
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']

    def _stamp_review(self, obj, request):
        obj.reviewed_by = request.user
        obj.reviewed_at = timezone.now()

    def save_model(self, request, obj, form, change):
        # Al cambiar el estado desde el formulario, dejar constancia de la revisión
        if change and 'status' in form.changed_data and obj.status_id in (
            TeacherApplicationStatus.APPROVED, TeacherApplicationStatus.REJECTED
        ):
            self._stamp_review(obj, request)
        super().save_model(request, obj, form, change)  # dispara la señal de promoción

    @admin.action(description='Aprobar solicitudes (convierte al usuario en DOCENTE)')
    def aprobar_solicitudes(self, request, queryset):
        aprobadas = 0
        for application in queryset:
            application.status_id = TeacherApplicationStatus.APPROVED
            self._stamp_review(application, request)
            application.save()  # dispara la señal que cambia el rol
            aprobadas += 1
        self.message_user(request, f'{aprobadas} solicitud(es) aprobada(s); usuarios promovidos a DOCENTE.')

    @admin.action(description='Rechazar solicitudes seleccionadas')
    def rechazar_solicitudes(self, request, queryset):
        rechazadas = queryset.exclude(status_id=TeacherApplicationStatus.APPROVED).count()
        for application in queryset.exclude(status_id=TeacherApplicationStatus.APPROVED):
            application.status_id = TeacherApplicationStatus.REJECTED
            self._stamp_review(application, request)
            application.save()
        self.message_user(request, f'{rechazadas} solicitud(es) rechazada(s).')
