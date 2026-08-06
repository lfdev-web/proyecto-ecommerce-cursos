# Siembra de las tablas catálogo de memberships: ciclos de facturación y estados.

from django.db import migrations

CYCLES = [
    ('MONTHLY', 'Mensual', 'Facturación cada mes.'),
    ('ANNUAL', 'Anual', 'Facturación cada año.'),
]

STATUSES = [
    ('ACTIVE', 'Activa', 'Membresía vigente con acceso completo.'),
    ('CANCELLED', 'Cancelada', 'Cancelada por el usuario; acceso hasta la expiración pagada.'),
    ('EXPIRED', 'Expirada', 'Venció sin renovarse.'),
    ('PENDING', 'Pendiente de pago', 'Creada pero sin pago confirmado.'),
]


def seed(apps, schema_editor):
    BillingCycle = apps.get_model('memberships', 'BillingCycle')
    MembershipStatus = apps.get_model('memberships', 'MembershipStatus')
    for code, name, description in CYCLES:
        BillingCycle.objects.update_or_create(code=code, defaults={'name': name, 'description': description})
    for code, name, description in STATUSES:
        MembershipStatus.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed(apps, schema_editor):
    apps.get_model('memberships', 'BillingCycle').objects.filter(code__in=[c[0] for c in CYCLES]).delete()
    apps.get_model('memberships', 'MembershipStatus').objects.filter(code__in=[s[0] for s in STATUSES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('memberships', '0002_billingcycle_membershipstatus'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
