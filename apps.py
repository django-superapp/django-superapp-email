from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppConfig(AppConfig):
    name = 'superapp.apps.email'
    verbose_name = _('Email')
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        # Import signals to register them
        import superapp.apps.email.signals
