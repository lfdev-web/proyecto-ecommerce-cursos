"""
Deja la base en limpio para volver a estructurar los datos.

Borra TODO el contenido transaccional (cursos, lecciones, alumnos, órdenes,
inscripciones, certificados, exámenes, reseñas, analítica, saldos, membresías
contratadas, solicitudes) y deja únicamente tres usuarios de demostración:
un administrador, un docente y un alumno.

Se conservan a propósito las tablas de referencia: categorías, cupones, planes
de membresía y todas las tablas catálogo (roles, estados, niveles, etc.), porque
son la estructura del sistema y no datos de prueba.

Uso:
    python manage.py reset_demo_data
    python manage.py reset_demo_data --keep-files   (no borra los archivos subidos)
"""
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()

ADMIN = {'email': 'admin@demo.com', 'password': 'Admin1234!', 'first_name': 'Admin', 'last_name': 'Demo'}
DOCENTE = {'email': 'docente@demo.com', 'password': 'Demo1234!', 'first_name': 'Docente', 'last_name': 'Demo'}
ALUMNO = {'email': 'alumno@demo.com', 'password': 'Demo1234!', 'first_name': 'Alumno', 'last_name': 'Demo'}


class Command(BaseCommand):
    help = 'Borra los datos de prueba y deja solo un admin, un docente y un alumno.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-files', action='store_true',
            help='Conserva los archivos subidos (cédulas, certificados, avatares).'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.analytics.models import ConversionFunnel, NavigationLog
        from apps.catalog.models import Course, CourseSlotRequest, Lesson, Review
        from apps.exams.models import AnswerOption, AttemptAnswer, Exam, ExamAttempt, Question
        from apps.catalog.models import Assignment
        from apps.library.models import (
            AssignmentSubmission, Certificate, Enrollment, LessonProgress, StudyStreak, WishlistItem,
        )
        from apps.memberships.models import MembershipPayment, UserMembership
        from apps.orders.models import Cart, CartItem, InstructorEarning, Order, OrderItem
        from apps.recommendations.models import RecommendationCache, UserCourseInteraction
        from apps.users.models import TeacherApplication, WalletTransaction

        # El orden importa: primero lo que apunta a cursos/usuarios con PROTECT.
        borrado = [
            ('Respuestas de examen', AttemptAnswer),
            ('Intentos de examen', ExamAttempt),
            ('Opciones de pregunta', AnswerOption),
            ('Preguntas', Question),
            ('Exámenes', Exam),
            ('Entregas de trabajo', AssignmentSubmission),
            ('Trabajos prácticos', Assignment),
            ('Certificados', Certificate),
            ('Progreso de lecciones', LessonProgress),
            ('Inscripciones', Enrollment),
            ('Rachas de estudio', StudyStreak),
            ('Wishlist', WishlistItem),
            ('Comisiones de docente', InstructorEarning),
            ('Items de orden', OrderItem),
            ('Órdenes', Order),
            ('Items de carrito', CartItem),
            ('Carritos', Cart),
            ('Reseñas', Review),
            ('Interacciones (ML)', UserCourseInteraction),
            ('Caché de recomendaciones', RecommendationCache),
            ('Logs de navegación', NavigationLog),
            ('Funnel de conversión', ConversionFunnel),
            ('Movimientos de saldo', WalletTransaction),
            ('Pagos de membresía', MembershipPayment),
            ('Membresías contratadas', UserMembership),
            ('Solicitudes de espacio', CourseSlotRequest),
            ('Solicitudes de docente', TeacherApplication),
            ('Lecciones', Lesson),
            ('Cursos', Course),
        ]

        self.stdout.write(self.style.WARNING('Borrando datos...'))
        for etiqueta, modelo in borrado:
            total, _ = modelo.objects.all().delete()
            self.stdout.write(f'  {etiqueta}: {total}')

        usuarios_borrados, _ = User.objects.all().delete()
        self.stdout.write(f'  Usuarios: {usuarios_borrados}')

        # Archivos subidos (documentos de solicitudes y avatares)
        if not options['keep_files']:
            for carpeta in ('teacher_applications', 'avatars'):
                ruta = settings.MEDIA_ROOT / carpeta
                if ruta.exists():
                    shutil.rmtree(ruta, ignore_errors=True)
                    self.stdout.write(f'  Archivos borrados: {carpeta}/')

        # --- Usuarios de demostración ---
        # Compartido con seed_demo_data: las cuentas deben ser las mismas se
        # llegue por donde se llegue.
        from apps.common.demo_accounts import CUENTAS, crear_cuentas_demo
        crear_cuentas_demo(log=lambda _: None)

        self.stdout.write(self.style.SUCCESS('\nBase reiniciada. Usuarios disponibles:'))
        for email, clave, _, _, rol in CUENTAS:
            self.stdout.write(f'  {rol:<8} {email:<20} / {clave}')
        self.stdout.write(
            '\nSe conservaron categorías, cupones, planes de membresía y las tablas catálogo.'
        )
