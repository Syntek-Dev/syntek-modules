"""US009 — Green phase: phone verification flow tests for ``syntek-auth``.

Tests cover ``generate_phone_otp``, ``verify_phone_otp``, ``resend_phone_otp``,
and ``is_phone_verified``.

Acceptance criteria under test
-------------------------------
- ``verifyPhone`` with a valid, unexpired OTP marks the phone as verified.
- ``verifyPhone`` with an incorrect OTP three times in a row invalidates the
  OTP and requires a new one to be requested.
- ``verifyPhone`` with an expired OTP returns ``error_code='otp_expired'``.
- ``generate_phone_otp`` returns a non-empty string.

Run with: ``syntek-dev test --python --python-package syntek-auth``
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone
from syntek_auth.services.phone_verification import (
    PhoneVerificationResult,
    generate_phone_otp,
    is_phone_verified,
    resend_phone_otp,
    verify_phone_otp,
)

pytestmark = pytest.mark.django_db


def _make_user(email: str) -> Any:
    """Create a test user with the given email address."""
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()  # noqa: N806
    return UserModel.objects.create_user(email=email, password="Pass1234!")  # type: ignore[attr-defined]


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
        expires_at = _tz.now() + timedelta(minutes=10)

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
# AC: generate_phone_otp returns a 6-character OTP string
# ---------------------------------------------------------------------------


class TestGeneratePhoneOtp:
    """generate_phone_otp must return a 6-character OTP string."""

    def test_returns_non_empty_string(self) -> None:
        """generate_phone_otp must return a non-empty string."""
        user = _make_user("otp_gen@example.com")
        otp = generate_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        assert isinstance(otp, str)
        assert len(otp) == 6

    def test_signature_accepts_user_id(self) -> None:
        """generate_phone_otp must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(generate_phone_otp)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "generate_phone_otp must accept a 'user_id' parameter"
        )


# ---------------------------------------------------------------------------
# AC: verify_phone_otp — valid OTP marks phone as verified
# ---------------------------------------------------------------------------


class TestVerifyPhoneOtpSuccess:
    """A valid, unexpired OTP must mark the phone number as verified."""

    def test_valid_otp_raises_not_implemented(self) -> None:
        """verify_phone_otp with a valid OTP must return success=True."""
        user = _make_user("otp_valid@example.com")
        otp = generate_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        result: PhoneVerificationResult = verify_phone_otp(
            user_id=user.pk,
            otp=otp,  # type: ignore[attr-defined]
        )
        assert result.success is True

    def test_success_result_has_correct_structure(self) -> None:
        """A valid OTP must return success=True with no error_code."""
        user = _make_user("otp_struct@example.com")
        otp = generate_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        result: PhoneVerificationResult = verify_phone_otp(
            user_id=user.pk,
            otp=otp,  # type: ignore[attr-defined]
        )
        assert result.success is True
        assert result.error_code is None


# ---------------------------------------------------------------------------
# AC: verify_phone_otp — three incorrect attempts invalidate the OTP
# ---------------------------------------------------------------------------


class TestVerifyPhoneOtpBruteForce:
    """Three incorrect OTP submissions must invalidate the OTP."""

    def test_first_incorrect_otp_raises_not_implemented(self) -> None:
        """The first incorrect OTP must return success=False with otp_invalid."""
        user = _make_user("otp_wrong1@example.com")
        generate_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        result: PhoneVerificationResult = verify_phone_otp(
            user_id=user.pk,
            otp="000000",  # type: ignore[attr-defined]
        )
        assert result.success is False

    def test_after_three_incorrect_attempts_otp_is_invalidated(self) -> None:
        """The third incorrect attempt must return error_code='otp_invalidated'."""
        user = _make_user("otp_brute@example.com")
        generate_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        result: PhoneVerificationResult = PhoneVerificationResult(success=False)
        for _ in range(3):
            result = verify_phone_otp(user_id=user.pk, otp="000000")  # type: ignore[attr-defined]
        assert result.error_code == "otp_invalidated", (
            f"Expected 'otp_invalidated' after 3 attempts; got {result.error_code!r}"
        )

    def test_after_three_incorrect_attempts_success_is_false(self) -> None:
        """The result after invalidation must have success=False."""
        user = _make_user("otp_brute2@example.com")
        generate_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        result: PhoneVerificationResult = PhoneVerificationResult(success=True)
        for _ in range(3):
            result = verify_phone_otp(user_id=user.pk, otp="ZZZZZZ")  # type: ignore[attr-defined]
        assert result.success is False

    def test_invalidated_otp_cannot_be_reused(self) -> None:
        """A correct OTP submitted after invalidation must fail."""
        user = _make_user("otp_reuse@example.com")
        correct_otp = generate_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        # Three wrong attempts — invalidates the OTP.
        for _ in range(3):
            verify_phone_otp(user_id=user.pk, otp="000000")  # type: ignore[attr-defined]
        # The correct OTP submitted after invalidation must fail.
        result: PhoneVerificationResult = verify_phone_otp(
            user_id=user.pk,
            otp=correct_otp,  # type: ignore[attr-defined]
        )
        assert result.success is False


