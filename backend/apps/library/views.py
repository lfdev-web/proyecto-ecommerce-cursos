from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from .actividades import estado_actividades
from .models import (
    Achievement, AssignmentSubmission, Certificate, Enrollment, LessonProgress,
    StudyStreak, UserAchievement, WishlistItem, TAMANO_MAX_ENTREGA,
)
from .serializers import EnrollmentSerializer, WishlistItemSerializer, StudyStreakSerializer
from .achievements import evaluate_achievements


class MyLibraryView(generics.ListAPIView):
    """
    Devuelve todos los cursos a los que el usuario tiene acceso (comprados + membresía).
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Precargamos lo que el serializer recorre por inscripción (progreso de
        # lecciones, intentos de examen y certificado) para no disparar N+1.
        return (
            Enrollment.objects
            .filter(user=self.request.user)
            .select_related('course', 'course__category', 'certificate')
            .prefetch_related('lesson_progresses', 'exam_attempts')
            .order_by('-enrolled_at')
        )


class EnrollmentLessonsView(APIView):
    """
    Temario del curso para un alumno inscrito: todas las lecciones en orden
    con su estado de completado. NO incluye el contenido (ver LessonContentView).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        completed_ids = set(
            LessonProgress.objects.filter(enrollment=enrollment, is_completed=True)
            .values_list('lesson_id', flat=True)
        )
        lessons = enrollment.course.lessons.order_by('order')
        return Response({
            'course_title': enrollment.course.title,
            'course_id': enrollment.course_id,
            'progress_percentage': enrollment.progress_percentage,
            'is_completed': enrollment.is_completed,
            'lessons': [
                {
                    'id': lesson.id,
                    'title': lesson.title,
                    'order': lesson.order,
                    'duration_minutes': lesson.duration_minutes,
                    'is_completed': lesson.id in completed_ids,
                }
                for lesson in lessons
            ],
            # Las dos actividades evaluadas viajan aquí para que el reproductor
            # las muestre sin una segunda petición.
            'activities': estado_actividades(enrollment),
        })


class CourseActivitiesView(APIView):
    """
    Estado de las dos actividades del curso: cuestionario y trabajo práctico.
    Es lo que decide si el alumno puede certificarse, así que se calcula en el
    servidor y no en el navegador.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        from .actividades import curso_terminado
        estado = estado_actividades(enrollment)
        return Response({
            'course_title': enrollment.course.title,
            'course_id': enrollment.course_id,
            'activities': estado,
            'can_certify': curso_terminado(enrollment, estado),
            'has_certificate': Certificate.objects.filter(enrollment=enrollment).exists(),
        })


class AssignmentSubmitView(APIView):
    """
    Entrega del trabajo práctico (Actividad 2). Recibe un archivo y un
    comentario opcional. Al aceptarse, si el curso ya cumple el resto de los
    requisitos, la señal de siempre emite el certificado.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, enrollment_id):
        from apps.catalog.models import Assignment
        from .models import EXTENSIONES_ENTREGA
        from .signals import _issue_certificate_if_needed

        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        assignment = get_object_or_404(Assignment, course=enrollment.course, is_active=True)

        if enrollment.progress_percentage < 100.0:
            return Response(
                {'detail': 'Completa todas las lecciones antes de entregar el trabajo.'},
                status=status.HTTP_400_BAD_REQUEST)

        if AssignmentSubmission.objects.filter(enrollment=enrollment).exists():
            return Response({'detail': 'Ya entregaste el trabajo de este curso.'},
                            status=status.HTTP_400_BAD_REQUEST)

        archivo = request.FILES.get('file')
        if not archivo:
            return Response({'detail': 'Adjunta el archivo de tu entrega.'},
                            status=status.HTTP_400_BAD_REQUEST)

        extension = archivo.name.rsplit('.', 1)[-1].lower() if '.' in archivo.name else ''
        if extension not in EXTENSIONES_ENTREGA:
            return Response(
                {'detail': f'Formato no permitido. Acepta: {", ".join(EXTENSIONES_ENTREGA)}.'},
                status=status.HTTP_400_BAD_REQUEST)
        if archivo.size > TAMANO_MAX_ENTREGA:
            return Response(
                {'detail': f'El archivo supera los {TAMANO_MAX_ENTREGA // (1024 * 1024)} MB.'},
                status=status.HTTP_400_BAD_REQUEST)

        AssignmentSubmission.objects.create(
            enrollment=enrollment,
            assignment=assignment,
            file=archivo,
            comment=request.data.get('comment', '')[:2000],
        )

        # La entrega puede ser la última pieza que faltaba para el certificado.
        _issue_certificate_if_needed(enrollment)
        evaluate_achievements(request.user)

        return Response({
            'detail': 'Trabajo entregado.',
            'activities': estado_actividades(enrollment),
            'certificate_issued': Certificate.objects.filter(enrollment=enrollment).exists(),
        }, status=status.HTTP_201_CREATED)


