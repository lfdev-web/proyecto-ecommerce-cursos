"""Crea las 3 cuentas de demostración sin volver a sembrar todo."""
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.users.models import (
    INITIAL_WALLET_BALANCE, CustomUser, WalletTransaction, WalletTransactionType,
)

CUENTAS = [
    ('admin@demo.com', 'Admin1234!', 'Admin', 'Demo', 'ADMIN'),
    ('docente@demo.com', 'Demo1234!', 'Docente', 'Demo', 'DOCENTE'),
    ('alumno@demo.com', 'Demo1234!', 'Alumno', 'Demo', 'ALUMNO'),
]

for email, clave, nombre, apellido, rol in CUENTAS:
    if CustomUser.objects.filter(email=email).exists():
        print(f'  ya existía: {email}')
        continue
    u = CustomUser(
        email=email, password=make_password(clave),
        first_name=nombre, last_name=apellido, role_id=rol,
        date_joined=timezone.now(), is_email_verified=True,
        balance=INITIAL_WALLET_BALANCE,
    )
    if rol == 'ADMIN':
        u.is_staff = True
        u.is_superuser = True
    u.save()
    WalletTransaction.objects.create(
        user=u, transaction_type_id=WalletTransactionType.WELCOME,
        amount=INITIAL_WALLET_BALANCE, balance_after=INITIAL_WALLET_BALANCE,
        description='Saldo simulado de bienvenida', created_at=timezone.now(),
    )
    print(f'  creado: {email} ({rol})')

print(f'\ntotal de usuarios: {CustomUser.objects.count()}')
