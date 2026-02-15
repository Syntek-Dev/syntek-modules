"""Session security model for hijacking detection.

Tracks session fingerprints, device changes, and suspicious patterns
to detect and prevent session hijacking attacks.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class SessionSecurity(models.Model):
    """Session security tracking for hijacking detection.

    Monitors session fingerprints and detects suspicious changes
    (IP changes, user agent changes, impossible travel, etc.).

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        session_key: Django session key (from django.contrib.sessions)
        device_fingerprint: JSON field with device characteristics
        ip_address_encrypted: Binary field containing encrypted IP
        ip_hash: HMAC-SHA256 hash for constant-time lookups
        user_agent: User agent string
        last_activity_at: Timestamp of last activity
        suspicious_flags: JSON field with detected suspicious patterns
        created_at: Session creation timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="session_security_entries",
    )

    # Session identification
    session_key = models.CharField(
        max_length=40,
        unique=True,
        db_index=True,
        help_text="Django session key",
    )

    # Device fingerprinting
    device_fingerprint = models.JSONField(
        default=dict,
        help_text="Device characteristics (screen, timezone, canvas, etc.)",
    )

    # IP address tracking (encrypted + hashed)
    ip_address_encrypted = models.BinaryField(help_text="Encrypted IP address (ChaCha20-Poly1305)")
    ip_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="HMAC-SHA256 hash for lookups",
    )

    # User agent tracking
    user_agent = models.CharField(
        max_length=500,
        help_text="Browser/device user agent",
    )

    # Activity tracking
    last_activity_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="Last activity timestamp (auto-updated)",
    )

    # Auto-logout configuration
    idle_timeout_seconds = models.IntegerField(
        default=1800,  # 30 minutes
        help_text="Idle timeout in seconds (0 = no timeout)",
    )

    absolute_timeout_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Absolute timeout timestamp (session expires regardless of activity)",
    )

    remember_me = models.BooleanField(
        default=False,
        help_text="Whether 'Remember Me' is enabled (extends idle timeout)",
    )

    auto_logout_warned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When auto-logout warning was shown to user",
    )

    activity_count = models.IntegerField(
        default=0,
        help_text="Number of activity events in this session",
    )

    # Suspicious pattern detection
    suspicious_flags = models.JSONField(
        default=dict,
        help_text="Detected suspicious patterns (ip_change, ua_change, etc.)",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "auth_session_security"
        verbose_name = "Session Security Entry"
        verbose_name_plural = "Session Security Entries"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["session_key"]),
            models.Index(fields=["last_activity_at"]),
            models.Index(fields=["absolute_timeout_at"]),
            models.Index(fields=["last_activity_at", "idle_timeout_seconds"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"Session security for {self.user} - {self.session_key[:8]}"

    def has_suspicious_activity(self) -> bool:
        """Check if session has any suspicious flags.

        Returns:
            bool: True if suspicious_flags is not empty
        """
        return bool(self.suspicious_flags)

    def add_suspicious_flag(self, flag_type: str, details: dict) -> None:
        """Add a suspicious activity flag.

        Args:
            flag_type: Type of suspicious activity (e.g., "ip_change")
            details: Dictionary with additional details
        """
        if not self.suspicious_flags:
            self.suspicious_flags = {}

        self.suspicious_flags[flag_type] = {
            "detected_at": str(models.DateTimeField().auto_now),
            "details": details,
        }
        self.save(update_fields=["suspicious_flags"])

    def clear_suspicious_flags(self) -> None:
        """Clear all suspicious flags (e.g., after user verification)."""
        self.suspicious_flags = {}
        self.save(update_fields=["suspicious_flags"])

    @classmethod
    def get_active_sessions_for_user(cls, user) -> models.QuerySet:
        """Get all active sessions for user.

        Args:
            user: User instance

        Returns:
            QuerySet of SessionSecurity instances
        """
        from django.utils import timezone
        from datetime import timedelta

        # Consider sessions active if activity within last 30 minutes
        cutoff_time = timezone.now() - timedelta(minutes=30)
        return cls.objects.filter(
            user=user,
            last_activity_at__gte=cutoff_time,
        ).order_by("-last_activity_at")
