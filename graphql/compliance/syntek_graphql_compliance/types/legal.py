"""GraphQL types for legal documents and acceptances.

This module defines Strawberry GraphQL types for legal document management,
including T&Cs, Privacy Policy, Cookie Policy, and DPAs.

GDPR Compliance:
- Article 7(1): Demonstrate consent was given
- Article 13/14: Transparency requirements
- Article 28: Data Processing Agreement management
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Required at runtime for Strawberry GraphQL
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - Required at runtime for Strawberry GraphQL

import strawberry

if TYPE_CHECKING:
    from apps.core.models.legal_acceptance import LegalAcceptance as LegalAcceptanceModel
    from apps.core.models.legal_document import LegalDocument as LegalDocumentModel


@strawberry.enum
class LegalDocumentKind(Enum):
    """Types of legal documents supported by the system."""

    TERMS_AND_CONDITIONS = "terms_and_conditions"
    PRIVACY_POLICY = "privacy_policy"
    COOKIE_POLICY = "cookie_policy"
    ACCEPTABLE_USE = "acceptable_use"
    DATA_PROCESSING_AGREEMENT = "dpa"
    SUB_PROCESSOR_LIST = "sub_processor_list"
    SLA = "sla"


@strawberry.enum
class AcceptanceMethod(Enum):
    """Methods by which user can accept legal documents."""

    CHECKBOX = "checkbox"
    CLICK_WRAP = "click_wrap"
    BROWSE_WRAP = "browse_wrap"
    SIGNED = "signed"
    API = "api"


@strawberry.type
class LegalDocumentType:
    """GraphQL type representing a legal document version.

    Attributes:
        id: UUID of the document
        document_type: Type of legal document
        version: Semantic version number
        title: Human-readable title
        content_url: URL to the full document
        effective_date: When this version became active
        summary_of_changes: Description of changes from previous version
        requires_re_acceptance: Whether users must re-accept this version
        is_active: Whether this is the current active version
        created_at: When this version was created
    """

    id: UUID
    document_type: LegalDocumentKind
    version: str
    title: str
    content_url: str
    effective_date: datetime
    summary_of_changes: str
    requires_re_acceptance: bool
    is_active: bool
    created_at: datetime

    @classmethod
    def from_model(cls, model: LegalDocumentModel | object) -> LegalDocumentType:
        """Create GraphQL type from Django model.

        Args:
            model: LegalDocument model instance

        Returns:
            LegalDocumentType instance
        """
        return cls(
            id=model.id,  # type: ignore[attr-defined]
            document_type=LegalDocumentKind(model.document_type),  # type: ignore[attr-defined]
            version=model.version,  # type: ignore[attr-defined]
            title=model.title,  # type: ignore[attr-defined]
            content_url=model.content_url,  # type: ignore[attr-defined]
            effective_date=model.effective_date,  # type: ignore[attr-defined]
            summary_of_changes=model.summary_of_changes,  # type: ignore[attr-defined]
            requires_re_acceptance=model.requires_re_acceptance,  # type: ignore[attr-defined]
            is_active=model.is_active,  # type: ignore[attr-defined]
            created_at=model.created_at,  # type: ignore[attr-defined]
        )


@strawberry.type
class LegalAcceptanceType:
    """GraphQL type representing a user's acceptance of a legal document.

    Attributes:
        id: UUID of the acceptance record
        document: The document that was accepted
        accepted_at: When the document was accepted
        acceptance_method: How the acceptance was given
    """

    id: UUID
    document: LegalDocumentType
    accepted_at: datetime
    acceptance_method: AcceptanceMethod

    @classmethod
    def from_model(cls, model: LegalAcceptanceModel | object) -> LegalAcceptanceType:
        """Create GraphQL type from Django model.

        Args:
            model: LegalAcceptance model instance

        Returns:
            LegalAcceptanceType instance
        """
        return cls(
            id=model.id,  # type: ignore[attr-defined]
            document=LegalDocumentType.from_model(model.document),  # type: ignore[attr-defined]
            accepted_at=model.accepted_at,  # type: ignore[attr-defined]
            acceptance_method=AcceptanceMethod(model.acceptance_method),  # type: ignore[attr-defined]
        )


@strawberry.type
class RegistrationRequirementsType:
    """Documents required for user registration.

    Attributes:
        terms_and_conditions: Active T&Cs document (if available)
        privacy_policy: Active Privacy Policy document (if available)
        is_complete: Whether all required documents are available
        missing_documents: List of missing document types
    """

    terms_and_conditions: LegalDocumentType | None
    privacy_policy: LegalDocumentType | None
    is_complete: bool
    missing_documents: list[str]


@strawberry.type
class ComplianceStatusType:
    """User's legal document compliance status.

    Attributes:
        all_accepted: Whether all required documents are accepted
        pending_documents: Documents requiring acceptance
        accepted_documents: Documents already accepted
        requires_action_before_login: Whether user must accept docs before login
    """

    all_accepted: bool
    pending_documents: list[LegalDocumentType]
    accepted_documents: list[LegalDocumentType]
    requires_action_before_login: bool


# Input types for mutations


@strawberry.input
class AcceptDocumentInput:
    """Input for accepting a single legal document.

    Attributes:
        document_id: UUID of the document to accept
        acceptance_method: How acceptance is being given
    """

    document_id: UUID
    acceptance_method: AcceptanceMethod = AcceptanceMethod.CHECKBOX


@strawberry.input
class AcceptMultipleDocumentsInput:
    """Input for accepting multiple documents (e.g., during registration).

    Attributes:
        document_ids: List of document UUIDs to accept
        acceptance_method: How acceptance is being given
    """

    document_ids: list[UUID]
    acceptance_method: AcceptanceMethod = AcceptanceMethod.CHECKBOX


# Payload types for mutations


@strawberry.type
class AcceptDocumentPayload:
    """Result of accepting a legal document.

    Attributes:
        success: Whether acceptance was recorded
        acceptance: The acceptance record (if successful)
        error: Error message (if failed)
    """

    success: bool
    acceptance: LegalAcceptanceType | None = None
    error: str | None = None


@strawberry.type
class AcceptMultipleDocumentsPayload:
    """Result of accepting multiple documents.

    Attributes:
        success: Whether all acceptances were recorded
        acceptances: List of acceptance records
        errors: List of error messages for failed acceptances
    """

    success: bool
    acceptances: list[LegalAcceptanceType]
    errors: list[str]


# Admin input types


@strawberry.input
class CreateLegalDocumentInput:
    """Input for creating a new legal document version (admin only).

    Attributes:
        document_type: Type of legal document
        version: Semantic version number
        title: Human-readable title
        content_url: URL to the full document
        content: Document content (for hash computation)
        effective_date: When this version becomes active
        summary_of_changes: Description of changes from previous version
        requires_re_acceptance: Whether users must re-accept this version
        is_active: Whether to set as the active version
    """

    document_type: LegalDocumentKind
    version: str
    title: str
    content_url: str
    content: str
    effective_date: datetime | None = None
    summary_of_changes: str = ""
    requires_re_acceptance: bool = False
    is_active: bool = True


@strawberry.type
class CreateLegalDocumentPayload:
    """Result of creating a legal document.

    Attributes:
        success: Whether document was created
        document: The created document (if successful)
        error: Error message (if failed)
    """

    success: bool
    document: LegalDocumentType | None = None
    error: str | None = None
