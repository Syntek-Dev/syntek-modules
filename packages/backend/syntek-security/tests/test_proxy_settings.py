"""US076 — Red phase: proxy trust settings tests for ``syntek-security``.

Tests cover:
- ``apply_proxy_settings()`` sets ``SECURE_PROXY_SSL_HEADER`` to the correct
  tuple ``("HTTP_X_FORWARDED_PROTO", "https")``.
- ``apply_proxy_settings()`` sets ``USE_X_FORWARDED_HOST = True``.
- ``apply_proxy_settings()`` sets ``SECURE_SSL_REDIRECT = True``.
- Settings already set by the consuming project are not overridden.
- ``SyntekSecurityConfig.ready()`` calls ``apply_proxy_settings()``.

All tests **fail** in the red phase because both ``apply_proxy_settings``
and ``SyntekSecurityConfig.ready()`` raise ``NotImplementedError``.

Run with: ``syntek-dev test --python --python-package syntek-security``
"""

from __future__ import annotations

import pytest
from django.conf import settings as django_settings

# ---------------------------------------------------------------------------
# AC: apply_proxy_settings injects the three required settings
# ---------------------------------------------------------------------------


class TestApplyProxySettings:
    """apply_proxy_settings must configure the three proxy-trust settings."""

    def test_sets_secure_proxy_ssl_header(self) -> None:
        """SECURE_PROXY_SSL_HEADER must be set to the canonical Syntek value."""
        from syntek_security.proxy_settings import (
            PROXY_SSL_HEADER,
            apply_proxy_settings,
        )

        apply_proxy_settings()

        assert hasattr(django_settings, "SECURE_PROXY_SSL_HEADER"), (
            "apply_proxy_settings must set SECURE_PROXY_SSL_HEADER on django.conf.settings"
        )
        assert django_settings.SECURE_PROXY_SSL_HEADER == PROXY_SSL_HEADER, (
            f"SECURE_PROXY_SSL_HEADER must equal {PROXY_SSL_HEADER!r}; "
            f"got {django_settings.SECURE_PROXY_SSL_HEADER!r}"
        )

    def test_secure_proxy_ssl_header_value_is_correct_tuple(self) -> None:
        """The SECURE_PROXY_SSL_HEADER value must be exactly
        ('HTTP_X_FORWARDED_PROTO', 'https')."""
        from syntek_security.proxy_settings import apply_proxy_settings

        apply_proxy_settings()

        expected = ("HTTP_X_FORWARDED_PROTO", "https")
        assert expected == django_settings.SECURE_PROXY_SSL_HEADER, (
            f"Expected {expected!r}, got {django_settings.SECURE_PROXY_SSL_HEADER!r}"
        )

    def test_sets_use_x_forwarded_host_true(self) -> None:
        """USE_X_FORWARDED_HOST must be set to True."""
        from syntek_security.proxy_settings import apply_proxy_settings

        apply_proxy_settings()

        assert hasattr(django_settings, "USE_X_FORWARDED_HOST"), (
            "apply_proxy_settings must set USE_X_FORWARDED_HOST"
        )
        assert django_settings.USE_X_FORWARDED_HOST is True, (
            f"USE_X_FORWARDED_HOST must be True; got {django_settings.USE_X_FORWARDED_HOST!r}"
        )

    def test_sets_secure_ssl_redirect_true(self) -> None:
        """SECURE_SSL_REDIRECT must be set to True."""
        from syntek_security.proxy_settings import apply_proxy_settings

        apply_proxy_settings()

        assert hasattr(django_settings, "SECURE_SSL_REDIRECT"), (
            "apply_proxy_settings must set SECURE_SSL_REDIRECT"
        )
        assert django_settings.SECURE_SSL_REDIRECT is True, (
            f"SECURE_SSL_REDIRECT must be True; got {django_settings.SECURE_SSL_REDIRECT!r}"
        )

    def test_all_three_settings_applied_in_single_call(self) -> None:
        """All three settings must be applied by a single call to apply_proxy_settings."""
        from syntek_security.proxy_settings import apply_proxy_settings

        apply_proxy_settings()

        assert hasattr(django_settings, "SECURE_PROXY_SSL_HEADER")
        assert hasattr(django_settings, "USE_X_FORWARDED_HOST")
        assert hasattr(django_settings, "SECURE_SSL_REDIRECT")

    # -------------------------------------------------------------------------
    # AC: Existing project settings are not overridden
    # -------------------------------------------------------------------------

    def test_does_not_override_existing_secure_proxy_ssl_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the project has already set SECURE_PROXY_SSL_HEADER, it must not
        be overridden by apply_proxy_settings."""
        from syntek_security.proxy_settings import apply_proxy_settings

        custom_value = ("HTTP_X_CUSTOM_HEADER", "yes")
        monkeypatch.setattr(django_settings, "SECURE_PROXY_SSL_HEADER", custom_value)

        apply_proxy_settings()

        assert custom_value == django_settings.SECURE_PROXY_SSL_HEADER, (
            "apply_proxy_settings must not override an existing SECURE_PROXY_SSL_HEADER; "
            f"expected {custom_value!r}, got {django_settings.SECURE_PROXY_SSL_HEADER!r}"
        )

    def test_does_not_override_existing_use_x_forwarded_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the project has already set USE_X_FORWARDED_HOST, it must not
        be overridden."""
        from syntek_security.proxy_settings import apply_proxy_settings

        monkeypatch.setattr(django_settings, "USE_X_FORWARDED_HOST", False)

        apply_proxy_settings()

        assert django_settings.USE_X_FORWARDED_HOST is False, (
            "apply_proxy_settings must not override an existing USE_X_FORWARDED_HOST=False"
        )

    def test_does_not_override_existing_secure_ssl_redirect(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the project has already set SECURE_SSL_REDIRECT, it must not
        be overridden."""
        from syntek_security.proxy_settings import apply_proxy_settings

        monkeypatch.setattr(django_settings, "SECURE_SSL_REDIRECT", False)

        apply_proxy_settings()

        assert django_settings.SECURE_SSL_REDIRECT is False, (
            "apply_proxy_settings must not override an existing SECURE_SSL_REDIRECT=False"
        )

    def test_idempotent_second_call_does_not_raise(self) -> None:
        """Calling apply_proxy_settings twice must not raise or produce incorrect
        settings values."""
        from syntek_security.proxy_settings import (
            PROXY_SSL_HEADER,
            apply_proxy_settings,
        )

        apply_proxy_settings()
        apply_proxy_settings()

        assert django_settings.SECURE_PROXY_SSL_HEADER == PROXY_SSL_HEADER
        assert django_settings.USE_X_FORWARDED_HOST is True
        assert django_settings.SECURE_SSL_REDIRECT is True


# ---------------------------------------------------------------------------
# AC: SyntekSecurityConfig.ready() calls apply_proxy_settings
# ---------------------------------------------------------------------------


class TestSyntekSecurityConfigReady:
    """SyntekSecurityConfig.ready() must call apply_proxy_settings on startup."""

    def test_ready_sets_secure_proxy_ssl_header(self) -> None:
        """After ready() is called, SECURE_PROXY_SSL_HEADER must be set."""
        from syntek_security.apps import SyntekSecurityConfig
        from syntek_security.proxy_settings import PROXY_SSL_HEADER

        # Remove any value that may have been set by an earlier test.
        if hasattr(django_settings, "SECURE_PROXY_SSL_HEADER"):
            delattr(django_settings, "SECURE_PROXY_SSL_HEADER")

        app_config = SyntekSecurityConfig(
            "syntek_security", __import__("syntek_security")
        )
        app_config.ready()

        assert django_settings.SECURE_PROXY_SSL_HEADER == PROXY_SSL_HEADER

    def test_ready_sets_use_x_forwarded_host(self) -> None:
        """After ready() is called, USE_X_FORWARDED_HOST must be True."""
        from syntek_security.apps import SyntekSecurityConfig

        if hasattr(django_settings, "USE_X_FORWARDED_HOST"):
            delattr(django_settings, "USE_X_FORWARDED_HOST")

        app_config = SyntekSecurityConfig(
            "syntek_security", __import__("syntek_security")
        )
        app_config.ready()

        assert django_settings.USE_X_FORWARDED_HOST is True

    def test_ready_sets_secure_ssl_redirect(self) -> None:
        """After ready() is called, SECURE_SSL_REDIRECT must be True."""
        from syntek_security.apps import SyntekSecurityConfig

        if hasattr(django_settings, "SECURE_SSL_REDIRECT"):
            delattr(django_settings, "SECURE_SSL_REDIRECT")

        app_config = SyntekSecurityConfig(
            "syntek_security", __import__("syntek_security")
        )
        app_config.ready()

        assert django_settings.SECURE_SSL_REDIRECT is True
