"""Django app configuration for Syntek Authentication module."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration for the Syntek Authentication app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "syntek_authentication"
    verbose_name = "Syntek Authentication"

    def ready(self):
        """Import signal handlers when app is ready."""
        # Import signals here to avoid circular imports
        # from . import signals
        pass
