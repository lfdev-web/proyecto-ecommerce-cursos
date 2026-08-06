from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, Coupon, InstructorEarning

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'get_total_price')
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price_at_purchase', 'course')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('total_amount',)


@admin.register(InstructorEarning)
class InstructorEarningAdmin(admin.ModelAdmin):
    """Comisiones de docentes: las genera el checkout, aquí solo se consultan."""
    list_display = ('instructor', 'course', 'gross_amount', 'commission_rate', 'net_amount', 'created_at')
    list_filter = ('commission_rate',)
    search_fields = ('instructor__email', 'course__title')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_pct', 'is_active', 'times_used', 'max_uses', 'valid_until')
    list_filter = ('is_active',)
    search_fields = ('code',)
    readonly_fields = ('times_used',)
