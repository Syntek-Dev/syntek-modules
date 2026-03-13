"""PendingOAuthSession model for ``syntek-auth`` — US009 / US076.

Stores a short-lived pending session record created when a user authenticates
via a MFA-gated OAuth provider (e.g. Google, Facebook).  The record acts as a
single-use ticket that must be exchanged for a full token pair by completing a
local MFA challenge via ``completeSocialMfa``.

The ``id`` column is a UUID used as the ``pending_token`` value returned to the
client.  The ``provider`` field is stored as AES-256-GCM ciphertext because the
provider identifier in combination with a pending session could reveal
authentication patterns.  The companion ``provider_token`` column holds a
deterministic HMAC-SHA256 token of the normalised provider identifier for
index-based lookups.

Rows are short-lived (default 600 seconds) and should be pruned by a
background task once expired.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from syntek_auth.models.user import EncryptedField


class PendingOAuthSession(models.Model):
    """Short-lived pending OAuth session awaiting local MFA completion.

    Attributes
    ----------
    id:
        UUID primary key.  Returned to the client as ``pending_token``.
    user:
        Foreign key to the authenticated user.  Cascades on delete.
    provider:
        AES-256-GCM ciphertext of the OAuth provider identifier
        (e.g. ``'google'``, ``'facebook'``).  Encrypted because provider
        identity in context of a pending session is sensitive.
    provider_token:
        HMAC-SHA256 of the normalised (lowercase, stripped) provider identifier.
        Used for index-based lookups and filtering — never query ``provider``
        directly as it is non-deterministic ciphertext.
    expires_at:
        Absolute expiry timestamp.  Rows past this time are treated as invalid
        and must be deleted.
    created_at:
        Timestamp set automatically on insertion.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pending_oauth_sessions",
    )
    provider = EncryptedField(
        verbose_name="provider",
        help_text="AES-256-GCM ciphertext of the OAuth provider identifier.",
    )
    provider_token = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="provider lookup token",
        help_text=(
            "HMAC-SHA256 of the normalised provider identifier.  "
            "Use this column for filtering — never filter on the ciphertext."
        ),
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "syntek_auth_pending_oauth_session"
        indexes = [  # noqa: RUF012
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        """Return a human-readable representation of the pending OAuth session."""
        return (
            f"PendingOAuthSession(provider_token={self.provider_token!r}, "
            f"user_id={self.user_id!r})"  # type: ignore[attr-defined]
        )
