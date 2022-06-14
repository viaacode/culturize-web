from django.apps import AppConfig

from api.util import load_access_key

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        load_access_key()

