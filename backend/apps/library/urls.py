from django.urls import path
from .views import (
    MyLibraryView, MarkLessonProgressView, CertificateDownloadView,
    WishlistView, WishlistItemAddView, WishlistItemRemoveView, StudyStreakView,
    EnrollmentLessonsView, LessonContentView, AchievementsView,
)

urlpatterns = [
    path('my-courses/', MyLibraryView.as_view(), name='my_library'),
    path('<int:enrollment_id>/lessons/', EnrollmentLessonsView.as_view(), name='enrollment_lessons'),
    path('<int:enrollment_id>/lessons/<int:lesson_id>/content/', LessonContentView.as_view(), name='lesson_content'),
    path('<int:enrollment_id>/progress/<int:lesson_id>/', MarkLessonProgressView.as_view(), name='mark_lesson_progress'),
    path('<int:enrollment_id>/certificate/', CertificateDownloadView.as_view(), name='certificate_download'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/add/<int:course_id>/', WishlistItemAddView.as_view(), name='wishlist_add'),
    path('wishlist/remove/<int:course_id>/', WishlistItemRemoveView.as_view(), name='wishlist_remove'),
    path('streak/', StudyStreakView.as_view(), name='study_streak'),
    path('achievements/', AchievementsView.as_view(), name='achievements'),
]
