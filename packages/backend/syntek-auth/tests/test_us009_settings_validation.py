"""US009 — Red phase: settings validation tests for ``syntek-auth``.

Tests cover the ``validate_settings`` function and ``SyntekAuthConfig.ready()``
integration for all ``SYNTEK_AUTH`` configuration keys.

Acceptance criteria under test
-------------------------------
- All required keys are validated; missing or invalid values raise
  ``ImproperlyConfigured`` with a descriptive message.
- ``LOGIN_FIELD='username'`` with ``REQUIRE_USERNAME=False`` is rejected.
- ``LOGIN_FIELD='phone'`` with ``REQUIRE_PHONE=False`` is rejected.
- ``MFA_METHODS=[]`` is rejected.
- An unrecognised MFA method identifier is rejected.
- ``LOCKOUT_STRATEGY`` must be ``'fixed'`` or ``'progressive'``.
- Negative integer values for duration/threshold settings are rejected.
- ``SyntekAuthConfig.ready()`` raises ``ImproperlyConfigured`` for invalid
  settings and does not raise for a valid minimal configuration.

All tests **fail** in the red phase because ``validate_settings`` raises
``NotImplementedError`` (the stub) rather than performing any validation.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from syntek_auth.conf import validate_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def minimal_valid_settings(**overrides: object) -> dict:  # type: ignore[type-arg]
    """Return a minimal ``SYNTEK_AUTH`` dict that passes all validation rules.

    Any supplied keyword arguments override the defaults, allowing individual
    tests to introduce a single invalid value.
    """
    base: dict = {  # type: ignore[type-arg]
        "LOGIN_FIELD": "email",
        "REQUIRE_EMAIL": True,
        "REQUIRE_USERNAME": False,
        "REQUIRE_PHONE": False,
        "USERNAME_MIN_LENGTH": 3,
        "USERNAME_MAX_LENGTH": 30,
        "USERNAME_ALLOWED_CHARS": r"^[a-zA-Z0-9_.\-]+$",
        "USERNAME_RESERVED": ["admin", "root"],
        "USERNAME_CASE_SENSITIVE": False,
        "PASSWORD_MIN_LENGTH": 12,
        "PASSWORD_MAX_LENGTH": 128,
        "PASSWORD_REQUIRE_UPPERCASE": True,
        "PASSWORD_REQUIRE_LOWERCASE": True,
        "PASSWORD_REQUIRE_DIGITS": True,
        "PASSWORD_REQUIRE_SYMBOLS": False,
        "PASSWORD_HISTORY": 5,
        "PASSWORD_EXPIRY_DAYS": 0,
        "PASSWORD_BREACH_CHECK": True,
        "MFA_REQUIRED": False,
        "MFA_METHODS": ["totp"],
        "MFA_BACKUP_CODES_COUNT": 12,
        "ACCESS_TOKEN_LIFETIME": 900,
        "REFRESH_TOKEN_LIFETIME": 604800,
        "ROTATE_REFRESH_TOKENS": True,
        "LOCKOUT_THRESHOLD": 5,
        "LOCKOUT_DURATION": 900,
        "LOCKOUT_STRATEGY": "progressive",
        "REGISTRATION_ENABLED": True,
        "EMAIL_VERIFICATION_REQUIRED": True,
        "PHONE_VERIFICATION_REQUIRED": False,
        "OIDC_PROVIDERS": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# AC: Minimal valid configuration passes without raising
# ---------------------------------------------------------------------------


class TestValidSettingsPass:
    """A fully specified, valid ``SYNTEK_AUTH`` dict must pass without error."""

    def test_minimal_valid_settings_does_not_raise(self) -> None:
        """Minimal valid settings must not raise any exception."""
        validate_settings(minimal_valid_settings())

    def test_mfa_methods_with_all_valid_values_does_not_raise(self) -> None:
        """All four recognised MFA methods are valid."""
        validate_settings(
            minimal_valid_settings(MFA_METHODS=["totp", "sms", "email_otp", "passkey"])
        )

    def test_login_field_email_or_username_with_require_username_true(self) -> None:
        """``LOGIN_FIELD='email_or_username'`` is valid when ``REQUIRE_USERNAME=True``."""
        validate_settings(
            minimal_valid_settings(
                LOGIN_FIELD="email_or_username",
                REQUIRE_USERNAME=True,
            )
        )

    def test_login_field_phone_with_require_phone_required(self) -> None:
        """``LOGIN_FIELD='phone'`` is valid when ``REQUIRE_PHONE='required'``."""
        validate_settings(
            minimal_valid_settings(
                LOGIN_FIELD="phone",
                REQUIRE_PHONE="required",
            )
        )

    def test_lockout_strategy_fixed_does_not_raise(self) -> None:
        """``LOCKOUT_STRATEGY='fixed'`` is a valid value."""
        validate_settings(minimal_valid_settings(LOCKOUT_STRATEGY="fixed"))

    def test_password_expiry_days_nonzero_does_not_raise(self) -> None:
        """A non-zero ``PASSWORD_EXPIRY_DAYS`` is valid."""
        validate_settings(minimal_valid_settings(PASSWORD_EXPIRY_DAYS=90))


# ---------------------------------------------------------------------------
# AC: LOGIN_FIELD / REQUIRE_USERNAME conflict
# ---------------------------------------------------------------------------


class TestLoginFieldUsernameConflict:
    """``LOGIN_FIELD='username'`` requires ``REQUIRE_USERNAME=True``."""

    def test_login_field_username_require_username_false_raises(self) -> None:
        """LOGIN_FIELD='username' with REQUIRE_USERNAME=False must raise."""
        settings = minimal_valid_settings(
            LOGIN_FIELD="username",
            REQUIRE_USERNAME=False,
        )

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert "LOGIN_FIELD" in msg or "REQUIRE_USERNAME" in msg, (
            f"Error must reference LOGIN_FIELD or REQUIRE_USERNAME; got: {msg!r}"
        )

    def test_login_field_email_or_username_require_username_false_raises(self) -> None:
        """LOGIN_FIELD='email_or_username' with REQUIRE_USERNAME=False must raise."""
        settings = minimal_valid_settings(
            LOGIN_FIELD="email_or_username",
            REQUIRE_USERNAME=False,
        )

        with pytest.raises(ImproperlyConfigured):
            validate_settings(settings)

    def test_login_field_username_require_username_true_does_not_raise(self) -> None:
        """LOGIN_FIELD='username' with REQUIRE_USERNAME=True is valid."""
        validate_settings(
            minimal_valid_settings(
                LOGIN_FIELD="username",
                REQUIRE_USERNAME=True,
            )
        )


# ---------------------------------------------------------------------------
# AC: LOGIN_FIELD / REQUIRE_PHONE conflict
# ---------------------------------------------------------------------------


class TestLoginFieldPhoneConflict:
    """``LOGIN_FIELD='phone'`` requires ``REQUIRE_PHONE`` to be set."""

    def test_login_field_phone_require_phone_false_raises(self) -> None:
        """LOGIN_FIELD='phone' with REQUIRE_PHONE=False must raise."""
        settings = minimal_valid_settings(
            LOGIN_FIELD="phone",
            REQUIRE_PHONE=False,
        )

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert "REQUIRE_PHONE" in msg or "LOGIN_FIELD" in msg, (
            f"Error must reference REQUIRE_PHONE or LOGIN_FIELD; got: {msg!r}"
        )

    def test_login_field_email_or_phone_require_phone_false_raises(self) -> None:
        """LOGIN_FIELD='email_or_phone' with REQUIRE_PHONE=False must raise."""
        settings = minimal_valid_settings(
            LOGIN_FIELD="email_or_phone",
            REQUIRE_PHONE=False,
        )

        with pytest.raises(ImproperlyConfigured):
            validate_settings(settings)


# ---------------------------------------------------------------------------
# AC: MFA_METHODS must not be empty
# ---------------------------------------------------------------------------


class TestMfaMethods:
    """``MFA_METHODS`` must contain at least one valid method."""

    def test_mfa_methods_empty_list_raises(self) -> None:
        """MFA_METHODS=[] must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(MFA_METHODS=[])

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert "MFA_METHODS" in msg, (
            f"Error message must reference MFA_METHODS; got: {msg!r}"
        )

    def test_mfa_methods_unrecognised_value_raises(self) -> None:
        """An unrecognised MFA method identifier must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(MFA_METHODS=["totp", "carrier_pigeon"])

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert "carrier_pigeon" in msg or "MFA_METHODS" in msg, (
            f"Error must name the invalid method or reference MFA_METHODS; got: {msg!r}"
        )

    def test_mfa_methods_not_a_list_raises(self) -> None:
        """MFA_METHODS must be a list — a string must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(MFA_METHODS="totp")

        with pytest.raises(ImproperlyConfigured):
            validate_settings(settings)


