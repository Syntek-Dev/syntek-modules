"""Login attempt tracking model.

Tracks all login attempts (successful and failed) for security monitoring,
rate limiting, and suspicious activity detection.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class LoginAttempt(models.Model):
    """Login attempt tracking for security and analytics.

    Tracks all authentication attempts with encrypted PII.
    Uses table partitioning (monthly) for performance at scale.

    Attributes:
        id: UUID primary key
        user: Foreign key to User model (null for failed attempts with unknown user)
        email: Plain text email for indexing (domain only, not PII)
        ip_address_encrypted: Binary field containing encrypted IP
        ip_hash: HMAC-SHA256 hash for constant-time lookups
        success: Boolean flag indicating successful login
        failure_reason: Reason code for failed attempts
        user_agent: User agent string
        created_at: Attempt timestamp (partition key)
    """

    # Failure reason choices
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_INACTIVE = "account_inactive"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    MFA_REQUIRED = "mfa_required"
    MFA_FAILED = "mfa_failed"
    IP_BLACKLISTED = "ip_blacklisted"
    RATE_LIMITED = "rate_limited"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    FAILURE_REASON_CHOICES = [
        (INVALID_CREDENTIALS, "Invalid email or password"),
        (ACCOUNT_LOCKED, "Account is locked"),
        (ACCOUNT_INACTIVE, "Account is inactive"),
        (EMAIL_NOT_VERIFIED, "Email not verified"),
        (MFA_REQUIRED, "MFA required but not provided"),
        (MFA_FAILED, "MFA verification failed"),
        (IP_BLACKLISTED, "IP address is blacklisted"),
        (RATE_LIMITED, "Rate limit exceeded"),
        (SUSPICIOUS_ACTIVITY, "Suspicious activity detected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_attempts",
        help_text="User (null if email not found)",
    )

    # Email for rate limiting (plain text, normalized)
    email = models.EmailField(
        max_length=255,
        db_index=True,
        help_text="Email used for login attempt (lowercase)",
    )

    # IP address storage (encrypted + hashed)
    ip_address_encrypted = models.BinaryField(help_text="Encrypted IP address (ChaCha20-Poly1305)")
    ip_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="HMAC-SHA256 hash for lookups",
    )

    # Attempt result
    success = models.BooleanField(
        db_index=True,
        help_text="True if login succeeded",
    )

    failure_reason = models.CharField(
        max_length=50,
        choices=FAILURE_REASON_CHOICES,
        blank=True,
        default="",
        help_text="Reason code for failed attempts",
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
        db_table = "auth_login_attempt"
        verbose_name = "Login Attempt"
        verbose_name_plural = "Login Attempts"
        indexes = [
            # Performance indexes for rate limiting queries
            models.Index(
                fields=["email", "success", "created_at"],
                name="idx_login_email_success",
            ),
            models.Index(
                fields=["ip_hash", "created_at"],
                name="idx_login_ip_time",
            ),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["created_at"]),  # For partitioning
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        status = "successful" if self.success else "failed"
        return f"{status} login attempt for {self.email} at {self.created_at}"

    @classmethod
    def get_recent_failures_for_email(cls, email: str, minutes: int = 15) -> models.QuerySet:
        """Get recent failed login attempts for email.

        Used for rate limiting and account lockout logic.

        Args:
            email: Email address (normalized)
            minutes: Lookback period in minutes (default: 15)

        Returns:
            QuerySet of failed LoginAttempt instances
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            email=email.lower(),
            success=False,
            created_at__gte=cutoff_time,
        ).order_by("-created_at")

    @classmethod
    def get_recent_failures_for_ip(cls, ip_hash: str, minutes: int = 60) -> models.QuerySet:
        """Get recent failed login attempts for IP address.

        Used for IP-based rate limiting and blacklist detection.

        Args:
            ip_hash: HMAC-SHA256 hash of IP address
            minutes: Lookback period in minutes (default: 60)

        Returns:
            QuerySet of failed LoginAttempt instances
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            ip_hash=ip_hash,
            success=False,
            created_at__gte=cutoff_time,
        ).order_by("-created_at")

    @classmethod
    def count_recent_failures(cls, email: str, minutes: int = 15) -> int:
        """Count failed login attempts for email in recent period.

        Args:
            email: Email address (normalized)
            minutes: Lookback period in minutes (default: 15)

        Returns:
            Number of failed attempts
        """
        return cls.get_recent_failures_for_email(email, minutes).count()