# ---------------------------------------------------------------------------
# AC: verify_phone_otp — expired OTP is rejected
# ---------------------------------------------------------------------------


class TestVerifyPhoneOtpExpired:
    """An expired OTP must be rejected with error_code='otp_expired'."""

    def test_expired_otp_raises_not_implemented(self) -> None:
        """An expired OTP must return success=False."""
        from syntek_auth.models.verification import VerificationCode

        user = _make_user("otp_expired@example.com")
        _make_verification_code(
            user,
            VerificationCode.CodeType.PHONE_VERIFY,
            "AABBCC",
            expires_at=timezone.now() - timedelta(minutes=11),
        )
        result: PhoneVerificationResult = verify_phone_otp(
            user_id=user.pk,
            otp="AABBCC",  # type: ignore[attr-defined]
        )
        assert result.success is False

    def test_expired_otp_returns_otp_expired_code(self) -> None:
        """An expired OTP must return error_code='otp_expired'."""
        from syntek_auth.models.verification import VerificationCode

        user = _make_user("otp_expiredcode@example.com")
        _make_verification_code(
            user,
            VerificationCode.CodeType.PHONE_VERIFY,
            "DDEEFF",
            expires_at=timezone.now() - timedelta(minutes=11),
        )
        result: PhoneVerificationResult = verify_phone_otp(
            user_id=user.pk,
            otp="DDEEFF",  # type: ignore[attr-defined]
        )
        assert result.error_code == "otp_expired"
        assert result.success is False

    def test_expired_otp_has_non_empty_message(self) -> None:
        """The error message for an expired OTP must not be empty."""
        from syntek_auth.models.verification import VerificationCode

        user = _make_user("otp_expiredmsg@example.com")
        _make_verification_code(
            user,
            VerificationCode.CodeType.PHONE_VERIFY,
            "112233",
            expires_at=timezone.now() - timedelta(minutes=11),
        )
        result: PhoneVerificationResult = verify_phone_otp(
            user_id=user.pk,
            otp="112233",  # type: ignore[attr-defined]
        )
        assert result.message, "Error message must be non-empty for expired OTP"


# ---------------------------------------------------------------------------
# AC: is_phone_verified
# ---------------------------------------------------------------------------


class TestIsPhoneVerified:
    """is_phone_verified must return False for unverified users."""

    def test_returns_false_for_unverified_user(self) -> None:
        """is_phone_verified must return False for a user with no verified phone."""
        user = _make_user("phoneunverified@example.com")
        assert is_phone_verified(user_id=user.pk) is False  # type: ignore[attr-defined]

    def test_signature_accepts_user_id(self) -> None:
        """is_phone_verified must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(is_phone_verified)
        params = list(sig.parameters.keys())
        assert "user_id" in params, (
            "is_phone_verified must accept a 'user_id' parameter"
        )


# ---------------------------------------------------------------------------
# AC: resend_phone_otp
# ---------------------------------------------------------------------------


class TestResendPhoneOtp:
    """resend_phone_otp must return True after generating a new OTP."""

    def test_returns_true(self) -> None:
        """resend_phone_otp must return True."""
        user = _make_user("resend_otp@example.com")
        result = resend_phone_otp(user_id=user.pk)  # type: ignore[attr-defined]
        assert result is True

    def test_signature_accepts_user_id(self) -> None:
        """resend_phone_otp must accept a user_id positional argument."""
        import inspect

        sig = inspect.signature(resend_phone_otp)
        params = list(sig.parameters.keys())
        assert "user_id" in params, "resend_phone_otp must accept a 'user_id' parameter"


# ---------------------------------------------------------------------------
# AC: PhoneVerificationResult dataclass structure
# ---------------------------------------------------------------------------


class TestPhoneVerificationResultStructure:
    """PhoneVerificationResult must have the correct fields and defaults."""

    def test_result_has_success_field(self) -> None:
        """PhoneVerificationResult must have a 'success' boolean field."""
        result = PhoneVerificationResult(success=True)
        assert result.success is True

    def test_result_has_error_code_field(self) -> None:
        """PhoneVerificationResult must have an 'error_code' field."""
        result = PhoneVerificationResult(success=False, error_code="otp_expired")
        assert result.error_code == "otp_expired"

    def test_result_has_message_field(self) -> None:
        """PhoneVerificationResult must have a 'message' field."""
        result = PhoneVerificationResult(
            success=False,
            error_code="otp_expired",
            message="OTP has expired; please request a new code.",
        )
        assert "expired" in result.message

    def test_result_defaults_error_code_to_none(self) -> None:
        """error_code must default to None."""
        result = PhoneVerificationResult(success=True)
        assert result.error_code is None

    def test_result_defaults_message_to_empty_string(self) -> None:
        """message must default to an empty string."""
        result = PhoneVerificationResult(success=True)
        assert result.message == ""
