"""
Pone en oferta los cursos del carrete de la portada.

Existe suelto y no solo dentro del seed por dos razones:

  1. En el servidor hay una base sembrada antes de que existieran las
     promociones. Volver a sembrar para conseguirlas costaría los usuarios,
     las compras y los certificados que ya están ahí.
  2. Las ofertas VENCEN (2 a 10 días). Aunque se hubieran sembrado, el
     carrete se vaciaría solo a la semana siguiente. Este comando se vuelve
     a correr y las renueva.

    python manage.py crear_promociones
    python manage.py crear_promociones --dias 30   # que duren hasta la defensa
    python manage.py crear_promociones --quitar    # dejar el catálogo sin ofertas
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Course

# (slug, porcentaje de descuento, días que dura la oferta)
# Los plazos son distintos a propósito: si todas vencieran el mismo día, las
# cuentas regresivas del carrete mostrarían el mismo número y se notaría que
# están puestas a mano.
OFERTAS = [
    ('machine-learning-con-scikit-learn', 40, 2),
    ('flutter-apps-multiplataforma', 35, 4),
    ('react-en-la-practica', 30, 3),
    ('docker-desde-cero', 30, 5),
    ('hacking-etico-y-pruebas-de-penetracion', 25, 7),
    ('sql-para-analisis-de-datos', 20, 10),
]


class Command(BaseCommand):
    help = 'Pone (o renueva) las ofertas del carrete de la portada.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias', type=int, default=None,
            help='Fuerza la misma duración para todas, en lugar de los plazos escalonados.')
        parser.add_argument(
            '--quitar', action='store_true',
            help='Quita todas las ofertas. El precio de lista no se toca.')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['quitar']:
            n = Course.objects.exclude(promo_price=None).update(
                promo_price=None, promo_until=None)
            self.stdout.write(self.style.SUCCESS(f'{n} ofertas retiradas.'))
            return

        ahora = timezone.now()
        aplicadas, faltantes = [], []

        for slug, pct, dias in OFERTAS:
            course = Course.objects.filter(slug=slug).first()
            if not course:
                faltantes.append(slug)
                continue
            # El precio de lista NUNCA se modifica: la oferta vive en sus dos
            # columnas propias, así que al vencer el curso vuelve solo a su
            # precio original sin tener que restaurar nada.
            course.promo_price = (
                course.price * Decimal(100 - pct) / Decimal(100)
            ).quantize(Decimal('0.01'))
            course.promo_until = ahora + timedelta(days=options['dias'] or dias)
            course.save(update_fields=['promo_price', 'promo_until'])
            aplicadas.append((course, pct))

        for course, pct in aplicadas:
            self.stdout.write(
                f'  -{pct}%  {course.title[:42]:<42} '
                f'${course.price} -> ${course.promo_price}  '
                f'hasta {course.promo_until:%d/%m/%Y}')

        self.stdout.write(self.style.SUCCESS(
            f'\n{len(aplicadas)} cursos en oferta.'))
        if faltantes:
            self.stdout.write(self.style.WARNING(
                'No existen en esta base: ' + ', '.join(faltantes)))