class DemoCompleteView(APIView):
    """
    Atajo de la cuenta de revisión: da por cumplido un curso — o todos — para
    poder llegar al certificado sin recorrer las lecciones una por una.

    Reservado a los usuarios con `can_autocomplete_demo`, y limitado a sus
    propias inscripciones. Cualquier otro recibe 403.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, enrollment_id=None):
        if not request.user.can_autocomplete_demo:
            return Response(
                {'detail': 'Tu cuenta no tiene habilitado el recorrido rápido.'},
                status=status.HTTP_403_FORBIDDEN)

        from .demo import completar_inscripcion

        if enrollment_id is not None:
            inscripciones = [get_object_or_404(
                Enrollment, id=enrollment_id, user=request.user)]
        else:
            inscripciones = list(
                Enrollment.objects.filter(user=request.user)
                .select_related('course').order_by('id'))

        if not inscripciones:
            return Response(
                {'detail': 'No tienes cursos en tu biblioteca todavía.'},
                status=status.HTTP_400_BAD_REQUEST)

        resultados = [completar_inscripcion(e) for e in inscripciones]
        nuevos = sum(1 for r in resultados if r['certificado_nuevo'])
        previos = sum(1 for r in resultados if r['certificado']) - nuevos

        # El correo del certificado sale UNA sola vez, al emitirlo. Decir
        # "emitidos, salen por correo" cuando ya existían haría esperar unos
        # correos que nunca van a llegar.
        partes = [f'{len(resultados)} curso(s) completado(s).']
        if nuevos:
            partes.append(f'{nuevos} certificado(s) emitido(s) ahora — esos salen por correo.')
        if previos:
            partes.append(
                f'{previos} ya estaban emitidos de antes: se descargan desde la '
                f'biblioteca, pero no se reenvían por correo.')
        if not nuevos and not previos:
            partes.append('Ningún certificado: revisa que los cursos tengan sus actividades.')

        return Response({
            'detail': ' '.join(partes),
            'certificados_nuevos': nuevos,
            'certificados_previos': previos,
            'cursos': resultados,
        })


class LessonContentView(APIView):
    """
    Contenido real de una lección (video y texto). Protegido: solo lo recibe
    un usuario con inscripción a ese curso — así el video_url no se filtra
    a quien no compró (antes viajaba en el detalle público del curso).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enrollment_id, lesson_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)

        from apps.catalog.models import Lesson
        lesson = get_object_or_404(Lesson, id=lesson_id, course=enrollment.course)

        progress = LessonProgress.objects.filter(enrollment=enrollment, lesson=lesson).first()
        return Response({
            'id': lesson.id,
            'title': lesson.title,
            'order': lesson.order,
            'duration_minutes': lesson.duration_minutes,
            'video_url': lesson.video_url,
            'content': lesson.content,
            'is_completed': bool(progress and progress.is_completed),
            'watch_percentage': progress.watch_percentage if progress else 0.0,
        })


