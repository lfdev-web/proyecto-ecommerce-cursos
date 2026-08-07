# Despliegue a producción

Guía para llevar el proyecto a un servidor real. El entorno de desarrollo
(`docker-compose.yml`) **no sirve para producción**: el backend corre con
`manage.py runserver` y el frontend con el servidor de desarrollo de Vite.
Para producción se usa `docker-compose.prod.yml`.

---

## Diferencias entre desarrollo y producción

| | Desarrollo | Producción |
|---|---|---|
| Backend | `manage.py runserver` (1 hilo) | `gunicorn`, 3 trabajadores |
| Frontend | Servidor de Vite (sin compilar) | SPA compilada servida por nginx |
| Origen | Dos puertos (3000 y 8000) + CORS | Un solo origen, nginx hace de proxy |
| Postgres / Redis | Puertos publicados al host | Solo accesibles en la red interna |
| Código | Montado como volumen | Copiado a la imagen (inmutable) |
| `DEBUG` | `True` | `False` |
| Estáticos del admin | Los sirve Django | `collectstatic` + nginx |

---

## Requisitos en el servidor

- Docker Engine y el plugin Compose.
- Puerto 80 libre (y 443 si vas a poner HTTPS).
- Un dominio apuntando al servidor.

---

## Pasos

### 1. Copiar el proyecto y crear el `.env`

```bash
git clone <tu-repo> && cd Proyecto_Ecommerce_Cursos
cp .env.example .env
```

### 2. Rellenar el `.env`

**Estas cuatro son obligatorias.** Con `DEBUG=False`, si falta `DJANGO_SECRET_KEY`
o `POSTGRES_PASSWORD` el sistema **no arranca** — es a propósito: antes arrancaba
con una clave escrita en el código y eso permitía firmar tokens de sesión válidos.

```bash
# Genera una clave nueva (NO reutilices la de desarrollo):
docker run --rm python:3.12-slim python -c \
  "import secrets; print(secrets.token_urlsafe(64))"
```

| Variable | Valor en producción |
|---|---|
| `DJANGO_SECRET_KEY` | La que acabas de generar |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `tudominio.com,www.tudominio.com` |
| `CORS_ALLOWED_ORIGINS` | `https://tudominio.com` |
| `POSTGRES_PASSWORD` | Contraseña fuerte y nueva |
| `REDIS_PASSWORD` | Contraseña fuerte y nueva |
| `REDIS_URL` | `redis://:LA_PASSWORD@redis:6379/0` |
| `CELERY_BROKER_URL` | `redis://:LA_PASSWORD@redis:6379/0` |
| `CELERY_RESULT_BACKEND` | `redis://:LA_PASSWORD@redis:6379/1` |
| `TRUSTED_PROXY_COUNT` | `2` (Caddy + nginx) |

> `CORS_ALLOWED_ORIGINS` alimenta también `CSRF_TRUSTED_ORIGINS`, que el Django
> Admin necesita para aceptar sus formularios. Si lo dejas vacío no vas a poder
> guardar nada en el admin.

### 3. Levantar

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

El backend corre las migraciones y el `collectstatic` solo, al arrancar.

### 4. Crear el administrador

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 5. Datos iniciales

Los catálogos (roles, estados, tipos) los siembran las migraciones. Para cargar
además los datos de demostración:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_demo_data
```

> **En una plataforma real no ejecutes el seed.** Crea usuarios de prueba con
> contraseñas conocidas (`Demo1234!`). Sirve para la defensa del proyecto, no
> para producción de verdad.

### 6. Actividades de los cursos

Cada curso tiene dos actividades evaluadas: un **cuestionario** y un **trabajo
práctico**. Sin ellas el alumno no se certifica. El seed ya las crea; sobre una
base sembrada **antes** de este cambio hay que crearlas aparte:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py crear_actividades
```

Es idempotente y no borra nada: solo agrega lo que falte, así que se puede
correr sobre la base que ya está en producción sin perder usuarios, compras ni
certificados. Vuelve a correrlo cuando agregues cursos nuevos.

### 7. Ofertas del carrete de la portada

El carrete de la portada se oculta si no hay ningún curso en oferta. Sobre una
base sembrada antes de las promociones no hay ninguno:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py crear_promociones
```

**Las ofertas vencen** (entre 2 y 10 días). Vuelve a correr el comando cuando el
carrete se quede vacío, o fija una duración larga:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py crear_promociones --dias 30
```

Con `--quitar` se retiran todas. El precio de lista nunca se toca: la oferta vive
en `promo_price`/`promo_until`, así que al vencer el curso vuelve solo a su precio
original.

