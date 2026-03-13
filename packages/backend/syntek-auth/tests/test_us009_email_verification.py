"""US009 — Green phase: email verification flow tests for ``syntek-auth``.

Tests cover ``generate_email_verification_token``, ``verify_email_token``,
``resend_verification_email``, and ``is_email_verified``.

Acceptance criteria under test
-------------------------------
- ``verifyEmail`` with a valid, unexpired, single-use token marks the account
  as verified and allows a full session to be issued.
- ``verifyEmail`` with an expired token returns ``error_code='token_expired'``.
- ``verifyEmail`` with an already-used token returns
  ``error_code='token_already_used'`` — tokens are single-use.
- An unverified account cannot access protected resources (401 with
  ``email_not_verified`` error code).
- ``resendVerificationEmail`` for an already-verified account returns
  ``success=False``.
- ``generate_email_verification_token`` returns a non-empty string.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from syntek_auth.services.email_verification import (
    EmailVerificationResult,
    generate_email_verification_token,
    is_email_verified,
    resend_verification_email,
    verify_email_token,
)

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.slow]


def _make_verification_code(
    user: object,
    code_type: str,
    token: str,
    *,
    expires_at: object = None,
    used_at: object = None,
) -> object:
    """Create a ``VerificationCode`` with the token encrypted at rest."""
    from datetime import timedelta

    from django.conf import settings as _settings
    from django.utils import timezone as _tz
    from syntek_auth.models.verification import VerificationCode
    from syntek_auth.services.lookup_tokens import make_token_token

    if expires_at is None:
        expires_at = _tz.now() + timedelta(hours=24)

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

    kwargs: dict = {  # type: ignore[type-arg]
        "user": user,
        "code_type": code_type,
        "token": encrypted,
        "token_token": make_token_token(token),
        "expires_at": expires_at,
    }
    if used_at is not None:
        kwargs["used_at"] = used_at

    return VerificationCode.objects.create(**kwargs)


# ---------------------------------------------------------------------------
# AC: generate_email_verification_token returns a usable token string
# ---------------------------------------------------------------------------


class TestGenerateEmailVerificationToken:
    """generate_email_verification_token must return a non-empty string."""

    def test_returns_non_empty_string(self) -> None:
        """A token must be generated for a valid user_id."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="token_test@example.com", password="Pass1234!"
        )
        token = generate_email_verification_token(user_id=user.pk)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_distinct_tokens_for_same_user(self) -> None:
        """Two successive calls must produce different tokens."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="token_distinct@example.com", password="Pass1234!"
        )
        token_a = generate_email_verification_token(user_id=user.pk)
        token_b = generate_email_verification_token(user_id=user.pk)
        assert token_a != token_b


# ---------------------------------------------------------------------------
# AC: verify_email_token — valid token marks account as verified
# ---------------------------------------------------------------------------


class TestVerifyEmailTokenSuccess:
    """A valid, unexpired, single-use token must verify the account."""

    def test_valid_token_returns_success_true(self) -> None:
        """verify_email_token with a valid token must return success=True."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="verify_success@example.com", password="Pass1234!"
        )
        token = generate_email_verification_token(user_id=user.pk)
        result: EmailVerificationResult = verify_email_token(token)
        assert result.success is True
        assert result.error_code is None

    def test_valid_token_sets_email_verified_flag(self) -> None:
        """After a successful verification, is_email_verified must return True."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="verify_flag@example.com", password="Pass1234!"
        )
        token = generate_email_verification_token(user_id=user.pk)
        verify_email_token(token)
        assert is_email_verified(user_id=user.pk) is True


# ---------------------------------------------------------------------------
# AC: verify_email_token — expired token is rejected
# ---------------------------------------------------------------------------


class TestVerifyEmailTokenExpired:
    """An expired verification token must return an appropriate error."""

    def test_expired_token_returns_success_false(self) -> None:
        """verify_email_token with an expired token must return success=False."""
        from django.contrib.auth import get_user_model
        from syntek_auth.models.verification import VerificationCode

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="expired_token@example.com", password="Pass1234!"
        )
        # Create an already-expired verification code.
        _plaintext = "expired-test-token-001"
        _make_verification_code(
            user,
            VerificationCode.CodeType.EMAIL_VERIFY,
            _plaintext,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        result: EmailVerificationResult = verify_email_token(_plaintext)
        assert result.success is False

    def test_expired_token_returns_token_expired_error_code(self) -> None:
        """The error_code must be 'token_expired' for an expired token."""
        from django.contrib.auth import get_user_model
        from syntek_auth.models.verification import VerificationCode

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="expired_code@example.com", password="Pass1234!"
        )
        _plaintext = "expired-test-token-002"
        _make_verification_code(
            user,
            VerificationCode.CodeType.EMAIL_VERIFY,
            _plaintext,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        result: EmailVerificationResult = verify_email_token(_plaintext)
        assert result.error_code == "token_expired", (
            f"Expected error_code='token_expired'; got {result.error_code!r}"
        )

    def test_expired_token_has_non_empty_message(self) -> None:
        """The error message must not be empty — users need actionable guidance."""
        from django.contrib.auth import get_user_model
        from syntek_auth.models.verification import VerificationCode

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="expired_msg@example.com", password="Pass1234!"
        )
        _plaintext = "expired-test-token-003"
        _make_verification_code(
            user,
            VerificationCode.CodeType.EMAIL_VERIFY,
            _plaintext,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        result: EmailVerificationResult = verify_email_token(_plaintext)
        assert result.message, "Error message must be non-empty for expired token"


# ---------------------------------------------------------------------------
# AC: verify_email_token — already-used token is rejected (single-use)
# ---------------------------------------------------------------------------


class TestVerifyEmailTokenAlreadyUsed:
    """A token that has already been consumed must be rejected."""

    def test_already_used_token_returns_success_false(self) -> None:
        """verify_email_token called twice with the same token must fail on second call."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="used_token@example.com", password="Pass1234!"
        )
        token = generate_email_verification_token(user_id=user.pk)
        verify_email_token(token)  # first use — succeeds
        result: EmailVerificationResult = verify_email_token(token)  # second use
        assert result.success is False

    def test_already_used_token_returns_token_already_used_error_code(self) -> None:
        """The error_code must be 'token_already_used' on a reused token."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="used_code@example.com", password="Pass1234!"
        )
        token = generate_email_verification_token(user_id=user.pk)
        verify_email_token(token)
        result: EmailVerificationResult = verify_email_token(token)
        assert result.error_code == "token_already_used", (
            f"Expected error_code='token_already_used'; got {result.error_code!r}"
        )


# ---------------------------------------------------------------------------
# AC: Unverified account is gated from protected resources
# ---------------------------------------------------------------------------


class TestUnverifiedAccountGating:
    """is_email_verified returns False for an unverified account."""

    def test_is_email_verified_returns_false_for_new_user(self) -> None:
        """A newly created user must not be email-verified."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="unverified@example.com", password="Pass1234!"
        )
        assert is_email_verified(user_id=user.pk) is False

    def test_is_email_verified_signature_accepts_user_id(self) -> None:
        """is_email_verified must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(is_email_verified)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "is_email_verified must accept a 'user_id' parameter"
        )


# ---------------------------------------------------------------------------
# AC: resendVerificationEmail for already-verified account returns error
# ---------------------------------------------------------------------------


class TestResendVerificationEmailAlreadyVerified:
    """Resending a verification email to an already-verified account must fail."""

    def test_resend_returns_false_when_already_verified(self) -> None:
        """resend_verification_email must return False for a verified account."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="already_verified@example.com", password="Pass1234!"
        )
        # Verify the account first.
        token = generate_email_verification_token(user_id=user.pk)
        verify_email_token(token)
        # Resend should now return False.
        result = resend_verification_email(user_id=user.pk)
        assert result is False

    def test_resend_returns_true_for_unverified_account(self) -> None:
        """resend_verification_email must return True for an unverified account."""
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        user = UserModel.objects.create_user(  # type: ignore[attr-defined]
            email="resend_unverified@example.com", password="Pass1234!"
        )
        result = resend_verification_email(user_id=user.pk)
        assert result is True

    def test_resend_signature_accepts_user_id(self) -> None:
        """resend_verification_email must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(resend_verification_email)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "resend_verification_email must accept a 'user_id' parameter"
        )


# ---------------------------------------------------------------------------
# AC: EmailVerificationResult dataclass structure
# ---------------------------------------------------------------------------


class TestEmailVerificationResultStructure:
    """EmailVerificationResult must have the correct fields."""

    def test_result_has_success_field(self) -> None:
        """EmailVerificationResult must have a 'success' boolean field."""
        result = EmailVerificationResult(success=True)
        assert result.success is True

    def test_result_has_error_code_field(self) -> None:
        """EmailVerificationResult must have an 'error_code' field."""
        result = EmailVerificationResult(success=False, error_code="token_expired")
        assert result.error_code == "token_expired"

    def test_result_has_message_field(self) -> None:
        """EmailVerificationResult must have a 'message' field."""
        result = EmailVerificationResult(
            success=False,
            error_code="token_expired",
            message="Token has expired; please request a new verification email.",
        )
        assert "expired" in result.message

    def test_result_defaults_error_code_to_none(self) -> None:
        """error_code must default to None (success case)."""
        result = EmailVerificationResult(success=True)
        assert result.error_code is None

    def test_result_defaults_message_to_empty_string(self) -> None:
        """message must default to an empty string."""
        result = EmailVerificationResult(success=True)
        assert result.message == ""
