import os
import re
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
# Default seguro: si la variable no está definida (ej. despliegue mal configurado),
# el sistema arranca en modo producción (DEBUG=False) en vez de exponer datos sensibles.
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'


def env_requerida_en_produccion(nombre, default_dev):
    """
    Devuelve la variable de entorno; en desarrollo acepta el valor de respaldo.

    En producción (DEBUG=False) la ausencia de la variable es un ERROR FATAL en vez
    de un default silencioso: si el .env no llega al contenedor, antes el sistema
    arrancaba igual con una clave que está escrita en el código, y cualquiera con
    acceso al repositorio podía firmar tokens válidos. Mejor no arrancar que
    arrancar inseguro.
    """
    valor = os.environ.get(nombre)
    if valor:
        return valor
    if DEBUG:
        return default_dev
    raise ImproperlyConfigured(
        f'Falta la variable de entorno {nombre}. Es obligatoria con DEBUG=False. '
        f'Defínela en el .env del servidor antes de levantar los contenedores.'
    )


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_requerida_en_produccion('DJANGO_SECRET_KEY', 'django-insecure-default-key-dev-only')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,backend').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'drf_spectacular',
    
    # Local apps
    'apps.common',
    'apps.users',
    'apps.catalog',
    'apps.orders',
    'apps.recommendations',
    'apps.library',
    'apps.memberships',
    'apps.analytics',
    'apps.exams',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # El throttling de DRF no llega al admin: /admin/login/ es una vista normal
    # de Django y aceptaba intentos sin límite.
    'apps.common.middleware.AdminLoginRateLimitMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'ecommerce_cursos_db'),
        'USER': os.environ.get('POSTGRES_USER', 'ecommerce_user'),
        'PASSWORD': env_requerida_en_produccion('POSTGRES_PASSWORD', 'dev_postgres_password_123'),
        'HOST': os.environ.get('POSTGRES_HOST', 'postgres_db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model (ADR-09)
AUTH_USER_MODEL = 'users.CustomUser'

# Internationalization
LANGUAGE_CODE = 'es-ec'

# Zona Horaria (ADR-11)
TIME_ZONE = 'America/Guayaquil'
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Permisos de lo que se sube a MEDIA_ROOT.
#
# En producción los archivos los ESCRIBE Django (como root) pero los SIRVE
# nginx (como usuario nginx). Sin esto, Django crea los directorios con el
# umask del proceso y pueden quedar en 700: nginx no puede recorrerlos y
# devuelve 403 aunque los archivos en sí sean legibles. El síntoma es
# desconcertante porque el archivo existe y tiene permisos correctos.
#
# El 0o755 da recorrido a todos sin permitir escritura; el 0o644, lectura.
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_PERMISSIONS = 0o644

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
# Cuántos proxies PROPIOS hay delante de Django. En producción son dos:
# Caddy (termina el TLS) y nginx (sirve el SPA y hace de proxy). En desarrollo
# es 0 y se usa REMOTE_ADDR.
#
# Importa para el límite de intentos: DRF identifica al visitante por su IP y,
# sin este número, toma la cabecera X-Forwarded-For ENTERA como identidad. Esa
# cabecera la puede escribir el propio cliente, así que cambiándola en cada
# petición tendría un contador nuevo cada vez y el límite de login no serviría
# de nada. Con el número correcto se lee la posición que escribió NUESTRO proxy
# y se ignora lo que el cliente haya puesto delante.
TRUSTED_PROXY_COUNT = int(os.environ.get('TRUSTED_PROXY_COUNT', 0))

REST_FRAMEWORK = {
    'NUM_PROXIES': TRUSTED_PROXY_COUNT,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Límite de peticiones. Sin esto el login aceptaba intentos ilimitados
    # (fuerza bruta) y el endpoint público de analítica podía inundarse de
    # eventos falsos, que además alimentan el entrenamiento del recomendador.
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',      # visitante anónimo navegando el catálogo
        'user': '300/min',     # usuario autenticado (el reproductor consulta seguido)
        'login': '8/min',      # intentos de autenticación por IP
        'registro': '5/hour',  # evita inflar la tabla de usuarios
        'analitica': '90/min',  # eventos de navegación por IP
        # Recargas: el límite existe para frenar el "card testing" (probar
        # muchos números de tarjeta seguidos), no para limitar el uso normal.
        # Por eso es por MINUTO y no por hora: un script se topa igual, pero
        # una persona probando nunca lo alcanza y, si lo alcanza, se libera en
        # 60 segundos en vez de dejarla bloqueada una hora.
        'recarga': '15/min',
        # Pedir el enlace de recuperación: cada intento manda un correo a
        # una dirección que elige quien llama, así que sin tope se podría
        # usar para inundar el buzón de otra persona.
        'password_reset': '5/hour',
        # Usar el enlace es otra cosa: no manda ningún correo y el usuario
        # legítimo puede necesitar varios intentos si su contraseña nueva
        # no pasa los validadores. Con el mismo tope que arriba, teclear
        # dos contraseñas débiles seguidas lo dejaba fuera una hora.
        'password_reset_confirm': '20/hour',
    },
}

