"""
Identificación del visitante detrás de los proxies.

Vive aquí y no dentro de una app porque la usan dos cosas que no se conocen
entre sí —la analítica y el límite de intentos del admin— y las dos tienen que
entender la cadena de proxies exactamente igual. Si cada una lo resolviera por
su cuenta, arreglar una dejaría la otra mal.
"""
from django.conf import settings


def ip_cliente(request):
    """
    IP real del visitante.

    `X-Forwarded-For` es una lista que va creciendo: cada proxy añade al final
    la IP de quien le habló. Las de la IZQUIERDA las pudo escribir el propio
    cliente, así que no valen nada. Solo son de fiar las últimas
    TRUSTED_PROXY_COUNT posiciones, que las escribieron proxies nuestros.

        cliente -> Caddy -> nginx -> Django
        X-Forwarded-For: <cliente>, <Caddy>       (nginx añade la de Caddy)
        con TRUSTED_PROXY_COUNT=2 -> cadena[-2] = <cliente>

    El número TIENE que ser exacto:

      - más chico de lo real: se devuelve la IP de un proxy nuestro, la misma
        para todo el mundo. Cualquier contador basado en esto se vuelve global
        y una sola persona puede bloquear a todas las demás;
      - más grande: se lee una posición que el cliente pudo inventar, y
        entonces le basta cambiarla en cada petición para tener un contador
        nuevo cada vez.

    Sin proxies declarados (desarrollo) se usa REMOTE_ADDR, que lo pone la capa
    de red y el navegador no puede falsificar.
    """
    saltos = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)
    if saltos > 0:
        reenviadas = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if reenviadas:
            cadena = [p.strip() for p in reenviadas.split(',') if p.strip()]
            if len(cadena) >= saltos:
                return cadena[-saltos]
    return request.META.get('REMOTE_ADDR')
