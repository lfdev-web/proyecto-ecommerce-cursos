"""
Panel Docente: endpoints de solo lectura para que el instructor vea sus
cursos, alumnos e ingresos. La creación/edición de cursos pasa por Django
Admin (flujo de aprobación del administrador, como Udemy con instructores nuevos).
"""
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.library.models import Enrollment
from apps.orders.models import InstructorEarning
from django.db import transaction
from django.utils.text import slugify

from .models import (
    Course, Lesson, Review, CourseSlotRequest, SlotRequestStatus, CourseStatus,
)
from .serializers import (
    CourseSlotRequestSerializer, TeacherCourseSerializer, TeacherLessonSerializer,
)


class IsDocente(permissions.BasePermission):
    """Solo docentes (o admin) pueden ver el panel de instructor."""
    message = 'Solo los docentes pueden acceder al panel de instructor.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role_id in ('DOCENTE', 'ADMIN')


class TeacherSummaryView(APIView):
    """KPIs globales del docente: cursos, alumnos, ingresos y calificación."""
    permission_classes = [IsDocente]

    def get(self, request):
        courses = Course.objects.filter(instructor=request.user)
        earnings = InstructorEarning.objects.filter(instructor=request.user)
        month_ago = timezone.now() - timezone.timedelta(days=30)

        return Response({
            'total_courses': courses.count(),
            'total_students': Enrollment.objects.filter(course__in=courses).count(),
            'total_earnings': earnings.aggregate(t=Sum('net_amount'))['t'] or 0,
            'earnings_last_30_days': earnings.filter(created_at__gte=month_ago).aggregate(t=Sum('net_amount'))['t'] or 0,
            'average_rating': Review.objects.filter(course__in=courses).aggregate(a=Avg('rating'))['a'],
            # El porcentaje depende del plan activo (Docente Oro = 80%), no es fijo:
            # el panel lo mostraba siempre como 70% y engañaba a los docentes con plan.
            'commission_rate': InstructorEarning.get_commission_rate_for(request.user),
        })


class TeacherCoursesView(APIView):
    """Los cursos del docente con alumnos, calificación e ingresos por curso."""
    permission_classes = [IsDocente]

    def get(self, request):
        courses = Course.objects.filter(instructor=request.user).select_related('category', 'status')

        # Métricas por curso en queries separadas (evita la inflación de
        # combinar Count/Avg/Sum sobre múltiples joins en una sola query)
        students = dict(
            Enrollment.objects.filter(course__in=courses)
            .values_list('course_id').annotate(n=Count('id'))
        )
        ratings = dict(
            Review.objects.filter(course__in=courses)
            .values_list('course_id').annotate(a=Avg('rating'))
        )
        earned = dict(
            InstructorEarning.objects.filter(course__in=courses)
            .values_list('course_id').annotate(t=Sum('net_amount'))
        )

        return Response([
            {
                'id': course.id,
                'title': course.title,
                'category_name': course.category.name,
                'price': course.price,
                'is_active': course.is_active,
                'status': course.status_id,
                'status_name': course.status.name,
                'review_notes': course.review_notes,
                'is_best_seller': course.is_best_seller,
                'students_count': students.get(course.id, 0),
                'average_rating': round(ratings[course.id], 2) if course.id in ratings else None,
                'total_earned': earned.get(course.id, 0),
            }
            for course in courses
        ])


