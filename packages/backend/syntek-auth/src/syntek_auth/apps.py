"""Django AppConfig for syntek-auth — US009 / US076."""

from __future__ import annotations

from django.apps import AppConfig


class SyntekAuthConfig(AppConfig):
    """Application configuration for ``syntek-auth``.

    Performs startup validation of ``SYNTEK_AUTH`` settings, including:

    - Full settings validation (US009) via :func:`~syntek_auth.conf.validate_settings`.
    - SSO provider allowlist enforcement (US076) via
      :func:`~syntek_auth.allowlist.validate_oauth_providers`.

    Both validators raise ``ImproperlyConfigured`` on failure.
    """

    name = "syntek_auth"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Validate ``SYNTEK_AUTH`` settings on startup.

        Reads ``SYNTEK_AUTH`` from Django settings and runs both the full
        settings validator (US009) and the SSO allowlist check (US076).

        Raises
        ------
        ImproperlyConfigured
            If any configured value is invalid or any OAuth provider is blocked.
        """
        from django.conf import settings

        from syntek_auth.backends.allowlist import validate_oauth_providers
        from syntek_auth.conf import validate_settings

        syntek_auth_settings: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]

        # US009: validate all SYNTEK_AUTH keys — only runs when the key is present
        if syntek_auth_settings:
            validate_settings(syntek_auth_settings)

        # US076: SSO provider allowlist check (always runs, even on empty settings)
        validate_oauth_providers(syntek_auth_settings)
