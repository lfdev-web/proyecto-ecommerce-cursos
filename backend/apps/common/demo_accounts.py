"""
Las cuentas conocidas para recorrer la aplicación.

Vive aquí y no dentro del seed porque hacen falta por dos caminos distintos:
al sembrar la base desde cero, y suelto en un servidor que YA está sembrado
(scripts/crear_usuarios_demo.py). Si cada camino tuviera su propia copia,
tarde o temprano crearían cuentas distintas.
"""
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.utils import timezone

# email, contraseña, nombre, apellido, rol
CUENTAS = [
    ('admin@demo.com', 'Admin1234!', 'Admin', 'Demo', 'ADMIN'),
    ('docente@demo.com', 'Demo1234!', 'Docente', 'Demo', 'DOCENTE'),
    ('alumno@demo.com', 'Demo1234!', 'Alumno', 'Demo', 'ALUMNO'),
    # Cuenta de revisión: puede dar por completado un curso de un clic para
    # llegar al certificado sin recorrer las lecciones una por una.
    ('revisor@demo.com', 'Demo1234!', 'Revisor', 'Demo', 'ALUMNO'),
]

REVISOR = 'revisor@demo.com'
# Cursos con los que arranca la cuenta de revisión. Se eligen de categorías
# distintas para que el recorrido no se vea repetitivo, y son los que ya
# tenían examen: así el cuestionario que se aprueba tiene preguntas de verdad.
CURSOS_REVISOR = [
    'Python desde cero',
    'React en la práctica',
    'SQL para análisis de datos',
    'Docker desde cero',
    'Fundamentos de ciberseguridad',
    'Análisis de datos con Python y Pandas',
]


def crear_cuentas_demo(log=print):
    """
    Crea las cuentas que falten (idempotente) y devuelve cuántas creó.
    Nunca toca las que ya existen: en el servidor pueden tener historial.
    """
    from apps.users.models import (
        INITIAL_WALLET_BALANCE, CustomUser, WalletTransaction, WalletTransactionType,
    )

    creadas = 0
    for email, clave, nombre, apellido, rol in CUENTAS:
        if CustomUser.objects.filter(email=email).exists():
            log(f'  ya existía: {email}')
            continue

        usuario = CustomUser(
            email=email, password=make_password(clave),
            first_name=nombre, last_name=apellido, role_id=rol,
            date_joined=timezone.now(), is_email_verified=True,
            balance=INITIAL_WALLET_BALANCE,
            can_autocomplete_demo=(email == REVISOR),
        )
        if rol == 'ADMIN':
            usuario.is_staff = True
            usuario.is_superuser = True
        usuario.save()

        WalletTransaction.objects.create(
            user=usuario, transaction_type_id=WalletTransactionType.WELCOME,
            amount=INITIAL_WALLET_BALANCE, balance_after=INITIAL_WALLET_BALANCE,
            description='Saldo simulado de bienvenida', created_at=timezone.now(),
        )
        log(f'  creado: {email} ({rol})')
        creadas += 1

    _preparar_revisor(log)
    return creadas


def _preparar_revisor(log=print):
    """
    Le da a la cuenta de revisión una membresía de alumno activa y sus cursos.

    Sin cursos en la biblioteca, el botón de recorrido rápido no tendría nada
    que completar. Se inscribe por membresía y no por compra porque una
    inscripción PURCHASED sin una orden detrás sería un registro incoherente.
    """
    from apps.catalog.models import Course
    from apps.library.models import Enrollment, EnrollmentType
    from apps.memberships.models import MembershipPlan, PlanAudience, UserMembership
    from apps.users.models import CustomUser

    revisor = CustomUser.objects.filter(email=REVISOR).first()
    if not revisor:
        return

    plan = (MembershipPlan.objects
            .filter(audience_id=PlanAudience.ALUMNO, is_active=True)
            .order_by('-price').first())
    if plan and not UserMembership.objects.filter(
            user=revisor, audience_id=PlanAudience.ALUMNO).exists():
        UserMembership.objects.create(
            user=revisor, plan=plan, audience_id=PlanAudience.ALUMNO,
            status_id='ACTIVE', expires_at=timezone.now() + timedelta(days=365),
            auto_renew=True,
        )
        log(f'  membresía «{plan.name}» activada para {REVISOR}')

    cursos = list(Course.objects.filter(title__in=CURSOS_REVISOR))
    if not cursos:  # base sin el catálogo de demostración: tomar los primeros publicados
        cursos = list(Course.objects.filter(status_id='PUBLISHED', is_active=True)[:6])

    nuevas = 0
    for course in cursos:
        _, creada = Enrollment.objects.get_or_create(
            user=revisor, course=course,
            defaults={'enrollment_type_id': EnrollmentType.MEMBERSHIP},
        )
        nuevas += int(creada)
    if nuevas:
        log(f'  {nuevas} cursos agregados a la biblioteca de {REVISOR}')
