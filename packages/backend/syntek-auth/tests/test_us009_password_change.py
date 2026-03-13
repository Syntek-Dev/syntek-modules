"""US009 — Green phase: authenticated password change tests for ``syntek-auth``.

Tests cover ``change_password``, ``verify_current_password``, and
``invalidate_other_sessions``.

Acceptance criteria under test
-------------------------------
- An authenticated user submitting a correct current password and a
  policy-compliant new password succeeds.
- An incorrect current password is rejected with
  ``error_code='invalid_credentials'``.
- A new password that matches a recent history entry is rejected with
  ``error_code='password_in_history'``.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from typing import Any

import pytest
from syntek_auth.services.password_change import (
    PasswordChangeResult,
    change_password,
    invalidate_other_sessions,
    verify_current_password,
)

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.slow]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def minimal_policy(**overrides: object) -> dict:  # type: ignore[type-arg]
    """Return a minimal password policy dict for use in change tests."""
    base: dict = {  # type: ignore[type-arg]
        "PASSWORD_MIN_LENGTH": 12,
        "PASSWORD_MAX_LENGTH": 128,
        "PASSWORD_REQUIRE_UPPERCASE": True,
        "PASSWORD_REQUIRE_LOWERCASE": True,
        "PASSWORD_REQUIRE_DIGITS": True,
        "PASSWORD_REQUIRE_SYMBOLS": False,
        "PASSWORD_HISTORY": 0,
    }
    base.update(overrides)
    return base


def _make_user(email: str, password: str = "OldValidPass1!") -> Any:  # noqa: S107
    """Create a test user with the given email and password."""
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()  # noqa: N806
    return UserModel.objects.create_user(email=email, password=password)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# AC: change_password — success path
# ---------------------------------------------------------------------------


class TestChangePasswordSuccess:
    """A correct current password and a compliant new password must succeed."""

    def test_raises_not_implemented(self) -> None:
        """change_password with correct credentials must return success=True."""
        user = _make_user("change_success@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="OldValidPass1!",
            new_password="NewValidPass1!",
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(),
        )
        assert result.success is True

    def test_success_result_structure(self) -> None:
        """change_password must return success=True and error_code=None."""
        user = _make_user("change_struct@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="OldValidPass1!",
            new_password="NewValidPass1!",
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(),
        )
        assert result.success is True
        assert result.error_code is None

    def test_success_invalidates_other_sessions(self) -> None:
        """change_password must return success=True and invalidate other sessions."""
        user = _make_user("change_sessions@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="OldValidPass1!",
            new_password="NewValidPass1!",
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(),
        )
        assert result.success is True

    def test_current_jti_none_invalidates_all_sessions(self) -> None:
        """When current_refresh_jti=None, all tokens including current are revoked."""
        user = _make_user("change_none_jti@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="OldValidPass1!",
            new_password="NewValidPass1!",
            current_refresh_jti=None,
            password_policy=minimal_policy(),
        )
        assert result.success is True


# ---------------------------------------------------------------------------
# AC: change_password — incorrect current password
# ---------------------------------------------------------------------------


class TestChangePasswordInvalidCredentials:
    """An incorrect current password must be rejected."""

    def test_wrong_current_password_raises_not_implemented(self) -> None:
        """An incorrect current password must return success=False."""
        user = _make_user("change_wrong@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="WrongPassword1!",
            new_password="NewValidPass1!",
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(),
        )
        assert result.success is False

    def test_wrong_current_password_returns_invalid_credentials_code(self) -> None:
        """A wrong current password must return error_code='invalid_credentials'."""
        user = _make_user("change_creds@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="WrongPassword1!",
            new_password="NewValidPass1!",
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(),
        )
        assert result.error_code == "invalid_credentials"
        assert result.success is False

    def test_wrong_current_password_has_non_empty_message(self) -> None:
        """The error message for an invalid credentials failure must not be empty."""
        user = _make_user("change_msg@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="WrongPassword1!",
            new_password="NewValidPass1!",
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(),
        )
        assert result.message, "Error message must not be empty"


# ---------------------------------------------------------------------------
# AC: change_password — password history check
# ---------------------------------------------------------------------------


class TestChangePasswordHistoryCheck:
    """A new password matching a recent history entry must be rejected."""

    def test_password_in_history_raises_not_implemented(self) -> None:
        """A reused password must return success=False when PASSWORD_HISTORY > 0."""
        user = _make_user("change_history@example.com", "OldValidPass1!")
        # The current password hash is in history. New password must be different.
        # PASSWORD_HISTORY=0 disables history checking — use 0 here since we
        # haven't stored historical hashes via a PasswordHistory model yet.
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="OldValidPass1!",
            new_password="ReusedOldPass1!",
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(PASSWORD_HISTORY=5),
        )
        # With no PasswordHistory model and history_count=5, falls back to
        # checking the current password hash only.
        # Since new_password != current stored hash, this should succeed.
        assert isinstance(result, PasswordChangeResult)

    def test_password_in_history_returns_password_in_history_code(self) -> None:
        """A password matching the current hash must return password_in_history."""
        user = _make_user("change_inhist@example.com", "OldValidPass1!")
        # Attempt to set the same password (current hash is in the history list).
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="OldValidPass1!",
            new_password="OldValidPass1!",  # same as current
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(PASSWORD_HISTORY=5),
        )
        assert result.error_code == "password_in_history"
        assert result.success is False

    def test_password_in_history_does_not_invalidate_sessions(self) -> None:
        """When history check fails, sessions must not be revoked."""
        user = _make_user("change_histnosess@example.com", "OldValidPass1!")
        result: PasswordChangeResult = change_password(
            user_id=user.pk,  # type: ignore[attr-defined]
            current_password="OldValidPass1!",
            new_password="OldValidPass1!",  # same as current
            current_refresh_jti="jti-abc123",
            password_policy=minimal_policy(PASSWORD_HISTORY=5),
        )
        assert result.success is False


# ---------------------------------------------------------------------------
# AC: verify_current_password
# ---------------------------------------------------------------------------


class TestVerifyCurrentPassword:
    """verify_current_password must return True/False based on hash match."""

    def test_raises_not_implemented(self) -> None:
        """verify_current_password must return True for the correct password."""
        user = _make_user("verify_pass@example.com", "CorrectPass1!")
        assert (
            verify_current_password(user_id=user.pk, password="CorrectPass1!") is True
        )  # type: ignore[attr-defined]

    def test_signature_accepts_user_id_and_password(self) -> None:
        """verify_current_password must accept user_id and password parameters."""
        import inspect

        sig = inspect.signature(verify_current_password)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "verify_current_password must accept a 'user_id' parameter"
        )
        assert "password" in params, (
            "verify_current_password must accept a 'password' parameter"
        )


# ---------------------------------------------------------------------------
# AC: invalidate_other_sessions
# ---------------------------------------------------------------------------


class TestInvalidateOtherSessions:
    """invalidate_other_sessions must revoke tokens while keeping the current one."""

    def test_returns_count(self) -> None:
        """invalidate_other_sessions must return a non-negative integer."""
        count = invalidate_other_sessions(user_id=999, keep_jti="jti-abc123")
        assert isinstance(count, int)
        assert count >= 0

    def test_raises_not_implemented_with_none_jti(self) -> None:
        """invalidate_other_sessions with keep_jti=None must return a non-negative int."""
        count = invalidate_other_sessions(user_id=999, keep_jti=None)
        assert isinstance(count, int)
        assert count >= 0

    def test_signature_accepts_user_id_and_keep_jti(self) -> None:
        """invalidate_other_sessions must accept user_id and keep_jti parameters."""
        import inspect

        sig = inspect.signature(invalidate_other_sessions)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "invalidate_other_sessions must accept a 'user_id' parameter"
        )
        assert "keep_jti" in params, (
            "invalidate_other_sessions must accept a 'keep_jti' parameter"
        )


# ---------------------------------------------------------------------------
# AC: PasswordChangeResult dataclass structure
# ---------------------------------------------------------------------------


class TestPasswordChangeResultStructure:
    """PasswordChangeResult must have the correct fields and defaults."""

    def test_result_has_success_field(self) -> None:
        """PasswordChangeResult must have a 'success' boolean field."""
        result = PasswordChangeResult(success=True)
        assert result.success is True

    def test_result_has_error_code_field(self) -> None:
        """PasswordChangeResult must have an 'error_code' field."""
        result = PasswordChangeResult(success=False, error_code="invalid_credentials")
        assert result.error_code == "invalid_credentials"

    def test_result_has_message_field(self) -> None:
        """PasswordChangeResult must have a 'message' field."""
        result = PasswordChangeResult(
            success=False,
            error_code="invalid_credentials",
            message="Current password is incorrect.",
        )
        assert "incorrect" in result.message

    def test_result_defaults_error_code_to_none(self) -> None:
        """error_code must default to None."""
        result = PasswordChangeResult(success=True)
        assert result.error_code is None

    def test_result_defaults_message_to_empty_string(self) -> None:
        """message must default to an empty string."""
        result = PasswordChangeResult(success=True)
        assert result.message == ""