# Caché compartida (Redis, backend nativo de Django 4+, sin dependencias extra).
# DRF guarda aquí los contadores del throttling: con la LocMemCache por defecto
# cada worker de gunicorn llevaría su propio conteo y el límite real de login
# sería 8/min POR WORKER.
#
# La URL se deriva de REDIS_URL cambiándole el número de base de datos (Celery
# usa la 0 y la 1). Así la contraseña de Redis vive en un solo lugar del .env.
_REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('CACHE_URL') or re.sub(r'/\d+$', '/2', _REDIS_URL),
    }
}

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 15))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Celery settings
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Reentrena el motor de recomendaciones (SVD) cada noche a las 3am.
# django_celery_beat.DatabaseScheduler sincroniza este dict a la BD al arrancar celery beat.
CELERY_BEAT_SCHEDULE = {
    'train-recommendations-nightly': {
        'task': 'apps.recommendations.tasks.train_svd_and_update_recommendations',
        'schedule': crontab(hour=3, minute=0),
    },
}

# CORS Config
# En desarrollo (DEBUG=True) se permite cualquier origen por comodidad.
# En producción se restringe a los orígenes explícitos de CORS_ALLOWED_ORIGINS.
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]

# ---------------------------------------------------------------------------
# Endurecimiento para producción
# ---------------------------------------------------------------------------
# Todo esto SOLO se activa con DEBUG=False. En desarrollo local no hay HTTPS,
# así que activarlo redirigiría http://localhost a https:// y rompería el
# entorno de trabajo.
if not DEBUG:
    # nginx/Traefik termina el TLS y reenvía por HTTP al contenedor; sin esta
    # cabecera Django creería que la petición no es segura y entraría en un
    # bucle de redirecciones con SECURE_SSL_REDIRECT.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Configurable porque hay dos casos donde debe apagarse: cuando el TLS se
    # termina en un balanceador externo que ya redirige, y al probar la imagen
    # de producción en local (sin certificado, esto dejaría el sitio inaccesible).
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'

    # HSTS: el navegador recuerda que este dominio es solo HTTPS. Se arranca en
    # 1 hora a propósito: si algo sale mal en el despliegue se revierte rápido.
    # Subir a 31536000 (1 año) recién cuando el HTTPS esté probado y estable.
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 3600))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False

    # Las cookies de sesión y CSRF (Django Admin) nunca viajan en claro.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

    # El navegador no adivina el tipo de contenido (evita que un archivo subido
    # a /media se interprete como HTML o JS).
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

    # El Django Admin usa formularios con CSRF: hay que declarar el dominio real.
    CSRF_TRUSTED_ORIGINS = [
        origin for origin in CORS_ALLOWED_ORIGINS if origin.startswith('https://')
    ]

# ---------------------------------------------------------------------------
# Correo
# ---------------------------------------------------------------------------
# Por defecto los correos se IMPRIMEN en la consola en vez de enviarse: así el
# proyecto funciona recién clonado, sin credenciales, y se puede ver el
# contenido completo en el log. Definiendo EMAIL_HOST se pasa a envío real.
#
# Para Gmail hace falta una "contraseña de aplicación" (no la del correo), que
# se genera en myaccount.google.com/apppasswords con la verificación en dos
# pasos activada.
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')

if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_TIMEOUT = 20
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Remitente. Gmail ignora un "from" que no sea la cuenta autenticada, así que
# se usa EMAIL_HOST_USER como valor por defecto.
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f'CursosTech <{os.environ.get("EMAIL_HOST_USER", "no-reply@cursostech.local")}>',
)

# Nombre y URL que aparecen en los correos
SITE_NAME = os.environ.get('SITE_NAME', 'CursosTech')
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:3000')

# Cuánto dura el enlace de recuperación de contraseña. El de Django son 3
# días; una hora es de sobra para quien acaba de pedirlo y reduce la
# ventana en que un enlace olvidado en el buzón sigue sirviendo.
PASSWORD_RESET_TIMEOUT = 60 * 60

# Tope de tamaño de las peticiones (subida de avatar y cédula del docente).
# Django rechaza con 400 cualquier cuerpo mayor, antes de tocar el disco.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
