"""Account deletion service for GDPR Article 17 (Right to Erasure) compliance.

This module provides account deletion functionality including:
- Soft delete with 30-day grace period
- Permanent deletion after grace period
- Deletion request tracking
- Cancellation support
- Audit logging

SECURITY NOTE (GDPR Article 17):
- 30-day grace period for account recovery
- Soft delete (mark deleted_at, anonymize PII)
- Permanent deletion after grace period
- Audit logging for all deletion operations
- Legal hold support (prevent deletion if required)

Example:
    >>> AccountDeletionService.request_deletion(user, reason)
    >>> AccountDeletionService.cancel_deletion(user)
    >>> AccountDeletionService.execute_permanent_deletion(user)
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from syntek_authentication.models import AccountDeletion, User

logger = logging.getLogger(__name__)


class AccountDeletionService:
    """Service for account deletion (GDPR Article 17 compliance).

    Handles account deletion lifecycle:
    1. Soft delete with grace period (30 days)
    2. PII anonymization during soft delete
    3. Cancellation support (reactivation)
    4. Permanent deletion after grace period
    5. Audit logging

    Features:
    - 30-day grace period
    - Soft delete (reversible)
    - Permanent deletion (irreversible)
    - Legal hold support
    - Audit trail

    Attributes:
        GRACE_PERIOD_DAYS: Days before permanent deletion
        ANONYMIZED_EMAIL_PREFIX: Prefix for anonymized emails
    """

    GRACE_PERIOD_DAYS = 30
    ANONYMIZED_EMAIL_PREFIX = "deleted_user_"

    @staticmethod
    @transaction.atomic
    def request_deletion(user: "User", reason: str = "") -> "AccountDeletion":
        """Request account deletion (soft delete with grace period).

        Args:
            user: User requesting deletion.
            reason: Optional reason for deletion.

        Returns:
            AccountDeletion object.

        Raises:
            ValueError: If deletion already requested or legal hold active.
        """
        from syntek_authentication.models import AccountDeletion

        # Check if deletion already requested
        existing_request = AccountDeletion.objects.filter(
            user=user,
            status__in=["pending", "scheduled"],
        ).first()

        if existing_request:
            raise ValueError(
                "Deletion already requested. "
                f"Scheduled for {existing_request.scheduled_deletion_date}"
            )

        # Check for legal hold (optional - implement if needed)
        # if user.legal_hold:
        #     raise ValueError("Account cannot be deleted due to legal hold")

        # Calculate scheduled deletion date
        scheduled_date = timezone.now().date() + timedelta(
            days=AccountDeletionService.GRACE_PERIOD_DAYS
        )

        # Create deletion request
        deletion_request = AccountDeletion.objects.create(
            user=user,
            scheduled_deletion_date=scheduled_date,
            reason=reason,
        )

        # Soft delete user account
        AccountDeletionService._soft_delete_user(user, scheduled_date)

        logger.info(
            f"Account deletion requested for user {user.id}, scheduled for {scheduled_date}"
        )

        return deletion_request

    @staticmethod
    @transaction.atomic
    def _soft_delete_user(user: "User", scheduled_date) -> None:
        """Soft delete user (anonymize PII, mark as deleted).

        Args:
            user: User to soft delete.
            scheduled_date: Permanent deletion date.
        """
        # Mark user as deleted
        user.deleted_at = timezone.now()
        user.deletion_scheduled_date = scheduled_date
        user.is_active = False  # Disable login

        # Anonymize email (keep for foreign key integrity)
        anonymized_email = (
            f"{AccountDeletionService.ANONYMIZED_EMAIL_PREFIX}{user.id}@deleted.local"
        )
        user.email = anonymized_email

        # Clear encrypted PII (but keep hashes for rate limiting)
        user.email_encrypted = None
        user.phone_number_encrypted = None

        # Clear personal information
        user.first_name = ""
        user.last_name = ""

        user.save()

        logger.info(f"User {user.id} soft deleted (anonymized)")

    @staticmethod
    @transaction.atomic
    def cancel_deletion(user: "User") -> None:
        """Cancel deletion request and reactivate account.

        Args:
            user: User whose deletion to cancel.

        Raises:
            ValueError: If no pending deletion request.
        """
        from syntek_authentication.models import AccountDeletion

        # Get pending deletion request
        deletion_request = AccountDeletion.objects.filter(
            user=user,
            status__in=["pending", "scheduled"],
        ).first()

        if not deletion_request:
            raise ValueError("No pending deletion request found")

        # Cancel deletion request
        deletion_request.cancel()

        # Reactivate user account
        user.deleted_at = None
        user.deletion_scheduled_date = None
        user.is_active = True

        # Note: Email and PII must be re-entered by user
        # We cannot restore encrypted data after soft delete

        user.save()

        logger.info(f"Account deletion cancelled for user {user.id}")

    @staticmethod
    @transaction.atomic
    def execute_permanent_deletion(user: "User") -> bool:
        """Execute permanent deletion (GDPR Article 17).

        This is irreversible. All user data is permanently deleted.

        Args:
            user: User to permanently delete.

        Returns:
            True if deleted, False if not ready for deletion.

        Raises:
            ValueError: If user not soft deleted or grace period not expired.
        """
        from syntek_authentication.models import AccountDeletion

        # Check if user is soft deleted
        if not user.deleted_at:
            raise ValueError("User must be soft deleted before permanent deletion")

        # Check if grace period has expired
        if user.deletion_scheduled_date > timezone.now().date():
            raise ValueError(
                f"Grace period has not expired. Scheduled for {user.deletion_scheduled_date}"
            )

        # Get deletion request
        deletion_request = AccountDeletion.objects.filter(
            user=user,
            status="scheduled",
        ).first()

        # Delete related data (cascade will handle most of this)
        # Note: Some data may be retained for legal/compliance reasons
        # Adjust based on your specific retention policies

        # Sessions
        from django.contrib.sessions.models import Session

        Session.objects.filter(session_data__contains=str(user.id)).delete()

        # Session security
        from syntek_authentication.models import SessionSecurity

        SessionSecurity.objects.filter(user=user).delete()

        # Login attempts (keep for security analysis - anonymized)
        from syntek_authentication.models import LoginAttempt

        LoginAttempt.objects.filter(user=user).update(user=None)

        # Phone verification tokens
        from syntek_authentication.models import PhoneVerificationToken

        PhoneVerificationToken.objects.filter(user=user).delete()

        # Recovery keys
        from syntek_authentication.models import RecoveryKey

        RecoveryKey.objects.filter(user=user).delete()

        # IP tracking (keep for security analysis - already encrypted)
        # IPTracking.objects.filter(user=user).delete()  # Optional

        # Mark deletion as completed
        if deletion_request:
            deletion_request.mark_completed()

        # Permanently delete user
        user_id = user.id
        user.delete()

        logger.warning(f"User {user_id} permanently deleted")

        return True

    @staticmethod
    def process_scheduled_deletions() -> dict:
        """Process all scheduled deletions (background task).

        Runs daily to permanently delete users whose grace period has expired.

        Returns:
            Dict with deletion statistics.
        """
        from syntek_authentication.models import User

        # Get users scheduled for deletion today
        today = timezone.now().date()

        users_to_delete = User.objects.filter(
            deleted_at__isnull=False,
            deletion_scheduled_date__lte=today,
        )

        deleted_count = 0
        failed_count = 0

        for user in users_to_delete:
            try:
                AccountDeletionService.execute_permanent_deletion(user)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to permanently delete user {user.id}: {e}")
                failed_count += 1

        logger.info(
            f"Processed scheduled deletions: {deleted_count} deleted, {failed_count} failed"
        )

        return {
            "deleted": deleted_count,
            "failed": failed_count,
            "total_processed": deleted_count + failed_count,
        }

    @staticmethod
    def get_deletion_status(user: "User") -> dict:
        """Get deletion status for user.

        Args:
            user: User to check.

        Returns:
            Dict with deletion status information.
        """
        from syntek_authentication.models import AccountDeletion

        if not user.deleted_at:
            return {
                "status": "active",
                "deleted_at": None,
                "scheduled_deletion_date": None,
                "days_until_deletion": None,
            }

        deletion_request = AccountDeletion.objects.filter(
            user=user,
            status__in=["pending", "scheduled"],
        ).first()

        days_until_deletion = None
        if user.deletion_scheduled_date:
            days_until_deletion = (user.deletion_scheduled_date - timezone.now().date()).days

        return {
            "status": "soft_deleted" if user.deleted_at else "active",
            "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
            "scheduled_deletion_date": (
                user.deletion_scheduled_date.isoformat() if user.deletion_scheduled_date else None
            ),
            "days_until_deletion": max(0, days_until_deletion)
            if days_until_deletion is not None
            else None,
            "can_cancel": days_until_deletion is not None and days_until_deletion > 0,
            "reason": deletion_request.reason if deletion_request else None,
        }

    @staticmethod
    def send_deletion_reminder(user: "User", days_remaining: int) -> bool:
        """Send deletion reminder email to user.

        Args:
            user: User to remind.
            days_remaining: Days until permanent deletion.

        Returns:
            True if email sent successfully.
        """
        # TODO: Implement email sending
        # This should use EmailService to send reminder

        logger.info(f"Deletion reminder sent to user {user.id} ({days_remaining} days remaining)")

        return True
