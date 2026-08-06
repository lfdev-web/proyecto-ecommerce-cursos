import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


STATUSES = [
    ('PENDING', 'Pendiente', 'Solicitud enviada, en espera de revisión del administrador.'),
    ('APPROVED', 'Aprobada', 'Solicitud aprobada; el usuario fue promovido a docente.'),
    ('REJECTED', 'Rechazada', 'Solicitud rechazada por el administrador.'),
]


def seed_statuses(apps, schema_editor):
    Status = apps.get_model('users', 'TeacherApplicationStatus')
    for code, name, description in STATUSES:
        Status.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed_statuses(apps, schema_editor):
    apps.get_model('users', 'TeacherApplicationStatus').objects.filter(
        code__in=[s[0] for s in STATUSES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_customuser_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherApplicationStatus',
            fields=[
                ('code', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Estado de solicitud de docente',
                'verbose_name_plural': 'Estados de solicitud de docente',
            },
        ),
        migrations.CreateModel(
            name='TeacherApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('headline', models.CharField(help_text='Especialidad o titular profesional', max_length=150)),
                ('bio', models.TextField(help_text='Experiencia y motivación para enseñar')),
                ('id_document', models.FileField(upload_to='teacher_applications/id/')),
                ('credentials_document', models.FileField(blank=True, null=True, upload_to='teacher_applications/credentials/')),
                ('rejection_reason', models.TextField(blank=True, default='')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.ForeignKey(db_column='status', default='PENDING', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='users.teacherapplicationstatus')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_teacher_applications', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Solicitud de docente',
                'verbose_name_plural': 'Solicitudes de docente',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='teacherapplication',
            constraint=models.UniqueConstraint(
                condition=models.Q(('status', 'PENDING')),
                fields=('user',),
                name='uq_one_pending_application_per_user',
            ),
        ),
        migrations.RunPython(seed_statuses, unseed_statuses),
    ]
