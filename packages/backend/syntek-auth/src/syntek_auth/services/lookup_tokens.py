"""HMAC-SHA256 lookup token helpers for encrypted unique fields — syntek-auth.

Encrypted fields use non-deterministic AES-256-GCM, so the ciphertext itself
cannot carry a DB UNIQUE constraint.  Instead, a deterministic HMAC-SHA256
token of the normalised plaintext is stored in a companion ``*_token`` column
that holds the uniqueness constraint.

Write path:
    service layer  →  ``encrypt_field(plaintext)``  →  save ciphertext
    service layer  →  ``make_*_token(plaintext)``   →  save token

Read path (lookup):
    ``filter(email_token=make_email_token(identifier))``  →  DB row

All token functions require ``SYNTEK_AUTH['FIELD_HMAC_KEY']`` to be present
in Django settings.  The key must be at least 32 bytes (256 bits) and read
from an environment variable — never hardcoded.
"""

from __future__ import annotations

import hashlib
import hmac as _hmac

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _hmac_key() -> bytes:
    """Return the HMAC key from ``SYNTEK_AUTH['FIELD_HMAC_KEY']``.

    Raises
    ------
    ImproperlyConfigured
        If the key is absent or empty.
    """
    cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    key = cfg.get("FIELD_HMAC_KEY")
    if not key:
        raise ImproperlyConfigured(
            "SYNTEK_AUTH['FIELD_HMAC_KEY'] must be set for encrypted field "
            "lookup token generation.  Set it to a cryptographically random "
            "value of at least 32 bytes read from an environment variable."
        )
    return key.encode("utf-8") if isinstance(key, str) else bytes(key)


def make_email_token(email: str) -> str:
    """Return the HMAC-SHA256 lookup token for ``email``.

    Strips whitespace and lowercases the address before hashing so that
    lookups are case-insensitive and tolerant of surrounding spaces.

    Parameters
    ----------
    email:
        The plaintext email address.

    Returns
    -------
    str
        A 64-character hex string (SHA-256 digest).
    """
    normalised = email.strip().lower()
    return _hmac.new(
        _hmac_key(), normalised.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def make_phone_token(phone: str) -> str:
    """Return the HMAC-SHA256 lookup token for ``phone``.

    Strips whitespace only — phone numbers are stored and compared as-supplied
    (no normalisation beyond stripping).

    Parameters
    ----------
    phone:
        The plaintext phone number.

    Returns
    -------
    str
        A 64-character hex string (SHA-256 digest).
    """
    normalised = phone.strip()
    return _hmac.new(
        _hmac_key(), normalised.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def make_jti_token(jti: str) -> str:
    """Return the HMAC-SHA256 lookup token for a JWT Token ID (``jti``).

    Strips surrounding whitespace only — JTI values are case-sensitive hex
    strings and must not be lowercased.

    Parameters
    ----------
    jti:
        The plaintext JWT Token ID claim (``jti``).

    Returns
    -------
    str
        A 64-character hex string (SHA-256 digest).
    """
    normalised = jti.strip()
    return _hmac.new(
        _hmac_key(), normalised.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def make_token_token(token: str) -> str:
    """Return the HMAC-SHA256 lookup token for a ``VerificationCode.token``.

    Strips surrounding whitespace only — verification tokens are case-sensitive
    URL-safe base64 or uppercase hex strings and must not be lowercased.

    Parameters
    ----------
    token:
        The plaintext verification token.

    Returns
    -------
    str
        A 64-character hex string (SHA-256 digest).
    """
    normalised = token.strip()
    return _hmac.new(
        _hmac_key(), normalised.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def make_provider_token(provider: str) -> str:
    """Return the HMAC-SHA256 lookup token for ``provider``.

    Normalises to lowercase and strips whitespace before hashing so that
    lookups are case-insensitive (``'Google'`` and ``'google'`` produce the
    same token).

    Parameters
    ----------
    provider:
        The plaintext OAuth provider identifier (e.g. ``'google'``).

    Returns
    -------
    str
        A 64-character hex string (SHA-256 digest).
    """
    normalised = provider.strip().lower()
    return _hmac.new(
        _hmac_key(), normalised.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def make_username_token(username: str, *, case_sensitive: bool = False) -> str:
    """Return the HMAC-SHA256 lookup token for ``username``.

    When ``case_sensitive`` is ``False`` (the default) the username is
    lowercased before hashing, matching ``USERNAME_CASE_SENSITIVE = False``
    in ``SYNTEK_AUTH`` settings.

    Parameters
    ----------
    username:
        The plaintext username.
    case_sensitive:
        When ``True``, the token is computed from the username as-supplied
        (only stripped of surrounding whitespace).

    Returns
    -------
    str
        A 64-character hex string (SHA-256 digest).
    """
    normalised = username.strip() if case_sensitive else username.strip().lower()
    return _hmac.new(
        _hmac_key(), normalised.encode("utf-8"), hashlib.sha256
    ).hexdigest()
