# Siembra de la tabla catálogo de niveles de curso.

from django.db import migrations

LEVELS = [
    ('BASICO', 'Básico', 'Sin conocimientos previos.'),
    ('INTERMEDIO', 'Intermedio', 'Requiere fundamentos del tema.'),
    ('AVANZADO', 'Avanzado', 'Para perfiles con experiencia.'),
]


def seed(apps, schema_editor):
    CourseLevel = apps.get_model('catalog', 'CourseLevel')
    for code, name, description in LEVELS:
        CourseLevel.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed(apps, schema_editor):
    apps.get_model('catalog', 'CourseLevel').objects.filter(code__in=[l[0] for l in LEVELS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_courselevel_course_cover_image_course_language_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
