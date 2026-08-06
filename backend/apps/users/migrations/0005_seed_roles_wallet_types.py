# Siembra de las tablas catálogo de users: roles y tipos de movimiento de saldo.

from django.db import migrations

ROLES = [
    ('ADMIN', 'Administrador', 'Control total de la plataforma y del panel de analítica.'),
    ('DOCENTE', 'Docente', 'Crea y dicta cursos; accede a su panel de instructor.'),
    ('ALUMNO', 'Alumno', 'Compra cursos, estudia y obtiene certificados.'),
]

WALLET_TYPES = [
    ('WELCOME', 'Saldo de bienvenida', 'Saldo simulado inicial otorgado al registrarse.'),
    ('PURCHASE', 'Compra de cursos', 'Egreso por checkout de cursos.'),
    ('MEMBERSHIP', 'Pago de membresía', 'Egreso por suscripción a un plan de membresía.'),
    ('REFERRAL_BONUS', 'Bono de referido', 'Ingreso por el programa de referidos.'),
]


def seed(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    WalletTransactionType = apps.get_model('users', 'WalletTransactionType')
    for code, name, description in ROLES:
        Role.objects.update_or_create(code=code, defaults={'name': name, 'description': description})
    for code, name, description in WALLET_TYPES:
        WalletTransactionType.objects.update_or_create(code=code, defaults={'name': name, 'description': description})


def unseed(apps, schema_editor):
    apps.get_model('users', 'Role').objects.filter(code__in=[r[0] for r in ROLES]).delete()
    apps.get_model('users', 'WalletTransactionType').objects.filter(code__in=[t[0] for t in WALLET_TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_role_wallettransactiontype_wallettransaction'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
