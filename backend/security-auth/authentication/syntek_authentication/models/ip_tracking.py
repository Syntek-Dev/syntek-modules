"""IP tracking model for security monitoring.

Tracks user login IP addresses with geolocation data.
Implements encryption for PII compliance and table partitioning for performance.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class IPTracking(models.Model):
    """IP address tracking for security monitoring and analytics.

    Tracks login IP addresses with encrypted geolocation data.
    Uses table partitioning (monthly) for performance at scale.

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        ip_address_encrypted: Binary field containing encrypted IP
        ip_hash: HMAC-SHA256 hash for constant-time lookups
        location_data_encrypted: JSONB field with encrypted city/country
        user_agent: User agent string (truncated to 500 chars)
        created_at: Tracking timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ip_tracking_entries",
    )

    # IP address storage (encrypted + hashed)
    ip_address_encrypted = models.BinaryField(help_text="Encrypted IP address (ChaCha20-Poly1305)")
    ip_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="HMAC-SHA256 hash for lookups",
    )

    # Geolocation data (encrypted JSONB: {city, country, region})
    location_data_encrypted = models.BinaryField(
        null=True,
        blank=True,
        help_text="Encrypted JSON with geolocation data",
    )

    # User agent tracking
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Browser/device user agent",
    )

    # Timestamp (partition key for monthly partitioning)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "auth_ip_tracking"
        verbose_name = "IP Tracking Entry"
        verbose_name_plural = "IP Tracking Entries"
        indexes = [
            # Performance indexes for common queries
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["ip_hash", "created_at"]),
            models.Index(fields=["created_at"]),  # For partitioning
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"IP tracking for {self.user} at {self.created_at}"

    @classmethod
    def get_recent_ips_for_user(cls, user, days: int = 30) -> models.QuerySet:
        """Get recent IP tracking entries for user.

        Args:
            user: User instance
            days: Number of days to look back (default: 30)

        Returns:
            QuerySet of IPTracking instances
        """
        from datetime import timedelta

        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            user=user,
            created_at__gte=cutoff_date,
        ).order_by("-created_at")


class IPWhitelist(models.Model):
    """IP whitelist for trusted addresses.

    Allows certain IP addresses to bypass certain security checks
    (e.g., skip CAPTCHA, extended session timeout).

    Attributes:
        id: UUID primary key
        user: Foreign key to User model (null for global whitelist)
        ip_address_encrypted: Binary field containing encrypted IP
        ip_hash: HMAC-SHA256 hash for constant-time lookups
        reason: Explanation for whitelisting
        created_at: Whitelist entry creation timestamp
        created_by: Admin user who created entry
        expires_at: Optional expiry timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ip_whitelist_entries",
        help_text="User-specific whitelist (null for global)",
    )

    # IP address storage (encrypted + hashed)
    ip_address_encrypted = models.BinaryField(help_text="Encrypted IP address (ChaCha20-Poly1305)")
    ip_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="HMAC-SHA256 hash for lookups",
    )

    # Metadata
    reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for whitelisting this IP",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_ip_whitelists",
        help_text="Admin who created this whitelist entry",
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional expiry date for temporary whitelist",
    )

    class Meta:
        db_table = "auth_ip_whitelist"
        verbose_name = "IP Whitelist Entry"
        verbose_name_plural = "IP Whitelist Entries"
        indexes = [
            models.Index(fields=["user", "ip_hash"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        user_str = self.user or "Global"
        return f"IP whitelist for {user_str}"

    def is_expired(self) -> bool:
        """Check if whitelist entry has expired.

        Returns:
            bool: True if expires_at is set and past
        """
        if not self.expires_at:
            return False
        from django.utils import timezone

        return timezone.now() > self.expires_at


class IPBlacklist(models.Model):
    """IP blacklist for blocked addresses.

    Blocks IP addresses that exhibit suspicious behaviour or are
    associated with attacks (brute force, credential stuffing, etc.).

    Attributes:
        id: UUID primary key
        ip_hash: HMAC-SHA256 hash for constant-time lookups
        reason: Reason for blacklisting
        created_at: Blacklist entry creation timestamp
        expires_at: Expiry timestamp (for temporary blocks)
        permanent: Boolean flag for permanent bans
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # IP hash only (no storage of actual IP for blacklist)
    ip_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="HMAC-SHA256 hash of blocked IP",
    )

    # Metadata
    reason = models.TextField(
        help_text="Reason for blacklisting (e.g., brute force attempt)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Expiry date for temporary blocks",
    )

    permanent = models.BooleanField(
        default=False,
        help_text="Permanent ban (never expires)",
    )

    class Meta:
        db_table = "auth_ip_blacklist"
        verbose_name = "IP Blacklist Entry"
        verbose_name_plural = "IP Blacklist Entries"
        indexes = [
            models.Index(fields=["ip_hash", "expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        status = "permanent" if self.permanent else "temporary"
        return f"IP blacklist ({status})"

    def is_active(self) -> bool:
        """Check if blacklist entry is currently active.

        Returns:
            bool: True if permanent or not yet expired
        """
        if self.permanent:
            return True
        if not self.expires_at:
            return True
        from django.utils import timezone

        return timezone.now() <= self.expires_at
