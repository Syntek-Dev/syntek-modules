"""US009 — Auth backend tests for ``syntek-auth``.

Tests cover the uncovered branches in ``syntek_auth.backends.auth_backend``:

- ``resolve_login_field`` with ``LOGIN_FIELD='username'`` (line 66)
- ``resolve_login_field`` with ``LOGIN_FIELD='email_or_username'`` via email path
- ``resolve_login_field`` with ``LOGIN_FIELD='email_or_phone'``
- ``resolve_login_field`` with an unrecognised ``login_field`` returns None
- ``SyntekAuthBackend.authenticate`` — success, missing credentials, inactive user,
  wrong password
- ``SyntekAuthBackend.get_user`` — found and not-found cases

All tests that touch the database are decorated with ``@pytest.mark.django_db``.
Users are created via ``UserFactory`` to ensure HMAC lookup tokens are computed
correctly.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

import pytest
from syntek_auth.backends.auth_backend import SyntekAuthBackend, resolve_login_field

# ---------------------------------------------------------------------------
# resolve_login_field — username
# ---------------------------------------------------------------------------


class TestResolveLoginFieldUsername:
    """``resolve_login_field`` with ``LOGIN_FIELD='username'`` queries by username token."""

    @pytest.mark.django_db
    def test_username_lookup_finds_user(self) -> None:
        """A matching username must return the corresponding user."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(username="alice_username")
        result = resolve_login_field("alice_username", "username")
        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_username_lookup_returns_none_when_not_found(self) -> None:
        """A username with no matching account must return None."""
        result = resolve_login_field("nonexistent_user", "username")
        assert result is None

    @pytest.mark.django_db
    def test_username_lookup_is_case_insensitive_by_default(
        self, settings: object
    ) -> None:
        """With ``USERNAME_CASE_SENSITIVE=False`` (default), lookup is case-insensitive."""
        import django.conf

        cfg = dict(getattr(django.conf.settings, "SYNTEK_AUTH", {}))
        cfg["USERNAME_CASE_SENSITIVE"] = False

        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(username="CasedUser")

        # Patch settings so resolve_login_field sees case_sensitive=False.
        with __import__("unittest.mock", fromlist=["patch"]).patch.object(
            django.conf.settings, "SYNTEK_AUTH", cfg
        ):
            result = resolve_login_field("caseduser", "username")

        assert result is not None
        assert result.pk == user.pk


# ---------------------------------------------------------------------------
# resolve_login_field — email_or_username (email path)
# ---------------------------------------------------------------------------


class TestResolveLoginFieldEmailOrUsername:
    """``resolve_login_field`` with ``LOGIN_FIELD='email_or_username'`` tries email first."""

    @pytest.mark.django_db
    def test_finds_user_by_email_when_email_supplied(self) -> None:
        """When the identifier looks like an email, the user is found via email token."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(email="charlie@example.com")
        result = resolve_login_field("charlie@example.com", "email_or_username")
        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_falls_back_to_username_when_email_not_found(self) -> None:
        """When no email match exists, the username fallback must find the user."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(username="charlie_uname")
        result = resolve_login_field("charlie_uname", "email_or_username")
        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_returns_none_when_neither_matches(self) -> None:
        """When neither email nor username matches, None must be returned."""
        result = resolve_login_field("ghost@nowhere.example", "email_or_username")
        assert result is None


# ---------------------------------------------------------------------------
# resolve_login_field — email_or_phone
# ---------------------------------------------------------------------------


class TestResolveLoginFieldEmailOrPhone:
    """``resolve_login_field`` with ``LOGIN_FIELD='email_or_phone'`` tries email then phone."""

    @pytest.mark.django_db
    def test_finds_user_by_email(self) -> None:
        """An email address must match via the email token."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(email="dave@example.com")
        result = resolve_login_field("dave@example.com", "email_or_phone")
        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_finds_user_by_phone_when_email_not_found(self) -> None:
        """A phone number not matching any email must fall back to the phone token."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(phone="+447700900456")
        result = resolve_login_field("+447700900456", "email_or_phone")
        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_returns_none_when_neither_matches(self) -> None:
        """When neither email nor phone matches, None must be returned."""
        result = resolve_login_field("+447700000000", "email_or_phone")
        assert result is None


# ---------------------------------------------------------------------------
# resolve_login_field — unrecognised login_field
# ---------------------------------------------------------------------------


class TestResolveLoginFieldUnknown:
    """``resolve_login_field`` with an unrecognised ``login_field`` returns None."""

    @pytest.mark.django_db
    def test_unknown_field_returns_none(self) -> None:
        """An unrecognised ``login_field`` value must return None without raising."""
        result = resolve_login_field("anything", "magic_token")
        assert result is None


