"""Phone verification token model.

Handles phone number verification via SMS codes.
Implements OWASP security practices for token generation and storage.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class PhoneVerificationToken(models.Model):
    """Phone verification token for SMS-based verification.

    Stores verification codes sent via SMS for phone number verification.
    Uses cryptographically secure token generation and automatic expiry.

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        phone_number_encrypted: Binary field containing encrypted phone number
        phone_hash: HMAC-SHA256 hash for constant-time lookups
        code: 6-digit verification code (plain text for SMS sending)
        code_hash: HMAC-SHA256 hash of code for database verification
        created_at: Token creation timestamp
        expires_at: Token expiry timestamp (default: 15 minutes)
        used_at: Timestamp when token was successfully used
        attempts: Number of verification attempts (max 5)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="phone_verification_tokens",
    )

    # Phone number storage (encrypted + hashed for lookup)
    phone_number_encrypted = models.BinaryField(
        help_text="Encrypted phone number (ChaCha20-Poly1305)"
    )
    phone_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="HMAC-SHA256 hash for constant-time lookups",
    )

    # Verification code (6-digit numeric)
    code = models.CharField(
        max_length=10,
        help_text="Plain text code for SMS sending (short-lived)",
    )
    code_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="HMAC-SHA256 hash of code for verification",
    )

    # Timestamps and expiry
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    # Rate limiting and security
    attempts = models.IntegerField(
        default=0,
        help_text="Number of verification attempts (max 5)",
    )

    class Meta:
        db_table = "auth_phone_verification_token"
        verbose_name = "Phone Verification Token"
        verbose_name_plural = "Phone Verification Tokens"
        indexes = [
            models.Index(fields=["phone_hash", "used_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"Phone verification for {self.user} - {self.created_at}"

    def save(self, *args, **kwargs):
        """Save with auto-calculated expiry.

        Sets expires_at to 15 minutes from creation if not set.
        """
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        """Check if token has expired.

        Returns:
            bool: True if current time > expires_at
        """
        return timezone.now() > self.expires_at

    def is_used(self) -> bool:
        """Check if token has been used.

        Returns:
            bool: True if used_at is set
        """
        return self.used_at is not None

    def is_valid(self) -> bool:
        """Check if token is valid (not expired, not used, attempts < 5).

        Returns:
            bool: True if token can be used for verification
        """
        return not self.is_expired() and not self.is_used() and self.attempts < 5

    def increment_attempts(self) -> None:
        """Increment verification attempts counter.

        Saves the model after incrementing.
        """
        self.attempts += 1
        self.save(update_fields=["attempts"])

    def mark_as_used(self) -> None:
        """Mark token as successfully used.

        Sets used_at to current time and saves.
        """
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
