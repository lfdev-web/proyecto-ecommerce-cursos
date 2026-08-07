"""
Envío de correos de la plataforma.

Todos los envíos pasan por Celery, nunca por la petición HTTP. Si el SMTP está
lento o caído, mandarlo en línea haría que la compra tardara segundos o —peor—
que fallara una compra ya cobrada solo porque no se pudo avisar por correo.
El cobro y el aviso son cosas distintas y no deben compartir suerte.

Con EMAIL_HOST sin definir, Django imprime los correos en la consola: el flujo
se puede demostrar completo sin configurar ningún servidor.
"""
import logging
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def _enviar(asunto, cuerpo, destinatario, adjunto=None):
    """
    Envía un correo de texto. `adjunto` es (nombre, bytes, tipo_mime).

    Nunca propaga la excepción: un fallo de correo no debe romper la tarea que
    lo disparó ni dejar reintentos infinitos en la cola. Queda en el log.
    """
    try:
        mensaje = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario],
        )
        if adjunto:
            mensaje.attach(*adjunto)
        mensaje.send(fail_silently=False)
        logger.info('Correo enviado a %s: %s', destinatario, asunto)
        return True
    except Exception:
        logger.exception('No se pudo enviar el correo a %s (%s)', destinatario, asunto)
        return False


# ---------------------------------------------------------------------------
# Factura de compra
# ---------------------------------------------------------------------------

@shared_task(name='apps.common.emails.enviar_factura')
def enviar_factura(order_id):
    from weasyprint import HTML
    from apps.orders.models import Order

    orden = (Order.objects
             .select_related('user', 'status', 'coupon')
             .prefetch_related('items__course__instructor')
             .filter(id=order_id).first())
    if not orden:
        logger.warning('enviar_factura: la orden %s no existe', order_id)
        return

    items = list(orden.items.all())
    subtotal = sum((i.price_at_purchase for i in items), Decimal('0.00'))
    nombre = f'{orden.user.first_name} {orden.user.last_name}'.strip() or orden.user.email

    html = render_to_string('orders/invoice.html', {
        'orden': orden, 'items': items, 'subtotal': subtotal,
        'nombre_cliente': nombre, 'sitio': settings.SITE_NAME,
        'sitio_url': settings.SITE_URL, 'generado_en': timezone.now(),
    })
    pdf = HTML(string=html).write_pdf()

    titulos = '\n'.join(f'  · {i.course.title}' for i in items)
    cuerpo = (
        f'Hola {nombre}:\n\n'
        f'Gracias por tu compra en {settings.SITE_NAME}. Ya tienes acceso a:\n\n'
        f'{titulos}\n\n'
        f'Total pagado: ${orden.total_amount}\n'
        f'Referencia: {orden.transaction_reference or orden.id}\n\n'
        f'Adjuntamos la factura en PDF.\n\n'
        f'Empieza a estudiar cuando quieras en {settings.SITE_URL}/mi-biblioteca\n\n'
        f'— El equipo de {settings.SITE_NAME}'
    )
    _enviar(
        f'Tu compra en {settings.SITE_NAME} — Factura {orden.transaction_reference or orden.id}',
        cuerpo, orden.user.email,
        adjunto=(f'factura-{orden.id}.pdf', pdf, 'application/pdf'),
    )


# ---------------------------------------------------------------------------
# Certificado
# ---------------------------------------------------------------------------

@shared_task(name='apps.common.emails.enviar_certificado')
def enviar_certificado(certificate_id):
    from weasyprint import HTML
    from apps.library.models import Certificate

    cert = (Certificate.objects
            .select_related('enrollment__user', 'enrollment__course')
            .filter(id=certificate_id).first())
    if not cert:
        logger.warning('enviar_certificado: el certificado %s no existe', certificate_id)
        return

    usuario = cert.enrollment.user
    # Mismo contexto EXACTO que la descarga desde la biblioteca (library/views.py):
    # si los nombres de las variables no coinciden, la plantilla renderiza los
    # campos vacíos y el PDF sale en blanco sin dar ningún error.
    html = render_to_string('library/certificate.html', {
        'student_name': cert.student_name or (
            f'{usuario.first_name} {usuario.last_name}'.strip() or usuario.email
        ),
        'course_title': cert.course_title or cert.enrollment.course.title,
        'course_duration_hours': cert.course_duration_hours,
        'issued_at': cert.issued_at.strftime('%d/%m/%Y'),
        'verification_code': cert.verification_code,
    })
    pdf = HTML(string=html).write_pdf()

    cuerpo = (
        f'¡Felicitaciones, {cert.student_name}!\n\n'
        f'Completaste «{cert.course_title}» y tu certificado ya está emitido.\n\n'
        f'Código de verificación: {cert.verification_code}\n'
        f'Duración del curso: {cert.course_duration_hours} horas\n\n'
        f'Lo adjuntamos en PDF. También puedes descargarlo cuando quieras desde '
        f'{settings.SITE_URL}/mi-biblioteca\n\n'
        f'— El equipo de {settings.SITE_NAME}'
    )
    _enviar(
        f'Tu certificado de «{cert.course_title}»',
        cuerpo, usuario.email,
        adjunto=(f'certificado-{cert.verification_code}.pdf', pdf, 'application/pdf'),
    )


# ---------------------------------------------------------------------------
# Comprobante de recarga
# ---------------------------------------------------------------------------

@shared_task(name='apps.common.emails.enviar_comprobante_recarga')
def enviar_comprobante_recarga(recharge_id):
    from apps.users.models import WalletRecharge

    recarga = (WalletRecharge.objects
               .select_related('user')
               .filter(id=recharge_id).first())
    if not recarga:
        logger.warning('enviar_comprobante_recarga: la recarga %s no existe', recharge_id)
        return

    usuario = recarga.user
    nombre = f'{usuario.first_name} {usuario.last_name}'.strip() or usuario.email
    cuerpo = (
        f'Hola {nombre}:\n\n'
        f'Tu recarga de saldo se procesó correctamente.\n\n'
        f'  Monto acreditado : ${recarga.amount}\n'
        f'  Saldo disponible : ${usuario.balance}\n'
        f'  Tarjeta          : •••• {recarga.card_last4}\n'
        f'  Comprobante      : {recarga.reference}\n'
        f'  Fecha            : {recarga.completed_at:%d/%m/%Y %H:%M}\n\n'
        f'Recuerda que este es un saldo simulado con fines educativos.\n\n'
        f'— El equipo de {settings.SITE_NAME}'
    )
    _enviar(
        f'Recarga de ${recarga.amount} confirmada — {recarga.reference}',
        cuerpo, usuario.email,
    )
