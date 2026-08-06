# Siembra de la tabla catálogo de estados de orden.

from django.db import migrations

STATUSES = [
    ('PENDING', 'Pendiente', 'Orden creada, pago aún no confirmado.'),
    ('COMPLETED', 'Completada', 'Pago simulado aprobado; cursos inscritos.'),
    ('FAILED', 'Fallida', 'El pago simulado no pudo completarse.'),
    ('REFUNDED', 'Reembolsada', 'Orden revertida; saldo devuelto.'),
]


def seed(apps, schema_editor):
    OrderStatus = apps.get_model('orders', 'OrderStatus')
    for code, name, description in STATUSES:
        OrderStatus.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed(apps, schema_editor):
    apps.get_model('orders', 'OrderStatus').objects.filter(code__in=[s[0] for s in STATUSES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_orderstatus_order_card_last4_order_coupon_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
