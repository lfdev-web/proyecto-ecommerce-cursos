# Siembra la tabla catálogo de tipos de inscripción y rellena el snapshot
# histórico de los certificados ya emitidos antes de este cambio.

from decimal import Decimal

from django.db import migrations

TYPES = [
    ('PURCHASED', 'Comprado', 'Acceso adquirido por compra directa del curso.'),
    ('MEMBERSHIP', 'Membresía', 'Acceso otorgado por una membresía activa.'),
]


def seed_types(apps, schema_editor):
    EnrollmentType = apps.get_model('library', 'EnrollmentType')
    for code, name, description in TYPES:
        EnrollmentType.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed_types(apps, schema_editor):
    apps.get_model('library', 'EnrollmentType').objects.filter(code__in=[t[0] for t in TYPES]).delete()


def backfill_certificates(apps, schema_editor):
    Certificate = apps.get_model('library', 'Certificate')
    for cert in Certificate.objects.select_related('enrollment__user', 'enrollment__course').all():
        user = cert.enrollment.user
        course = cert.enrollment.course
        full_name = f"{user.first_name} {user.last_name}".strip() or user.email
        total_minutes = sum(lesson.duration_minutes for lesson in course.lessons.all())
        cert.student_name = full_name
        cert.course_title = course.title
        cert.course_duration_hours = (Decimal(total_minutes) / Decimal('60')).quantize(Decimal('0.01'))
        # No se guardó la fecha exacta de completado; la emisión es la mejor aproximación
        cert.completed_at = cert.issued_at
        cert.save(update_fields=['student_name', 'course_title', 'course_duration_hours', 'completed_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_enrollmenttype_certificate_completed_at_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_types, unseed_types),
        migrations.RunPython(backfill_certificates, migrations.RunPython.noop),
    ]