### 8. Cuentas de demostración

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py cuentas_demo
```

Crea las que falten y deja a cada una en su punto de partida. Al terminar
imprime un resumen con las credenciales y el estado de cada cuenta.

**Es idempotente y nunca cambia la contraseña de una cuenta que ya existe.**
Si ya cambiaste la del administrador —que es lo correcto, porque la de este
repositorio es pública— se respeta, y el resumen lo dice en vez de imprimir
una contraseña que no funciona.

| Cuenta | Contraseña | Con qué arranca | Para qué sirve |
|---|---|---|---|
| `admin@demo.com` | `Admin1234!` | — | Django Admin y panel de analítica |
| `docente@demo.com` | `Demo1234!` | Plan Docente VIP y **3 cursos con ventas, alumnos y reseñas** | El negocio visto desde quien enseña: ingresos, comisión, alumnos por curso, pedir cupo y publicar |
| `alumno@demo.com` | `Demo1234!` | $500 de saldo y la **biblioteca vacía** | El recorrido completo: catálogo → carrito → pago → lecciones → actividades → certificado |
| `revisor@demo.com` | `Demo1234!` | Membresía y **6 cursos** | Lo mismo, pero con el botón que completa todos sus cursos de un clic |

Los tres cursos del docente (`Python desde cero`, `React en la práctica` y
`Docker desde cero`) están también en la biblioteca del revisor a propósito:
así el docente lo ve en su lista de alumnos y las dos pantallas se sostienen
entre sí.

#### Repetir el recorrido después de un ensayo

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py cuentas_demo --ensayo
```

Deja las dos cuentas de alumno en su punto de partida:

- **`alumno@demo.com`**: biblioteca vacía y saldo repuesto. **Sus órdenes NO se
  borran** — son el historial de compras y el docente cobró comisión por ellas;
  borrarlas descuadraría su panel.
- **`revisor@demo.com`**: certificados y progreso borrados, pero conserva sus
  seis cursos.

> **Por qué hay que reiniciar al revisor para enseñar los correos.** Un
> certificado se emite —y se envía— **una sola vez**. Si ya está emitido,
> pulsar el botón de recorrido rápido no manda ningún correo; solo vuelve a
> confirmar lo que ya estaba hecho. La respuesta lo dice explícitamente
> («X ya estaban emitidos de antes… no se reenvían por correo»), pero si lo
> que quieres es que el revisor VEA llegar el correo, hay que reiniciar antes.
>
> Con `--limpiar-alumno` y `--limpiar-revisor` se puede hacer por separado.

> `revisor@demo.com` existe porque completar un curso a mano son siete
> lecciones, un cuestionario y una entrega, y quien revisa la plataforma
> necesita ver el certificado y el correo, no repetir ese trámite. Es una
> puerta trasera deliberada: vive en la columna `can_autocomplete_demo` de la
> tabla de usuarios, está apagada por defecto y solo puede completar las
> inscripciones **de su propio dueño**. Cualquier otra cuenta que la invoque
> recibe 403. En una plataforma real esa columna no existiría — si algún día
> este proyecto deja de ser una demostración, hay que quitarla.

---

## HTTPS

El compose publica solo el puerto 80. Django ya trae activadas las cabeceras de
seguridad con `DEBUG=False` (redirección a HTTPS, HSTS, cookies seguras), pero
**necesita que algo termine el TLS delante**. Dos opciones:

### Opción A — Caddy delante (recomendada, certificado automático)

```yaml
# añade este servicio a docker-compose.prod.yml y quita el "ports" del frontend
caddy:
  image: caddy:2-alpine
  restart: always
  ports: ["80:80", "443:443"]
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile
    - caddy_data:/data
  networks: [ecommerce_net]
```

```
# Caddyfile
tudominio.com {
    reverse_proxy frontend:80
}
```

Caddy pide y renueva el certificado de Let's Encrypt solo.

### Opción B — Certificado propio en nginx

Monta los certificados en el contenedor `frontend` y añade un bloque
`listen 443 ssl;` en `frontend/nginx.conf`.

> **Sin HTTPS no despliegues con `DEBUG=False`**: `SECURE_SSL_REDIRECT` va a
> redirigir todo a `https://` y el sitio quedará inaccesible.

---

## Comprobaciones después de desplegar

```bash
# 1. Django no reporta problemas de configuración de producción
docker compose -f docker-compose.prod.yml exec backend python manage.py check --deploy

# 2. Todos los contenedores arriba
docker compose -f docker-compose.prod.yml ps

# 3. La API responde
curl -I https://tudominio.com/api/catalog/courses/

# 4. La SPA carga y sus rutas internas no dan 404 al recargar
curl -I https://tudominio.com/mi-biblioteca

# 5. El admin se ve CON estilos (si no, falló collectstatic)
#    https://tudominio.com/admin/

# 6. El límite de intentos de login funciona: al noveno intento seguido
#    con contraseña incorrecta debe responder 429
```

