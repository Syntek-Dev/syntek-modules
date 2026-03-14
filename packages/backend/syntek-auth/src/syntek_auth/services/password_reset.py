"""Password reset (forgot password) service for ``syntek-auth`` — US009.

Handles account-enumeration-safe reset requests, single-use token generation
(default TTL from ``PASSWORD_RESET_TOKEN_TTL``, falling back to 3600 seconds),
password history checking, and refresh token invalidation on successful reset.

Anti-enumeration: ``request_password_reset`` always returns ``True``
regardless of whether the supplied email matches an account.  When the
account exists and is verified, a reset token is created.  The caller is
responsible for delivering the token (e.g. via an email dispatch signal).
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
        from syntek_pyo3 import KeyRing, encrypt_field  # type: ignore[import-not-found]

        _ring = KeyRing()
        _ring.add(1, field_key)
        return encrypt_field(plaintext, _ring, "VerificationCode", "token")
    except ImportError:
        return plaintext


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

#: Default password reset token TTL in seconds (1 hour).
_DEFAULT_RESET_TTL_SECONDS: int = 3600

#: Maximum attempts to generate a unique reset token.
_MAX_TOKEN_ATTEMPTS: int = 3


@dataclass(frozen=True)
class PasswordResetResult:
    """Result returned by ``confirm_password_reset``.

    Attributes
    ----------
    success:
        ``True`` when the password was successfully changed.
    error_code:
        Machine-readable error identifier when ``success=False``.
        One of: ``'token_expired'``, ``'token_already_used'``,
        ``'token_invalid'``, ``'password_in_history'``.
    message:
        Human-readable description of the outcome.
    """

    success: bool
    error_code: str | None = None
    message: str = ""


def _generate_unique_reset_token() -> str:
    """Generate a URL-safe cryptographically random reset token.

    Retries on unique-constraint collision.

    Returns
    -------
    str
        A unique URL-safe token string (approximately 43 characters).

    Raises
    ------
    RuntimeError
        If a unique token cannot be generated after the allowed attempts.
    """
    from syntek_auth.models.verification import VerificationCode

    for _ in range(_MAX_TOKEN_ATTEMPTS):
        token = secrets.token_urlsafe(32)
        if not VerificationCode.objects.filter(
            token_token=make_token_token(token)
        ).exists():
            return token
    raise RuntimeError(
        f"Failed to generate a unique password reset token after "
        f"{_MAX_TOKEN_ATTEMPTS} attempts."
    )


def request_password_reset(email: str) -> bool:
    """Initiate a password-reset flow for the given email address.

    Always returns ``True`` regardless of whether ``email`` matches an
    existing account (anti-enumeration).  When the account exists and is
    verified, a single-use reset token is created.  When the account does
    not exist or is unverified, no token is created and the response is
    identical.

    Parameters
    ----------
    email:
        The email address submitted by the user.

    Returns
    -------
    bool
        Always ``True``.
    """
    UserModel = get_user_model()  # noqa: N806

    try:
        from syntek_auth.services.lookup_tokens import make_email_token

        user = UserModel.objects.get(email_token=make_email_token(email))
    except UserModel.DoesNotExist:
        return True

    # Only create a reset token for verified accounts.
    if not getattr(user, "email_verified", False):
        return True

    generate_password_reset_token(user.pk)
    return True


def generate_password_reset_token(user_id: int) -> str:
    """Generate a single-use password reset token for the given user.

    Reads the TTL from ``SYNTEK_AUTH['PASSWORD_RESET_TOKEN_TTL']`` (default
    3600 seconds).  Invalidates any existing pending reset tokens before
    creating the new one.

    Parameters
    ----------
    user_id:
        Primary key of the user requesting a password reset.

    Returns
    -------
    str
        A URL-safe plaintext token string (approximately 43 characters).
    """
    from django.conf import settings as django_settings

    from syntek_auth.models.verification import VerificationCode

    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.get(pk=user_id)

    cfg: dict = getattr(django_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    ttl_seconds: int = int(
        cfg.get("PASSWORD_RESET_TOKEN_TTL", _DEFAULT_RESET_TTL_SECONDS)
    )

    now = timezone.now()

    # Invalidate existing pending reset tokens for this user.
    VerificationCode.objects.filter(
        user=user,
        code_type=VerificationCode.CodeType.PASSWORD_RESET,
        used_at__isnull=True,
        expires_at__gt=now,
    ).delete()

    token = _generate_unique_reset_token()
    VerificationCode.objects.create(
        user=user,
        code_type=VerificationCode.CodeType.PASSWORD_RESET,
        token=_encrypt_token(token),
        token_token=make_token_token(token),
        expires_at=now + timedelta(seconds=ttl_seconds),
    )
    return token


def confirm_password_reset(
    token: str,
    new_password: str,
    password_policy: dict,  # type: ignore[type-arg]
) -> PasswordResetResult:
    """Apply the password reset for the user identified by ``token``.

    Validates that the token is single-use and unexpired, checks the new
    password against ``password_policy`` and the user's password history,
    persists the new hash, and — when ``PASSWORD_RESET_INVALIDATES_SESSIONS``
    is ``True`` — invalidates all existing refresh tokens.

    Parameters
    ----------
    token:
        The plaintext reset token from the email link.
    new_password:
        The new password supplied by the user.
    password_policy:
        The ``SYNTEK_AUTH`` settings dict (used for history and policy checks).

    Returns
    -------
    PasswordResetResult
        ``success=True`` on success; ``success=False`` with an ``error_code``
        on failure.
    """
    from django.conf import settings as django_settings

    from syntek_auth.models.verification import VerificationCode
    from syntek_auth.services.password import (
        check_password_history,
        validate_password_policy,
    )

    now = timezone.now()

    try:
        code = VerificationCode.objects.select_related("user").get(
            token_token=make_token_token(token),
            code_type=VerificationCode.CodeType.PASSWORD_RESET,
        )
    except VerificationCode.DoesNotExist:
        return PasswordResetResult(
            success=False,
            error_code="token_invalid",
            message="Reset token not found.",
        )

    # Check already-used state.
    if code.used_at is not None:
        return PasswordResetResult(
            success=False,
            error_code="token_already_used",
            message=(
                "This reset token has already been used. "
                "Please request a new password reset."
            ),
        )

    # Check expiry.
    if code.expires_at <= now:
        return PasswordResetResult(
            success=False,
            error_code="token_expired",
            message=(
                "This reset token has expired. Please request a new password reset."
            ),
        )

    user = code.user

    # Validate the new password against policy.
    policy_result = validate_password_policy(new_password, password_policy)
    if not policy_result.valid:
        violation_messages = "; ".join(v.message for v in policy_result.violations)
        return PasswordResetResult(
            success=False,
            error_code="policy_violation",
            message=violation_messages,
        )

    # Check password history.
    history_count: int = int(password_policy.get("PASSWORD_HISTORY", 0))
    if history_count > 0:
        # Collect previous hashes from the PasswordHistory model if available,
        # falling back to the current password hash.
        previous_hashes: list[str] = []
        if hasattr(user, "password") and user.password:
            previous_hashes.append(user.password)

        # Check additional history if the PasswordHistory model is installed.
        try:
            from syntek_auth.models.password_history import (  # type: ignore[import]
                PasswordHistory,
            )

            previous_hashes = list(
                PasswordHistory.objects.filter(user=user)
                .order_by("-created_at")
                .values_list("password_hash", flat=True)
            )
        except ImportError:
            pass

        if check_password_history(new_password, previous_hashes, history_count):
            return PasswordResetResult(
                success=False,
                error_code="password_in_history",
                message=(
                    "The new password matches a recently used password. "
                    "Please choose a different password."
                ),
            )

    # Persist the new password hash.
    user.set_password(new_password)
    user.save(update_fields=["password"])

    # Mark the token as used.
    code.used_at = now
    code.save(update_fields=["used_at"])

    # Optionally invalidate all refresh tokens.
    cfg: dict = getattr(django_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    if cfg.get("PASSWORD_RESET_INVALIDATES_SESSIONS", True):
        invalidate_all_refresh_tokens(user.pk)

    return PasswordResetResult(
        success=True,
        message="Password reset successfully.",
    )


def invalidate_all_refresh_tokens(user_id: int) -> int:
    """Revoke all active refresh tokens belonging to the given user.

    Deletes all ``RefreshToken`` rows for ``user_id`` and removes the
    corresponding JTIs from the in-process revocation store.

    Parameters
    ----------
    user_id:
        Primary key of the user whose sessions are being revoked.

    Returns
    -------
    int
        Number of tokens revoked.
    """
    from syntek_auth.models.tokens import RefreshToken
    from syntek_auth.services.tokens import (
        _REVOKED_TOKENS,  # type: ignore[attr-defined]
    )

    tokens = RefreshToken.objects.filter(user_id=user_id)
    # jti_token values are already the HMAC keys used in _REVOKED_TOKENS.
    jti_tokens = list(tokens.values_list("jti_token", flat=True))
    count, _ = tokens.delete()

    for jti_token in jti_tokens:
        _REVOKED_TOKENS[jti_token] = True

    return count
