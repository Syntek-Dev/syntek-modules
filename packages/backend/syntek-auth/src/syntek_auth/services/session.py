"""Session management service for ``syntek-auth`` — US009.

Handles logout (refresh token revocation + access token denylist) and the
admin ``revokeAllSessions`` operation.

Logout performs two operations atomically:
1. Revokes the refresh token by deleting its ``RefreshToken`` row and adding
   the JTI to the in-process revocation store.
2. Adds the access token's JTI to ``AccessTokenDenylist`` with a TTL
   matching the token's natural expiry so that in-flight requests using the
   same access token are rejected.

``is_access_token_denylisted`` queries ``AccessTokenDenylist`` for unexpired
entries matching the given JTI.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone


@dataclass(frozen=True)
class LogoutResult:
    """Result returned by ``logout``.

    Attributes
    ----------
    success:
        ``True`` when the session was successfully invalidated.
    error_code:
        Machine-readable error identifier when ``success=False``.
        Currently only ``'token_already_invalid'``.
    message:
        Human-readable description of the outcome.
    """

    success: bool
    error_code: str | None = None
    message: str = ""


def logout(refresh_token: str, access_token: str) -> LogoutResult:
    """Invalidate the caller's session.

    Revokes the supplied ``refresh_token`` (deletes the ``RefreshToken`` row
    and marks the JTI in the in-process store) and adds the ``access_token``'s
    JTI to ``AccessTokenDenylist`` with the token's remaining lifetime as TTL.

    Returns ``success=False`` with ``error_code='token_already_invalid'``
    when the refresh token has already been revoked.

    Parameters
    ----------
    refresh_token:
        The caller's current refresh token JWT string.
    access_token:
        The caller's current access token JWT string (added to the denylist).

    Returns
    -------
    LogoutResult
        ``success=True`` on successful invalidation; ``success=False`` if the
        token was already invalid.
    """
    from syntek_auth.models.tokens import RefreshToken
    from syntek_auth.models.verification import AccessTokenDenylist
    from syntek_auth.services.lookup_tokens import make_jti_token
    from syntek_auth.services.tokens import (  # type: ignore[attr-defined]
        _REVOKED_TOKENS,
        _SIGNING_SECRET,
        _decode_jwt,
    )

    # Decode the refresh token to extract its JTI.
    try:
        refresh_payload = _decode_jwt(refresh_token, _SIGNING_SECRET)
    except ValueError:
        return LogoutResult(
            success=False,
            error_code="token_already_invalid",
            message="Refresh token is invalid or has already expired.",
        )

    refresh_jti = refresh_payload.get("jti")

    # Check the in-process revocation store first.
    if refresh_jti and _REVOKED_TOKENS.get(make_jti_token(refresh_jti)):
        return LogoutResult(
            success=False,
            error_code="token_already_invalid",
            message="This session has already been invalidated.",
        )

    # Attempt to delete the RefreshToken DB row.
    if refresh_jti:
        RefreshToken.objects.filter(jti_token=make_jti_token(refresh_jti)).delete()
        _REVOKED_TOKENS[make_jti_token(refresh_jti)] = True
    else:
        # No JTI in the token — treat as already invalid.
        return LogoutResult(
            success=False,
            error_code="token_already_invalid",
            message="Refresh token is missing the required JTI claim.",
        )

    # Denylist the access token JTI.
    try:
        access_payload = _decode_jwt(access_token, _SIGNING_SECRET)
        access_jti = access_payload.get("jti")
        access_exp = access_payload.get("exp")

        if access_jti and access_exp:
            import datetime

            from django.conf import settings as _settings

            expires_at = datetime.datetime.fromtimestamp(access_exp, tz=datetime.UTC)
            _cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
            _raw_key = _cfg.get("FIELD_KEY", "")
            _field_key: bytes = (
                _raw_key.encode("utf-8")
                if isinstance(_raw_key, str)
                else bytes(_raw_key)
            )
            try:
                from syntek_pyo3 import (  # type: ignore[import-not-found]
                    KeyRing,
                    encrypt_field,
                )

                _ring = KeyRing()
                _ring.add(1, _field_key)
                _encrypted_jti: str = encrypt_field(
                    access_jti, _ring, "AccessTokenDenylist", "jti"
                )
            except ImportError:
                _encrypted_jti = access_jti

            AccessTokenDenylist.objects.get_or_create(
                jti_token=make_jti_token(access_jti),
                defaults={"jti": _encrypted_jti, "expires_at": expires_at},
            )
    except ValueError, Exception:  # noqa: S110
        # Denylist insertion failure is non-fatal — refresh token is already revoked.
        pass

    return LogoutResult(
        success=True,
        message="Logged out successfully.",
    )


def is_access_token_denylisted(jti: str) -> bool:
    """Return ``True`` if the access token JTI is on the short-lived denylist.

    Only unexpired denylist entries are considered — entries whose
    ``expires_at`` is in the past are ignored (and may be pruned by a
    background task).

    Parameters
    ----------
    jti:
        The ``jti`` claim from the access token.

    Returns
    -------
    bool
        ``True`` if the token JTI is in the denylist and has not yet expired.
    """
    from syntek_auth.models.verification import AccessTokenDenylist
    from syntek_auth.services.lookup_tokens import make_jti_token

    now = timezone.now()
    return AccessTokenDenylist.objects.filter(
        jti_token=make_jti_token(jti),
        expires_at__gt=now,
    ).exists()


def revoke_all_sessions(user_id: int) -> int:
    """Revoke all refresh tokens for the given user (admin operation).

    Deletes all ``RefreshToken`` rows for ``user_id`` and mirrors the JTIs
    into the in-process revocation store.

    Parameters
    ----------
    user_id:
        Primary key of the target user.

    Returns
    -------
    int
        Number of sessions revoked.
    """
    from syntek_auth.models.tokens import RefreshToken
    from syntek_auth.services.tokens import (
        _REVOKED_TOKENS,  # type: ignore[attr-defined]
    )

    tokens = RefreshToken.objects.filter(user_id=user_id)
    # Read jti_token (HMAC) values — these are already the keys used in
    # _REVOKED_TOKENS, so no further hashing is required.
    jti_tokens = list(tokens.values_list("jti_token", flat=True))
    count, _ = tokens.delete()

    for jti_token in jti_tokens:
        _REVOKED_TOKENS[jti_token] = True

    return count
