"""
Las cuatro cuentas para recorrer la aplicación, y el estado con el que cada
una tiene que arrancar.

Vive aquí y no dentro del seed porque hace falta por dos caminos: al sembrar la
base desde cero, y suelto en un servidor que YA está sembrado. Si cada camino
tuviera su copia, tarde o temprano crearían cuentas distintas.

Cada cuenta existe para enseñar una cosa:

    admin@demo.com    el panel de administración
    docente@demo.com  cómo se ve el negocio desde el lado de quien enseña
    alumno@demo.com   el recorrido completo, de comprar a certificarse
    revisor@demo.com  el mismo recorrido, pero saltándoselo de un clic

REGLA QUE NO SE ROMPE: a una cuenta que ya existe NUNCA se le toca la
contraseña. Quien despliega puede haber cambiado la del administrador —que es
lo correcto, porque la de este archivo es pública— y volver a ponérsela sería
reabrirle la puerta sin avisarle.
"""
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.utils import timezone

# email, contraseña, nombre, apellido, rol
CUENTAS = [
    ('admin@demo.com', 'Admin1234!', 'Admin', 'Demo', 'ADMIN'),
    ('docente@demo.com', 'Demo1234!', 'Docente', 'Demo', 'DOCENTE'),
    ('alumno@demo.com', 'Demo1234!', 'Alumno', 'Demo', 'ALUMNO'),
    ('revisor@demo.com', 'Demo1234!', 'Revisor', 'Demo', 'ALUMNO'),
]

ADMIN = 'admin@demo.com'
DOCENTE = 'docente@demo.com'
ALUMNO = 'alumno@demo.com'
REVISOR = 'revisor@demo.com'

# Cursos que pasan a manos de docente@demo.com. Se eligen de categorías
# distintas y son cursos con historial: al reasignarlos, su panel muestra
# alumnos, ingresos y calificaciones de verdad desde el primer momento.
CURSOS_DOCENTE = [
    'Python desde cero',
    'React en la práctica',
    'Docker desde cero',
]

# Cursos con los que arranca la cuenta de revisión. Incluyen los tres de
# arriba a propósito: así el docente ve al revisor en su lista de alumnos.
CURSOS_REVISOR = CURSOS_DOCENTE + [
    'SQL para análisis de datos',
    'Fundamentos de ciberseguridad',
    'Análisis de datos con Python y Pandas',
]


# ---------------------------------------------------------------------------
def crear_cuentas_demo(log=print):
    """Crea las cuentas que falten. Nunca modifica las que ya existen."""
    from apps.users.models import (
        INITIAL_WALLET_BALANCE, CustomUser, WalletTransaction, WalletTransactionType,
    )

    creadas = 0
    for email, clave, nombre, apellido, rol in CUENTAS:
        if CustomUser.objects.filter(email=email).exists():
            log(f'  ya existía (no se toca): {email}')
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
        log(f'  creada: {email} ({rol})')
        creadas += 1
    return creadas


# ---------------------------------------------------------------------------
def preparar_docente(log=print):
    """
    Deja a docente@demo.com con plan activo y cursos propios.

    Sin esto su panel sale vacío: la cuenta se crea al final del seed y no
    hereda nada, así que no habría ingresos, ni alumnos, ni reseñas — nada que
    enseñar. En vez de inventarle cursos nuevos (que tampoco tendrían ventas),
    se le TRASPASAN cursos ya vendidos de un docente del seed.

    Al traspasar hay que mover también las ganancias: el panel las filtra por
    `InstructorEarning.instructor`, no por el curso. Si se moviera solo el
    curso, el docente vería sus alumnos pero cero ingresos, y el docente
    anterior seguiría cobrando por cursos que ya no son suyos.
    """
    from apps.catalog.models import Course, CourseSlotRequest
    from apps.memberships.models import MembershipPlan, PlanAudience, UserMembership
    from apps.orders.models import InstructorEarning
    from apps.users.models import CustomUser

    docente = CustomUser.objects.filter(email=DOCENTE).first()
    if not docente:
        return

    # 1) Plan de docente: sin plan activo no tiene cupos y no puede publicar.
    #    Se elige el de más cupos para que pueda crear cursos en vivo durante
    #    la demostración sin toparse con el límite.
    plan = (MembershipPlan.objects
            .filter(audience_id=PlanAudience.DOCENTE, is_active=True)
            .order_by('-course_slots').first())
    if plan and not UserMembership.objects.filter(
            user=docente, audience_id=PlanAudience.DOCENTE).exists():
        UserMembership.objects.create(
            user=docente, plan=plan, audience_id=PlanAudience.DOCENTE,
            status_id='ACTIVE', expires_at=timezone.now() + timedelta(days=365),
            auto_renew=True,
        )
        log(f'  plan «{plan.name}» activado para {DOCENTE}')

    # 2) Traspaso de cursos
    traspasados = 0
    for titulo in CURSOS_DOCENTE:
        curso = Course.objects.filter(title=titulo).first()
        if not curso or curso.instructor_id == docente.id:
            continue
        curso.instructor = docente
        curso.save(update_fields=['instructor'])
        InstructorEarning.objects.filter(course=curso).update(instructor=docente)
        # La solicitud de cupo con la que se creó el curso también cambia de
        # dueño, si no el conteo de cupos quedaría descuadrado entre los dos.
        CourseSlotRequest.objects.filter(created_course=curso).update(teacher=docente)
        traspasados += 1

    if traspasados:
        log(f'  {traspasados} cursos traspasados a {DOCENTE} (con sus ganancias)')