# ---------------------------------------------------------------------------
# AC: LOCKOUT_STRATEGY must be 'fixed' or 'progressive'
# ---------------------------------------------------------------------------


class TestLockoutStrategy:
    """LOCKOUT_STRATEGY must be one of the two valid values."""

    def test_lockout_strategy_invalid_value_raises(self) -> None:
        """An invalid LOCKOUT_STRATEGY must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(LOCKOUT_STRATEGY="exponential")

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert "LOCKOUT_STRATEGY" in msg, (
            f"Error must reference LOCKOUT_STRATEGY; got: {msg!r}"
        )

    def test_lockout_strategy_empty_string_raises(self) -> None:
        """An empty string for LOCKOUT_STRATEGY must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(LOCKOUT_STRATEGY="")

        with pytest.raises(ImproperlyConfigured):
            validate_settings(settings)


# ---------------------------------------------------------------------------
# AC: Negative integer settings are rejected
# ---------------------------------------------------------------------------


class TestNegativeIntegerSettings:
    """Integer settings that must be non-negative are validated."""

    @pytest.mark.parametrize(
        "key",
        [
            "PASSWORD_MIN_LENGTH",
            "PASSWORD_MAX_LENGTH",
            "PASSWORD_HISTORY",
            "PASSWORD_EXPIRY_DAYS",
            "MFA_BACKUP_CODES_COUNT",
            "ACCESS_TOKEN_LIFETIME",
            "REFRESH_TOKEN_LIFETIME",
            "LOCKOUT_THRESHOLD",
            "LOCKOUT_DURATION",
            "USERNAME_MIN_LENGTH",
            "USERNAME_MAX_LENGTH",
        ],
    )
    def test_negative_integer_raises(self, key: str) -> None:
        """A negative integer for any numeric setting must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(**{key: -1})

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert key in msg, (
            f"Error must reference the offending key '{key}'; got: {msg!r}"
        )


# ---------------------------------------------------------------------------
# AC: Wrong type for boolean settings
# ---------------------------------------------------------------------------


class TestBooleanTypeValidation:
    """Boolean settings must be Python bools, not truthy/falsy non-bools."""

    @pytest.mark.parametrize(
        "key",
        [
            "REQUIRE_EMAIL",
            "REQUIRE_USERNAME",
            "PASSWORD_REQUIRE_UPPERCASE",
            "PASSWORD_REQUIRE_LOWERCASE",
            "PASSWORD_REQUIRE_DIGITS",
            "PASSWORD_REQUIRE_SYMBOLS",
            "PASSWORD_BREACH_CHECK",
            "MFA_REQUIRED",
            "ROTATE_REFRESH_TOKENS",
            "REGISTRATION_ENABLED",
            "EMAIL_VERIFICATION_REQUIRED",
            "USERNAME_CASE_SENSITIVE",
        ],
    )
    def test_non_bool_value_raises(self, key: str) -> None:
        """A non-bool value for a bool setting must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(**{key: 1})  # int 1, not True

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert key in msg, (
            f"Error must reference the offending key '{key}'; got: {msg!r}"
        )


