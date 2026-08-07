"""
Hace que los correos de las cuentas de demostración lleguen a un buzón real.

Sirve para que, durante la revisión, la factura y el certificado se vean llegar
de verdad a una bandeja de entrada en lugar de quedar en el log del worker.

Las credenciales NO cambian: `alumno@demo.com` sigue siendo el usuario del
login. Lo que se cambia es `notification_email`, que solo dice a dónde mandar
el aviso. Por eso varias cuentas pueden apuntar al mismo buzón — `email` es
único, este campo no.

    python manage.py correo_demo tucorreo@ejemplo.com
    python manage.py correo_demo tucorreo@ejemplo.com --cuenta revisor@demo.com
    python manage.py correo_demo --quitar
"""
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from apps.common.demo_accounts import CUENTAS
from apps.users.models import CustomUser

EMAILS_DEMO = [c[0] for c in CUENTAS]


class Command(BaseCommand):
    help = 'Redirige los correos de las cuentas de demostración a un buzón real.'

    def add_arguments(self, parser):
        parser.add_argument('correo', nargs='?', default=None,
                            help='Buzón real que recibirá los avisos.')
        parser.add_argument('--cuenta', action='append', default=None,
                            help='Limitar a estas cuentas (se puede repetir).')
        parser.add_argument('--quitar', action='store_true',
                            help='Volver a mandar los avisos al email de cada cuenta.')

    def handle(self, *args, **options):
        objetivo = options['cuenta'] or EMAILS_DEMO
        usuarios = CustomUser.objects.filter(email__in=objetivo)

        if not usuarios.exists():
            raise CommandError(
                'No encontré esas cuentas. ¿Corriste cuentas_demo?')

        if options['quitar']:
            n = usuarios.update(notification_email='')
            self.stdout.write(self.style.SUCCESS(
                f'{n} cuentas vuelven a recibir en su propio email.'))
            return

        correo = options['correo']
        if not correo:
            raise CommandError('Falta el correo. Ej: manage.py correo_demo tu@correo.com')
        try:
            validate_email(correo)
        except ValidationError:
            raise CommandError(f'«{correo}» no parece un correo válido.')

        n = usuarios.update(notification_email=correo)

        self.stdout.write(self.style.SUCCESS(
            f'\n{n} cuentas mandarán sus avisos a {correo}:'))
        for u in usuarios.order_by('email'):
            self.stdout.write(f'  login {u.email:<20} -> avisos a {u.notification_email}')

        self.stdout.write(
            '\nLas contraseñas y los usuarios de login NO cambiaron.\n'
            'Si EMAIL_HOST no está configurado, los correos siguen yendo al log '
            'del worker de Celery y no llegarán a ninguna bandeja.')