---

## Lista de verificación final

- [ ] `DJANGO_DEBUG=False` en el `.env` del servidor
- [ ] `DJANGO_SECRET_KEY` nueva, distinta a la de desarrollo
- [ ] Contraseñas de Postgres y Redis nuevas y fuertes
- [ ] `DJANGO_ALLOWED_HOSTS` con el dominio real (no `*`)
- [ ] `CORS_ALLOWED_ORIGINS` con `https://` y el dominio real
- [ ] `.env` **no** está en el repositorio (ya está en `.gitignore`)
- [ ] HTTPS funcionando antes de exponer el sitio
- [ ] `manage.py check --deploy` sin advertencias críticas
- [ ] Superusuario creado y su contraseña guardada en un gestor
- [ ] Copia de seguridad de la base configurada (ver abajo)

---

## Endurecer el servidor

Lo que trae la aplicación ya (no hay que hacer nada):

| Defensa | Dónde |
|---|---|
| Límite de intentos en la API (8/min por IP) | throttling de DRF, contadores en Redis |
| Límite de intentos en `/admin/login/` (6, bloqueo 15 min) | `apps.common.middleware` |
| HTTPS obligatorio, HSTS, cookies seguras | Django con `DEBUG=False` |
| CSP, `nosniff`, `X-Frame-Options`, `Permissions-Policy` | `frontend/nginx.conf` |
| Formatos de subida restringidos | `apps.library.models.EXTENSIONES_ENTREGA` |
| Postgres y Redis sin puertos publicados | `docker-compose.prod.yml` |

Lo que hay que hacer **en el sistema operativo**, una sola vez:

```bash
# 1. Cortafuegos: solo SSH, HTTP y HTTPS
sudo apt update && sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status verbose
```

> **Antes de activarlo, comprueba que `sudo ufw allow OpenSSH` está puesto.**
> Si activas el cortafuegos sin permitir el puerto 22 pierdes el acceso al
> servidor y hay que entrar por la consola del panel del proveedor.

```bash
# 2. Bloquear a quien insista con el SSH
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

```bash
# 3. Actualizaciones de seguridad automáticas
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

```bash
# 4. Cambiar la contraseña del administrador
#    Las de demostración están en el repositorio: si es público, cualquiera
#    puede entrar al admin como superusuario.
docker compose -f docker-compose.prod.yml exec backend python manage.py changepassword admin@demo.com
```

Comprobar que las defensas responden:

```bash
# 9 intentos de login seguidos: los últimos deben dar 429
for i in $(seq 1 9); do
  curl -s -o /dev/null -w "%{http_code} " -X POST https://tudominio.com/api/auth/login/ \
    -H 'Content-Type: application/json' -d '{"email":"a@b.com","password":"x"}'
done; echo

# Cabeceras de seguridad presentes
curl -sI https://tudominio.com/ | grep -iE "content-security|strict-transport|x-frame|referrer"
```

---

## Copias de seguridad

```bash
# Respaldar
docker compose -f docker-compose.prod.yml exec -T postgres_db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > respaldo_$(date +%F).sql

# Restaurar
docker compose -f docker-compose.prod.yml exec -T postgres_db \
  psql -U "$POSTGRES_USER" "$POSTGRES_DB" < respaldo_2026-07-31.sql
```

Los archivos subidos por usuarios (avatares, cédulas de los docentes y las
**entregas de los trabajos prácticos**) viven en el volumen `media_files`.
Respáldalo también:

```bash
docker run --rm -v proyecto_ecommerce_cursos_media_files:/media \
  -v "$(pwd)":/respaldo alpine \
  tar czf /respaldo/media_$(date +%F).tar.gz -C /media .
```

---

## Actualizar la aplicación

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Las migraciones se aplican solas al arrancar el backend. Lo que **no** es
automático son los datos: si la actualización trae contenido nuevo (actividades,
cuentas, ofertas), hay que crearlo con su comando. Ver los pasos 6 a 8.

---

## Correo (opcional pero recomendado)

Sin configurar nada, los correos se **imprimen en el log** del worker de Celery
en vez de enviarse. El flujo se puede demostrar completo así. Para que salgan de
verdad, con Gmail:

1. Activa la **verificación en dos pasos** en tu cuenta de Google.
2. Genera una **contraseña de aplicación** en `myaccount.google.com/apppasswords`
   (son 16 caracteres, no es la contraseña de tu correo).
