"""GraphQL queries for legal documents.

This module provides queries for retrieving legal documents and
checking user compliance status.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 - Required at runtime for Strawberry GraphQL

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.models import LegalDocument as LegalDocumentModel  # type: ignore[import]
from apps.core.services.legal_document_service import LegalDocumentService  # type: ignore[import]

from syntek_graphql_compliance.types.legal import (  # type: ignore[import]
    ComplianceStatusType,
    LegalAcceptanceType,
    LegalDocumentKind,
    LegalDocumentType,
    RegistrationRequirementsType,
)


@strawberry.type
class LegalQuery:
    """GraphQL queries for legal documents and compliance."""

    @strawberry.field
    def registration_requirements(self) -> RegistrationRequirementsType:
        """Get documents required for user registration.

        Returns documents that must be accepted during registration.
        This is a public query - no authentication required.

        Returns:
            RegistrationRequirementsType with T&Cs and Privacy Policy
        """
        requirements = LegalDocumentService.get_registration_requirements()

        return RegistrationRequirementsType(
            terms_and_conditions=(
                LegalDocumentType.from_model(requirements.terms_and_conditions)
                if requirements.terms_and_conditions
                else None
            ),
            privacy_policy=(
                LegalDocumentType.from_model(requirements.privacy_policy)
                if requirements.privacy_policy
                else None
            ),
            is_complete=requirements.is_complete,
            missing_documents=requirements.missing_documents,
        )

    @strawberry.field
    def active_legal_documents(self) -> list[LegalDocumentType]:
        """Get all currently active legal documents.

        Returns all active document versions (T&Cs, Privacy Policy, etc.).
        This is a public query - no authentication required.

        Returns:
            List of active LegalDocumentType
        """
        documents = LegalDocumentModel.objects.filter(
            is_active=True,
            organisation__isnull=True,  # Platform-wide documents only
        )

        return [LegalDocumentType.from_model(doc) for doc in documents]

    @strawberry.field
    def legal_document(self, id: UUID) -> LegalDocumentType | None:
        """Get a specific legal document by ID.

        Args:
            id: UUID of the document to retrieve

        Returns:
            LegalDocumentType or None if not found
        """
        try:
            document = LegalDocumentModel.objects.get(id=id)
            return LegalDocumentType.from_model(document)
        except LegalDocumentModel.DoesNotExist:
            return None

    @strawberry.field
    def legal_document_by_type(
        self,
        document_type: LegalDocumentKind,
    ) -> LegalDocumentType | None:
        """Get the active document for a specific type.

        Args:
            document_type: Type of document to retrieve

        Returns:
            Active LegalDocumentType or None if not found
        """
        document = LegalDocumentModel.get_active_document(document_type.value)
        if document:
            return LegalDocumentType.from_model(document)
        return None

    @strawberry.field
    def legal_document_history(
        self,
        document_type: LegalDocumentKind,
    ) -> list[LegalDocumentType]:
        """Get version history for a document type.

        Args:
            document_type: Type of document to get history for

        Returns:
            List of document versions ordered by date (newest first)
        """
        documents = LegalDocumentService.get_document_history(document_type.value)
        return [LegalDocumentType.from_model(doc) for doc in documents]

    @strawberry.field
    def my_compliance_status(self, info: Info) -> ComplianceStatusType:
        """Get current user's legal document compliance status.

        Requires authentication. Returns which documents the user
        has accepted and which require acceptance.

        Args:
            info: Strawberry request info

        Returns:
            ComplianceStatusType with acceptance status
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return ComplianceStatusType(
                all_accepted=False,
                pending_documents=[],
                accepted_documents=[],
                requires_action_before_login=True,
            )

        compliance = LegalDocumentService.check_user_compliance(user)
        requires_action = LegalDocumentService.requires_acceptance_before_login(user)

        return ComplianceStatusType(
            all_accepted=compliance.all_accepted,
            pending_documents=[
                LegalDocumentType.from_model(doc) for doc in compliance.pending_documents
            ],
            accepted_documents=[
                LegalDocumentType.from_model(doc) for doc in compliance.accepted_documents
            ],
            requires_action_before_login=requires_action,
        )

    @strawberry.field
    def my_legal_acceptances(self, info: Info) -> list[LegalAcceptanceType]:
        """Get current user's legal document acceptance history.

        Requires authentication. Returns all documents the user has accepted.

        Args:
            info: Strawberry request info

        Returns:
            List of LegalAcceptanceType ordered by date (newest first)
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return []

        acceptances = LegalDocumentService.get_user_acceptances(user)
        return [LegalAcceptanceType.from_model(acc) for acc in acceptances]
