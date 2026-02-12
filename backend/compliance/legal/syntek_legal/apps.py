"""Django app configuration for Syntek Legal."""

from django.apps import AppConfig


class SyntekLegalConfig(AppConfig):
    """Configuration for the Syntek Legal app."""

    default_auto_field = "django.db.models.BigAutoField"  # type: ignore[assignment]
    name = "syntek_legal"
    verbose_name = "Syntek Legal Document Management"

    def ready(self):
        """Import signals and perform app initialization."""
        # Import signals here if needed in the future
        pass
