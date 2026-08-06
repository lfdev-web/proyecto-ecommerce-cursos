# Siembra de la tabla catálogo de tipos de interacción con sus pesos SVD.

from django.db import migrations

TYPES = [
    ('VIEW', 'Visualización', 'Vista del detalle del curso — señal débil de interés.', 0.5),
    ('CART_ADD', 'Agregado al carrito', 'Intención de compra moderada.', 1.0),
    ('WISHLIST', 'Lista de deseos', 'Interés deliberado guardado para después.', 1.5),
    ('REVIEW', 'Reseña / compromiso', 'Compromiso demostrado con el contenido.', 2.0),
    ('PURCHASE', 'Compra', 'Señal más fuerte posible de interés.', 3.0),
]


def seed(apps, schema_editor):
    InteractionType = apps.get_model('recommendations', 'InteractionType')
    for code, name, description, weight in TYPES:
        InteractionType.objects.update_or_create(
            code=code, defaults={'name': name, 'description': description, 'weight': weight}
        )


def unseed(apps, schema_editor):
    apps.get_model('recommendations', 'InteractionType').objects.filter(code__in=[t[0] for t in TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recommendations', '0002_interactiontype'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
