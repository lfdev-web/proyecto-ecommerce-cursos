from decimal import Decimal
from django.db import migrations, models


def set_default_member_discount(apps, schema_editor):
    """
    Da un descuento de miembro a los planes activos existentes para que el
    beneficio se vea en la demo (los planes nuevos nacen en 0 y se configuran
    en el admin). 15% es un valor de club razonable.
    """
    MembershipPlan = apps.get_model('memberships', 'MembershipPlan')
    MembershipPlan.objects.filter(is_active=True, member_discount_pct=0).update(
        member_discount_pct=Decimal('15.00')
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('memberships', '0004_alter_membershipplan_billing_cycle_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='membershipplan',
            name='member_discount_pct',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=5,
                help_text='Descuento (%) aplicado a todas las compras de cursos del miembro activo (0-100)'
            ),
        ),
        migrations.RunPython(set_default_member_discount, noop),
    ]
