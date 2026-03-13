"""US076 — SSO provider allowlist tests for ``syntek-auth``.

Tests cover:
- Providers in MFA_GATED_PROVIDERS pass startup validation without raising
  (they are MFA-gated at the OAuth callback layer, not blocked at startup).
- ``is_mfa_gated_provider()`` correctly identifies gated vs. allowed providers.
- ``MFA_GATED_PROVIDERS`` and ``BUILTIN_ALLOWED_PROVIDERS`` are disjoint sets
  containing exactly the expected provider identifiers.
- All 8 built-in allowed providers pass validation without error (unchanged).
- An uncertified custom OIDC provider (no ``mfa_enforced: True``) is rejected.
- A custom OIDC provider with ``mfa_enforced: True`` is accepted.
- An empty ``OAUTH_PROVIDERS`` list passes without error.
- ``SyntekAuthConfig.ready()`` does not raise for MFA-gated providers.

Red phase: importing ``MFA_GATED_PROVIDERS`` and ``is_mfa_gated_provider`` fails
with ``ImportError`` because ``backends/allowlist.py`` still exports
``BLOCKED_PROVIDERS`` and does not yet export these new symbols.  Every test in
this file therefore fails at collection time in the red phase.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from syntek_auth.backends.allowlist import (
    BUILTIN_ALLOWED_PROVIDERS,
    MFA_GATED_PROVIDERS,
    is_mfa_gated_provider,
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
# AC: MFA-gated providers pass startup validation (no longer raise)
# ---------------------------------------------------------------------------


class TestMfaGatedProviders:
    """Every provider in MFA_GATED_PROVIDERS must pass startup validation.

    These providers are allowed through ``AppConfig.ready()`` — they are gated
    at the OAuth callback layer (``PendingOAuthSession`` flow) not at startup.
    """

    @pytest.mark.parametrize("provider_id", sorted(MFA_GATED_PROVIDERS))
    def test_mfa_gated_provider_does_not_raise(self, provider_id: str) -> None:
        """Configuring any MFA-gated provider must NOT raise at startup."""
        syntek_auth = settings_with_providers(single_provider(provider_id))
        # Must not raise — the gating happens at oidcCallback, not at startup.
        validate_oauth_providers(syntek_auth)

    def test_google_is_mfa_gated_does_not_raise(self) -> None:
        """Google is MFA-gated — must pass startup validation."""
        syntek_auth = settings_with_providers(single_provider("google"))
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_facebook_is_mfa_gated_does_not_raise(self) -> None:
        """Facebook is MFA-gated — must pass startup validation."""
        syntek_auth = settings_with_providers(single_provider("facebook"))
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_discord_is_mfa_gated_does_not_raise(self) -> None:
        """Discord is MFA-gated — must pass startup validation."""
        syntek_auth = settings_with_providers(single_provider("discord"))
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_twitter_is_mfa_gated_does_not_raise(self) -> None:
        """Twitter / X is MFA-gated — must pass startup validation."""
        syntek_auth = settings_with_providers(single_provider("twitter"))
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_mfa_gated_provider_mixed_case_normalised(self) -> None:
        """Provider identifiers are normalised to lowercase — 'Google' passes."""
        syntek_auth = settings_with_providers(single_provider("Google"))
        validate_oauth_providers(syntek_auth)  # must not raise
        assert is_mfa_gated_provider("google") is True

    def test_mfa_gated_and_builtin_allowed_providers_can_coexist_in_config(
        self,
    ) -> None:
        """A list containing a MFA-gated provider alongside an allowed provider
        must pass — both types are permitted at startup."""
        syntek_auth = settings_with_providers(
            single_provider("google"),
            single_provider("github"),
        )
        validate_oauth_providers(syntek_auth)  # must not raise

    def test_is_mfa_gated_provider_returns_true_for_gated(self) -> None:
        """is_mfa_gated_provider must return True for every gated provider."""
        assert is_mfa_gated_provider("google") is True
        assert is_mfa_gated_provider("facebook") is True
        assert is_mfa_gated_provider("instagram") is True
        assert is_mfa_gated_provider("linkedin") is True
        assert is_mfa_gated_provider("twitter") is True
        assert is_mfa_gated_provider("x") is True
        assert is_mfa_gated_provider("apple") is True
        assert is_mfa_gated_provider("discord") is True
        assert is_mfa_gated_provider("microsoft") is True

    def test_is_mfa_gated_provider_returns_false_for_allowed(self) -> None:
        """is_mfa_gated_provider must return False for built-in allowed providers."""
        assert is_mfa_gated_provider("github") is False
        assert is_mfa_gated_provider("okta") is False
        assert is_mfa_gated_provider("defguard") is False
        assert is_mfa_gated_provider("authentik") is False

    def test_is_mfa_gated_provider_returns_false_for_unknown(self) -> None:
        """is_mfa_gated_provider must return False for an unknown identifier."""
        assert is_mfa_gated_provider("unknown-idp") is False
        assert is_mfa_gated_provider("my-corp-sso") is False

    def test_is_mfa_gated_provider_normalises_case(self) -> None:
        """is_mfa_gated_provider is case-insensitive."""
        assert is_mfa_gated_provider("Google") is True
        assert is_mfa_gated_provider("FACEBOOK") is True
        assert is_mfa_gated_provider("Twitter") is True

    def test_mfa_gated_providers_contains_expected_set(self) -> None:
        """MFA_GATED_PROVIDERS must be exactly the nine expected identifiers."""
        assert (
            frozenset(
                {
                    "google",
                    "facebook",
                    "instagram",
                    "linkedin",
                    "twitter",
                    "x",
                    "apple",
                    "discord",
                    "microsoft",
                }
            )
            == MFA_GATED_PROVIDERS
        )

    def test_mfa_gated_and_builtin_allowed_sets_are_disjoint(self) -> None:
        """No provider can appear in both MFA_GATED_PROVIDERS and BUILTIN_ALLOWED_PROVIDERS."""
        overlap = MFA_GATED_PROVIDERS & BUILTIN_ALLOWED_PROVIDERS
        assert overlap == frozenset(), (
            f"Providers in both sets would be ambiguous: {overlap!r}"
        )


# ---------------------------------------------------------------------------
# AC: Allowed built-in providers pass validation (unchanged from US076)
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
# AC: Custom / self-hosted OIDC providers (unchanged from US076)
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
# AC: Empty provider list (unchanged from US076)
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

    def test_ready_with_mfa_gated_provider_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must NOT raise when SYNTEK_AUTH contains an MFA-gated provider.

        MFA-gated providers (e.g. Google) are permitted at startup — the gating
        occurs at the OAuth callback layer, not at AppConfig.ready().
        """
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        monkeypatch.setattr(
            django_settings,
            "SYNTEK_AUTH",
            {"OAUTH_PROVIDERS": [{"provider": "google"}]},
            raising=False,
        )

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))
        app_config.ready()  # must NOT raise

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
