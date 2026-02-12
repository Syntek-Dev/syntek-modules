"""Django app configuration for Syntek MFA."""

from django.apps import AppConfig


class SyntekMFAConfig(AppConfig):
    """Configuration for the Syntek MFA app."""

    default_auto_field = "django.db.models.BigAutoField"  # type: ignore[assignment]
    name = "syntek_mfa"
    verbose_name = "Syntek Multi-Factor Authentication"

    def ready(self):
        """Import signals and perform app initialization."""
        # Import signals here if needed in the future
        pass