3. Añade al `.env` del servidor:

> **Con una cuenta institucional (`@universidad.edu`) esto no suele funcionar.**
> En Google Workspace el administrador del dominio puede desactivar las
> contraseñas de aplicación para todos, y desde el perfil de usuario no hay
> manera de habilitarlas: la página de `apppasswords` simplemente no aparece.
> No es un problema que puedas resolver tú. Usa una cuenta de Gmail personal
> como servidor de salida y deja la institucional como buzón de llegada
> (`manage.py correo_demo`, más abajo). Enviar y recibir son cosas distintas.

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tucorreo@gmail.com
EMAIL_HOST_PASSWORD=xxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=CursosTech <tucorreo@gmail.com>
SITE_NAME=CursosTech
SITE_URL=https://lfldev.online
```

4. Reinicia el backend y el worker:

```bash
docker compose -f docker-compose.prod.yml up -d backend celery_worker
```

Gmail **ignora un remitente distinto a la cuenta autenticada**, así que
`DEFAULT_FROM_EMAIL` debe usar el mismo correo de `EMAIL_HOST_USER`. El límite
es de unos 500 correos al día.

### Alternativa sin Gmail

Si no quieres exponer una cuenta personal, cualquier proveedor de SMTP sirve;
solo cambian las cuatro variables. Con **Brevo** (300 correos gratis al día):

```bash
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<el login SMTP que te da Brevo>
EMAIL_HOST_PASSWORD=<la clave SMTP>
DEFAULT_FROM_EMAIL=CursosTech <el remitente que verificaste en Brevo>
```

A diferencia de Gmail, aquí el remitente sí puede ser distinto del usuario SMTP,
pero **hay que verificar esa dirección en el panel de Brevo** antes de usarla.

### Que los correos de la demostración lleguen a tu bandeja

Las cuentas de demostración usan direcciones `@demo.com`, que no existen. Para
enseñar en vivo cómo llega la factura o el certificado, redirige sus avisos a un
buzón real:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py correo_demo tucorreo@ejemplo.com
```

Las credenciales **no cambian**: `alumno@demo.com` sigue siendo el usuario del
login. Lo que se cambia es `notification_email`, un campo aparte que solo dice a
dónde mandar el aviso — por eso las cuatro cuentas pueden apuntar al mismo buzón
aunque `email` sea único. Con `--quitar` se deshace, y con `--cuenta` se limita a
una sola cuenta.

> Esto **no sustituye** a la configuración de SMTP de arriba. Sin `EMAIL_HOST`,
> el correo se sigue imprimiendo en el log del worker y no llega a ninguna
> bandeja, apunte a donde apunte.

### Comprobar que el correo funciona

```bash
# Diagnóstico: dice si está configurado y si las credenciales sirven
docker compose -f docker-compose.prod.yml exec backend python manage.py probar_correo

# Y además envía un mensaje real
docker compose -f docker-compose.prod.yml exec backend python manage.py probar_correo tucorreo@ejemplo.com
```

Separa las tres causas de «no me llegó el correo», que desde fuera se ven
iguales:

| Lo que dice | Qué pasa |
|---|---|
| `EMAIL_HOST no está definido` | Faltan las variables en el `.env`. Los correos se imprimen en el log y no salen |
| `FALLÓ: SMTPAuthenticationError` | La contraseña no sirve. Con Gmail tiene que ser la de aplicación, 16 caracteres **sin espacios** |
| `Entregado al servidor SMTP` | Salió. Si aun así no aparece, está en spam |

> Buscar `Correo enviado` en el log del worker **solo sirve después** de haber
> hecho algo que genere un correo (una compra, un certificado, una recarga).
> Si no has disparado nada, el log está vacío y eso no significa que esté mal.

### Qué se envía

| Cuándo | Contenido |
|---|---|
| Al completar una compra | Factura en PDF con el detalle y el descuento aplicado |
| Al emitirse un certificado | Certificado en PDF, solo la primera vez |
| Al aprobarse una recarga | Comprobante con la referencia y el saldo resultante |

El certificado se emite cuando se cumplen **las tres** condiciones: 100% de las
lecciones, cuestionario aprobado y trabajo práctico entregado. Si falta
cualquiera, no hay certificado ni correo.

Los tres salen por **Celery**, nunca dentro de la petición: si el SMTP está
caído, la compra sigue siendo válida y el fallo solo queda en el log. Verificar
que se enviaron:

```bash
docker compose -f docker-compose.prod.yml logs celery_worker | grep "Correo enviado"
```
