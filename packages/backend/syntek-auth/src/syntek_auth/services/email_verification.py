"""Email verification service for ``syntek-auth`` — US009.

Handles single-use token generation, expiry, and account-gating logic for
email verification.

- Generates a cryptographically random, URL-safe token (32 bytes via
  ``secrets.token_urlsafe``).
- Persists the token in ``VerificationCode`` with a configurable TTL
  (default: 24 hours).
- Marks the account's ``email_verified`` flag on successful verification.
- Rejects expired tokens (``error_code='token_expired'``) and already-used
  tokens (``error_code='token_already_used'``) with distinct error codes.
- Invalidates pending tokens before issuing a replacement.
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
    """Return AES-256-GCM ciphertext of ``plaintext`` using ``FIELD_KEY``.

    Falls back to the plaintext value when ``syntek_pyo3`` is unavailable
    (e.g. test environments without the Rust extension).
    """
    cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    raw_key = cfg.get("FIELD_KEY", "")
    field_key: bytes = (
        raw_key.encode("utf-8") if isinstance(raw_key, str) else bytes(raw_key)
    )
    try:
        from syntek_pyo3 import KeyRing, encrypt_field  # type: ignore[import-not-found]

        _ring = KeyRing()
        _ring.add(1, field_key)
        return encrypt_field(plaintext, _ring, "VerificationCode", "token")
    except ImportError:
        return plaintext


# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------

#: Default email verification token TTL in seconds (24 hours).
_EMAIL_VERIFY_TTL_SECONDS: int = 86400

#: Maximum attempts to generate a unique token before giving up.
_MAX_TOKEN_ATTEMPTS: int = 3


@dataclass(frozen=True)
class EmailVerificationResult:
    """Result returned by ``verify_email_token``.

    Attributes
    ----------
    success:
        ``True`` when the token was valid and the account is now verified.
    error_code:
        Machine-readable error identifier when ``success=False``.
        One of: ``'token_expired'``, ``'token_already_used'``,
        ``'token_invalid'``, ``'already_verified'``.
    message:
        Human-readable description of the outcome.
    """

    success: bool
    error_code: str | None = None
    message: str = ""


def _generate_unique_token() -> str:
    """Generate a URL-safe cryptographically random token, retrying on collision.

    Returns
    -------
    str
        A unique URL-safe token string (approximately 43 characters).

    Raises
    ------
    RuntimeError
        If a unique token cannot be generated after three attempts.
    """
    from syntek_auth.models.verification import VerificationCode

    for _ in range(_MAX_TOKEN_ATTEMPTS):
        token = secrets.token_urlsafe(32)
        if not VerificationCode.objects.filter(
            token_token=make_token_token(token)
        ).exists():
            return token
    raise RuntimeError(
        "Failed to generate a unique email verification token after "
        f"{_MAX_TOKEN_ATTEMPTS} attempts."
    )


def generate_email_verification_token(user_id: int) -> str:
    """Generate a single-use email verification token for the given user.

    Invalidates any existing pending tokens for the user before creating
    the new one.  The token is stored in plaintext in ``VerificationCode``
    with a 24-hour TTL.

    Parameters
    ----------
    user_id:
        Primary key of the user who needs to verify their email address.

    Returns
    -------
    str
        A URL-safe plaintext token string (approximately 43 characters).

    Raises
    ------
    RuntimeError
        If a unique token cannot be generated after three attempts.
    """
    from syntek_auth.models.verification import VerificationCode

    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.get(pk=user_id)

    # Invalidate existing pending email verification tokens.
    now = timezone.now()
    VerificationCode.objects.filter(
        user=user,
        code_type=VerificationCode.CodeType.EMAIL_VERIFY,
        used_at__isnull=True,
        expires_at__gt=now,
    ).delete()

    token = _generate_unique_token()
    VerificationCode.objects.create(
        user=user,
        code_type=VerificationCode.CodeType.EMAIL_VERIFY,
        token=_encrypt_token(token),
        token_token=make_token_token(token),
        expires_at=now + timedelta(seconds=_EMAIL_VERIFY_TTL_SECONDS),
    )
    return token


def verify_email_token(token: str) -> EmailVerificationResult:
    """Validate ``token`` and mark the corresponding account's email as verified.

    Checks that the token exists, has not expired, and has not already been
    used.  On success, marks ``user.email_verified = True`` and records
    ``used_at`` on the ``VerificationCode`` row.

    Parameters
    ----------
    token:
        The plaintext verification token from the email link.

    Returns
    -------
    EmailVerificationResult
        ``success=True`` when the token is valid and the account is now
        verified; ``success=False`` with an ``error_code`` otherwise.
    """
    from syntek_auth.models.verification import VerificationCode

    now = timezone.now()

    try:
        code = VerificationCode.objects.select_related("user").get(
            token_token=make_token_token(token),
            code_type=VerificationCode.CodeType.EMAIL_VERIFY,
        )
    except VerificationCode.DoesNotExist:
        return EmailVerificationResult(
            success=False,
            error_code="token_invalid",
            message="Verification token not found.",
        )

    # Check if already used.
    if code.used_at is not None:
        return EmailVerificationResult(
            success=False,
            error_code="token_already_used",
            message=(
                "This verification token has already been used. "
                "Please request a new verification email."
            ),
        )

    # Check expiry.
    if code.expires_at <= now:
        return EmailVerificationResult(
            success=False,
            error_code="token_expired",
            message=(
                "This verification token has expired. "
                "Please request a new verification email."
            ),
        )

    # Mark the code as used and verify the email.
    code.used_at = now
    code.save(update_fields=["used_at"])

    user = code.user
    user.email_verified = True  # type: ignore[attr-defined]
    user.save(update_fields=["email_verified"])

    return EmailVerificationResult(
        success=True,
        message="Email address verified successfully.",
    )


def resend_verification_email(user_id: int) -> bool:
    """Issue a new verification email for the given user.

    Returns ``False`` when the account is already verified so that the
    caller can surface a clear error.  When not yet verified, invalidates
    any pending tokens and generates a new one.

    Parameters
    ----------
    user_id:
        Primary key of the user requesting a new verification email.

    Returns
    -------
    bool
        ``True`` if a new token was generated; ``False`` if the account is
        already verified (no new token issued).
    """
    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.get(pk=user_id)

    if user.email_verified:  # type: ignore[attr-defined]
        return False

    # Generate a new token (invalidates existing pending tokens internally).
    generate_email_verification_token(user_id)
    return True


def is_email_verified(user_id: int) -> bool:
    """Return ``True`` when the user's email address has been verified.

    Parameters
    ----------
    user_id:
        Primary key of the user to check.

    Returns
    -------
    bool
        ``True`` if the ``email_verified`` flag is set on the user record.
    """
    UserModel = get_user_model()  # noqa: N806
    return bool(
        UserModel.objects.filter(pk=user_id, email_verified=True).exists()  # type: ignore[attr-defined]
    )
