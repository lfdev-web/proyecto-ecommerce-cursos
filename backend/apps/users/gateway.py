"""
Pasarela de pago SIMULADA para recargar el saldo.

No existe ninguna integración con un procesador real: no se contacta ningún
servicio externo, no se mueve dinero y no se guarda el número de tarjeta.
La decisión de aprobar o rechazar se toma aquí mismo, a partir del número
ingresado.

El comportamiento es DETERMINISTA a propósito: cada número de prueba produce
siempre el mismo resultado. Un rechazo aleatorio se vería más "realista", pero
haría imposible demostrar el manejo de errores de forma confiable — podría
fallar justo cuando se quiere mostrar el camino feliz, o negarse a fallar
cuando se quiere mostrar el error.

Los números son los de prueba estándar de la industria (los mismos que publica
Stripe en su documentación), así que son reconocibles y todos pasan Luhn.
"""
import secrets

from apps.orders.utils.luhn import is_valid_luhn

# Número -> (aprobada, motivo del rechazo)
TARJETAS_DE_PRUEBA = {
    '4000000000000002': (False, 'La tarjeta fue rechazada por el banco emisor.'),
    '4000000000009995': (False, 'Fondos insuficientes en la tarjeta.'),
    '4000000000000069': (False, 'La tarjeta está vencida.'),
    '4000000000000127': (False, 'El código de seguridad (CVV) es incorrecto.'),
    '4000000000000119': (False, 'Error de procesamiento. Intenta nuevamente.'),
}

# Se muestran en la pantalla de la pasarela como ayuda para probar.
TARJETAS_APROBADAS = ['4242424242424242', '4539578763621486', '5555555555554444']


def normalizar(numero):
    return (numero or '').replace(' ', '').replace('-', '')


def autorizar(numero_tarjeta):
    """
    Decide si la pasarela simulada aprueba el cobro.

    Devuelve (aprobada: bool, motivo: str, ultimos4: str).
    Cualquier número que pase Luhn y no esté en la lista de fallos se aprueba.
    """
    numero = normalizar(numero_tarjeta)
    ultimos4 = numero[-4:] if len(numero) >= 4 else ''

    if not is_valid_luhn(numero):
        return False, 'El número de tarjeta no es válido.', ultimos4

    if numero in TARJETAS_DE_PRUEBA:
        aprobada, motivo = TARJETAS_DE_PRUEBA[numero]
        return aprobada, motivo, ultimos4

    return True, '', ultimos4


def generar_referencia():
    """Código de comprobante que se muestra al usuario tras la recarga."""
    return f'RCG-{secrets.token_hex(4).upper()}'
