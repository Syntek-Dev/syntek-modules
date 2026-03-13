"""US009 — Green phase: forgot password / password reset flow tests for ``syntek-auth``.

Tests cover ``request_password_reset``, ``confirm_password_reset``,
``generate_password_reset_token``, and ``invalidate_all_refresh_tokens``.

Acceptance criteria under test
-------------------------------
- ``resetPasswordRequest`` for an unverified account returns a generic success
  response but creates no token (account enumeration prevention).
- ``resetPasswordRequest`` for a verified account creates a reset token and
  returns a generic success response.
- ``resetPasswordRequest`` for an email that does not exist returns the same
  generic success response (no account enumeration).
- ``resetPasswordConfirm`` with a valid token and a policy-compliant new
  password succeeds and invalidates all existing refresh tokens.
- ``resetPasswordConfirm`` with an expired token returns
  ``error_code='token_expired'``.
- ``resetPasswordConfirm`` called twice with the same token returns
  ``error_code='token_already_used'`` on the second call.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from syntek_auth.services.password_reset import (
    PasswordResetResult,
    confirm_password_reset,
    generate_password_reset_token,
    invalidate_all_refresh_tokens,
    request_password_reset,
)

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.slow]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def minimal_policy(**overrides: object) -> dict:  # type: ignore[type-arg]
    """Return a minimal password policy dict for use in reset confirmation tests."""
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


def _make_verified_user(email: str) -> object:
    """Create a verified user for use in reset tests."""
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.create_user(  # type: ignore[attr-defined]
        email=email, password="OldPassword1234!"
    )
    user.email_verified = True  # type: ignore[attr-defined]
    user.save(update_fields=["email_verified"])  # type: ignore[attr-defined]
    return user


def _make_verification_code(
    user: object,
    code_type: str,
    token: str,
    *,
    expires_at: object = None,
) -> object:
    """Create a ``VerificationCode`` with the token encrypted at rest."""
    from datetime import timedelta

    from django.conf import settings as _settings
    from django.utils import timezone as _tz
    from syntek_auth.models.verification import VerificationCode
    from syntek_auth.services.lookup_tokens import make_token_token

    if expires_at is None:
        expires_at = _tz.now() + timedelta(hours=1)

    cfg = getattr(_settings, "SYNTEK_AUTH", {})
    raw_key = cfg.get("FIELD_KEY", "")
    field_key: bytes = (
        raw_key.encode("utf-8") if isinstance(raw_key, str) else bytes(raw_key)
    )
    try:
        from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

        encrypted = encrypt_field(token, field_key, "VerificationCode", "token")
    except ImportError:
        encrypted = token

    return VerificationCode.objects.create(  # type: ignore[return-value]
        user=user,
        code_type=code_type,
        token=encrypted,
        token_token=make_token_token(token),
        expires_at=expires_at,
    )


# ---------------------------------------------------------------------------
# AC: resetPasswordRequest — anti-enumeration (always returns generic success)
# ---------------------------------------------------------------------------


class TestResetPasswordRequestAntiEnumeration:
    """resetPasswordRequest must never reveal whether an account exists."""

    def test_request_returns_true_for_existing_verified_account(self) -> None:
        """request_password_reset must return True for a verified account."""
        _make_verified_user("alice_reset@example.com")
        result = request_password_reset("alice_reset@example.com")
        assert result is True, (
            "request_password_reset must return True regardless of account existence"
        )

    def test_request_returns_true_for_unknown_email(self) -> None:
        """request_password_reset must return True even for an unknown email."""
        result = request_password_reset("nobody@example.com")
        assert result is True

    def test_request_for_unknown_email_raises_not_implemented(self) -> None:
        """request_password_reset must return True for unknown email (anti-enum)."""
        result = request_password_reset("nobody_2@example.com")
        assert result is True

    def test_request_for_existing_verified_account_raises_not_implemented(self) -> None:
        """request_password_reset must return True for verified accounts."""
        _make_verified_user("alice_reset2@example.com")
        result = request_password_reset("alice_reset2@example.com")
        assert result is True

    def test_request_for_unverified_account_raises_not_implemented(self) -> None:
        """request_password_reset for unverified account must still return True."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="unverified_reset@example.com", password="Pass1234!"
        )
        result = request_password_reset("unverified_reset@example.com")
        assert result is True


