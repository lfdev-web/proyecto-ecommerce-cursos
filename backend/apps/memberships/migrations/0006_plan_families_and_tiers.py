from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


AUDIENCES = [
    ('ALUMNO', 'Alumno', 'Planes de consumo: descuento en la compra de cursos.'),
    ('DOCENTE', 'Docente', 'Planes de creador: cupos para publicar cursos y mejor comisión.'),
]

TIERS = [
    ('BRONCE', 'Bronce', 1, 'Nivel de entrada.'),
    ('PLATA', 'Plata', 2, 'Nivel intermedio.'),
    ('ORO', 'Oro', 3, 'Nivel avanzado.'),
    ('VIP', 'VIP', 4, 'Nivel máximo, sin límites.'),
]

# (nombre, descripción, ciclo, precio, descuento_alumno, cupos, comisión, público, nivel)
PLANS = [
    # --- Familia ALUMNO: el beneficio es el descuento en cada compra ---
    ('Alumno Bronce', 'Descuento del 10% en todos los cursos.',
     'MONTHLY', Decimal('9.99'), Decimal('10.00'), 0, Decimal('0.70'), 'ALUMNO', 'BRONCE'),
    ('Alumno Plata', 'Descuento del 18% en todos los cursos.',
     'MONTHLY', Decimal('19.99'), Decimal('18.00'), 0, Decimal('0.70'), 'ALUMNO', 'PLATA'),
    ('Alumno Oro', 'Descuento del 25% en todos los cursos.',
     'MONTHLY', Decimal('34.99'), Decimal('25.00'), 0, Decimal('0.70'), 'ALUMNO', 'ORO'),

    # --- Familia DOCENTE: el beneficio son cupos de curso y mejor comisión ---
    ('Docente Bronce', 'Publica hasta 1 curso. Te llevas el 70% de cada venta.',
     'MONTHLY', Decimal('14.99'), Decimal('0.00'), 1, Decimal('0.70'), 'DOCENTE', 'BRONCE'),
    ('Docente Plata', 'Publica hasta 3 cursos. Te llevas el 75% de cada venta.',
     'MONTHLY', Decimal('29.99'), Decimal('0.00'), 3, Decimal('0.75'), 'DOCENTE', 'PLATA'),
    ('Docente Oro', 'Publica hasta 6 cursos. Te llevas el 80% de cada venta.',
     'MONTHLY', Decimal('49.99'), Decimal('0.00'), 6, Decimal('0.80'), 'DOCENTE', 'ORO'),
    ('Docente VIP', 'Cursos ilimitados. Te llevas el 85% de cada venta.',
     'MONTHLY', Decimal('89.99'), Decimal('0.00'), 999, Decimal('0.85'), 'DOCENTE', 'VIP'),
]


def seed_lookups(apps, schema_editor):
    """Se siembra ANTES de crear las FK, si no las columnas con default fallarían."""
    PlanAudience = apps.get_model('memberships', 'PlanAudience')
    PlanTier = apps.get_model('memberships', 'PlanTier')
    for code, name, description in AUDIENCES:
        PlanAudience.objects.update_or_create(code=code, defaults={'name': name, 'description': description})
    for code, name, rank, description in TIERS:
        PlanTier.objects.update_or_create(
            code=code, defaults={'name': name, 'rank': rank, 'description': description}
        )


def unseed_lookups(apps, schema_editor):
    apps.get_model('memberships', 'PlanTier').objects.filter(code__in=[t[0] for t in TIERS]).delete()
    apps.get_model('memberships', 'PlanAudience').objects.filter(code__in=[a[0] for a in AUDIENCES]).delete()


def seed_plans(apps, schema_editor):
    MembershipPlan = apps.get_model('memberships', 'MembershipPlan')
    for name, desc, cycle, price, discount, slots, commission, audience, tier in PLANS:
        MembershipPlan.objects.update_or_create(
            name=name,
            defaults={
                'description': desc,
                'billing_cycle_id': cycle,
                'price': price,
                'member_discount_pct': discount,
                'course_slots': slots,
                'instructor_commission_pct': commission,
                'audience_id': audience,
                'tier_id': tier,
                'is_active': True,
                'courses_limit': 0,
                'discount_pct': Decimal('0.00'),
            },
        )


def unseed_plans(apps, schema_editor):
    apps.get_model('memberships', 'MembershipPlan').objects.filter(
        name__in=[p[0] for p in PLANS]
    ).delete()


class Migration(migrations.Migration):

    # PostgreSQL no permite crear el índice de una FK en la misma transacción en
    # la que se acaba de poblar esa columna sobre filas existentes ("pending
    # trigger events"). Ejecutando cada operación por separado, el problema
    # desaparece: cada paso confirma antes de pasar al siguiente.
    atomic = False

    dependencies = [
        ('memberships', '0005_membershipplan_member_discount_pct'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanAudience',
            fields=[
                ('code', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Público del plan',
                'verbose_name_plural': 'Públicos de plan',
            },
        ),
        migrations.CreateModel(
            name='PlanTier',
            fields=[
                ('code', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('rank', models.PositiveIntegerField(default=0, help_text='Orden del nivel (mayor = mejor)')),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Nivel de plan',
                'verbose_name_plural': 'Niveles de plan',
                'ordering': ['rank'],
            },
        ),
        migrations.RunPython(seed_lookups, unseed_lookups),

        migrations.AddField(
            model_name='membershipplan',
            name='course_slots',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Cupos de curso incluidos en el plan (solo planes de docente). 0 = ninguno'
            ),
        ),
        migrations.AddField(
            model_name='membershipplan',
            name='instructor_commission_pct',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.70'), max_digits=4,
                help_text='Porcentaje de cada venta que se lleva el docente con este plan (ej. 0.80 = 80%)'
            ),
        ),
        migrations.AddField(
            model_name='membershipplan',
            name='audience',
            field=models.ForeignKey(
                db_column='audience', default='ALUMNO',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='plans', to='memberships.planaudience'
            ),
        ),
        migrations.AddField(
            model_name='membershipplan',
            name='tier',
            field=models.ForeignKey(
                db_column='tier', default='BRONCE',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='plans', to='memberships.plantier'
            ),
        ),
        migrations.AddField(
            model_name='usermembership',
            name='audience',
            field=models.ForeignKey(
                db_column='audience', default='ALUMNO',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='memberships', to='memberships.planaudience'
            ),
        ),
        migrations.AlterField(
            model_name='usermembership',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='memberships', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterUniqueTogether(
            name='usermembership',
            unique_together={('user', 'audience')},
        ),
        migrations.RunPython(seed_plans, unseed_plans),
    ]
