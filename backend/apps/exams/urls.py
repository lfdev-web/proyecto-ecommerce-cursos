from django.urls import path

from .views import CourseExamInfoView, StartAttemptView, SubmitAttemptView

urlpatterns = [
    path('course/<int:course_id>/', CourseExamInfoView.as_view(), name='exam-info'),
    path('course/<int:course_id>/start/', StartAttemptView.as_view(), name='exam-start'),
    path('attempts/<int:attempt_id>/submit/', SubmitAttemptView.as_view(), name='exam-submit'),
]
