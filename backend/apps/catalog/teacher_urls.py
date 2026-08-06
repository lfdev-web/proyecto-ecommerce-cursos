from django.urls import path
from .teacher_views import (
    TeacherSummaryView, TeacherCoursesView, TeacherCourseStudentsView,
    TeacherSlotRequestView, TeacherCourseCreateView, TeacherCourseDetailView,
    TeacherCourseSubmitView, TeacherLessonsView, TeacherLessonDetailView,
)

urlpatterns = [
    path('summary/', TeacherSummaryView.as_view(), name='teacher_summary'),
    path('courses/', TeacherCoursesView.as_view(), name='teacher_courses'),
    path('courses/<int:course_id>/students/', TeacherCourseStudentsView.as_view(), name='teacher_course_students'),
    path('slot-requests/', TeacherSlotRequestView.as_view(), name='teacher_slot_requests'),

    # Creación y edición de cursos por el docente
    path('courses/create/', TeacherCourseCreateView.as_view(), name='teacher_course_create'),
    path('courses/<int:course_id>/', TeacherCourseDetailView.as_view(), name='teacher_course_detail'),
    path('courses/<int:course_id>/submit/', TeacherCourseSubmitView.as_view(), name='teacher_course_submit'),
    path('courses/<int:course_id>/lessons/', TeacherLessonsView.as_view(), name='teacher_course_lessons'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/', TeacherLessonDetailView.as_view(),
         name='teacher_course_lesson_detail'),
]
