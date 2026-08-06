from django.apps import AppConfig

class RecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.recommendations'

    def ready(self):
        pass  # No hay signals en recommendations, las interacciones se registran directamente

