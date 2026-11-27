from django.apps import AppConfig

class RequestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'requests'

    def ready(self):
        from . import signals  # <--- ВОТ ТУТ ПОСТАВЬ ТОЧКУ ПЕРЕД import