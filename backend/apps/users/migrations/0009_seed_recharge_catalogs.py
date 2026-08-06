# Siembra los catálogos de la recarga de saldo: los estados de una recarga y
# el nuevo tipo de movimiento del libro mayor.

from django.db import migrations

RECHARGE_STATUSES = [
    ('PENDING', 'Pendiente', 'Recarga iniciada, esperando autorización en la pasarela.'),
    ('APPROVED', 'Aprobada', 'La pasarela autorizó el cobro y el saldo fue acreditado.'),
    ('DECLINED', 'Rechazada', 'La pasarela rechazó la tarjeta; no se acreditó saldo.'),
    ('CANCELLED', 'Cancelada', 'El usuario abandonó el pago en la pasarela.'),
    ('EXPIRED', 'Expirada', 'Pasaron más de 15 minutos sin autorizar el cobro.'),
]

WALLET_TYPES = [
    ('RECHARGE', 'Recarga de saldo', 'Ingreso por recarga a través de la pasarela de pago simulada.'),
]


def seed(apps, schema_editor):
    RechargeStatus = apps.get_model('users', 'RechargeStatus')
    WalletTransactionType = apps.get_model('users', 'WalletTransactionType')
    for code, name, description in RECHARGE_STATUSES:
        RechargeStatus.objects.update_or_create(
            code=code, defaults={'name': name, 'description': description}
        )
    for code, name, description in WALLET_TYPES:
        WalletTransactionType.objects.update_or_create(
            code=code, defaults={'name': name, 'description': description}
        )


def unseed(apps, schema_editor):
    apps.get_model('users', 'RechargeStatus').objects.filter(
        code__in=[s[0] for s in RECHARGE_STATUSES]
    ).delete()
    apps.get_model('users', 'WalletTransactionType').objects.filter(
        code__in=[t[0] for t in WALLET_TYPES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_rechargestatus_walletrecharge'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
