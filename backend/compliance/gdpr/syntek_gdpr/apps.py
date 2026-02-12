"""Django app configuration for Syntek GDPR."""

from django.apps import AppConfig


class SyntekGDPRConfig(AppConfig):
    """Configuration for the Syntek GDPR app."""

    default_auto_field = "django.db.models.BigAutoField"  # type: ignore[assignment]
    name = "syntek_gdpr"
    verbose_name = "Syntek GDPR Compliance"

    def ready(self):
        """Import signals and perform app initialization."""
        # Import signals here if needed in the future
        pass
