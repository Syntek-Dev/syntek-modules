"""Django AppConfig for syntek-auth — US076 skeleton."""

from __future__ import annotations

from django.apps import AppConfig


class SyntekAuthConfig(AppConfig):
    """Application configuration for ``syntek-auth``.

    Performs startup validation of ``SYNTEK_AUTH`` settings, including SSO
    provider allowlist enforcement (US076).
    """

    name = "syntek_auth"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Validate ``SYNTEK_AUTH`` settings on startup.

        Reads ``SYNTEK_AUTH`` from Django settings and delegates to
        :func:`~syntek_auth.allowlist.validate_oauth_providers`.  Raises
        ``ImproperlyConfigured`` if any configured OAuth provider is blocked
        or uncertified.

        Raises
        ------
        ImproperlyConfigured
            If any configured OAuth provider is blocked or uncertified.
        """
        from django.conf import settings

        from syntek_auth.allowlist import validate_oauth_providers

        syntek_auth_settings: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        validate_oauth_providers(syntek_auth_settings)
