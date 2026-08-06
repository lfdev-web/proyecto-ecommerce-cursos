from django.urls import path
from .views import MembershipPlanListView, SubscribeView, MyMembershipView, CancelMembershipView

urlpatterns = [
    path('plans/', MembershipPlanListView.as_view(), name='membership_plans'),
    path('subscribe/', SubscribeView.as_view(), name='membership_subscribe'),
    path('my-status/', MyMembershipView.as_view(), name='membership_status'),
    path('cancel/', CancelMembershipView.as_view(), name='membership_cancel'),
]
