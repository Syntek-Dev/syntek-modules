"""TOTP MFA service for ``syntek-auth`` — US009.

Handles TOTP secret generation, provisioning URI construction, OTP verification,
and backup code management.

TOTP implementation follows RFC 6238 (TOTP) and RFC 4226 (HOTP) using Python's
standard library ``hmac`` and ``hashlib`` modules.  No third-party library is
required for the core algorithm.  The provisioning URI follows the ``otpauth://``
format recognised by all major authenticator apps.

Backup codes are generated as 8-character alphanumeric strings, hashed with
Django's password hasher (Argon2id when configured), and stored in the
``BackupCode`` model.  Plaintext codes are returned only at setup time and
never stored.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
import urllib.parse
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: TOTP time step in seconds (RFC 6238 default).
_TOTP_STEP_SECONDS: int = 30

#: TOTP code length (RFC 6238 default).
_TOTP_DIGITS: int = 6

#: Number of time steps to accept on either side of the current window.
#: A value of 1 allows ±30 seconds of clock drift.
_TOTP_WINDOW: int = 1

#: Number of bytes in the generated TOTP secret (160-bit).
_SECRET_BYTES: int = 20

#: Length of each backup code in characters (alphanumeric).
_BACKUP_CODE_LENGTH: int = 8


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TotpSetupData:
    """Data returned when TOTP is enabled for a user.

    Attributes
    ----------
    provisioning_uri:
        The ``otpauth://totp/...`` URI used to populate a QR code in an
        authenticator app.
    backup_codes:
        Plaintext single-use backup codes.  Shown once at setup and never
        stored; the caller must present these to the user immediately.
    """

    provisioning_uri: str
    backup_codes: list[str]


# ---------------------------------------------------------------------------
# RFC 6238 TOTP implementation (pure stdlib)
# ---------------------------------------------------------------------------


def _hotp(key_bytes: bytes, counter: int) -> int:
    """Compute an HOTP value for the given key and counter.

    Implements RFC 4226 §5.3.

    Parameters
    ----------
    key_bytes:
        The decoded TOTP secret bytes.
    counter:
        The moving counter value.

    Returns
    -------
    int
        The raw HOTP integer (truncated to the configured digit count).
    """
    msg = struct.pack(">Q", counter)
    h = hmac.new(key_bytes, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF
    return code % (10**_TOTP_DIGITS)


def _totp_at(key_bytes: bytes, timestamp: int) -> str:
    """Compute the TOTP code for the given timestamp.

    Parameters
    ----------
    key_bytes:
        The decoded TOTP secret bytes.
    timestamp:
        Unix timestamp in seconds.

    Returns
    -------
    str
        Zero-padded ``_TOTP_DIGITS``-digit TOTP code.
    """
    counter = timestamp // _TOTP_STEP_SECONDS
    return str(_hotp(key_bytes, counter)).zfill(_TOTP_DIGITS)


def generate_totp_secret() -> str:
    """Generate a cryptographically random TOTP secret.

    Returns a base32-encoded string suitable for storage and for use in
    ``otpauth://`` URIs.

    Returns
    -------
    str
        A base32-encoded 160-bit (20-byte) TOTP secret without padding.
    """
    return base64.b32encode(os.urandom(_SECRET_BYTES)).decode("ascii").rstrip("=")


def build_provisioning_uri(secret: str, account_name: str, issuer: str) -> str:
    """Construct an ``otpauth://totp/`` provisioning URI.

    The URI is compatible with all RFC 6238 authenticator apps (Google
    Authenticator, Aegis, etc.).

    Parameters
    ----------
    secret:
        The base32-encoded TOTP secret (without padding).
    account_name:
        The user-facing label shown in the authenticator app (typically
        the user's email address).
    issuer:
        The application or organisation name shown in the authenticator app.

    Returns
    -------
    str
        A complete ``otpauth://totp/...`` URI string.
    """
    label = urllib.parse.quote(f"{issuer}:{account_name}", safe="")
    params = urllib.parse.urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": str(_TOTP_DIGITS),
            "period": str(_TOTP_STEP_SECONDS),
        }
    )
    return f"otpauth://totp/{label}?{params}"


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a user-supplied TOTP code against the stored secret.

    Accepts codes within ``_TOTP_WINDOW`` time steps of the current step
    to tolerate minor clock drift.

    Parameters
    ----------
    secret:
        The base32-encoded TOTP secret stored for this user.
    code:
        The 6-digit code submitted by the user.

    Returns
    -------
    bool
        ``True`` if the code matches within the accepted window.
    """
    code_clean = code.strip()
    if not code_clean.isdigit() or len(code_clean) != _TOTP_DIGITS:
        return False

    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    try:
        key_bytes = base64.b32decode(padded, casefold=True)
    except Exception:
        return False

    now = int(time.time())
    for delta in range(-_TOTP_WINDOW, _TOTP_WINDOW + 1):
        expected = _totp_at(key_bytes, now + delta * _TOTP_STEP_SECONDS)
        if hmac.compare_digest(expected, code_clean):
            return True

    return False


# ---------------------------------------------------------------------------
# Backup code management
# ---------------------------------------------------------------------------


def generate_backup_codes(count: int) -> list[str]:
    """Generate ``count`` single-use backup codes.

    Each code is an 8-character alphanumeric string generated using
    ``secrets.choice`` for cryptographic quality.

    Parameters
    ----------
    count:
        Number of backup codes to generate (``MFA_BACKUP_CODES_COUNT``).

    Returns
    -------
    list[str]
        Plaintext backup codes.  Must be displayed to the user exactly once.
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return [
        "".join(secrets.choice(alphabet) for _ in range(_BACKUP_CODE_LENGTH))
        for _ in range(count)
    ]


def store_backup_codes(user_id: int, codes: list[str]) -> None:
    """Hash and store ``codes`` in the ``BackupCode`` table.

    Existing backup codes for the user are deleted before the new codes are
    inserted.  Each code is hashed via Django's password hasher (``make_password``)
    so that no plaintext is stored.

    Parameters
    ----------
    user_id:
        Primary key of the user whose backup codes are being stored.
    codes:
        Plaintext backup codes to hash and persist.
    """
    from django.conf import settings as _settings
    from django.contrib.auth.hashers import make_password

    from syntek_auth.models.tokens import BackupCode

    _cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    _raw_key = _cfg.get("FIELD_KEY", "")
    _field_key: bytes = (
        _raw_key.encode("utf-8") if isinstance(_raw_key, str) else bytes(_raw_key)
    )
    try:
        from syntek_pyo3 import encrypt_field  # type: ignore[import-not-found]

        def _hash_and_encrypt(plaintext_code: str) -> str:
            return encrypt_field(
                make_password(plaintext_code), _field_key, "BackupCode", "code_hash"
            )

    except ImportError:

        def _hash_and_encrypt(plaintext_code: str) -> str:  # type: ignore[misc]
            return make_password(plaintext_code)

    # Clear old codes first.
    BackupCode.objects.filter(user_id=user_id).delete()

    BackupCode.objects.bulk_create(
        [
            BackupCode(user_id=user_id, code_hash=_hash_and_encrypt(code))
            for code in codes
        ]
    )


def consume_backup_code(user_id: int, code: str) -> bool:
    """Attempt to consume a backup code for the given user.

    Iterates over the user's stored ``BackupCode`` rows, verifying the
    supplied code against each hash.  On a match the row is deleted
    (single-use guarantee) and ``True`` is returned.  ``False`` is returned
    when no match is found.

    Parameters
    ----------
    user_id:
        Primary key of the user attempting to use a backup code.
    code:
        The plaintext backup code submitted by the user.

    Returns
    -------
    bool
        ``True`` if the code matched and was consumed; ``False`` otherwise.
    """
    import contextlib

    from django.conf import settings as _settings
    from django.contrib.auth.hashers import check_password

    from syntek_auth.models.tokens import BackupCode

    _cfg: dict = getattr(_settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    _raw_key = _cfg.get("FIELD_KEY", "")
    _field_key: bytes = (
        _raw_key.encode("utf-8") if isinstance(_raw_key, str) else bytes(_raw_key)
    )

    for backup in BackupCode.objects.filter(user_id=user_id):
        stored_hash = backup.code_hash
        # Decrypt the stored ciphertext to retrieve the Argon2id hash.
        with contextlib.suppress(Exception):
            from syntek_pyo3 import decrypt_field  # type: ignore[import-not-found]

            stored_hash = decrypt_field(
                stored_hash, _field_key, "BackupCode", "code_hash"
            )

        if check_password(code, stored_hash):
            backup.delete()
            return True

    return False


# ---------------------------------------------------------------------------
# TOTP setup and user model helpers
# ---------------------------------------------------------------------------


def enable_totp_for_user(
    user_id: int,
    issuer: str,
    backup_codes_count: int,
) -> TotpSetupData:
    """Enable TOTP for a user and return setup data.

    Generates a new TOTP secret, stores it on the user model (via the
    ``totp_secret`` attribute if present), generates and stores backup codes,
    and returns the provisioning URI and plaintext backup codes.

    When the user model does not have a ``totp_secret`` attribute (i.e. the
    field has not yet been added to the model), the secret is returned but
    not persisted.  This allows the mutation layer to operate without a
    migration dependency.

    Parameters
    ----------
    user_id:
        Primary key of the user enabling TOTP.
    issuer:
        The application name shown in the authenticator app.
    backup_codes_count:
        Number of backup codes to generate (``MFA_BACKUP_CODES_COUNT``).

    Returns
    -------
    TotpSetupData
        Provisioning URI and plaintext backup codes.
    """
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()  # noqa: N806
    user = UserModel.objects.get(pk=user_id)

    secret = generate_totp_secret()

    # Persist on the model only when the field exists.
    if hasattr(user, "totp_secret"):
        user.totp_secret = secret  # type: ignore[attr-defined]
        user.save(update_fields=["totp_secret"])

    account_name: str = getattr(user, "email", str(user_id))
    provisioning_uri = build_provisioning_uri(secret, account_name, issuer)

    codes = generate_backup_codes(backup_codes_count)
    store_backup_codes(user_id, codes)

    return TotpSetupData(provisioning_uri=provisioning_uri, backup_codes=codes)
