"""Django app configuration for Syntek Monitoring."""

from django.apps import AppConfig


class SyntekMonitoringConfig(AppConfig):
    """Configuration for the Syntek Monitoring app."""

    default_auto_field = "django.db.models.BigAutoField"  # type: ignore[assignment]
    name = "syntek_monitoring"
    verbose_name = "Syntek Security Monitoring"

    def ready(self):
        """Import signals and perform app initialization."""
        # Import signals here if needed in the future
        pass
