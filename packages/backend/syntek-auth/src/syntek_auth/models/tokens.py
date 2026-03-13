"""Token models for ``syntek-auth`` — US009.

Defines ``RefreshToken`` and ``BackupCode`` as concrete Django models.

``RefreshToken`` tracks long-lived refresh tokens by JTI (JWT Token ID).
The ``jti`` column is stored as AES-256-GCM ciphertext; the companion
``jti_token`` column holds a deterministic HMAC-SHA256 of the JTI for
fast, unique indexed lookups.

``BackupCode`` stores a single-use MFA recovery code as an Argon2id hash,
encrypted at rest via ``EncryptedField``.  The plaintext code is never
stored — only the hash, then the hash is encrypted.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from syntek_auth.models.user import EncryptedField


class RefreshToken(models.Model):
    """Persisted refresh token record keyed by JTI.

    Attributes
    ----------
    user:
        Foreign key to the owning user.  Cascades on delete so that all tokens
        are removed when a user account is deleted.
    jti:
        AES-256-GCM ciphertext of the JWT Token ID claim from the refresh
        token.  Never query this column directly — use ``jti_token`` instead.
    jti_token:
        HMAC-SHA256 of the plaintext JTI.  Unique and indexed for fast
        revocation lookups.
    created_at:
        Timestamp set automatically when the row is first inserted.
    expires_at:
        Absolute expiry time for the refresh token.  Expired rows may be
        pruned by a background task.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    jti = EncryptedField(
        verbose_name="JTI",
        help_text="AES-256-GCM ciphertext of the JWT Token ID.",
    )
    jti_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="JTI lookup token",
        help_text=(
            "HMAC-SHA256 of the plaintext JTI.  "
            "Use this column for lookups — never filter on the ciphertext."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "syntek_auth_refresh_token"

    def __str__(self) -> str:
        """Return a human-readable representation of the refresh token record."""
        return f"RefreshToken(jti_token={self.jti_token!r})"


class BackupCode(models.Model):
    """Single-use MFA backup code stored as an encrypted Argon2id hash.

    Attributes
    ----------
    user:
        Foreign key to the owning user.  Cascades on delete so that all codes
        are removed when a user account is deleted.
    code_hash:
        AES-256-GCM ciphertext of the Argon2id hash of the plaintext backup
        code.  No plaintext is ever stored — only the hash, which is then
        encrypted at rest.
    created_at:
        Timestamp set automatically when the row is first inserted.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="backup_codes",
    )
    code_hash = EncryptedField(
        verbose_name="code hash",
        help_text="AES-256-GCM ciphertext of the Argon2id hash of the backup code.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "syntek_auth_backup_code"

    def __str__(self) -> str:
        """Return a human-readable representation of the backup code record."""
        return f"BackupCode(user_id={self.user_id!r})"  # type: ignore[attr-defined]
