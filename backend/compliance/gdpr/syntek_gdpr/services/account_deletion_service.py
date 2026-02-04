"""Account deletion service for GDPR Article 17 compliance.

This module implements the Right to Erasure (Article 17) by providing
functionality for users to request and confirm permanent deletion of
their accounts.

GDPR Requirements:
- Users can request deletion of their personal data
- Confirmation workflow prevents accidental deletions
- Some data may be retained for legal compliance (anonymised)
- Audit logs are anonymised, not deleted (7 year retention)

Deletion Workflow:
1. User requests deletion -> Confirmation email sent
2. User clicks confirmation link with token
3. User enters password to confirm
4. Account and related data deleted/anonymised
5. Confirmation email sent

Example:
    >>> from syntek_gdpr.services.account_deletion_service import AccountDeletionService
    >>> request = AccountDeletionService.request_deletion(user, "No longer needed")
    >>> # User receives email with confirmation token
    >>> AccountDeletionService.confirm_deletion(token, password)
"""

import hashlib

from django.conf import settings
from django.utils import timezone

# Import models - these need to be available in the target environment
try:
    from syntek_audit.models import AuditLog
except ImportError:
    AuditLog = None  # type: ignore[assignment, misc]

try:
    from syntek_authentication.models import (
        BackupCode,
        EmailVerificationToken,
        PasswordHistory,
        PasswordResetToken,
        TOTPDevice,
        User,  # type: ignore[reportUnusedImport]
        UserProfile,
    )
except ImportError:
    User = None  # type: ignore[assignment, misc]
    UserProfile = None  # type: ignore[assignment, misc]
    TOTPDevice = None  # type: ignore[assignment, misc]
    BackupCode = None  # type: ignore[assignment, misc]
    PasswordHistory = None  # type: ignore[assignment, misc]
    PasswordResetToken = None  # type: ignore[assignment, misc]
    EmailVerificationToken = None  # type: ignore[assignment, misc]

try:
    from syntek_sessions.models import SessionToken
except ImportError:
    SessionToken = None  # type: ignore[assignment, misc]

from syntek_gdpr.models import ConsentRecord

# Import services if available
try:
    from syntek_audit.services import AuditService
except ImportError:
    AuditService = None  # type: ignore[assignment, misc]

try:
    from syntek_authentication.services import EmailService
except ImportError:
    EmailService = None  # type: ignore[assignment, misc]


