"""Authenticated password change service for ``syntek-auth`` — US009.

Handles current-password verification, policy and history enforcement, and
invalidation of all refresh tokens except the caller's current session.

When ``PASSWORD_CHANGE_INVALIDATES_OTHER_SESSIONS`` is ``True`` (the default),
all refresh tokens except the one identified by ``current_refresh_jti`` are
deleted.  Passing ``current_refresh_jti=None`` revokes all tokens.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model


@dataclass(frozen=True)
class PasswordChangeResult:
    """Result returned by ``change_password``.

    Attributes
    ----------
    success:
        ``True`` when the password was successfully changed.
    error_code:
        Machine-readable error identifier when ``success=False``.
        One of: ``'invalid_credentials'``, ``'password_in_history'``,
        ``'policy_violation'``.
    message:
        Human-readable description of the outcome.
    """

    success: bool
    error_code: str | None = None
    message: str = ""


def verify_current_password(user_id: int, password: str) -> bool:
    """Return ``True`` if ``password`` matches the user's stored hash.

    Uses Django's ``AbstractBaseUser.check_password`` for hash verification.

    Parameters
    ----------
    user_id:
        Primary key of the user.
    password:
        The plaintext password to verify.

    Returns
    -------
    bool
        ``True`` if the password matches the stored hash.
    """
    UserModel = get_user_model()  # noqa: N806
    try:
        user = UserModel.objects.get(pk=user_id)
    except UserModel.DoesNotExist:
        return False
    return bool(user.check_password(password))


def invalidate_other_sessions(user_id: int, keep_jti: str | None) -> int:
    """Revoke all refresh tokens for ``user_id`` except the one matching ``keep_jti``.

    When ``keep_jti`` is ``None``, all tokens are revoked.  Deleted JTIs are
    also added to the in-process revocation store in ``services.tokens`` so
    that in-flight requests with those tokens are rejected immediately.

    Parameters
    ----------
    user_id:
        Primary key of the user.
    keep_jti:
        JTI of the refresh token to preserve.  ``None`` revokes all tokens.

    Returns
    -------
    int
        Number of tokens revoked.
    """
    from syntek_auth.models.tokens import RefreshToken
    from syntek_auth.services.tokens import (
        _REVOKED_TOKENS,  # type: ignore[attr-defined]
    )

    qs = RefreshToken.objects.filter(user_id=user_id)
    if keep_jti is not None:
        qs = qs.exclude(jti=keep_jti)

    jtis = list(qs.values_list("jti", flat=True))
    count, _ = qs.delete()

    for jti in jtis:
        _REVOKED_TOKENS[jti] = True

    return count


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    current_refresh_jti: str | None,
    password_policy: dict,  # type: ignore[type-arg]
) -> PasswordChangeResult:
    """Change the authenticated user's password.

    Verifies the current password, checks the new password against
    ``password_policy`` and the user's stored password history, persists
    the new hash, and invalidates all refresh tokens except the one
    identified by ``current_refresh_jti`` when
    ``PASSWORD_CHANGE_INVALIDATES_OTHER_SESSIONS`` is ``True``.

    Parameters
    ----------
    user_id:
        Primary key of the authenticated user.
    current_password:
        The user's current plaintext password.
    new_password:
        The desired new plaintext password.
    current_refresh_jti:
        JTI of the caller's current refresh token — this session remains
        valid after the change.  ``None`` invalidates all tokens.
    password_policy:
        The ``SYNTEK_AUTH`` settings dict.

    Returns
    -------
    PasswordChangeResult
        ``success=True`` on success; ``success=False`` with an ``error_code``
        on failure.
    """
    from django.conf import settings as django_settings

    from syntek_auth.services.password import (
        check_password_history,
        validate_password_policy,
    )

    # Verify the current password.
    if not verify_current_password(user_id, current_password):
        return PasswordChangeResult(
            success=False,
            error_code="invalid_credentials",
            message="The current password is incorrect.",
        )

    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.get(pk=user_id)

    # Validate the new password against the configured policy.
    policy_result = validate_password_policy(new_password, password_policy)
    if not policy_result.valid:
        violation_messages = "; ".join(v.message for v in policy_result.violations)
        return PasswordChangeResult(
            success=False,
            error_code="policy_violation",
            message=violation_messages,
        )

    # Check password history.
    history_count: int = int(password_policy.get("PASSWORD_HISTORY", 0))
    if history_count > 0:
        previous_hashes: list[str] = []
        if hasattr(user, "password") and user.password:
            previous_hashes.append(user.password)

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
            return PasswordChangeResult(
                success=False,
                error_code="password_in_history",
                message=(
                    "The new password matches a recently used password. "
                    "Please choose a different password."
                ),
            )

    # Persist the new password.
    user.set_password(new_password)
    user.save(update_fields=["password"])

    # Invalidate other sessions when configured.
    cfg: dict = getattr(django_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    if cfg.get("PASSWORD_CHANGE_INVALIDATES_OTHER_SESSIONS", True):
        invalidate_other_sessions(user_id, keep_jti=current_refresh_jti)

    return PasswordChangeResult(
        success=True,
        message="Password changed successfully.",
    )
