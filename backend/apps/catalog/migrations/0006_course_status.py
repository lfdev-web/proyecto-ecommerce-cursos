import django.db.models.deletion
from django.db import migrations, models


STATUSES = [
    ('DRAFT', 'Borrador', 'El docente lo está armando; no es visible en el catálogo.'),
    ('IN_REVIEW', 'En revisión', 'Enviado al administrador para su aprobación.'),
    ('PUBLISHED', 'Publicado', 'Visible en el catálogo y disponible para la venta.'),
    ('REJECTED', 'Devuelto', 'El administrador lo devolvió con observaciones.'),
]


def seed_statuses(apps, schema_editor):
    Status = apps.get_model('catalog', 'CourseStatus')
    for code, name, description in STATUSES:
        Status.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed_statuses(apps, schema_editor):
    apps.get_model('catalog', 'CourseStatus').objects.filter(
        code__in=[s[0] for s in STATUSES]
    ).delete()


def publish_existing_courses(apps, schema_editor):
    """Los cursos que ya existían estaban en el catálogo: quedan como publicados."""
    Course = apps.get_model('catalog', 'Course')
    Course.objects.all().update(status_id='PUBLISHED')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('catalog', '0005_courseslotrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseStatus',
            fields=[
                ('code', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Estado de curso',
                'verbose_name_plural': 'Estados de curso',
            },
        ),
        migrations.RunPython(seed_statuses, unseed_statuses),
        migrations.AddField(
            model_name='course',
            name='review_notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='course',
            name='submitted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='published_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='status',
            field=models.ForeignKey(
                db_column='status', default='DRAFT',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='courses', to='catalog.coursestatus'
            ),
        ),
        migrations.RunPython(publish_existing_courses, noop),
    ]
