"""
Diagnóstico del envío de correo: dice si está configurado, si las credenciales
sirven y manda un mensaje de prueba.

Existe porque "no me llegó el correo" tiene tres causas muy distintas y desde
fuera se ven igual: que el SMTP no esté configurado (y el correo se imprima en
el log), que la contraseña no sirva, o que el mensaje salga pero el filtro del
destinatario lo mande a spam. Este comando separa las tres.

    python manage.py probar_correo                      # solo diagnostica
    python manage.py probar_correo tucorreo@ejemplo.com  # además envía
"""
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Comprueba la configuración de correo y envía un mensaje de prueba.'

    def add_arguments(self, parser):
        parser.add_argument('destino', nargs='?', default=None,
                            help='A dónde mandar la prueba. Sin esto solo diagnostica.')

    def handle(self, *args, **options):
        backend = settings.EMAIL_BACKEND.rsplit('.', 1)[-1]
        es_smtp = 'smtp' in settings.EMAIL_BACKEND.lower()

        self.stdout.write('\n--- Configuración ---')
        self.stdout.write(f'  backend        : {backend}')
        if not es_smtp:
            self.stdout.write(self.style.WARNING(
                '\n  EMAIL_HOST no está definido.\n'
                '  Los correos se IMPRIMEN en el log del worker y no llegan a\n'
                '  ninguna bandeja. Añade las variables EMAIL_* al .env del\n'
                '  servidor y reinicia backend y celery_worker.'))
            return

        self.stdout.write(f'  servidor       : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}'
                          f'  TLS={settings.EMAIL_USE_TLS}')
        self.stdout.write(f'  usuario        : {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'  remitente      : {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'  contraseña     : {"definida" if settings.EMAIL_HOST_PASSWORD else "VACÍA"}')

        # Gmail descarta cualquier remitente distinto de la cuenta autenticada.
        # Si no coinciden, el correo sale pero con otra dirección y cuesta
        # entender por qué.
        if 'gmail' in settings.EMAIL_HOST and settings.EMAIL_HOST_USER not in settings.DEFAULT_FROM_EMAIL:
            self.stdout.write(self.style.WARNING(
                f'  AVISO: DEFAULT_FROM_EMAIL no contiene {settings.EMAIL_HOST_USER}. '
                f'Gmail lo va a reescribir.'))

        self.stdout.write('\n--- Autenticación ---')
        try:
            conexion = get_connection()
            conexion.open()
            conexion.close()
            self.stdout.write(self.style.SUCCESS('  OK — el servidor acepta las credenciales.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  FALLÓ: {type(e).__name__}: {e}'))
            self.stdout.write(
                '  Con Gmail: la contraseña tiene que ser una CONTRASEÑA DE\n'
                '  APLICACIÓN de 16 caracteres SIN espacios, no la del correo.')
            return

        destino = options['destino']
        if not destino:
            self.stdout.write(
                '\nPara enviar una prueba: manage.py probar_correo tucorreo@ejemplo.com')
            return

        self.stdout.write(f'\n--- Enviando a {destino} ---')
        mensaje = EmailMessage(
            subject=f'Prueba de {settings.SITE_NAME} — {timezone.now():%d/%m/%Y %H:%M}',
            body=(
                f'Si estás leyendo esto, el envío de correo de '
                f'{settings.SITE_NAME} funciona.\n\n'
                f'Servidor: {settings.EMAIL_HOST}\n'
                f'Remitente: {settings.DEFAULT_FROM_EMAIL}\n'
                f'Sitio: {settings.SITE_URL}\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destino],
        )
        enviados = mensaje.send(fail_silently=False)
        if enviados:
            self.stdout.write(self.style.SUCCESS(
                f'  Entregado al servidor SMTP.\n\n'
                f'  Que el SMTP lo acepte NO garantiza que llegue a la bandeja:\n'
                f'  revisa también la carpeta de spam. Si está ahí, márcalo como\n'
                f'  confiable ANTES de la revisión.'))
        else:
            self.stdout.write(self.style.ERROR('  El servidor no aceptó el mensaje.'))
