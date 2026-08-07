"""
Crea las 4 cuentas de demostración sin volver a sembrar toda la base.

    docker compose -f docker-compose.prod.yml cp scripts/crear_usuarios_demo.py backend:/tmp/cd.py
    docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "exec(open('/tmp/cd.py').read())"

La lógica está en apps/common/demo_accounts.py, compartida con el seed, para
que las cuentas sean idénticas se llegue por donde se llegue.
"""
from apps.common.demo_accounts import CUENTAS, crear_cuentas_demo
from apps.users.models import CustomUser

creadas = crear_cuentas_demo()

print(f'\nCuentas creadas ahora: {creadas}')
for email, clave, _, _, rol in CUENTAS:
    print(f'  {email:<20} {clave:<12} {rol}')
print('\nrevisor@demo.com puede completar cursos de un clic desde Mi biblioteca.')
print(f'total de usuarios: {CustomUser.objects.count()}')
