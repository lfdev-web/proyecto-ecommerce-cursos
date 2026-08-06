import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


STATUSES = [
    ('PENDING', 'Pendiente', 'Solicitud enviada, en espera de revisión del administrador.'),
    ('APPROVED', 'Aprobada', 'Espacio habilitado; el docente ya puede crear el curso.'),
    ('REJECTED', 'Rechazada', 'Solicitud rechazada por el administrador.'),
]


def seed_statuses(apps, schema_editor):
    Status = apps.get_model('catalog', 'SlotRequestStatus')
    for code, name, description in STATUSES:
        Status.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed_statuses(apps, schema_editor):
    apps.get_model('catalog', 'SlotRequestStatus').objects.filter(
        code__in=[s[0] for s in STATUSES]
    ).delete()


class Migration(migrations.Migration):

    # Igual que en memberships: evitamos el error de "pending trigger events"
    # de PostgreSQL al crear índices de FK junto con la carga de datos.
    atomic = False

    dependencies = [
        ('catalog', '0004_course_level'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SlotRequestStatus',
            fields=[
                ('code', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Estado de solicitud de espacio',
                'verbose_name_plural': 'Estados de solicitud de espacio',
            },
        ),
        migrations.RunPython(seed_statuses, unseed_statuses),
        migrations.CreateModel(
            name='CourseSlotRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proposed_title', models.CharField(help_text='Título tentativo del curso', max_length=200)),
                ('justification', models.TextField(help_text='De qué trata el curso y por qué aporta al catálogo')),
                ('rejection_reason', models.TextField(blank=True, default='')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('is_consumed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_course', models.OneToOneField(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='slot_request', to='catalog.course')),
                ('proposed_category', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='slot_requests', to='catalog.category')),
                ('reviewed_by', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_slot_requests', to=settings.AUTH_USER_MODEL)),
                ('status', models.ForeignKey(
                    db_column='status', default='PENDING',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='+', to='catalog.slotrequeststatus')),
                ('teacher', models.ForeignKey(
                    limit_choices_to={'role': 'DOCENTE'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='slot_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Solicitud de espacio de curso',
                'verbose_name_plural': 'Solicitudes de espacio de curso',
                'ordering': ['-created_at'],
            },
        ),
    ]
