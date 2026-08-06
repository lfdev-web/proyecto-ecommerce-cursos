"""
Backfill: genera el ingreso del docente (70/30) para las ventas que ya
existían antes de crear InstructorEarning, con la fecha real de la orden.
"""
from decimal import Decimal

from django.db import migrations

INSTRUCTOR_RATE = Decimal('0.70')


def backfill_earnings(apps, schema_editor):
    OrderItem = apps.get_model('orders', 'OrderItem')
    InstructorEarning = apps.get_model('orders', 'InstructorEarning')

    items = (
        OrderItem.objects
        .filter(course__instructor__isnull=False, earning__isnull=True)
        .select_related('course', 'order')
    )
    InstructorEarning.objects.bulk_create([
        InstructorEarning(
            order_item=item,
            instructor_id=item.course.instructor_id,
            course_id=item.course_id,
            gross_amount=item.price_at_purchase,
            commission_rate=INSTRUCTOR_RATE,
            net_amount=(item.price_at_purchase * INSTRUCTOR_RATE).quantize(Decimal('0.01')),
        )
        for item in items
    ], batch_size=500)

    # auto_now_add pisó created_at con "ahora": corregir a la fecha real de cada orden
    schema_editor.execute("""
        UPDATE orders_instructorearning ie
        SET created_at = o.created_at
        FROM orders_orderitem oi
        JOIN orders_order o ON o.id = oi.order_id
        WHERE oi.id = ie.order_item_id
    """)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0006_instructorearning'),
    ]

    operations = [
        migrations.RunPython(backfill_earnings, noop),
    ]
