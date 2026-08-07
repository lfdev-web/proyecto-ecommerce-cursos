from django.urls import path
from .views import (
    CategoryListView, CourseListView, CourseDetailView, PromotedCoursesView,
    ReviewCreateView,
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    # Antes de <slug:slug> para que "promociones" no se interprete como el
    # slug de un curso.
    path('courses/promociones/', PromotedCoursesView.as_view(), name='course-promos'),
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/<slug:slug>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:course_id>/reviews/', ReviewCreateView.as_view(), name='course-review-create'),
]
