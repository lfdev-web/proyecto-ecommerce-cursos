import os
from celery import Celery
from django.conf import settings

# Establecer las opciones de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Usar el namespace de Django para la configuración
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas automáticamente desde todas las apps registradas
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Definición de colas
app.conf.task_routes = {
    'apps.recommendations.tasks.*': {'queue': 'ml_queue'},
    '*': {'queue': 'default'},
}
