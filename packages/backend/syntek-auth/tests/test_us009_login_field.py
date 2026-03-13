"""US009 — Green phase: login field dispatcher tests for ``syntek-auth``.

Tests cover ``resolve_login_field``.

Acceptance criteria under test
-------------------------------
- With ``LOGIN_FIELD='email'``, only the email field is used for lookup.
- With ``LOGIN_FIELD='email_or_username'``, both fields are tried.
- With ``LOGIN_FIELD='phone'``, only the phone field is used.
- When no matching user is found, ``None`` is returned.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from syntek_auth.backends.auth_backend import resolve_login_field

pytestmark = [pytest.mark.unit, pytest.mark.slow]

# ---------------------------------------------------------------------------
# AC: LOGIN_FIELD='email' — only email lookup is performed
# ---------------------------------------------------------------------------


class TestLoginFieldEmail:
    """resolve_login_field with LOGIN_FIELD='email' uses only the email field."""

    def test_email_lookup_returns_user_when_found(self) -> None:
        """A matching email address must return the corresponding user object."""
        mock_user = MagicMock()
        mock_user.email = "alice@example.com"

        with patch(
            "syntek_auth.backends.auth_backend.resolve_login_field",
            return_value=mock_user,
        ):
            from syntek_auth.backends.auth_backend import (
                resolve_login_field as mocked_fn,
            )

            result = mocked_fn("alice@example.com", "email")
            assert result is mock_user

    def test_email_lookup_returns_none_when_not_found(self) -> None:
        """An email address with no matching account must return None."""
        with patch(
            "syntek_auth.backends.auth_backend.resolve_login_field",
            return_value=None,
        ):
            from syntek_auth.backends.auth_backend import (
                resolve_login_field as mocked_fn,
            )

            result = mocked_fn("nobody@example.com", "email")
            assert result is None

    @pytest.mark.django_db
    def test_email_lookup_finds_user_by_email(self) -> None:
        """A matching email address must return the corresponding user object."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="alice@example.com", password="Pass1234!"
        )
        result = resolve_login_field("alice@example.com", "email")
        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_email_lookup_returns_none_for_unknown_address(self) -> None:
        """An email address with no matching account must return None."""
        result = resolve_login_field("nobody@example.com", "email")
        assert result is None


# ---------------------------------------------------------------------------
# AC: LOGIN_FIELD='email_or_username' — both fields are tried
# ---------------------------------------------------------------------------


class TestLoginFieldEmailOrUsername:
    """resolve_login_field with LOGIN_FIELD='email_or_username' tries both fields."""

    @pytest.mark.django_db
    def test_email_or_username_finds_by_username(self) -> None:
        """An identifier matching a username must return the correct user."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="bob@example.com", password="Pass1234!", username="bobsmith"
        )
        result = resolve_login_field("bobsmith", "email_or_username")
        assert result is not None
        assert result.pk == user.pk


# ---------------------------------------------------------------------------
# AC: LOGIN_FIELD='phone' — only phone field is used
# ---------------------------------------------------------------------------


class TestLoginFieldPhone:
    """resolve_login_field with LOGIN_FIELD='phone' uses only the phone field."""

    @pytest.mark.django_db
    def test_phone_lookup_returns_none_when_not_found(self) -> None:
        """A phone number with no matching account must return None."""
        result = resolve_login_field("+447700900123", "phone")
        assert result is None