# ---------------------------------------------------------------------------
# AC: Invalid LOGIN_FIELD value
# ---------------------------------------------------------------------------


class TestInvalidLoginField:
    """LOGIN_FIELD must be one of the five recognised values."""

    def test_unrecognised_login_field_raises(self) -> None:
        """An unrecognised LOGIN_FIELD value must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(LOGIN_FIELD="telegram")

        with pytest.raises(ImproperlyConfigured) as exc_info:
            validate_settings(settings)

        msg = str(exc_info.value)
        assert "LOGIN_FIELD" in msg, f"Error must reference LOGIN_FIELD; got: {msg!r}"

    def test_empty_string_login_field_raises(self) -> None:
        """An empty string for LOGIN_FIELD must raise ImproperlyConfigured."""
        settings = minimal_valid_settings(LOGIN_FIELD="")

        with pytest.raises(ImproperlyConfigured):
            validate_settings(settings)


# ---------------------------------------------------------------------------
# AC: SyntekAuthConfig.ready() calls validate_settings
# ---------------------------------------------------------------------------


class TestSyntekAuthConfigReadyCallsValidation:
    """SyntekAuthConfig.ready() must invoke validate_settings for non-empty SYNTEK_AUTH."""

    def test_ready_with_invalid_mfa_methods_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must raise ImproperlyConfigured when MFA_METHODS is empty."""
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        monkeypatch.setattr(
            django_settings,
            "SYNTEK_AUTH",
            minimal_valid_settings(MFA_METHODS=[]),
            raising=False,
        )

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))

        with pytest.raises(ImproperlyConfigured):
            app_config.ready()

    def test_ready_with_invalid_login_field_username_conflict_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must raise ImproperlyConfigured for the LOGIN_FIELD/REQUIRE_USERNAME
        conflict."""
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        monkeypatch.setattr(
            django_settings,
            "SYNTEK_AUTH",
            minimal_valid_settings(LOGIN_FIELD="username", REQUIRE_USERNAME=False),
            raising=False,
        )

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))

        with pytest.raises(ImproperlyConfigured):
            app_config.ready()

    def test_ready_with_valid_settings_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must not raise when SYNTEK_AUTH is fully valid."""
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        monkeypatch.setattr(
            django_settings,
            "SYNTEK_AUTH",
            minimal_valid_settings(),
            raising=False,
        )

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))
        app_config.ready()  # must not raise

    def test_ready_with_no_syntek_auth_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ready() must not raise when SYNTEK_AUTH is absent from settings."""
        from django.conf import settings as django_settings
        from syntek_auth.apps import SyntekAuthConfig

        if hasattr(django_settings, "SYNTEK_AUTH"):
            monkeypatch.delattr(django_settings, "SYNTEK_AUTH")

        app_config = SyntekAuthConfig("syntek_auth", __import__("syntek_auth"))
        app_config.ready()  # must not raise
