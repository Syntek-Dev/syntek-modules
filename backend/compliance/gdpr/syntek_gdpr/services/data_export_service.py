"""Data export service for GDPR Article 15 compliance.

This module implements the Right of Access (Article 15) by providing
functionality to export all user personal data in machine-readable
formats (JSON or CSV).

GDPR Requirements:
- Users can request a copy of all their personal data
- Data must be provided in a commonly used, machine-readable format
- Export must be available within 30 days (we aim for <24 hours)
- Download link expires after 24 hours for security

Example:
    >>> from syntek_gdpr.services.data_export_service import DataExportService
    >>> request = DataExportService.request_export(user, format="json")
    >>> # Async task processes the export
    >>> status = DataExportService.get_export_status(request.id)
    >>> url = DataExportService.get_download_url(request.id)
"""

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils import timezone

if TYPE_CHECKING:
    pass

# Import models - these need to be available in the target environment
try:
    from syntek_audit.models import AuditLog  # type: ignore[import]
except ImportError:
    AuditLog = None  # type: ignore[assignment, misc]

try:
    from syntek_authentication.models import (  # type: ignore[import]
        BackupCode,
        PasswordHistory,
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

try:
    from syntek_sessions.models import SessionToken  # type: ignore[import]
except ImportError:
    SessionToken = None  # type: ignore[assignment, misc]

from syntek_gdpr.models import ConsentRecord  # type: ignore[import]

# Import services if available
try:
    from syntek_audit.services import AuditService  # type: ignore[import]
except ImportError:
    AuditService = None  # type: ignore[assignment, misc]

# Import encryption utilities if available
try:
    from syntek_authentication.utils.encryption import IPEncryption  # type: ignore[import]
except ImportError:
    IPEncryption = None  # type: ignore[assignment, misc]


class DataExportRequest:
    """Placeholder for DataExportRequest model.

    This should be replaced with the actual model when the module is integrated.
    """

    class StatusChoices:
        """Export request status choices."""

        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
        EXPIRED = "expired"

    def __init__(self):
        """Initialize DataExportRequest placeholder."""
        self.id = None
        self.user = None
        self.format = "json"
        self.status = self.StatusChoices.PENDING
        self.file_path = None
        self.download_url = None
        self.expires_at = None
        self.completed_at = None
        self.metadata = {}

    def is_expired(self) -> bool:
        """Check if export has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def mark_as_expired(self) -> None:
        """Mark export as expired."""
        self.status = self.StatusChoices.EXPIRED


class AccountDeletionRequest:
    """Placeholder for AccountDeletionRequest model."""

    pass


class DataExportService:
    """Service for exporting user personal data (GDPR Article 15).

    Handles creation, processing, and delivery of user data exports.
    Exports include all personal data within scope:
    - User profile information
    - Organisation membership
    - Authentication history (audit logs)
    - Active sessions
    - 2FA device information (not secrets)
    - Password change history (timestamps only)
    - Consent records

    Security Features:
    - Exports stored in secure location with UUID filenames
    - Download URLs expire after 24 hours
    - All export requests are audit logged
    - Rate limiting prevents abuse (max 1 export per 24 hours)

    Attributes:
        EXPORT_DIR: Directory for storing export files
        DOWNLOAD_EXPIRY_HOURS: Hours until download URL expires
    """

    EXPORT_DIR = getattr(settings, "GDPR_EXPORT_DIR", "/tmp/gdpr_exports")  # noqa: S108
    DOWNLOAD_EXPIRY_HOURS = 24
    RATE_LIMIT_HOURS = 24  # One export per 24 hours

    @staticmethod
    def request_export(
        user,
        export_format: str = "json",
        ip_address: str = "",
        user_agent: str = "",
    ) -> DataExportRequest:
        """Create a new data export request.

        Creates a pending export request that will be processed asynchronously.
        Rate limited to one export per 24 hours per user.

        Args:
            user: User requesting the export.
            export_format: Export format ("json" or "csv").
            ip_address: IP address of the request (for audit logging).
            user_agent: User agent string (for audit logging).

        Returns:
            DataExportRequest instance.

        Raises:
            ValueError: If format is invalid or rate limit exceeded.
        """
        # Validate format
        if export_format not in ["json", "csv"]:
            raise ValueError("Export format must be 'json' or 'csv'")

        # TODO: Implement rate limiting check when DataExportRequest model is available

        # Create export request
        export_request = DataExportRequest()
        export_request.user = user
        export_request.format = export_format
        export_request.status = DataExportRequest.StatusChoices.PENDING

        # Audit log the request
        if AuditService:
            AuditService.log_event(
                action="data_export_requested",
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "export_id": str(export_request.id),
                    "format": export_format,
                },
            )

        return export_request

    @staticmethod
    def process_export(request_id) -> DataExportRequest:
        """Process a data export request.

        Generates the export file containing all user personal data.
        This method should be called from a Celery task.

        Args:
            request_id: UUID of the DataExportRequest.

        Returns:
            Updated DataExportRequest instance.

        Raises:
            ValueError: If request is not in pending status.
        """
        # TODO: Implement when DataExportRequest model is available
        raise NotImplementedError("DataExportRequest model not yet integrated")

    @staticmethod
    def get_export_status(request_id, user) -> DataExportRequest | None:
        """Get the status of a data export request.

        Args:
            request_id: UUID of the DataExportRequest.
            user: User requesting the status (for authorisation).

        Returns:
            DataExportRequest if found and belongs to user, None otherwise.
        """
        # TODO: Implement when DataExportRequest model is available
        return None

    @staticmethod
    def get_user_exports(user, limit: int = 10) -> list[DataExportRequest]:
        """Get recent export requests for a user.

        Args:
            user: User to get exports for.
            limit: Maximum number of exports to return.

        Returns:
            List of DataExportRequest instances.
        """
        # TODO: Implement when DataExportRequest model is available
        return []

    @staticmethod
    def get_download_url(request_id, user) -> str | None:
        """Get the download URL for a completed export.

        Args:
            request_id: UUID of the DataExportRequest.
            user: User requesting the URL (for authorisation).

        Returns:
            Download URL if export is completed and not expired, None otherwise.
        """
        # TODO: Implement when DataExportRequest model is available
        return None

    @staticmethod
    def cleanup_expired_exports() -> int:
        """Remove expired export files and update statuses.

        Should be called by a scheduled task daily.

        Returns:
            Number of exports cleaned up.
        """
        # TODO: Implement when DataExportRequest model is available
        return 0

    @staticmethod
    def _collect_user_data(user) -> dict[str, Any]:
        """Collect all personal data for a user.

        Gathers data from all models containing user personal information.

        Args:
            user: User to collect data for.

        Returns:
            Dictionary containing all user personal data.
        """
        data = {
            "export_metadata": {
                "export_date": timezone.now().isoformat(),
                "gdpr_article": "Article 15 (Right of Access) & Article 20 (Data Portability)",
                "data_controller": getattr(settings, "DATA_CONTROLLER_NAME", "Syntek CMS Platform"),
                "format_version": "1.0.0",
            },
            "user_profile": DataExportService._get_user_profile_data(user),
            "organisation": DataExportService._get_organisation_data(user),
            "email_verification": DataExportService._get_email_verification_data(user),
            "two_factor_authentication": DataExportService._get_2fa_data(user),
            "active_sessions": DataExportService._get_session_data(user),
            "authentication_history": DataExportService._get_audit_log_data(user),
            "password_history": DataExportService._get_password_history_data(user),
            "consent_records": DataExportService._get_consent_data(user),
            "deletion_requests": DataExportService._get_deletion_request_data(user),
            "processing_restriction": DataExportService._get_processing_restriction_data(user),
        }

        return data

    @staticmethod
    def _get_user_profile_data(user) -> dict[str, Any]:
        """Get user profile data."""
        profile_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": getattr(user, "first_name", ""),
            "last_name": getattr(user, "last_name", ""),
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
            if hasattr(user, "created_at") and user.created_at
            else None,
            "updated_at": user.updated_at.isoformat()
            if hasattr(user, "updated_at") and user.updated_at
            else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

        # Include extended profile if exists
        if UserProfile:
            try:
                profile = UserProfile.objects.get(user=user)
                profile_data["extended_profile"] = {
                    "phone": getattr(profile, "phone", ""),
                    "timezone": getattr(profile, "timezone", ""),
                    "language": getattr(profile, "language", ""),
                    "bio": getattr(profile, "bio", ""),
                }
            except UserProfile.DoesNotExist:
                profile_data["extended_profile"] = None

        return profile_data

    @staticmethod
    def _get_organisation_data(user) -> dict[str, Any] | None:
        """Get organisation membership data."""
        if not hasattr(user, "organisation") or not user.organisation:
            return None

        return {
            "id": str(user.organisation.id),
            "name": user.organisation.name,
            "slug": getattr(user.organisation, "slug", ""),
            "role": "Member",
            "joined_at": user.created_at.isoformat()
            if hasattr(user, "created_at") and user.created_at
            else None,
        }

    @staticmethod
    def _get_email_verification_data(user) -> dict[str, Any]:
        """Get email verification status data."""
        return {
            "email_verified": getattr(user, "email_verified", False),
            "email_verified_at": (
                user.email_verified_at.isoformat()
                if hasattr(user, "email_verified_at") and user.email_verified_at
                else None
            ),
        }

    @staticmethod
    def _get_2fa_data(user) -> dict[str, Any]:
        """Get 2FA status data (excluding secrets)."""
        if not TOTPDevice:
            return {"two_factor_enabled": False, "device_count": 0, "devices": []}

        devices = TOTPDevice.objects.filter(user=user, is_confirmed=True)

        return {
            "two_factor_enabled": getattr(user, "two_factor_enabled", False),
            "device_count": devices.count(),
            "devices": [
                {
                    "name": device.device_name,
                    "created_at": device.created_at.isoformat(),
                    "last_used_at": device.last_used_at.isoformat()
                    if device.last_used_at
                    else None,
                }
                for device in devices
            ],
            "backup_codes_remaining": BackupCode.objects.filter(user=user, is_used=False).count()
            if BackupCode
            else 0,
        }

    @staticmethod
    def _get_session_data(user) -> list[dict[str, Any]]:
        """Get active session data."""
        if not SessionToken:
            return []

        sessions = SessionToken.objects.filter(user=user, is_revoked=False)

        return [
            {
                "device_fingerprint": getattr(session, "device_fingerprint", ""),
                "user_agent": session.user_agent,
                "created_at": session.created_at.isoformat(),
                "last_activity_at": session.last_activity_at.isoformat()
                if hasattr(session, "last_activity_at")
                else None,
                "expires_at": session.expires_at.isoformat(),
            }
            for session in sessions
        ]

    @staticmethod
    def _get_audit_log_data(user, limit: int = 1000) -> list[dict[str, Any]]:
        """Get authentication history from audit logs."""
        if not AuditLog:
            return []

        logs = AuditLog.objects.filter(user=user).order_by("-created_at")[:limit]

        return [
            {
                "action": log.action,
                "timestamp": log.created_at.isoformat(),
                "ip_address": (
                    IPEncryption.decrypt_ip(log.ip_address)
                    if IPEncryption and log.ip_address
                    else None
                ),
                "user_agent": getattr(log, "user_agent", ""),
                "device_fingerprint": getattr(log, "device_fingerprint", ""),
            }
            for log in logs
        ]

    @staticmethod
    def _get_password_history_data(user) -> list[dict[str, Any]]:
        """Get password change history (timestamps only, not hashes)."""
        if not PasswordHistory:
            return []

        history = PasswordHistory.objects.filter(user=user).order_by("-created_at")

        return [
            {
                "changed_at": record.created_at.isoformat(),
            }
            for record in history
        ]

    @staticmethod
    def _get_consent_data(user) -> list[dict[str, Any]]:
        """Get consent records."""
        consents = ConsentRecord.objects.filter(user=user).order_by("-granted_at")  # type: ignore[attr-defined]

        return [
            {
                "consent_type": consent.consent_type,
                "granted": consent.granted,
                "version": consent.version,
                "granted_at": consent.granted_at.isoformat(),
                "withdrawn_at": (
                    consent.withdrawn_at.isoformat() if consent.withdrawn_at else None
                ),
            }
            for consent in consents
        ]

    @staticmethod
    def _get_deletion_request_data(user) -> list[dict[str, Any]]:
        """Get account deletion request history."""
        # TODO: Implement when AccountDeletionRequest model is integrated
        return []

    @staticmethod
    def _get_processing_restriction_data(user) -> dict[str, Any]:
        """Get processing restriction status."""
        return {
            "processing_restricted": getattr(user, "processing_restricted", False),
            "restriction_reason": getattr(user, "restriction_reason", ""),
            "restricted_at": (
                user.restricted_at.isoformat()
                if hasattr(user, "restricted_at") and user.restricted_at
                else None
            ),
        }

    @staticmethod
    def _generate_json_export(data: dict[str, Any], request_id) -> tuple[str, int]:
        """Generate JSON export file.

        Args:
            data: User data dictionary.
            request_id: Export request ID for filename.

        Returns:
            Tuple of (file_path, file_size).
        """
        # Ensure export directory exists
        export_dir = Path(DataExportService.EXPORT_DIR)
        export_dir.mkdir(parents=True, exist_ok=True)

        file_path = export_dir / f"{request_id}.json"

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        file_size = file_path.stat().st_size
        return str(file_path), file_size

    @staticmethod
    def _generate_csv_export(data: dict[str, Any], request_id) -> tuple[str, int]:
        """Generate CSV export file.

        Flattens the data structure into CSV format with multiple sections.

        Args:
            data: User data dictionary.
            request_id: Export request ID for filename.

        Returns:
            Tuple of (file_path, file_size).
        """
        # Ensure export directory exists
        export_dir = Path(DataExportService.EXPORT_DIR)
        export_dir.mkdir(parents=True, exist_ok=True)

        file_path = export_dir / f"{request_id}.csv"

        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write each section
            for section_name, section_data in data.items():
                writer.writerow([f"=== {section_name.upper()} ==="])

                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if isinstance(value, (dict, list)):
                            writer.writerow([key, json.dumps(value)])
                        else:
                            writer.writerow([key, value])

                elif isinstance(section_data, list):
                    if section_data and isinstance(section_data[0], dict):
                        # Write headers
                        headers = list(section_data[0].keys())
                        writer.writerow(headers)
                        # Write rows
                        for item in section_data:
                            writer.writerow([item.get(h, "") for h in headers])
                    else:
                        for item in section_data:
                            writer.writerow([item])

                writer.writerow([])  # Empty row between sections

        file_size = file_path.stat().st_size
        return str(file_path), file_size

    @staticmethod
    def _generate_download_url(request_id) -> str:
        """Generate a secure download URL for the export.

        In production, this would generate a signed URL.

        Args:
            request_id: Export request ID.

        Returns:
            Download URL string.
        """
        base_url = getattr(settings, "SITE_URL", "http://localhost:8000")
        return f"{base_url}/api/gdpr/exports/{request_id}/download/"

    @staticmethod
    def _get_record_counts(data: dict[str, Any]) -> dict[str, int]:
        """Get record counts for each data section.

        Args:
            data: User data dictionary.

        Returns:
            Dictionary of section names to record counts.
        """
        counts = {}
        for section_name, section_data in data.items():
            if isinstance(section_data, list):
                counts[section_name] = len(section_data)
            elif isinstance(section_data, dict):
                counts[section_name] = 1
            else:
                counts[section_name] = 0
        return counts
