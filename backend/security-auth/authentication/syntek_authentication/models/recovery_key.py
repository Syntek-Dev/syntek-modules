"""Recovery key model for account recovery.

Provides account recovery mechanism when MFA is lost or unavailable.
Implements algorithm versioning for cryptographic agility.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class RecoveryKey(models.Model):
    """Recovery key for account access when MFA is unavailable.

    Provides secure account recovery with algorithm versioning,
    expiry management, and usage tracking.

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        key_hash: HMAC-SHA256 hash of recovery key (for verification)
        algorithm_version: Algorithm version identifier (e.g., "argon2id-v1.3")
        algorithm_metadata: JSON field with algorithm parameters
        created_at: Key creation timestamp
        expires_at: Key expiry timestamp (default: 1 year)
        used_at: Timestamp when key was used
        used: Boolean flag for quick lookup
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recovery_keys",
    )

    # Recovery key storage (hashed only, plain key shown once at generation)
    key_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="HMAC-SHA256 hash of recovery key",
    )

    # Algorithm versioning for cryptographic agility
    algorithm_version = models.CharField(
        max_length=50,
        default="hmac-sha256-v1",
        help_text="Algorithm version identifier for future upgrades",
    )

    algorithm_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Algorithm parameters (key length, iterations, etc.)",
    )

    # Timestamps and expiry
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    # Usage tracking
    used = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Quick lookup for used keys (one-time use)",
    )

    class Meta:
        db_table = "auth_recovery_key"
        verbose_name = "Recovery Key"
        verbose_name_plural = "Recovery Keys"
        indexes = [
            models.Index(fields=["user", "used", "created_at"]),
            models.Index(fields=["used", "expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        status = "used" if self.used else "active"
        return f"Recovery key for {self.user} - {status}"

    def save(self, *args, **kwargs):
        """Save with auto-calculated expiry.

        Sets expires_at to 1 year from creation if not set.
        """
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=365)
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        """Check if recovery key has expired.

        Returns:
            bool: True if current time > expires_at
        """
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if recovery key is valid (not expired, not used).

        Returns:
            bool: True if key can be used for account recovery
        """
        return not self.is_expired() and not self.used

    def mark_as_used(self) -> None:
        """Mark recovery key as used (one-time use).

        Sets used=True and used_at timestamp.
        Recovery keys can only be used once for security.
        """
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=["used", "used_at"])

    @classmethod
    def get_active_keys_for_user(cls, user) -> models.QuerySet:
        """Get all valid (unexpired, unused) recovery keys for user.

        Args:
            user: User instance

        Returns:
            QuerySet of valid RecoveryKey instances
        """
        return cls.objects.filter(
            user=user,
            used=False,
            expires_at__gt=timezone.now(),
        ).order_by("-created_at")
