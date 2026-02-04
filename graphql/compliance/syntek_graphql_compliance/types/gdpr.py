"""GraphQL types for GDPR compliance operations.

This module defines Strawberry GraphQL types for GDPR-related data
including data export requests, account deletion requests, consent
records, and processing restriction status.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Required at runtime for Strawberry GraphQL
from enum import Enum

import strawberry


@strawberry.enum
class ExportFormat(Enum):
    """Export file format options."""

    JSON = "json"
    CSV = "csv"


@strawberry.enum
class ExportStatus(Enum):
    """Data export request status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@strawberry.enum
class DeletionStatus(Enum):
    """Account deletion request status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@strawberry.enum
class ConsentType(Enum):
    """Consent type categories."""

    ESSENTIAL = "essential"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    MARKETING = "marketing"


@strawberry.type
class DataExportRequestType:
    """GraphQL type for data export requests.

    Represents a user's request to export their personal data
    under GDPR Article 15 (Right of Access).
    """

    id: strawberry.ID
    status: ExportStatus
    format: ExportFormat
    download_url: str | None
    expires_at: datetime | None
    created_at: datetime
    completed_at: datetime | None
    file_size: int | None
    record_counts: strawberry.scalars.JSON | None

    @staticmethod
    def from_model(export_request: object) -> DataExportRequestType:
        """Convert DataExportRequest model to GraphQL type.

        Args:
            export_request: DataExportRequest model instance.

        Returns:
            DataExportRequestType instance.
        """
        metadata = getattr(export_request, "metadata", None) or {}  # type: ignore[attr-defined]

        return DataExportRequestType(
            id=strawberry.ID(str(getattr(export_request, "id", ""))),  # type: ignore[attr-defined]
            status=ExportStatus(getattr(export_request, "status", "")),  # type: ignore[attr-defined]
            format=ExportFormat(getattr(export_request, "format", "")),  # type: ignore[attr-defined]
            download_url=getattr(export_request, "download_url", None) or None,  # type: ignore[attr-defined]
            expires_at=getattr(export_request, "expires_at", None),  # type: ignore[attr-defined]
            created_at=getattr(export_request, "created_at", None),  # type: ignore[attr-defined]
            completed_at=getattr(export_request, "completed_at", None),  # type: ignore[attr-defined]
            file_size=metadata.get("file_size"),
            record_counts=metadata.get("record_counts"),
        )


@strawberry.type
class AccountDeletionRequestType:
    """GraphQL type for account deletion requests.

    Represents a user's request to delete their account
    under GDPR Article 17 (Right to Erasure).
    """

    id: strawberry.ID
    status: DeletionStatus
    reason: str | None
    data_retained: list[str]
    created_at: datetime
    confirmed_at: datetime | None
    completed_at: datetime | None

    @staticmethod
    def from_model(deletion_request: object) -> AccountDeletionRequestType:
        """Convert AccountDeletionRequest model to GraphQL type.

        Args:
            deletion_request: AccountDeletionRequest model instance.

        Returns:
            AccountDeletionRequestType instance.
        """
        return AccountDeletionRequestType(
            id=strawberry.ID(str(getattr(deletion_request, "id", ""))),  # type: ignore[attr-defined]
            status=DeletionStatus(getattr(deletion_request, "status", "")),  # type: ignore[attr-defined]
            reason=getattr(deletion_request, "reason", None) or None,  # type: ignore[attr-defined]
            data_retained=getattr(deletion_request, "data_retained", None) or [],  # type: ignore[attr-defined]
            created_at=getattr(deletion_request, "created_at", None),  # type: ignore[attr-defined]
            confirmed_at=getattr(deletion_request, "confirmed_at", None),  # type: ignore[attr-defined]
            completed_at=getattr(deletion_request, "completed_at", None),  # type: ignore[attr-defined]
        )


@strawberry.type
class ConsentRecordType:
    """GraphQL type for consent records.

    Represents a user's consent for a specific type of data processing.
    """

    id: strawberry.ID
    consent_type: ConsentType
    granted: bool
    version: str
    granted_at: datetime
    withdrawn_at: datetime | None

    @staticmethod
    def from_model(consent: object) -> ConsentRecordType:
        """Convert ConsentRecord model to GraphQL type.

        Args:
            consent: ConsentRecord model instance.

        Returns:
            ConsentRecordType instance.
        """
        return ConsentRecordType(
            id=strawberry.ID(str(getattr(consent, "id", ""))),  # type: ignore[attr-defined]
            consent_type=ConsentType(getattr(consent, "consent_type", "")),  # type: ignore[attr-defined]
            granted=getattr(consent, "granted", False),  # type: ignore[attr-defined]
            version=getattr(consent, "version", ""),  # type: ignore[attr-defined]
            granted_at=getattr(consent, "granted_at", None),  # type: ignore[attr-defined]
            withdrawn_at=getattr(consent, "withdrawn_at", None),  # type: ignore[attr-defined]
        )


@strawberry.type
class ProcessingRestrictionType:
    """GraphQL type for processing restriction status.

    Represents the current processing restriction status for a user
    under GDPR Article 18 (Right to Restriction of Processing).
    """

    processing_restricted: bool
    restriction_reason: str | None
    restricted_at: datetime | None
    allowed_processing: list[str] | None
    restricted_processing: list[str] | None


@strawberry.type
class DataExportPayload:
    """Response payload for data export mutation."""

    success: bool
    message: str
    export_request: DataExportRequestType | None


@strawberry.type
class AccountDeletionPayload:
    """Response payload for account deletion mutation."""

    success: bool
    message: str
    deletion_request: AccountDeletionRequestType | None


@strawberry.type
class ProcessingRestrictionPayload:
    """Response payload for processing restriction mutation."""

    success: bool
    message: str
    restriction: ProcessingRestrictionType | None


@strawberry.type
class ConsentPayload:
    """Response payload for consent mutation."""

    success: bool
    message: str
    consent: ConsentRecordType | None


@strawberry.input
class RequestDataExportInput:
    """Input for requesting a data export."""

    format: ExportFormat = ExportFormat.JSON


@strawberry.input
class RequestAccountDeletionInput:
    """Input for requesting account deletion."""

    reason: str | None = None


@strawberry.input
class ConfirmAccountDeletionInput:
    """Input for confirming account deletion."""

    token: str
    password: str


@strawberry.input
class CancelAccountDeletionInput:
    """Input for cancelling account deletion."""

    request_id: strawberry.ID


@strawberry.input
class ProcessingRestrictionInput:
    """Input for toggling processing restriction."""

    restrict: bool
    reason: str | None = None


@strawberry.input
class UpdateConsentInput:
    """Input for updating consent."""

    consent_type: ConsentType
    granted: bool
