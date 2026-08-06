from django.urls import path
from .views import RecommendationsForUserView, SimilarCoursesView, TrackInteractionView

urlpatterns = [
    path('for-me/', RecommendationsForUserView.as_view(), name='recommendations_for_user'),
    path('similar/<int:course_id>/', SimilarCoursesView.as_view(), name='similar_courses'),
    path('track/', TrackInteractionView.as_view(), name='track_interaction'),
]