# ---------------------------------------------------------------------------
# SyntekAuthBackend.authenticate
# ---------------------------------------------------------------------------


class TestSyntekAuthBackendAuthenticate:
    """Tests for ``SyntekAuthBackend.authenticate``."""

    @pytest.mark.django_db
    def test_authenticate_success(self, settings: object) -> None:
        """Valid credentials must return the authenticated user."""
        import django.conf

        cfg = dict(getattr(django.conf.settings, "SYNTEK_AUTH", {}))
        cfg["LOGIN_FIELD"] = "email"

        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(email="eve@example.com", password="SecurePass99!")

        backend = SyntekAuthBackend()
        with __import__("unittest.mock", fromlist=["patch"]).patch.object(
            django.conf.settings, "SYNTEK_AUTH", cfg
        ):
            result = backend.authenticate(
                None, username="eve@example.com", password="SecurePass99!"
            )

        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_authenticate_missing_username_returns_none(self) -> None:
        """Omitting ``username`` must return None without raising."""
        backend = SyntekAuthBackend()
        result = backend.authenticate(None, username=None, password="password")
        assert result is None

    @pytest.mark.django_db
    def test_authenticate_missing_password_returns_none(self) -> None:
        """Omitting ``password`` must return None without raising."""
        backend = SyntekAuthBackend()
        result = backend.authenticate(None, username="user@example.com", password=None)
        assert result is None

    @pytest.mark.django_db
    def test_authenticate_empty_username_returns_none(self) -> None:
        """An empty string ``username`` must return None."""
        backend = SyntekAuthBackend()
        result = backend.authenticate(None, username="", password="password")
        assert result is None

    @pytest.mark.django_db
    def test_authenticate_wrong_password_returns_none(self, settings: object) -> None:
        """An incorrect password must return None."""
        import django.conf

        cfg = dict(getattr(django.conf.settings, "SYNTEK_AUTH", {}))
        cfg["LOGIN_FIELD"] = "email"

        from syntek_auth.factories.user import UserFactory

        UserFactory.create(email="frank@example.com", password="RealPassword99!")

        backend = SyntekAuthBackend()
        with __import__("unittest.mock", fromlist=["patch"]).patch.object(
            django.conf.settings, "SYNTEK_AUTH", cfg
        ):
            result = backend.authenticate(
                None, username="frank@example.com", password="WrongPassword!"
            )

        assert result is None

    @pytest.mark.django_db
    def test_authenticate_inactive_user_returns_none(self, settings: object) -> None:
        """An inactive user must not be authenticated even with correct credentials."""
        import django.conf

        cfg = dict(getattr(django.conf.settings, "SYNTEK_AUTH", {}))
        cfg["LOGIN_FIELD"] = "email"

        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create(email="grace@example.com", password="Pass99!")
        user.is_active = False
        user.save(update_fields=["is_active"])

        backend = SyntekAuthBackend()
        with __import__("unittest.mock", fromlist=["patch"]).patch.object(
            django.conf.settings, "SYNTEK_AUTH", cfg
        ):
            result = backend.authenticate(
                None, username="grace@example.com", password="Pass99!"
            )

        assert result is None

    @pytest.mark.django_db
    def test_authenticate_nonexistent_user_returns_none(self, settings: object) -> None:
        """An email with no matching user must return None."""
        import django.conf

        cfg = dict(getattr(django.conf.settings, "SYNTEK_AUTH", {}))
        cfg["LOGIN_FIELD"] = "email"

        backend = SyntekAuthBackend()
        with __import__("unittest.mock", fromlist=["patch"]).patch.object(
            django.conf.settings, "SYNTEK_AUTH", cfg
        ):
            result = backend.authenticate(
                None, username="nobody@example.com", password="password"
            )

        assert result is None


# ---------------------------------------------------------------------------
# SyntekAuthBackend.get_user
# ---------------------------------------------------------------------------


class TestSyntekAuthBackendGetUser:
    """Tests for ``SyntekAuthBackend.get_user``."""

    @pytest.mark.django_db
    def test_get_user_returns_user_when_found(self) -> None:
        """``get_user`` must return the user when the primary key exists."""
        from syntek_auth.factories.user import UserFactory

        user = UserFactory.create()
        backend = SyntekAuthBackend()
        result = backend.get_user(user.pk)
        assert result is not None
        assert result.pk == user.pk

    @pytest.mark.django_db
    def test_get_user_returns_none_when_not_found(self) -> None:
        """``get_user`` must return None for a non-existent primary key."""
        backend = SyntekAuthBackend()
        result = backend.get_user(999999999)
        assert result is None
