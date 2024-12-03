
# apps.py

from django.apps import AppConfig

class mainConfig(AppConfig):
    name = 'main'

    def ready(self):
        import main.signals