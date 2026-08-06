from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, RegisterView, ProfileView, LogoutView,
    RechargeAuthorizeView, RechargeCancelView, RechargeDetailView,
    RechargeHistoryView, RechargeStartView,
    TeacherApplicationView, WalletTransactionsView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('profile/', ProfileView.as_view(), name='auth_profile'),
    path('wallet/transactions/', WalletTransactionsView.as_view(), name='wallet_transactions'),

    # Recarga de saldo por la pasarela simulada (dos pasos: iniciar y autorizar)
    path('wallet/recharge/', RechargeStartView.as_view(), name='recharge_start'),
    path('wallet/recharge/history/', RechargeHistoryView.as_view(), name='recharge_history'),
    path('wallet/recharge/<uuid:token>/', RechargeDetailView.as_view(), name='recharge_detail'),
    path('wallet/recharge/<uuid:token>/authorize/', RechargeAuthorizeView.as_view(), name='recharge_authorize'),
    path('wallet/recharge/<uuid:token>/cancel/', RechargeCancelView.as_view(), name='recharge_cancel'),

    path('teacher-application/', TeacherApplicationView.as_view(), name='teacher_application'),
]