class AccountDeletionRequest:
    """Placeholder for AccountDeletionRequest model.

    This should be replaced with the actual model when integrated.
    """

    class StatusChoices:
        """Deletion request status choices."""

        PENDING = "pending"
        CONFIRMED = "confirmed"
        PROCESSING = "processing"
        COMPLETED = "completed"
        CANCELLED = "cancelled"

    @staticmethod
    def generate_confirmation_token():
        """Generate confirmation token."""
        import secrets

        plain_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
        return plain_token, hashed_token

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for comparison."""
        return hashlib.sha256(token.encode()).hexdigest()

    def __init__(self):
        """Initialize AccountDeletionRequest placeholder."""
        self.id = None
        self.user = None
        self.reason = ""
        self.confirmation_token = ""
        self.status = self.StatusChoices.PENDING
        self.created_at = timezone.now()
        self.confirmed_at = None
        self.completed_at = None
        self.data_retained = []
        self.metadata = {}

    def is_expired(self, hours: int = 24) -> bool:
        """Check if request has expired."""
        from datetime import timedelta

        expiry_time = self.created_at + timedelta(hours=hours)
        return timezone.now() > expiry_time


class DataExportRequest:
    """Placeholder for DataExportRequest model."""

    pass


class AccountDeletionService:
    """Service for account deletion (GDPR Article 17).

    Handles the complete account deletion workflow including request
    creation, confirmation, and execution. Implements proper data
    retention for legal compliance.

    Deletion Strategy:
    - Immediate deletion: User profile, sessions, tokens, 2FA devices
    - Anonymisation: Audit logs (user reference removed, structure preserved)
    - Retention: Anonymised audit logs for 7 years (legal compliance)

    Security Features:
    - Confirmation token with 24-hour expiry
    - Password verification required for confirmation
    - All deletion events are audit logged
    - Email notifications at each step

    Attributes:
        CONFIRMATION_EXPIRY_HOURS: Hours until confirmation token expires
    """

    CONFIRMATION_EXPIRY_HOURS = 24

    @staticmethod
    def request_deletion(
        user,
        reason: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> AccountDeletionRequest:
        """Request account deletion.

        Creates a pending deletion request and sends a confirmation email.
        The user must confirm within 24 hours.

        Args:
            user: User requesting deletion.
            reason: Optional reason for deletion.
            ip_address: IP address of the request (for audit logging).
            user_agent: User agent string (for audit logging).

        Returns:
            AccountDeletionRequest instance.

        Raises:
            ValueError: If user already has a pending deletion request.
        """
        # TODO: Implement when AccountDeletionRequest model is available
        deletion_request = AccountDeletionRequest()
        deletion_request.user = user
        deletion_request.reason = reason

        # Audit log the request
        if AuditService:
            AuditService.log_event(
                action="account_deletion_requested",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "request_id": str(deletion_request.id),
                    "reason_provided": bool(reason),
                },
            )

        return deletion_request

    @staticmethod
    def confirm_deletion(
        token: str,
        password: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> AccountDeletionRequest:
        """Confirm and execute account deletion.

        Verifies the confirmation token and password, then processes
        the deletion. This operation is irreversible.

        Args:
            token: Plain text confirmation token from email.
            password: User's current password for verification.
            ip_address: IP address of the request (for audit logging).
            user_agent: User agent string (for audit logging).

        Returns:
            Updated AccountDeletionRequest instance.

        Raises:
            ValueError: If token is invalid, expired, or password is wrong.
        """
        # TODO: Implement when AccountDeletionRequest model is available
        raise NotImplementedError("AccountDeletionRequest model not yet integrated")

    @staticmethod
    def process_deletion(request_id) -> AccountDeletionRequest:
        """Process the account deletion.

        Executes the actual deletion of user data. Should be called
        after confirmation or from a task queue.

        Args:
            request_id: UUID of the AccountDeletionRequest.

        Returns:
            Updated AccountDeletionRequest instance.

        Raises:
            ValueError: If request is not confirmed.
        """
        # TODO: Implement when AccountDeletionRequest model is available
        raise NotImplementedError("AccountDeletionRequest model not yet integrated")

    @staticmethod
    def cancel_deletion(
        request_id,
        user,
        ip_address: str = "",
        user_agent: str = "",
    ) -> AccountDeletionRequest:
        """Cancel a pending deletion request.

        Args:
            request_id: UUID of the AccountDeletionRequest.
            user: User cancelling the request (for authorisation).
            ip_address: IP address of the request (for audit logging).
            user_agent: User agent string (for audit logging).

        Returns:
            Updated AccountDeletionRequest instance.

        Raises:
            ValueError: If request is not pending or doesn't belong to user.
        """
        # TODO: Implement when AccountDeletionRequest model is available
        raise NotImplementedError("AccountDeletionRequest model not yet integrated")

    @staticmethod
    def get_user_deletion_requests(user) -> list[AccountDeletionRequest]:
        """Get all deletion requests for a user.

        Args:
            user: User to get requests for.

        Returns:
            List of AccountDeletionRequest instances.
        """
        # TODO: Implement when AccountDeletionRequest model is available
        return []

    @staticmethod
    def _anonymise_audit_logs(user) -> int:
        """Anonymise audit logs for a user.

        Removes user reference and PII from metadata while preserving
        the log structure for legal compliance.

        Args:
            user: User whose logs should be anonymised.

        Returns:
            Number of logs anonymised.
        """
        if not AuditLog:
            return 0

        logs = AuditLog.objects.filter(user=user)
        count = logs.count()

        for log in logs:
            # Remove user reference
            log.user = None

            # Anonymise metadata (remove email, names, etc.)
            if log.metadata:
                anonymised_metadata = {}
                for key, value in log.metadata.items():
                    if key not in ["email", "user_email", "first_name", "last_name", "name"]:
                        anonymised_metadata[key] = value
                anonymised_metadata["anonymised"] = True
                anonymised_metadata["anonymised_at"] = timezone.now().isoformat()
                log.metadata = anonymised_metadata

            log.save(update_fields=["user", "metadata"])

        return count

    @staticmethod
    def _delete_user_data(user) -> dict[str, int]:
        """Delete all user-related data.

        Removes data from related models that should not be retained.

        Args:
            user: User whose data should be deleted.

        Returns:
            Dictionary of model names to deletion counts.
        """
        counts = {}

        # Delete session tokens
        if SessionToken:
            counts["session_tokens"] = SessionToken.objects.filter(user=user).delete()[0]

        # Delete TOTP devices
        if TOTPDevice:
            counts["totp_devices"] = TOTPDevice.objects.filter(user=user).delete()[0]

        # Delete backup codes
        if BackupCode:
            counts["backup_codes"] = BackupCode.objects.filter(user=user).delete()[0]

        # Delete password reset tokens
        if PasswordResetToken:
            counts["password_reset_tokens"] = PasswordResetToken.objects.filter(user=user).delete()[0]

        # Delete email verification tokens
        if EmailVerificationToken:
            counts["email_verification_tokens"] = EmailVerificationToken.objects.filter(
                user=user
            ).delete()[0]

        # Delete password history
        if PasswordHistory:
            counts["password_history"] = PasswordHistory.objects.filter(user=user).delete()[0]

        # Delete consent records
        counts["consent_records"] = ConsentRecord.objects.filter(user=user).delete()[0]

        # Delete data export requests (and their files)
        # TODO: Implement when DataExportRequest model is available

        # Delete user profile
        if UserProfile:
            counts["user_profile"] = UserProfile.objects.filter(user=user).delete()[0]

        return counts

    @staticmethod
    def _get_data_retention_summary(user) -> list[str]:
        """Get summary of data that will be retained after deletion.

        Args:
            user: User being deleted.

        Returns:
            List of data retention notices.
        """
        retained = []

        if AuditLog:
            audit_log_count = AuditLog.objects.filter(user=user).count()
            if audit_log_count > 0:
                retained.append(
                    f"Anonymised audit logs ({audit_log_count} entries) - "
                    "retained for 7 years for legal compliance"
                )

        retained.append("Account deletion request record - retained for compliance tracking")

        return retained

    @staticmethod
    def _send_confirmation_email(user, token: str) -> None:
        """Send deletion confirmation email.

        Args:
            user: User to send email to.
            token: Plain text confirmation token.
        """
        if not EmailService:
            return

        base_url = getattr(settings, "SITE_URL", "http://localhost:8000")
        confirmation_url = f"{base_url}/account/delete/confirm?token={token}"

        EmailService.send_email(
            to_email=user.email,
            subject="Confirm Account Deletion Request",
            template_name="account_deletion_confirmation",
            context={
                "user": user,
                "confirmation_url": confirmation_url,
                "expiry_hours": AccountDeletionService.CONFIRMATION_EXPIRY_HOURS,
            },
        )

    @staticmethod
    def _send_deletion_complete_email(email: str) -> None:
        """Send deletion complete notification email.

        Args:
            email: Email address to send to.
        """
        if not EmailService:
            return

        EmailService.send_email(
            to_email=email,
            subject="Account Deletion Complete",
            template_name="account_deletion_complete",
            context={
                "email": email,
            },
        )

    @staticmethod
    def _hash_email(email: str) -> str:
        """Hash email for anonymised logging.

        Args:
            email: Email to hash.

        Returns:
            SHA256 hash of the email (first 16 characters).
        """
        return hashlib.sha256(email.lower().encode()).hexdigest()[:16]