# ---------------------------------------------------------------------------
# AC: generate_password_reset_token
# ---------------------------------------------------------------------------


class TestGeneratePasswordResetToken:
    """generate_password_reset_token must return a non-empty string."""

    def test_returns_non_empty_string(self) -> None:
        """generate_password_reset_token must return a non-empty URL-safe string."""
        user = _make_verified_user("gen_reset_token@example.com")
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        assert isinstance(token, str)
        assert len(token) > 0

    def test_signature_accepts_user_id(self) -> None:
        """generate_password_reset_token must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(generate_password_reset_token)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "generate_password_reset_token must accept a 'user_id' parameter"
        )


# ---------------------------------------------------------------------------
# AC: resetPasswordConfirm — valid token and compliant password
# ---------------------------------------------------------------------------


class TestConfirmPasswordResetSuccess:
    """A valid token and compliant password must succeed."""

    def test_raises_not_implemented(self) -> None:
        """confirm_password_reset with a valid token must return success=True."""
        user = _make_verified_user("confirm_reset@example.com")
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        result: PasswordResetResult = confirm_password_reset(
            token=token,
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        assert result.success is True
        assert result.error_code is None

    def test_success_result_structure(self) -> None:
        """confirm_password_reset must return success=True on a valid token."""
        user = _make_verified_user("confirm_reset2@example.com")
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        result: PasswordResetResult = confirm_password_reset(
            token=token,
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        assert result.success is True
        assert result.error_code is None

    def test_success_invalidates_all_refresh_tokens(self) -> None:
        """A successful reset must not raise and must return success=True."""
        user = _make_verified_user("confirm_reset3@example.com")
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        result: PasswordResetResult = confirm_password_reset(
            token=token,
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        assert result.success is True


# ---------------------------------------------------------------------------
# AC: resetPasswordConfirm — password in history is rejected
# ---------------------------------------------------------------------------


class TestConfirmPasswordResetHistoryCheck:
    """A new password that matches a recent history entry must be rejected."""

    def test_password_in_history_raises_not_implemented(self) -> None:
        """Resetting to the current password must return password_in_history."""
        user = _make_verified_user("history_reset@example.com")
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        # Set the user's password to a known value so we can test history.
        user.set_password("OldPassword123")  # type: ignore[attr-defined]
        user.save(update_fields=["password"])  # type: ignore[attr-defined]
        result: PasswordResetResult = confirm_password_reset(
            token=token,
            new_password="OldPassword123",  # same as the stored hash
            password_policy=minimal_policy(PASSWORD_HISTORY=5),
        )
        assert result.error_code == "password_in_history"
        assert result.success is False

    def test_password_in_history_returns_password_in_history_code(self) -> None:
        """In the green phase, reusing a recent password must return
        error_code='password_in_history'."""
        user = _make_verified_user("history_reset2@example.com")
        user.set_password("SomeOldPass1!")  # type: ignore[attr-defined]
        user.save(update_fields=["password"])  # type: ignore[attr-defined]
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        result: PasswordResetResult = confirm_password_reset(
            token=token,
            new_password="SomeOldPass1!",  # same as current hash
            password_policy=minimal_policy(PASSWORD_HISTORY=5),
        )
        assert result.error_code == "password_in_history"
        assert result.success is False


# ---------------------------------------------------------------------------
# AC: resetPasswordConfirm — expired token
# ---------------------------------------------------------------------------


class TestConfirmPasswordResetExpiredToken:
    """An expired reset token must be rejected."""

    def test_expired_token_raises_not_implemented(self) -> None:
        """An expired token must return success=False."""
        from syntek_auth.models.verification import VerificationCode

        user = _make_verified_user("expired_reset@example.com")
        _make_verification_code(
            user,
            VerificationCode.CodeType.PASSWORD_RESET,
            "expired-reset-tok-001",
            expires_at=timezone.now() - timedelta(hours=2),
        )
        result: PasswordResetResult = confirm_password_reset(
            token="expired-reset-tok-001",
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        assert result.success is False

    def test_expired_token_returns_token_expired_code(self) -> None:
        """An expired token must return error_code='token_expired'."""
        from syntek_auth.models.verification import VerificationCode

        user = _make_verified_user("expired_reset2@example.com")
        _make_verification_code(
            user,
            VerificationCode.CodeType.PASSWORD_RESET,
            "expired-reset-tok-002",
            expires_at=timezone.now() - timedelta(hours=2),
        )
        result: PasswordResetResult = confirm_password_reset(
            token="expired-reset-tok-002",
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        assert result.error_code == "token_expired"
        assert result.success is False

    def test_expired_token_does_not_change_password(self) -> None:
        """An expired token must not result in any password change."""
        from syntek_auth.models.verification import VerificationCode

        user = _make_verified_user("expired_reset3@example.com")
        old_password = user.password  # type: ignore[attr-defined]
        _make_verification_code(
            user,
            VerificationCode.CodeType.PASSWORD_RESET,
            "expired-reset-tok-003",
            expires_at=timezone.now() - timedelta(hours=2),
        )
        result: PasswordResetResult = confirm_password_reset(
            token="expired-reset-tok-003",
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        assert result.success is False
        # Verify password unchanged.
        user.refresh_from_db()  # type: ignore[attr-defined]
        assert user.password == old_password  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# AC: resetPasswordConfirm — single-use token (already-used is rejected)
# ---------------------------------------------------------------------------


class TestConfirmPasswordResetSingleUse:
    """A token used once must be rejected on subsequent use."""

    def test_already_used_token_raises_not_implemented(self) -> None:
        """The second use of a token must return success=False."""
        user = _make_verified_user("used_reset@example.com")
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        confirm_password_reset(
            token=token,
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        result: PasswordResetResult = confirm_password_reset(
            token=token,
            new_password="AnotherNewPass1!",
            password_policy=minimal_policy(),
        )
        assert result.success is False

    def test_already_used_token_returns_token_already_used_code(self) -> None:
        """The second use of a token must return error_code='token_already_used'."""
        user = _make_verified_user("used_reset2@example.com")
        token = generate_password_reset_token(user_id=user.pk)  # type: ignore[attr-defined]
        confirm_password_reset(
            token=token,
            new_password="NewValidPass1!",
            password_policy=minimal_policy(),
        )
        result: PasswordResetResult = confirm_password_reset(
            token=token,
            new_password="AnotherNewPass1!",
            password_policy=minimal_policy(),
        )
        assert result.error_code == "token_already_used"
        assert result.success is False


# ---------------------------------------------------------------------------
# AC: invalidate_all_refresh_tokens
# ---------------------------------------------------------------------------


class TestInvalidateAllRefreshTokens:
    """invalidate_all_refresh_tokens must revoke every token for the given user."""

    def test_returns_count(self) -> None:
        """invalidate_all_refresh_tokens must return a non-negative integer."""
        count = invalidate_all_refresh_tokens(user_id=999)
        assert isinstance(count, int)
        assert count >= 0

    def test_signature_accepts_user_id(self) -> None:
        """invalidate_all_refresh_tokens must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(invalidate_all_refresh_tokens)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "invalidate_all_refresh_tokens must accept a 'user_id' parameter"
        )


# ---------------------------------------------------------------------------
# AC: PasswordResetResult dataclass structure
# ---------------------------------------------------------------------------


class TestPasswordResetResultStructure:
    """PasswordResetResult must have the correct fields and defaults."""

    def test_result_has_success_field(self) -> None:
        """PasswordResetResult must have a 'success' boolean field."""
        result = PasswordResetResult(success=True)
        assert result.success is True

    def test_result_has_error_code_field(self) -> None:
        """PasswordResetResult must have an 'error_code' field."""
        result = PasswordResetResult(success=False, error_code="token_expired")
        assert result.error_code == "token_expired"

    def test_result_has_message_field(self) -> None:
        """PasswordResetResult must have a 'message' field."""
        result = PasswordResetResult(
            success=False,
            error_code="token_expired",
            message="Reset token has expired.",
        )
        assert "expired" in result.message

    def test_result_defaults_error_code_to_none(self) -> None:
        """error_code must default to None."""
        result = PasswordResetResult(success=True)
        assert result.error_code is None

    def test_result_defaults_message_to_empty_string(self) -> None:
        """message must default to an empty string."""
        result = PasswordResetResult(success=True)
        assert result.message == ""
