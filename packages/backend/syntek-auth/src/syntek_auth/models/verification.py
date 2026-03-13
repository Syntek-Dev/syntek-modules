"""Verification and denylist models for ``syntek-auth`` — US009.

Defines ``VerificationCode`` for email/phone OTP and password-reset tokens,
and ``AccessTokenDenylist`` for short-lived access token invalidation on logout.

``VerificationCode`` stores a cryptographically random single-use token as
AES-256-GCM ciphertext.  The companion ``token_token`` column holds a
deterministic HMAC-SHA256 of the plaintext token and carries the uniqueness
constraint.

``AccessTokenDenylist`` tracks access token JTIs that must be rejected before
their natural expiry.  The ``jti`` column is encrypted; ``jti_token`` carries
the HMAC and uniqueness constraint.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from syntek_auth.models.user import EncryptedField


class VerificationCode(models.Model):
    """Single-use verification code for email, phone, and password-reset flows.

    Attributes
    ----------
    user:
        Foreign key to the owning user.  Cascades on delete.
    code_type:
        Discriminator indicating the purpose of the code.
    token:
        AES-256-GCM ciphertext of the cryptographically random plaintext token.
        Never query this column directly — use ``token_token`` instead.
    token_token:
        HMAC-SHA256 of the plaintext token.  Unique at the DB level and used
        for all token lookups.
    expires_at:
        Absolute expiry timestamp.  Expired codes are treated as invalid
        regardless of the ``used_at`` flag.
    used_at:
        Set when the code is consumed.  ``None`` means the code has not
        yet been used.
    attempt_count:
        Tracks incorrect OTP submissions for brute-force prevention.
        Relevant only for ``phone_verify`` codes.
    created_at:
        Timestamp set automatically on insertion.
    """

    class CodeType(models.TextChoices):
        """Discriminator for the intended use of a ``VerificationCode``."""

        EMAIL_VERIFY = "email_verify", "Email verification"
        PHONE_VERIFY = "phone_verify", "Phone OTP verification"
        PASSWORD_RESET = "password_reset", "Password reset"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_codes",
    )
    code_type = models.CharField(
        max_length=20,
        choices=CodeType.choices,
    )
    token = EncryptedField(
        verbose_name="token",
        help_text="AES-256-GCM ciphertext of the plaintext verification token.",
    )
    token_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="token lookup token",
        help_text=(
            "HMAC-SHA256 of the plaintext verification token.  "
            "Use this column for lookups — never filter on the ciphertext."
        ),
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "syntek_auth_verification_code"
        indexes = [  # noqa: RUF012
            models.Index(
                fields=["user", "code_type", "expires_at"],
                name="syntek_vc_lookup_idx",
            ),
        ]

    def __str__(self) -> str:
        """Return a human-readable representation of the verification code."""
        return (
            f"VerificationCode(type={self.code_type!r}, "
            f"user_id={self.user_id!r})"  # type: ignore[attr-defined]
        )


class AccessTokenDenylist(models.Model):
    """Short-lived denylist entry for invalidated access token JTIs.

    Added on logout so that access tokens cannot be reused until their
    natural expiry.  The ``expires_at`` field allows background pruning of
    stale rows.

    Attributes
    ----------
    jti:
        AES-256-GCM ciphertext of the JWT Token ID claim from the access
        token.  Never query this column directly — use ``jti_token`` instead.
    jti_token:
        HMAC-SHA256 of the plaintext JTI.  Unique and indexed for fast
        denylist lookups.
    expires_at:
        The natural expiry of the original access token.  Rows where
        ``expires_at`` is in the past may be deleted by a background task.
    created_at:
        Timestamp set automatically on insertion.
    """

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
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "syntek_auth_access_token_denylist"

    def __str__(self) -> str:
        """Return a human-readable representation of the denylist entry."""
        return f"AccessTokenDenylist(jti_token={self.jti_token!r})"
