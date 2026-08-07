"""
Punto de entrada de las tareas de esta app para Celery.

`autodiscover_tasks()` importa únicamente el módulo `tasks` de cada aplicación
instalada. Las tareas de correo viven en `emails.py` porque ahí se entiende
mejor qué son, así que se importan aquí para que Celery las registre: el
decorador @shared_task las inscribe al importarse el módulo.

Sin este archivo las tareas existen pero el worker no las conoce, y cada envío
falla con "Received unregistered task".
"""
from .emails import (  # noqa: F401  (importadas por su efecto de registro)
    enviar_certificado,
    enviar_comprobante_recarga,
    enviar_factura,
)

__all__ = ['enviar_factura', 'enviar_certificado', 'enviar_comprobante_recarga']
