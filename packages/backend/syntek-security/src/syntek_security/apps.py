"""Django AppConfig for syntek-security — US076 skeleton."""

from __future__ import annotations

from django.apps import AppConfig


class SyntekSecurityConfig(AppConfig):
    """Application configuration for ``syntek-security``.

    Applies proxy-trust settings on startup so that Django correctly honours
    TLS termination by the Nginx reverse proxy (US076).
    """

    name = "syntek_security"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Apply proxy-trust settings and validate ``SYNTEK_SECURITY`` on startup.

        Delegates to :func:`~syntek_security.proxy_settings.apply_proxy_settings`
        to inject ``SECURE_PROXY_SSL_HEADER``, ``USE_X_FORWARDED_HOST``, and
        ``SECURE_SSL_REDIRECT`` onto Django settings when they are not already set.
        """
        from syntek_security.proxy_settings import apply_proxy_settings

        apply_proxy_settings()
