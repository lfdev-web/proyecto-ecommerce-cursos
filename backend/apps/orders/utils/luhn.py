import re

def is_valid_luhn(card_number: str) -> bool:
    """
    WARNING: PCI-DSS COMPLIANCE NOTICE
    ==================================
    Este proyecto es un entorno de demostración/desarrollo. 
    Bajo los estándares PCI-DSS (Payment Card Industry Data Security Standard):
    1. NUNCA se debe almacenar el PAN (Primary Account Number) completo 
       ni el CVV en texto plano en la base de datos o logs.
    2. Las validaciones de tarjetas de crédito reales deben ser manejadas por 
       una pasarela de pagos certificada (ej. Stripe, PayPal, Kushki) que 
       provea tokenización.
    3. Este algoritmo de Luhn debe usarse únicamente para validación preliminar
       en el frontend o de forma temporal en memoria durante el procesamiento.

    Implementación del Algoritmo de Luhn en Python:
    """
    # Remover espacios y guiones
    card_number = re.sub(r'[\s-]', '', card_number)

    # Verificar que solo contenga dígitos y sea de una longitud razonable
    if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
        return False

    total = 0
    reverse_digits = card_number[::-1]

    for i, char in enumerate(reverse_digits):
        digit = int(char)
        
        # Duplicar cada segundo dígito comenzando desde la derecha
        if i % 2 == 1:
            digit *= 2
            # Si el resultado es mayor a 9, sumar sus dígitos (equivale a restar 9)
            if digit > 9:
                digit -= 9
                
        total += digit

    return total % 10 == 0
