from django.urls import path
from .views import CartView, CartItemAddView, CartItemRemoveView, CheckoutView, OrderListView

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/add/<int:course_id>/', CartItemAddView.as_view(), name='cart-item-add'),
    path('cart/remove/<int:course_id>/', CartItemRemoveView.as_view(), name='cart-item-remove'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('history/', OrderListView.as_view(), name='order-history'),
]