class MarkLessonProgressView(APIView):
    """
    Endpoint para marcar una lección como completada o en progreso.
    Automáticamente recalcula el progreso del curso completo.
    El signal post_save activa el trigger al 20% para el motor de recomendaciones.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, enrollment_id, lesson_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)

        from apps.catalog.models import Lesson
        lesson = get_object_or_404(Lesson, id=lesson_id, course=enrollment.course)

        is_completed = request.data.get('is_completed', True)
        watch_percentage = request.data.get('watch_percentage', 100.0)

        lesson_progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={
                'is_completed': is_completed,
                'watch_percentage': watch_percentage,
            }
        )

        if not created:
            lesson_progress.is_completed = is_completed
            lesson_progress.watch_percentage = watch_percentage
            lesson_progress.save()

        return Response({
            'lesson': lesson.title,
            'is_completed': lesson_progress.is_completed,
            'course_progress': enrollment.progress_percentage,
            'course_completed': enrollment.is_completed,
        }, status=status.HTTP_200_OK)


class CertificateDownloadView(APIView):
    """
    Genera y descarga el PDF del certificado (simulado) de un curso completado.
    El Certificate ya fue creado automáticamente por la señal en signals.py
    cuando el Enrollment llegó al 100% — este endpoint solo lo renderiza en PDF.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        certificate = get_object_or_404(Certificate, enrollment=enrollment)

        # El PDF se renderiza desde el snapshot histórico guardado al emitir:
        # aunque el curso o el usuario cambien después, el documento no cambia.
        html_string = render_to_string('library/certificate.html', {
            'student_name': certificate.student_name or (
                f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
            ),
            'course_title': certificate.course_title or enrollment.course.title,
            'course_duration_hours': certificate.course_duration_hours,
            'issued_at': certificate.issued_at.strftime('%d/%m/%Y'),
            'verification_code': certificate.verification_code,
        })

        from weasyprint import HTML
        pdf_bytes = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificado-{enrollment.course.slug}.pdf"'
        return response


class WishlistView(generics.ListAPIView):
    """
    Lista los cursos guardados en la wishlist del usuario.
    """
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('course', 'course__category')


class WishlistItemAddView(APIView):
    """
    Agrega un curso a la wishlist y registra la interacción para el motor de recomendaciones.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        from apps.catalog.models import Course
        from apps.recommendations.models import UserCourseInteraction

        course = get_object_or_404(Course, id=course_id, is_active=True, status_id='PUBLISHED')

        item, created = WishlistItem.objects.get_or_create(user=request.user, course=course)
        if not created:
            return Response({'detail': 'El curso ya está en tu wishlist.'}, status=status.HTTP_400_BAD_REQUEST)

        UserCourseInteraction.objects.get_or_create(
            user=request.user,
            course=course,
            interaction_type_id='WISHLIST'
        )

        return Response({'detail': 'Curso agregado a tu wishlist.'}, status=status.HTTP_201_CREATED)


class WishlistItemRemoveView(APIView):
    """
    Elimina un curso de la wishlist del usuario.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, course_id):
        item = get_object_or_404(WishlistItem, user=request.user, course_id=course_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AchievementsView(APIView):
    """
    Catálogo completo de medallas con el estado del usuario (ganada o no).
    Antes de responder re-evalúa las reglas: eso otorga medallas pendientes
    y auto-repara a los usuarios históricos del seed (creados sin señales).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        evaluate_achievements(request.user)

        earned = {
            ua.achievement_id: ua.earned_at
            for ua in UserAchievement.objects.filter(user=request.user)
        }
        return Response({
            'total': Achievement.objects.count(),
            'earned_count': len(earned),
            'achievements': [
                {
                    'code': a.code,
                    'name': a.name,
                    'description': a.description,
                    'icon': a.icon,
                    'earned': a.code in earned,
                    'earned_at': earned.get(a.code),
                }
                for a in Achievement.objects.all()
            ],
        })


class StudyStreakView(generics.RetrieveAPIView):
    """
    Devuelve la racha de estudio actual del usuario (se crea vacía si aún no existe).
    """
    serializer_class = StudyStreakSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        streak, _ = StudyStreak.objects.get_or_create(user=self.request.user)
        return streak
