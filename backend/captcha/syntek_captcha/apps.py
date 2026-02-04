"""Django app configuration for Syntek Captcha."""

from django.apps import AppConfig


class SyntekCaptchaConfig(AppConfig):
    """Configuration for the Syntek Captcha app."""

    default_auto_field = "django.db.models.BigAutoField"  # type: ignore[assignment]
    name = "syntek_captcha"
    verbose_name = "Syntek reCAPTCHA Integration"

    def ready(self):
        """Import signals and perform app initialization."""
        # Import signals here if needed in the future
        pass
