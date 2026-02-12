"""GDPR compliance models.

Implements GDPR requirements for data subject rights, consent tracking,
and audit logging of PII access.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class AccountDeletion(models.Model):
    """Account deletion request tracking.

    Tracks account deletion requests with 30-day grace period
    before permanent deletion (GDPR Article 17 - Right to Erasure).

    Attributes:
        id: UUID primary key
        user: Foreign key to User model
        requested_at: Deletion request timestamp
        scheduled_deletion_date: Date for permanent deletion (30 days from request)
        completed_at: Permanent deletion timestamp
        status: Deletion workflow status
        reason: Optional reason for deletion
    """

    # Status choices
    PENDING = "pending"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (PENDING, "Pending - within grace period"),
        (SCHEDULED, "Scheduled for permanent deletion"),
        (COMPLETED, "Completed - account permanently deleted"),
        (CANCELLED, "Cancelled - user reactivated account"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deletion_requests",
    )

    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)

    scheduled_deletion_date = models.DateField(
        db_index=True,
        help_text="Date when permanent deletion will occur (30 days from request)",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when permanent deletion was completed",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        db_index=True,
    )

    reason = models.TextField(
        blank=True,
        default="",
        help_text="Optional reason for account deletion",
    )

    class Meta:
        db_table = "auth_account_deletion"
        verbose_name = "Account Deletion Request"
        verbose_name_plural = "Account Deletion Requests"
        indexes = [
            models.Index(fields=["status", "scheduled_deletion_date"]),
            models.Index(fields=["user", "status"]),
        ]
        ordering = ["-requested_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"Deletion request for {self.user} - {self.status}"

    def cancel(self) -> None:
        """Cancel deletion request (user reactivated account).

        Sets status to CANCELLED and clears user's deleted_at field.
        """
        self.status = self.CANCELLED
        self.save(update_fields=["status"])

        # Clear user's soft delete timestamp
        self.user.deleted_at = None
        self.user.deletion_scheduled_date = None
        self.user.save(update_fields=["deleted_at", "deletion_scheduled_date"])

    def mark_completed(self) -> None:
        """Mark deletion as completed after permanent removal."""
        from django.utils import timezone

        self.status = self.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])


class PIIAccessLog(models.Model):
    """PII access audit log.

    Logs all admin access to encrypted PII for GDPR compliance
    (Article 32 - Security of Processing).

    Attributes:
        id: UUID primary key
        admin_user: Admin who accessed PII
        action: Action performed (view, export, modify)
        resource_type: Type of PII accessed (email, phone, ip)
        resource_id: ID of the accessed resource
        user_affected: User whose PII was accessed
        ip_address: IP address of admin
        accessed_at: Access timestamp
    """

    # Action choices
    VIEW = "view"
    EXPORT = "export"
    MODIFY = "modify"
    DELETE = "delete"

    ACTION_CHOICES = [
        (VIEW, "View - PII was decrypted and viewed"),
        (EXPORT, "Export - PII was exported to file"),
        (MODIFY, "Modify - PII was updated"),
        (DELETE, "Delete - PII was deleted"),
    ]

    # Resource type choices
    EMAIL = "email"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"
    FULL_PROFILE = "full_profile"

    RESOURCE_TYPE_CHOICES = [
        (EMAIL, "Email address"),
        (PHONE, "Phone number"),
        (IP_ADDRESS, "IP address"),
        (FULL_PROFILE, "Full user profile"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pii_access_logs_as_admin",
        help_text="Admin who accessed the PII",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
    )

    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        db_index=True,
    )

    resource_id = models.UUIDField(
        help_text="ID of the accessed resource (User ID, IPTracking ID, etc.)",
    )

    user_affected = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pii_access_logs_as_subject",
        help_text="User whose PII was accessed",
    )

    ip_address = models.GenericIPAddressField(
        help_text="IP address of admin performing action",
    )

    accessed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "auth_pii_access_log"
        verbose_name = "PII Access Log"
        verbose_name_plural = "PII Access Logs"
        indexes = [
            models.Index(fields=["user_affected", "accessed_at"]),
            models.Index(fields=["admin_user", "accessed_at"]),
            models.Index(fields=["action", "accessed_at"]),
        ]
        ordering = ["-accessed_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.admin_user} {self.action} {self.resource_type} for {self.user_affected}"


class ConsentLog(models.Model):
    """Consent audit trail.

    Tracks consent granted/withdrawn for phone/SMS communications
    and other data processing activities (GDPR Article 7 - Consent).

    Attributes:
        id: UUID primary key
        user: User who gave/withdrew consent
        consent_type: Type of consent (phone, marketing, etc.)
        granted: True if consent granted, False if withdrawn
        version: Privacy policy/terms version at time of consent
        region: Geographic region (EU, USA, etc.)
        ip_address: IP address when consent was given
        user_agent: User agent when consent was given
        created_at: Consent change timestamp
    """

    # Consent type choices
    PHONE = "phone"
    MARKETING_EMAIL = "marketing_email"
    MARKETING_SMS = "marketing_sms"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"

    CONSENT_TYPE_CHOICES = [
        (PHONE, "Phone/SMS communications"),
        (MARKETING_EMAIL, "Marketing emails"),
        (MARKETING_SMS, "Marketing SMS"),
        (ANALYTICS, "Analytics and tracking"),
        (THIRD_PARTY_SHARING, "Third-party data sharing"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consent_logs",
    )

    consent_type = models.CharField(
        max_length=30,
        choices=CONSENT_TYPE_CHOICES,
        db_index=True,
    )

    granted = models.BooleanField(
        db_index=True,
        help_text="True if consent granted, False if withdrawn",
    )

    version = models.CharField(
        max_length=20,
        help_text="Privacy policy/terms version at time of consent",
    )

    region = models.CharField(
        max_length=10,
        help_text="Geographic region (e.g., 'EU', 'USA', 'CA')",
    )

    ip_address = models.GenericIPAddressField(
        help_text="IP address when consent was given/withdrawn",
    )

    user_agent = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="User agent when consent was given/withdrawn",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "auth_consent_log"
        verbose_name = "Consent Log"
        verbose_name_plural = "Consent Logs"
        indexes = [
            models.Index(fields=["user", "consent_type", "created_at"]),
            models.Index(fields=["consent_type", "granted"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        action = "granted" if self.granted else "withdrawn"
        return f"{self.user} {action} {self.consent_type} consent"

    @classmethod
    def get_current_consent(cls, user, consent_type: str) -> bool:
        """Get current consent status for user and consent type.

        Args:
            user: User instance
            consent_type: Type of consent to check

        Returns:
            bool: True if consent is currently granted
        """
        latest_log = (
            cls.objects.filter(user=user, consent_type=consent_type).order_by("-created_at").first()
        )

        if not latest_log:
            return False

        return latest_log.granted
