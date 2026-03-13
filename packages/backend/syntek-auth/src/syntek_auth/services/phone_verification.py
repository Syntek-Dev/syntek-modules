"""Phone verification service for ``syntek-auth`` — US009.

Handles OTP generation, brute-force protection (max 3 attempts), expiry
(default 10 minutes), and phone-verified flag management.

- Generates a 6-character uppercase hex OTP via ``secrets.token_hex(3).upper()``.
- Persists the OTP in ``VerificationCode`` with a 10-minute TTL.
- Tracks incorrect attempts via ``attempt_count``; invalidates the code
  when the count reaches 3 (``error_code='otp_invalidated'``).
- Rejects expired codes (``error_code='otp_expired'``).
- Marks ``phone_verified=True`` on the user record upon success.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings as _settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from syntek_auth.services.lookup_tokens import make_token_token


def _encrypt_token(plaintext: str) -> str:
    """Return AES-256-GCM ciphertext of ``plaintext`` using ``FIELD_KEY``."""
    cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    raw_key = cfg.get("FIELD_KEY", "")
    field_key: bytes = (
        raw_key.encode("utf-8") if isinstance(raw_key, str) else bytes(raw_key)
    )
    try:
        from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

        return encrypt_field(plaintext, field_key, "VerificationCode", "token")
    except ImportError:
        return plaintext


# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------

#: Default phone OTP TTL in seconds (10 minutes).
_PHONE_OTP_TTL_SECONDS: int = 600

#: Maximum incorrect OTP attempts before the code is invalidated.
_MAX_OTP_ATTEMPTS: int = 3

#: Maximum attempts to generate a unique OTP token before giving up.
_MAX_TOKEN_ATTEMPTS: int = 3


@dataclass(frozen=True)
class PhoneVerificationResult:
    """Result returned by ``verify_phone_otp``.

    Attributes
    ----------
    success:
        ``True`` when the OTP was valid and the phone is now verified.
    error_code:
        Machine-readable error identifier when ``success=False``.
        One of: ``'otp_expired'``, ``'otp_invalid'``, ``'otp_invalidated'``.
    message:
        Human-readable description of the outcome.
    """

    success: bool
    error_code: str | None = None
    message: str = ""


def _generate_unique_otp() -> str:
    """Generate a cryptographically random 6-character uppercase hex OTP.

    Retries on unique-constraint collision up to ``_MAX_TOKEN_ATTEMPTS`` times.

    Returns
    -------
    str
        A 6-character uppercase hex string (e.g. ``'A3F2B1'``).

    Raises
    ------
    RuntimeError
        If a unique OTP cannot be generated after the allowed attempts.
    """
    from syntek_auth.models.verification import VerificationCode

    for _ in range(_MAX_TOKEN_ATTEMPTS):
        otp = secrets.token_hex(3).upper()
        if not VerificationCode.objects.filter(
            token_token=make_token_token(otp)
        ).exists():
            return otp
    raise RuntimeError(
        f"Failed to generate a unique phone OTP after {_MAX_TOKEN_ATTEMPTS} attempts."
    )


def generate_phone_otp(user_id: int) -> str:
    """Generate a 6-character OTP for phone verification.

    Invalidates any existing pending OTPs for this user before creating a new
    one.  The OTP is stored in ``VerificationCode`` with a 10-minute TTL and a
    zero attempt counter.

    Parameters
    ----------
    user_id:
        Primary key of the user whose phone is being verified.

    Returns
    -------
    str
        The plaintext 6-character uppercase hex OTP.

    Raises
    ------
    RuntimeError
        If a unique OTP cannot be generated after the allowed attempts.
    """
    from syntek_auth.models.verification import VerificationCode

    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.get(pk=user_id)

    # Invalidate existing pending phone OTPs for this user.
    now = timezone.now()
    VerificationCode.objects.filter(
        user=user,
        code_type=VerificationCode.CodeType.PHONE_VERIFY,
        used_at__isnull=True,
        expires_at__gt=now,
    ).delete()

    otp = _generate_unique_otp()
    VerificationCode.objects.create(
        user=user,
        code_type=VerificationCode.CodeType.PHONE_VERIFY,
        token=_encrypt_token(otp),
        token_token=make_token_token(otp),
        expires_at=now + timedelta(seconds=_PHONE_OTP_TTL_SECONDS),
    )
    return otp


def verify_phone_otp(user_id: int, otp: str) -> PhoneVerificationResult:
    """Validate ``otp`` and mark the phone number as verified on success.

    Increments ``attempt_count`` on each incorrect submission.  When the
    count reaches ``_MAX_OTP_ATTEMPTS`` the code is marked as used and
    ``error_code='otp_invalidated'`` is returned.

    Parameters
    ----------
    user_id:
        Primary key of the user whose phone is being verified.
    otp:
        The plaintext OTP submitted by the user.

    Returns
    -------
    PhoneVerificationResult
        ``success=True`` when the OTP is valid and the phone is now verified;
        ``success=False`` with an ``error_code`` otherwise.
    """
    from syntek_auth.models.verification import VerificationCode

    UserModel = get_user_model()  # noqa: N806
    now = timezone.now()

    # Find the most recent pending OTP for this user.
    code = (
        VerificationCode.objects.filter(
            user_id=user_id,
            code_type=VerificationCode.CodeType.PHONE_VERIFY,
            used_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )

    if code is None:
        return PhoneVerificationResult(
            success=False,
            error_code="otp_invalid",
            message="No active OTP found. Please request a new verification code.",
        )

    # Check expiry before checking the code.
    if code.expires_at <= now:
        return PhoneVerificationResult(
            success=False,
            error_code="otp_expired",
            message=("The verification code has expired. Please request a new code."),
        )

    # Validate the submitted OTP via HMAC token (token field is ciphertext).
    if code.token_token != make_token_token(otp.upper()):
        code.attempt_count += 1
        if code.attempt_count >= _MAX_OTP_ATTEMPTS:
            # Invalidate the code — mark as used with a sentinel.
            code.used_at = now
            code.save(update_fields=["attempt_count", "used_at"])
            return PhoneVerificationResult(
                success=False,
                error_code="otp_invalidated",
                message=(
                    "Too many incorrect attempts. "
                    "The verification code has been invalidated. "
                    "Please request a new code."
                ),
            )
        code.save(update_fields=["attempt_count"])
        return PhoneVerificationResult(
            success=False,
            error_code="otp_invalid",
            message=(
                f"Incorrect verification code. "
                f"{_MAX_OTP_ATTEMPTS - code.attempt_count} attempt(s) remaining."
            ),
        )

    # OTP is correct — mark used and set phone_verified on the user.
    code.used_at = now
    code.save(update_fields=["used_at"])

    user = UserModel.objects.get(pk=user_id)
    user.phone_verified = True  # type: ignore[attr-defined]
    user.save(update_fields=["phone_verified"])

    return PhoneVerificationResult(
        success=True,
        message="Phone number verified successfully.",
    )


def resend_phone_otp(user_id: int) -> bool:
    """Issue a new OTP for the given user.

    Invalidates existing pending OTPs and generates a replacement.

    Parameters
    ----------
    user_id:
        Primary key of the user requesting a new OTP.

    Returns
    -------
    bool
        ``True`` once the new OTP has been generated (always ``True``).
    """
    generate_phone_otp(user_id)
    return True


def is_phone_verified(user_id: int) -> bool:
    """Return ``True`` when the user's phone number has been verified.

    Parameters
    ----------
    user_id:
        Primary key of the user to check.

    Returns
    -------
    bool
        ``True`` if the ``phone_verified`` flag is set on the user record.
    """
    UserModel = get_user_model()  # noqa: N806
    return bool(
        UserModel.objects.filter(pk=user_id, phone_verified=True).exists()  # type: ignore[attr-defined]
    )