class TeacherSlotRequestView(APIView):
    """
    Portal de espacios de curso del docente.
    GET  -> resumen de cupos de su plan + historial de solicitudes.
    POST -> envía una solicitud de espacio para un curso nuevo.
    """
    permission_classes = [IsDocente]

    def get(self, request):
        requests_qs = (
            CourseSlotRequest.objects
            .filter(teacher=request.user)
            .select_related('status', 'proposed_category', 'created_course')
        )
        return Response({
            'summary': CourseSlotRequest.slot_summary(request.user),
            'requests': CourseSlotRequestSerializer(requests_qs, many=True).data,
        })

    def post(self, request):
        summary = CourseSlotRequest.slot_summary(request.user)

        if not summary['has_active_plan']:
            return Response(
                {'detail': 'Necesitas un plan de docente activo para solicitar espacios de curso.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if summary['available'] <= 0:
            return Response(
                {'detail': 'Ya usaste todos los cupos de tu plan. Mejora tu plan para publicar más cursos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if summary['pending_requests'] > 0:
            return Response(
                {'detail': 'Ya tienes una solicitud pendiente de revisión.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CourseSlotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(teacher=request.user, status_id=SlotRequestStatus.PENDING)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def _unique_slug(title):
    """Slug único a partir del título (el modelo lo exige único)."""
    base = slugify(title)[:180] or 'curso'
    slug, n = base, 2
    while Course.objects.filter(slug=slug).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


class TeacherCourseCreateView(APIView):
    """
    Crea un curso nuevo consumiendo un espacio aprobado por el administrador.
    El curso nace en BORRADOR: no aparece en el catálogo hasta que el docente
    lo envíe a revisión y el admin lo apruebe.
    """
    permission_classes = [IsDocente]

    @transaction.atomic
    def post(self, request):
        slot = (
            CourseSlotRequest.objects
            .select_for_update()
            .filter(teacher=request.user, status_id=SlotRequestStatus.APPROVED, is_consumed=False)
            .order_by('created_at')
            .first()
        )
        if not slot:
            return Response(
                {'detail': 'No tienes ningún espacio aprobado. Solicita un espacio de curso primero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TeacherCourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save(
            instructor=request.user,
            slug=_unique_slug(serializer.validated_data['title']),
            status_id=CourseStatus.DRAFT,
            is_active=True,
        )

        slot.is_consumed = True
        slot.created_course = course
        slot.save(update_fields=['is_consumed', 'created_course'])

        return Response(TeacherCourseSerializer(course).data, status=status.HTTP_201_CREATED)


class TeacherCourseDetailView(APIView):
    """
    Ver, editar y enviar a revisión un curso propio.
    Solo se puede editar mientras esté en BORRADOR o DEVUELTO.
    """
    permission_classes = [IsDocente]

    def _get_course(self, request, course_id):
        return get_object_or_404(Course, id=course_id, instructor=request.user)

    def get(self, request, course_id):
        course = self._get_course(request, course_id)
        return Response({
            'course': TeacherCourseSerializer(course).data,
            'lessons': TeacherLessonSerializer(course.lessons.order_by('order'), many=True).data,
        })

    def patch(self, request, course_id):
        course = self._get_course(request, course_id)
        if course.status_id not in (CourseStatus.DRAFT, CourseStatus.REJECTED):
            return Response(
                {'detail': 'Solo puedes editar el curso mientras está en borrador o devuelto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = TeacherCourseSerializer(course, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TeacherCourseSubmitView(APIView):
    """Envía el curso a revisión del administrador."""
    permission_classes = [IsDocente]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, instructor=request.user)

        if course.status_id not in (CourseStatus.DRAFT, CourseStatus.REJECTED):
            return Response(
                {'detail': 'Este curso ya fue enviado o está publicado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if course.lessons.count() == 0:
            return Response(
                {'detail': 'Agrega al menos una lección antes de enviar el curso a revisión.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course.status_id = CourseStatus.IN_REVIEW
        course.submitted_at = timezone.now()
        course.review_notes = ''
        course.save(update_fields=['status', 'submitted_at', 'review_notes'])
        return Response({'detail': 'Curso enviado a revisión.', 'status': course.status_id})


class TeacherLessonsView(APIView):
    """Crea lecciones dentro de un curso propio (solo en borrador o devuelto)."""
    permission_classes = [IsDocente]

    def _editable_course(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        if course.status_id not in (CourseStatus.DRAFT, CourseStatus.REJECTED):
            return None, Response(
                {'detail': 'Solo puedes editar las lecciones mientras el curso está en borrador o devuelto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return course, None

    def post(self, request, course_id):
        course, error = self._editable_course(request, course_id)
        if error:
            return error
        serializer = TeacherLessonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Si no mandan orden, va al final del temario
        order = serializer.validated_data.get('order') or (course.lessons.count() + 1)
        serializer.save(course=course, order=order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeacherLessonDetailView(APIView):
    """Edita o elimina una lección de un curso propio."""
    permission_classes = [IsDocente]

    def _get(self, request, course_id, lesson_id):
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        return course, lesson

    def patch(self, request, course_id, lesson_id):
        course, lesson = self._get(request, course_id, lesson_id)
        if course.status_id not in (CourseStatus.DRAFT, CourseStatus.REJECTED):
            return Response({'detail': 'El curso no es editable en este estado.'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = TeacherLessonSerializer(lesson, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, course_id, lesson_id):
        course, lesson = self._get(request, course_id, lesson_id)
        if course.status_id not in (CourseStatus.DRAFT, CourseStatus.REJECTED):
            return Response({'detail': 'El curso no es editable en este estado.'},
                            status=status.HTTP_400_BAD_REQUEST)
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherCourseStudentsView(APIView):
    """Alumnos inscritos en un curso del docente, con su progreso."""
    permission_classes = [IsDocente]

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        enrollments = (
            Enrollment.objects.filter(course=course)
            .select_related('user')
            .order_by('-enrolled_at')
        )
        return Response({
            'course_title': course.title,
            'students': [
                {
                    'name': f'{e.user.first_name} {e.user.last_name}'.strip() or e.user.email,
                    'email': e.user.email,
                    'enrolled_at': e.enrolled_at,
                    'progress_percentage': e.progress_percentage,
                    'is_completed': e.is_completed,
                }
                for e in enrollments
            ],
        })
