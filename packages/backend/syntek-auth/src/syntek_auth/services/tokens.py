"""JWT token management for ``syntek-auth`` — US009.

Handles access token issuance, refresh token rotation, and validation.

Tokens are HS256 JWTs signed with a per-process generated secret key.
The refresh token store is an in-process dict (suitable for testing and
single-process deployments).  Production deployments should replace the
revocation store with a shared cache (e.g. Valkey/Redis) by overriding
``_REVOKED_TOKENS``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

from syntek_auth.services.lookup_tokens import make_jti_token

# ---------------------------------------------------------------------------
# Module-level signing secret — generated once per process.
# Tests rely on this being consistent within a test run.
# ---------------------------------------------------------------------------

_SIGNING_SECRET: bytes = secrets.token_bytes(32)

# ---------------------------------------------------------------------------
# In-process revocation store: maps refresh token JTI → True when revoked.
# ---------------------------------------------------------------------------

_REVOKED_TOKENS: dict[str, bool] = {}


@dataclass(frozen=True)
class TokenPair:
    """An access + refresh token pair.

    Attributes
    ----------
    access_token:
        Short-lived JWT access token (HS256).
    refresh_token:
        Long-lived JWT refresh token (HS256).
    """

    access_token: str
    refresh_token: str


# ---------------------------------------------------------------------------
# Internal JWT helpers
# ---------------------------------------------------------------------------


def _b64url_encode(data: bytes) -> str:
    """Return URL-safe base64 encoding of ``data`` without padding characters."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Decode a URL-safe base64 string, adding padding as required."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _make_jwt(payload: dict, secret: bytes) -> str:  # type: ignore[type-arg]
    """Encode ``payload`` as an HS256 JWT signed with ``secret``.

    Parameters
    ----------
    payload:
        The claims dict to encode.
    secret:
        HMAC-SHA256 signing secret.

    Returns
    -------
    str
        The compact JWT string (header.payload.signature).
    """
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header}.{body}"
    sig = hmac.new(secret, signing_input.encode(), hashlib.sha256).digest()
    signature = _b64url_encode(sig)
    return f"{signing_input}.{signature}"


def _decode_jwt(token: str, secret: bytes) -> dict:  # type: ignore[type-arg]
    """Verify and decode a JWT produced by :func:`_make_jwt`.

    Parameters
    ----------
    token:
        The compact JWT string to validate.
    secret:
        HMAC-SHA256 signing secret — must match the key used to sign.

    Returns
    -------
    dict
        The decoded payload.

    Raises
    ------
    ValueError
        If the token is malformed, the signature is invalid, or the token has
        expired.
    """
    if not token:
        raise ValueError("Token must not be empty.")

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid JWT structure — expected 3 parts, got {len(parts)}.")

    header_b64, body_b64, sig_b64 = parts

    # Verify signature
    signing_input = f"{header_b64}.{body_b64}"
    expected_sig = _b64url_encode(
        hmac.new(secret, signing_input.encode(), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected_sig, sig_b64):
        raise ValueError(
            "JWT signature verification failed — token has been tampered with."
        )

    # Decode payload
    try:
        payload: dict = json.loads(_b64url_decode(body_b64).decode("utf-8"))  # type: ignore[type-arg]
    except Exception as exc:
        raise ValueError(f"JWT payload is not valid JSON: {exc}") from exc

    # Validate expiry
    exp = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise ValueError("JWT has expired.")

    return payload


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def issue_token_pair(
    user_id: int,
    access_lifetime_seconds: int,
    refresh_lifetime_seconds: int,
) -> TokenPair:
    """Issue a new access + refresh token pair for ``user_id``.

    Both tokens are HS256 JWTs.  The refresh token carries a unique ``jti``
    claim that is used to detect reuse after rotation.

    Parameters
    ----------
    user_id:
        Primary key of the authenticated user.
    access_lifetime_seconds:
        Lifetime of the access token in seconds.
    refresh_lifetime_seconds:
        Lifetime of the refresh token in seconds.

    Returns
    -------
    TokenPair
        The newly issued token pair.
    """
    now = time.time()

    access_payload: dict = {  # type: ignore[type-arg]
        "sub": user_id,
        "iat": now,
        "exp": now + access_lifetime_seconds,
        "typ": "access",
        "jti": secrets.token_hex(16),
    }

    refresh_payload: dict = {  # type: ignore[type-arg]
        "sub": user_id,
        "iat": now,
        "exp": now + refresh_lifetime_seconds,
        "typ": "refresh",
        "jti": secrets.token_hex(16),
    }

    return TokenPair(
        access_token=_make_jwt(access_payload, _SIGNING_SECRET),
        refresh_token=_make_jwt(refresh_payload, _SIGNING_SECRET),
    )


def rotate_refresh_token(
    refresh_token: str,
    access_lifetime_seconds: int,
    refresh_lifetime_seconds: int,
) -> TokenPair:
    """Consume ``refresh_token`` and issue a new token pair.

    The old refresh token's ``jti`` is added to the revocation store
    immediately.  A subsequent call with the same token raises ``ValueError``.

    Parameters
    ----------
    refresh_token:
        The refresh token submitted by the client.
    access_lifetime_seconds:
        Lifetime of the new access token in seconds.
    refresh_lifetime_seconds:
        Lifetime of the new refresh token in seconds.

    Returns
    -------
    TokenPair
        A new access + refresh token pair.

    Raises
    ------
    ValueError
        If the supplied refresh token is invalid, expired, or already revoked.
    """
    try:
        payload = _decode_jwt(refresh_token, _SIGNING_SECRET)
    except ValueError as exc:
        raise ValueError(f"Invalid refresh token: {exc}") from exc

    jti = payload.get("jti")
    if not jti:
        raise ValueError("Refresh token is missing the required 'jti' claim.")

    if _REVOKED_TOKENS.get(make_jti_token(jti)):
        raise ValueError("Refresh token has already been revoked (reuse detected).")

    # Revoke the consumed token before issuing the new pair
    _REVOKED_TOKENS[make_jti_token(jti)] = True

    return issue_token_pair(
        user_id=payload["sub"],
        access_lifetime_seconds=access_lifetime_seconds,
        refresh_lifetime_seconds=refresh_lifetime_seconds,
    )


def revoke_refresh_token(refresh_token: str) -> bool:
    """Revoke a refresh token by its JTI.

    Decodes the token to extract the ``jti`` claim and marks it as revoked
    in the in-process revocation store.  Does not raise on invalid input —
    returns ``False`` instead so that callers can treat an invalid logout
    token gracefully.

    Parameters
    ----------
    refresh_token:
        The refresh token string submitted by the client.

    Returns
    -------
    bool
        ``True`` if the token was successfully revoked, ``False`` if the token
        is malformed, has no ``jti`` claim, or cannot be decoded.
    """
    try:
        payload = _decode_jwt(refresh_token, _SIGNING_SECRET)
    except ValueError:
        return False
    jti = payload.get("jti")
    if not jti:
        return False
    _REVOKED_TOKENS[make_jti_token(jti)] = True
    return True


def validate_access_token(token: str) -> dict:  # type: ignore[type-arg]
    """Validate ``token`` and return the decoded payload.

    Parameters
    ----------
    token:
        A JWT access token string.

    Returns
    -------
    dict
        The decoded payload (e.g. ``{'sub': 1, 'exp': ...}``).

    Raises
    ------
    ValueError
        If the token is invalid, expired, or has been tampered with.
    """
    try:
        return _decode_jwt(token, _SIGNING_SECRET)
    except ValueError:
        raise
