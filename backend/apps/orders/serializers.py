from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from apps.catalog.serializers import CourseListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'course', 'course_id', 'added_at')


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(source='get_total_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'items', 'total_price', 'updated_at')


class CheckoutSerializer(serializers.Serializer):
    card_number = serializers.CharField(
        max_length=19,
        write_only=True,
        help_text="Número de tarjeta para validación Luhn (no se almacena)"
    )
    coupon_code = serializers.CharField(
        max_length=30,
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Código de cupón de descuento (opcional)"
    )

    def validate_card_number(self, value):
        from .utils.luhn import is_valid_luhn
        if not is_valid_luhn(value):
            raise serializers.ValidationError("Número de tarjeta inválido. Por favor verifica los datos.")
        return value

    def validate_coupon_code(self, value):
        if not value:
            return value
        from .models import Coupon
        try:
            coupon = Coupon.objects.get(code__iexact=value)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Cupón no encontrado.")
        if not coupon.is_valid():
            raise serializers.ValidationError("Este cupón ya no es válido.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'course', 'price_at_purchase')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'status', 'total_amount', 'created_at', 'items')