# ---------------------------------------------------------------------------
def preparar_alumno(log=print, limpiar=False):
    """
    Deja a alumno@demo.com listo para hacer el recorrido de compra completo:
    con saldo y —si se pide— con la biblioteca vacía.

    `limpiar` borra sus inscripciones, entregas y certificados. Es destructivo
    y por eso hay que pedirlo a mano: sirve para volver al punto de partida
    después de un ensayo, no para el uso normal.
    """
    from apps.users.models import INITIAL_WALLET_BALANCE, CustomUser

    alumno = CustomUser.objects.filter(email=ALUMNO).first()
    if not alumno:
        return

    if limpiar:
        from apps.exams.models import AttemptAnswer, ExamAttempt
        from apps.library.models import (
            AssignmentSubmission, Certificate, Enrollment, LessonProgress,
        )
        from apps.orders.models import Cart, Order

        inscripciones = Enrollment.objects.filter(user=alumno)
        intentos = ExamAttempt.objects.filter(enrollment__in=inscripciones)
        AttemptAnswer.objects.filter(attempt__in=intentos).delete()
        intentos.delete()
        Certificate.objects.filter(enrollment__in=inscripciones).delete()
        AssignmentSubmission.objects.filter(enrollment__in=inscripciones).delete()
        LessonProgress.objects.filter(enrollment__in=inscripciones).delete()
        n = inscripciones.count()
        inscripciones.delete()
        Cart.objects.filter(user=alumno).delete()
        # Las órdenes NO se borran: son el historial de compras y el docente
        # cobró comisión por ellas. Borrarlas descuadraría su panel.
        pedidos = Order.objects.filter(user=alumno).count()
        log(f'  biblioteca de {ALUMNO} vaciada ({n} cursos); '
            f'se conservan {pedidos} órdenes del historial')

    if alumno.balance < INITIAL_WALLET_BALANCE:
        alumno.balance = INITIAL_WALLET_BALANCE
        alumno.save(update_fields=['balance'])
        log(f'  saldo de {ALUMNO} repuesto a ${INITIAL_WALLET_BALANCE}')


# ---------------------------------------------------------------------------
def preparar_revisor(log=print):
    """
    Le da a la cuenta de revisión su membresía y sus cursos.

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

    if not revisor.can_autocomplete_demo:
        revisor.can_autocomplete_demo = True
        revisor.save(update_fields=['can_autocomplete_demo'])
        log(f'  recorrido rápido habilitado para {REVISOR}')

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
    if not cursos:  # base sin el catálogo de demostración
        cursos = list(Course.objects.filter(status_id='PUBLISHED', is_active=True)[:6])

    nuevas = 0
    for curso in cursos:
        _, creada = Enrollment.objects.get_or_create(
            user=revisor, course=curso,
            defaults={'enrollment_type_id': EnrollmentType.MEMBERSHIP},
        )
        nuevas += int(creada)
    if nuevas:
        log(f'  {nuevas} cursos agregados a la biblioteca de {REVISOR}')


# ---------------------------------------------------------------------------
def preparar_todo(log=print, limpiar_alumno=False):
    """Crea las cuentas que falten y deja a cada una en su punto de partida."""
    creadas = crear_cuentas_demo(log)
    preparar_docente(log)
    preparar_alumno(log, limpiar=limpiar_alumno)
    preparar_revisor(log)
    return creadas
