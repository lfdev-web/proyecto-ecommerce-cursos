"""
Límite de intentos de inicio de sesión en el admin de Django.

El throttling de DRF (`login: 8/min`) protege `/api/auth/login/`, pero **no
llega al admin**: `/admin/login/` es una vista normal de Django, no pasa por
DRF, y por defecto acepta intentos sin límite. Es decir, la puerta mejor
protegida era la de la API y la que da acceso total estaba abierta.

Se cuenta en la caché de Redis, no en memoria del proceso: con tres workers de
gunicorn, un contador en memoria daría tres veces más intentos de los
permitidos y cada worker olvidaría lo que vieron los otros.

No sustituye a una contraseña fuerte — la retrasa. Un atacante con la
contraseña correcta entra al primer intento; esto solo encarece adivinarla.
"""
import logging

from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

RUTA_LOGIN_ADMIN = '/admin/login/'
MAX_INTENTOS = 6
# Segundos que dura el bloqueo tras agotar los intentos.
BLOQUEO_SEGUNDOS = 15 * 60


def _ip_cliente(request):
    """
    IP real del visitante.

    Se lee de REMOTE_ADDR y no de X-Forwarded-For a propósito: esa cabecera la
    puede escribir el propio cliente, y un contador indexado por un valor que
    el atacante elige no cuenta nada — bastaría cambiarla en cada intento para
    tener siempre un contador nuevo. El valor de REMOTE_ADDR lo pone la capa de
    red y no se puede falsificar desde el navegador.

    Detrás del proxy esto agrupa a todos los visitantes bajo la IP de nginx.
    Es el precio de no confiar en una cabecera falsificable, y para el login
    del admin —donde casi nadie entra— es un precio aceptable.
    """
    return request.META.get('REMOTE_ADDR', 'desconocida')


class AdminLoginRateLimitMiddleware(MiddlewareMixin):
    """Bloquea el formulario de login del admin tras varios fallos seguidos."""

    def process_request(self, request):
        if request.path != RUTA_LOGIN_ADMIN or request.method != 'POST':
            return None

        clave = f'admin-login-fallos:{_ip_cliente(request)}'
        fallos = cache.get(clave, 0)

        if fallos >= MAX_INTENTOS:
            logger.warning(
                'Login del admin bloqueado para %s (%s intentos fallidos)',
                _ip_cliente(request), fallos)
            return HttpResponse(
                'Demasiados intentos fallidos. Vuelve a intentarlo en '
                f'{BLOQUEO_SEGUNDOS // 60} minutos.',
                status=429, content_type='text/plain; charset=utf-8')
        return None

    def process_response(self, request, response):
        if request.path != RUTA_LOGIN_ADMIN or request.method != 'POST':
            return response

        clave = f'admin-login-fallos:{_ip_cliente(request)}'

        # Django responde 302 cuando el login es correcto y 200 (vuelve a
        # pintar el formulario con el error) cuando falla.
        if response.status_code == 302:
            cache.delete(clave)
            return response

        if response.status_code == 200:
            # add() solo escribe si la clave no existe: así el TTL se fija en
            # el primer fallo y la ventana no se renueva sola con cada intento
            # —si no, un atacante constante nunca la dejaría expirar, pero
            # tampoco se desbloquearía nunca un usuario legítimo.
            cache.add(clave, 0, BLOQUEO_SEGUNDOS)
            try:
                cache.incr(clave)
            except ValueError:
                # La clave expiró entre el add() y el incr(): empezar de nuevo.
                cache.set(clave, 1, BLOQUEO_SEGUNDOS)

        return response
