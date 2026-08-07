"""
Deja las cuentas de demostración listas para el recorrido.

Es idempotente y se puede correr sobre la base que ya está en producción:
crea lo que falte y no toca lo que ya existe. En particular **nunca cambia la
contraseña de una cuenta existente** — si ya cambiaste la del administrador,
se respeta.

    python manage.py cuentas_demo
    python manage.py cuentas_demo --limpiar-alumno   # volver al punto de partida
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.common.demo_accounts import (
    ADMIN, ALUMNO, CUENTAS, DOCENTE, REVISOR, preparar_todo,
)


class Command(BaseCommand):
    help = 'Crea y prepara las cuentas de demostración (idempotente).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar-alumno', action='store_true', dest='limpiar_alumno',
            help='Vacía la biblioteca de alumno@demo.com para repetir el '
                 'recorrido de compra desde cero. Conserva su historial de órdenes.')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Preparando cuentas...')
        preparar_todo(log=self.stdout.write, limpiar_alumno=options['limpiar_alumno'])
        self._resumen()

    # ------------------------------------------------------------------
    def _resumen(self):
        from apps.catalog.models import Course
        from apps.library.models import Certificate, Enrollment
        from apps.orders.models import InstructorEarning
        from apps.users.models import CustomUser
        from django.db.models import Sum

        self.stdout.write(self.style.SUCCESS('\nCuentas listas:\n'))

        for email, clave, _, _, rol in CUENTAS:
            u = CustomUser.objects.filter(email=email).first()
            if not u:
                self.stdout.write(self.style.ERROR(f'  {email}: NO EXISTE'))
                continue

            # La contraseña que se imprime es la del archivo. Si alguien la
            # cambió a mano —lo esperable en el administrador— este comando no
            # la conoce, así que se avisa en vez de mentir.
            muestra = clave
            if not u.check_password(clave):
                muestra = '(cambiada — no es la de este archivo)'

            self.stdout.write(f'  {rol:<8} {email:<20} {muestra}')

            if email == DOCENTE:
                cursos = Course.objects.filter(instructor=u)
                alumnos = Enrollment.objects.filter(course__in=cursos).count()
                ingresos = (InstructorEarning.objects.filter(instructor=u)
                            .aggregate(t=Sum('net_amount'))['t'] or 0)
                self.stdout.write(
                    f'           {cursos.count()} cursos · {alumnos} alumnos · '
                    f'${ingresos:.2f} en ingresos')
                for c in cursos:
                    self.stdout.write(f'             - {c.title}')

            elif email == ALUMNO:
                n = Enrollment.objects.filter(user=u).count()
                self.stdout.write(
                    f'           saldo ${u.balance} · {n} cursos en la biblioteca'
                    + ('  (listo para comprar desde cero)' if n == 0 else ''))

            elif email == REVISOR:
                n = Enrollment.objects.filter(user=u).count()
                certs = Certificate.objects.filter(enrollment__user=u).count()
                self.stdout.write(
                    f'           {n} cursos · {certs} certificados · '
                    f'recorrido rápido: {"SÍ" if u.can_autocomplete_demo else "NO"}')

            elif email == ADMIN:
                self.stdout.write(
                    '           Django Admin en /admin/ y panel de analítica')

        self.stdout.write(
            '\nA dónde llegan los correos de estas cuentas: '
            'manage.py correo_demo <tu correo>')
