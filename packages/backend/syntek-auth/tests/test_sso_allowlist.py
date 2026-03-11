"""US076 — Red phase: SSO provider allowlist tests for ``syntek-auth``.

Tests cover:
- Blocked providers raise ``ImproperlyConfigured`` at startup with a message
  that names the offending provider.
- All 8 blocked providers are individually rejected.
- All 7 built-in allowed providers pass validation without error.
- An uncertified custom OIDC provider (no ``mfa_enforced: True``) is rejected.
- A custom OIDC provider with ``mfa_enforced: True`` is accepted.
- An empty ``OAUTH_PROVIDERS`` list passes without error.
- ``SyntekAuthConfig.ready()`` calls the allowlist check.

All tests **fail** in the red phase because both ``validate_oauth_providers``
and ``SyntekAuthConfig.ready()`` raise ``NotImplementedError``.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from syntek_auth.allowlist import (
    BLOCKED_PROVIDERS,
    BUILTIN_ALLOWED_PROVIDERS,
    validate_oauth_providers,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def settings_with_providers(*providers: dict) -> dict:  # type: ignore[type-arg]
    """Return a minimal ``SYNTEK_AUTH`` dict with the supplied provider list."""
    return {"OAUTH_PROVIDERS": list(providers)}


def single_provider(name: str, **extra: object) -> dict:  # type: ignore[type-arg]
    """Return a single provider dict with the given identifier."""
    return {"provider": name, **extra}


# ---------------------------------------------------------------------------
# AC: Blocked providers raise ImproperlyConfigured
# ---------------------------------------------------------------------------


class TestBlockedProviders:
    """Every provider in BLOCKED_PROVIDERS must raise ImproperlyConfigured."""

    @pytest.mark.parametrize("provider_id", sorted(BLOCKED_PROVIDERS))
    def test_blocked_provider_raises_improperly_configured(
        self, provider_id: str
    ) -> None:
        """Configuring any blocked provider must raise ImproperlyConfigured."""
        syntek_auth = settings_with_providers(single_provider(provider_id))

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_oauth_providers(syntek_auth)

        msg = str(exc_info.value)
        assert provider_id in msg.lower(), (
            f"Error message must name the blocked provider '{provider_id}'; got: {msg!r}"
        )

    def test_google_blocked_names_provider_in_message(self) -> None:
        """Google-specific: error message must name 'google' explicitly."""
        syntek_auth = settings_with_providers(single_provider("google"))

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_oauth_providers(syntek_auth)

        assert "google" in str(exc_info.value).lower()

    def test_facebook_blocked_raises_improperly_configured(self) -> None:
        """Facebook must be rejected unconditionally."""
        syntek_auth = settings_with_providers(single_provider("facebook"))

        with pytest.raises(ImproperlyConfigured):
            validate_oauth_providers(syntek_auth)

    def test_discord_blocked_raises_improperly_configured(self) -> None:
        """Discord must be rejected unconditionally."""
        syntek_auth = settings_with_providers(single_provider("discord"))

        with pytest.raises(ImproperlyConfigured):
            validate_oauth_providers(syntek_auth)

    def test_twitter_blocked_raises_improperly_configured(self) -> None:
        """Twitter / X must be rejected unconditionally."""
        syntek_auth = settings_with_providers(single_provider("twitter"))

        with pytest.raises(ImproperlyConfigured):
            validate_oauth_providers(syntek_auth)

    def test_error_message_includes_docs_reference(self) -> None:
        """The error message must mention SYNTEK_AUTH['OAUTH_ALLOWED_PROVIDERS']."""
        syntek_auth = settings_with_providers(single_provider("google"))

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_oauth_providers(syntek_auth)

        msg = str(exc_info.value)
        assert "OAUTH_ALLOWED_PROVIDERS" in msg or "does not enforce MFA" in msg, (
            f"Error must reference OAUTH_ALLOWED_PROVIDERS or explain MFA requirement; got: {msg!r}"
        )

    def test_blocked_provider_mixed_case_is_rejected(self) -> None:
        """Provider identifiers should be normalised to lowercase before checking."""
        syntek_auth = settings_with_providers(single_provider("Google"))

        with pytest.raises(ImproperlyConfigured):
            validate_oauth_providers(syntek_auth)

    def test_first_blocked_provider_fails_fast(self) -> None:
        """When multiple providers are listed and the first is blocked, the error
        must reference that first provider."""
        syntek_auth = settings_with_providers(
            single_provider("google"),
            single_provider("github"),
        )

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_oauth_providers(syntek_auth)

        assert "google" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# AC: Allowed built-in providers pass validation
# ---------------------------------------------------------------------------


class TestAllowedBuiltinProviders:
    """All providers in BUILTIN_ALLOWED_PROVIDERS must pass without error."""

    @pytest.mark.parametrize("provider_id", sorted(BUILTIN_ALLOWED_PROVIDERS))
    def test_allowed_provider_does_not_raise(self, provider_id: str) -> None:
        """Configuring a built-in allowed provider must not raise."""
        syntek_auth = settings_with_providers(single_provider(provider_id))

        # Must not raise any exception.
        validate_oauth_providers(syntek_auth)

    def test_github_allowed_does_not_raise(self) -> None:
        """GitHub is platform-mandatory 2FA — must pass without an mfa_enforced flag."""
        syntek_auth = settings_with_providers(single_provider("github"))
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_okta_allowed_does_not_raise(self) -> None:
        """Okta enforces MFA at application policy level — must pass."""
        syntek_auth = settings_with_providers(single_provider("okta"))
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_entra_allowed_does_not_raise(self) -> None:
        """Microsoft Entra ID (business accounts) — must pass."""
        syntek_auth = settings_with_providers(single_provider("entra"))
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_multiple_allowed_providers_pass(self) -> None:
        """Multiple built-in allowed providers in a single list must all pass."""
        syntek_auth = settings_with_providers(
            single_provider("github"),
            single_provider("okta"),
            single_provider("defguard"),
        )
        validate_oauth_providers(syntek_auth)  # must not raise


# ---------------------------------------------------------------------------
# AC: Custom / self-hosted OIDC providers
# ---------------------------------------------------------------------------


class TestCustomOidcProviders:
    """Self-hosted OIDC providers must carry mfa_enforced: True to pass."""

    def test_custom_provider_without_mfa_enforced_raises(self) -> None:
        """A custom OIDC provider that does not carry ``mfa_enforced: True`` must
        raise ``ImproperlyConfigured``."""
        syntek_auth = settings_with_providers(
            single_provider("my-custom-idp"),  # no mfa_enforced key
        )

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_oauth_providers(syntek_auth)

        msg = str(exc_info.value)
        assert "my-custom-idp" in msg.lower() or "mfa" in msg.lower(), (
            f"Error must reference the uncertified provider or MFA; got: {msg!r}"
        )

    def test_custom_provider_with_mfa_enforced_false_raises(self) -> None:
        """A custom provider with ``mfa_enforced: False`` must be rejected."""
        syntek_auth = settings_with_providers(
            single_provider("my-idp", mfa_enforced=False),
        )

        with pytest.raises(ImproperlyConfigured):
            validate_oauth_providers(syntek_auth)

    def test_custom_provider_with_mfa_enforced_true_passes(self) -> None:
        """A custom OIDC provider with ``mfa_enforced: True`` must pass."""
        syntek_auth = settings_with_providers(
            single_provider("my-company-keycloak", mfa_enforced=True),
        )

        # Must not raise.
        validate_oauth_providers(syntek_auth)

    def test_defguard_self_hosted_with_mfa_enforced_true_passes(self) -> None:
        """Defguard listed as a custom provider with mfa_enforced: True passes."""
        syntek_auth = settings_with_providers(
            single_provider("defguard", mfa_enforced=True),
        )
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_mixed_valid_and_invalid_custom_providers_raises(self) -> None:
        """A list containing a valid custom provider followed by an uncertified
        one must raise — the uncertified provider is caught."""
        syntek_auth = settings_with_providers(
            single_provider("certified-idp", mfa_enforced=True),
            single_provider("uncertified-idp"),  # no mfa_enforced
        )

        with pytest.raises(ImproperlyConfigured):
            validate_oauth_providers(syntek_auth)


# ---------------------------------------------------------------------------
# AC: Empty provider list
# ---------------------------------------------------------------------------


class TestEmptyProviderList:
    """An empty OAUTH_PROVIDERS list must pass without error."""

    def test_empty_providers_list_does_not_raise(self) -> None:
        """No providers configured — validation must pass silently."""
        syntek_auth = settings_with_providers()
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_missing_oauth_providers_key_does_not_raise(self) -> None:
        """A ``SYNTEK_AUTH`` dict with no ``OAUTH_PROVIDERS`` key must pass."""
        validate_oauth_providers({})  # no OAUTH_PROVIDERS key at all


# ---------------------------------------------------------------------------
# AC: SyntekAuthConfig.ready() calls the allowlist check
# ---------------------------------------------------------------------------


class TestSyntekAuthConfigReady:
    """SyntekAuthConfig.ready() must delegate to validate_oauth_providers."""

    def test_ready_with_blocked_provider_raises_improperly_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must raise ImproperlyConfigured when SYNTEK_AUTH contains a
        blocked provider."""
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        monkeypatch.setattr(
            django_settings,
            "SYNTEK_AUTH",
            {"OAUTH_PROVIDERS": [{"provider": "google"}]},
            raising=False,
        )

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))

        with pytest.raises(ImproperlyConfigured):
            app_config.ready()

    def test_ready_with_allowed_provider_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must not raise when only allowed providers are configured."""
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        monkeypatch.setattr(
            django_settings,
            "SYNTEK_AUTH",
            {"OAUTH_PROVIDERS": [{"provider": "github"}]},
            raising=False,
        )

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))
        app_config.ready()  # must not raise

    def test_ready_with_no_syntek_auth_setting_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must not raise when SYNTEK_AUTH is not defined in settings."""
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        # Remove SYNTEK_AUTH entirely if it was set by a previous test.
        if hasattr(django_settings, "SYNTEK_AUTH"):
            monkeypatch.delattr(django_settings, "SYNTEK_AUTH")

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))
        app_config.ready()  # must not raise
