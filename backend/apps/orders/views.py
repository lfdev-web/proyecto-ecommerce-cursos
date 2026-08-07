from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem, OrderStatus, Coupon
from .serializers import CartSerializer, CheckoutSerializer, OrderSerializer
from apps.catalog.models import Course


class CartView(generics.RetrieveAPIView):
    """
    Recupera el carrito del usuario. Si no existe, lo crea.
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemAddView(APIView):
    """
    Agrega un curso al carrito.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Solo se puede comprar un curso publicado (no borradores ni en revisión)
        course = get_object_or_404(Course, id=course_id, is_active=True, status_id='PUBLISHED')
        
        # Verificar si ya está en el carrito
        if CartItem.objects.filter(cart=cart, course=course).exists():
            return Response({'detail': 'El curso ya está en el carrito.'}, status=status.HTTP_400_BAD_REQUEST)
            
        CartItem.objects.create(cart=cart, course=course)
        return Response({'detail': 'Curso agregado al carrito.'}, status=status.HTTP_201_CREATED)


class CartItemRemoveView(APIView):
    """
    Elimina un curso del carrito.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, course_id):
        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(CartItem, cart=cart, course_id=course_id)
        item.delete()
        return Response({'detail': 'Curso eliminado del carrito.'}, status=status.HTTP_204_NO_CONTENT)


class CheckoutView(APIView):
    """
    Procesa el pago del carrito. Combina dos validaciones independientes:
    1. Luhn sobre el número de tarjeta simulado (formato de tarjeta válido).
    2. Saldo del wallet simulado del usuario (fondos suficientes).
    Crea la Orden, descuenta el saldo, limpia el carrito e inscribe al usuario en los cursos.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_object_or_404(Cart, user=request.user)
        items = cart.items.select_related('course').all()

        if not items.exists():
            return Response({'detail': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        # Últimos 4 dígitos de la tarjeta simulada (nunca se almacena el PAN completo — PCI-DSS)
        card_number = serializer.validated_data['card_number']
        card_last4 = card_number.replace(' ', '').replace('-', '')[-4:]

        from decimal import Decimal
        # Se parte del precio EFECTIVO: si el curso está en promoción vigente,
        # la base del cálculo es el precio rebajado. El descuento por cupón o
        # membresía se aplica después, sobre ese monto ya rebajado.
        original_amount = sum(item.course.effective_price for item in items)

        # --- Descuentos: se aplica el MAYOR entre el cupón y la membresía activa,
        # no se suman (el cliente recibe el mejor descuento disponible). ---
        coupon = None
        coupon_pct = Decimal('0')
        coupon_code = serializer.validated_data.get('coupon_code')
        if coupon_code:
            coupon = Coupon.objects.select_for_update().get(code__iexact=coupon_code)
            if not coupon.is_valid():
                return Response({'detail': 'Este cupón ya no es válido.'}, status=status.HTTP_400_BAD_REQUEST)
            coupon_pct = coupon.discount_pct

        # Descuento de miembro si tiene una membresía de ALUMNO vigente
        from apps.memberships.models import PlanAudience, UserMembership
        membership_pct = Decimal('0')
        membership = (
            UserMembership.objects
            .filter(user=request.user, audience_id=PlanAudience.ALUMNO)
            .select_related('plan')
            .first()
        )
        if membership and membership.is_currently_active:
            membership_pct = membership.plan.member_discount_pct

        # El mejor descuento gana. Si el cupón no supera a la membresía, no se consume.
        use_coupon = coupon is not None and coupon_pct >= membership_pct and coupon_pct > 0
        best_pct = coupon_pct if use_coupon else max(membership_pct, Decimal('0'))
        if not use_coupon:
            coupon = None  # no marcamos ni registramos un cupón que no se aplicó

        discount_amount = (original_amount * best_pct / Decimal('100')).quantize(Decimal('0.01'))
        total_amount = original_amount - discount_amount

        # Bloquear la fila del usuario para evitar condiciones de carrera sobre el saldo
        user = type(request.user).objects.select_for_update().get(pk=request.user.pk)
        if user.balance < total_amount:
            return Response({
                'detail': 'Saldo insuficiente para completar la compra.',
                'balance': user.balance,
                'total_amount': total_amount,
            }, status=status.HTTP_400_BAD_REQUEST)

        user.balance -= total_amount
        user.save(update_fields=['balance'])

        if coupon:
            coupon.times_used += 1
            coupon.save(update_fields=['times_used'])

        # Crear la Orden con la auditoría del pago simulado
        order = Order.objects.create(
            user=request.user,
            status_id=OrderStatus.COMPLETED,
            total_amount=total_amount,
            coupon=coupon,
            discount_amount=original_amount - total_amount,
            card_last4=card_last4,
            transaction_reference=f"DEMO-{timezone.now().timestamp():.0f}",
        )

        # Registrar el egreso en el libro mayor del saldo simulado
        from apps.users.models import WalletTransactionType, record_wallet_transaction
        record_wallet_transaction(
            user, WalletTransactionType.PURCHASE, -total_amount,
            description=f'Compra de cursos — Orden #{order.id}'
        )

        # Mover items a OrderItem y matricular
        from apps.library.models import Enrollment, EnrollmentType
        from .models import InstructorEarning
        for item in items:
            order_item = OrderItem.objects.create(
                order=order,
                course=item.course,
                # Precio EFECTIVO, no el de lista: si el curso estaba en
                # promoción, es lo que realmente se cobró. Guardar el de lista
                # descuadraría la factura (las líneas no sumarían el total) y,
                # peor, la comisión del docente se calcularía sobre un monto
                # que la plataforma nunca cobró.
                price_at_purchase=item.course.effective_price
            )
            # Comisión del docente por la venta (70/30, si el curso tiene instructor)
            InstructorEarning.create_for_order_item(order_item)
            # Inscribir al usuario en el curso
            Enrollment.objects.get_or_create(
                user=request.user,
                course=item.course,
                defaults={'enrollment_type_id': EnrollmentType.PURCHASED}
            )
            
        # Limpiar carrito
        items.delete()

        # La factura se envía por Celery y solo DESPUÉS de confirmar la
        # transacción: el cobro ya está hecho y no debe depender de que el
        # servidor de correo responda. Si el SMTP falla, la compra sigue siendo
        # válida y el fallo queda en el log.
        from django.db import transaction as _tx
        from apps.common.emails import enviar_factura
        orden_id = order.id
        _tx.on_commit(lambda: enviar_factura.delay(orden_id))

        return Response({
            'detail': 'Compra completada exitosamente.',
            'order_id': order.id
        }, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """
    Historial de compras del usuario.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
