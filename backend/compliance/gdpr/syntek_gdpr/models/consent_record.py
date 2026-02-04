"""ConsentRecord model for GDPR consent management.

This module implements consent tracking for GDPR compliance (Articles 6, 7).
Records user consent for different types of data processing with version
tracking and audit trail.
"""

import uuid

from django.db import models


class ConsentRecord(models.Model):
    """Track user consent for different processing activities.

    Records consent given by users for various types of data processing.
    Implements GDPR requirements for consent (Articles 6, 7) including:
    - Freely given, specific, informed, and unambiguous
    - Ability to withdraw consent
    - Version tracking for consent policy changes
    - Audit trail with IP address and user agent

    Attributes:
        id: UUID primary key
        user: Foreign key to User who gave/withdrew consent
        consent_type: Type of consent (essential, functional, analytics, marketing)
        granted: Whether consent is currently granted
        version: Version of consent policy at time of grant/withdrawal
        ip_address: Encrypted IP address where consent was given
        user_agent: Browser user agent string
        granted_at: Timestamp when consent was granted
        withdrawn_at: Timestamp when consent was withdrawn (null if still granted)
        metadata: Additional consent metadata (JSON)
    """

    class ConsentType(models.TextChoices):
        """Types of consent for different processing activities."""

        ESSENTIAL = "essential", "Essential (Required)"  # type: ignore[assignment]
        FUNCTIONAL = "functional", "Functional"  # type: ignore[assignment]
        ANALYTICS = "analytics", "Analytics"  # type: ignore[assignment]
        MARKETING = "marketing", "Marketing"  # type: ignore[assignment]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.CASCADE,
        related_name="consent_records",
        help_text="User who gave or withdrew consent",
    )

    consent_type = models.CharField(
        max_length=20,
        choices=ConsentType.choices,
        help_text="Type of consent (essential, functional, analytics, marketing)",
    )

    granted = models.BooleanField(
        default=False,  # type: ignore[call-arg]
        help_text="Whether consent is currently granted",
    )

    version = models.CharField(
        max_length=20,
        default="1.0.0",
        help_text="Version of consent policy at time of grant/withdrawal",
    )

    ip_address = models.BinaryField(
        null=True,
        blank=True,
        help_text="Encrypted IP address where consent was given/withdrawn",
    )

    user_agent = models.TextField(
        blank=True,
        default="",
        help_text="Browser user agent string",
    )

    granted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when consent was granted",
    )

    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when consent was withdrawn",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional consent metadata (referrer, language, etc.)",
    )

    class Meta:
        db_table = "consent_records"
        verbose_name = "Consent Record"
        verbose_name_plural = "Consent Records"
        ordering = ["-granted_at"]
        indexes = [
            models.Index(fields=["user", "consent_type", "-granted_at"]),
            models.Index(fields=["user", "granted"]),
            models.Index(fields=["consent_type", "granted"]),
        ]
        # Ensure one active consent record per user per consent type
        constraints = [
            models.UniqueConstraint(
                fields=["user", "consent_type"],
                condition=models.Q(granted=True, withdrawn_at__isnull=True),
                name="unique_active_consent_per_type",
            )
        ]

    def __str__(self) -> str:
        """Return consent record description."""
        status = "Granted" if self.granted else "Withdrawn"
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        return f"{user_email} - {self.consent_type} ({status})"

    def save(self, *args, **kwargs):
        """Save consent record with IP address encryption.

        Automatically encrypts IP address if provided in metadata.
        """
        # Import here to avoid circular dependency
        try:
            from syntek_authentication.utils.encryption import IPEncryption  # type: ignore[import]

            # Encrypt IP address if present in metadata
            if "ip_address" in self.metadata and not self.ip_address:  # type: ignore[operator]
                ip_str = self.metadata["ip_address"]  # type: ignore[index]
                self.ip_address = IPEncryption.encrypt_ip(ip_str)
        except ImportError:
            pass  # Encryption utility not available

        super().save(*args, **kwargs)

    def get_ip_address(self) -> str | None:
        """Get decrypted IP address.

        Returns:
            Decrypted IP address string or None if not set
        """
        if not self.ip_address:
            return None

        try:
            from syntek_authentication.utils.encryption import IPEncryption  # type: ignore[import]

            return IPEncryption.decrypt_ip(self.ip_address)
        except ImportError:
            return None  # Encryption utility not available
