"""Legal document service for managing T&Cs, Privacy Policy, and DPAs.

This module provides the business logic for legal document management,
including version control, user acceptance tracking, and compliance checks.

GDPR Compliance:
- Article 7(1): Demonstrate consent was given
- Article 13/14: Transparency requirements
- Article 28: Data Processing Agreement management
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from syntek_legal.models.legal_acceptance import LegalAcceptance
from syntek_legal.models.legal_document import LegalDocument

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class AcceptanceResult:
    """Result of a legal document acceptance operation."""

    success: bool
    acceptance: LegalAcceptance | None = None
    error: str | None = None


@dataclass
class DocumentCheckResult:
    """Result of checking user's document acceptance status."""

    all_accepted: bool
    pending_documents: list[LegalDocument]
    accepted_documents: list[LegalDocument]


@dataclass
class RegistrationRequirements:
    """Documents required for user registration."""

    terms_and_conditions: LegalDocument | None
    privacy_policy: LegalDocument | None
    missing_documents: list[str]

    @property
    def is_complete(self) -> bool:
        """Check if all required documents are available."""
        return len(self.missing_documents) == 0


class LegalDocumentService:
    """Service for managing legal documents and user acceptances.

    Provides methods for:
    - Creating and versioning legal documents
    - Recording user acceptances
    - Checking compliance status
    - Managing re-acceptance requirements
    """

    # Document types required for registration
    REGISTRATION_REQUIRED_TYPES = [
        LegalDocument.DocumentType.TERMS_AND_CONDITIONS,
        LegalDocument.DocumentType.PRIVACY_POLICY,
    ]

    # Document types that may require periodic re-acceptance
    RE_ACCEPTANCE_TYPES = [
        LegalDocument.DocumentType.TERMS_AND_CONDITIONS,
        LegalDocument.DocumentType.PRIVACY_POLICY,
        LegalDocument.DocumentType.COOKIE_POLICY,
    ]

    @classmethod
    def create_document(
        cls,
        document_type: str,
        version: str,
        title: str,
        content_url: str,
        content: str,
        effective_date: timezone.datetime | None = None,
        summary_of_changes: str = "",
        requires_re_acceptance: bool = False,
        is_active: bool = True,
        organisation=None,
        created_by=None,
    ) -> LegalDocument:
        """Create a new legal document version.

        Args:
            document_type: Type of document (from LegalDocument.DocumentType)
            version: Semantic version string (e.g., "1.0.0")
            title: Human-readable document title
            content_url: URL to the full document
            content: Document content for hash computation
            effective_date: When document becomes active (default: now)
            summary_of_changes: Description of changes from previous version
            requires_re_acceptance: Whether users must re-accept this version
            is_active: Whether this is the active version
            organisation: Optional organisation for org-specific documents
            created_by: Admin user creating the document

        Returns:
            Created LegalDocument instance
        """
        content_hash = LegalDocument.compute_content_hash(content)

        document = LegalDocument.objects.create(  # type: ignore[attr-defined]
            document_type=document_type,
            version=version,
            title=title,
            content_hash=content_hash,
            content_url=content_url,
            effective_date=effective_date or timezone.now(),
            summary_of_changes=summary_of_changes,
            requires_re_acceptance=requires_re_acceptance,
            is_active=is_active,
            organisation=organisation,
            created_by=created_by,
        )

        logger.info(
            "Created legal document: %s v%s (active=%s, re-accept=%s)",
            document_type,
            version,
            is_active,
            requires_re_acceptance,
        )

        return document

    @classmethod
    def get_registration_requirements(cls) -> RegistrationRequirements:
        """Get documents required for user registration.

        Returns:
            RegistrationRequirements with available documents and any missing types
        """
        terms = LegalDocument.get_active_document(LegalDocument.DocumentType.TERMS_AND_CONDITIONS)
        privacy = LegalDocument.get_active_document(LegalDocument.DocumentType.PRIVACY_POLICY)

        missing = []
        if not terms:
            missing.append("Terms and Conditions")
        if not privacy:
            missing.append("Privacy Policy")

        return RegistrationRequirements(
            terms_and_conditions=terms,
            privacy_policy=privacy,
            missing_documents=missing,
        )

    @classmethod
    def check_user_compliance(cls, user) -> DocumentCheckResult:
        """Check if user has accepted all required documents.

        Checks both:
        1. Initial acceptance of required documents
        2. Re-acceptance of updated versions with requires_re_acceptance=True

        Args:
            user: User to check compliance for

        Returns:
            DocumentCheckResult with acceptance status
        """
        pending = []
        accepted = []

        for doc_type in cls.RE_ACCEPTANCE_TYPES:
            active_doc = LegalDocument.get_active_document(doc_type)
            if not active_doc:
                continue

            has_accepted = LegalAcceptance.has_user_accepted_document(user, active_doc)

            if has_accepted:
                accepted.append(active_doc)
            else:
                # Check if this is a new version requiring re-acceptance
                if active_doc.requires_re_acceptance:
                    pending.append(active_doc)
                else:
                    # Check if user has accepted any version of this type
                    has_any = LegalAcceptance.has_user_accepted_document_type(user, doc_type)
                    if not has_any:
                        pending.append(active_doc)
                    else:
                        accepted.append(active_doc)

        return DocumentCheckResult(
            all_accepted=len(pending) == 0,
            pending_documents=pending,
            accepted_documents=accepted,
        )

    @classmethod
    def record_acceptance(
        cls,
        user,
        document_id: UUID,
        ip_address: str | None = None,
        user_agent: str = "",
        acceptance_method: str = "checkbox",
        metadata: dict | None = None,
    ) -> AcceptanceResult:
        """Record user acceptance of a legal document.

        Args:
            user: User accepting the document
            document_id: UUID of the document being accepted
            ip_address: Optional IP address string
            user_agent: Optional browser user agent
            acceptance_method: Method of acceptance
            metadata: Optional additional context

        Returns:
            AcceptanceResult with success status and acceptance record
        """
        with transaction.atomic():  # type: ignore[attr-defined]
            try:
                document = LegalDocument.objects.get(id=document_id)  # type: ignore[attr-defined]
            except LegalDocument.DoesNotExist:  # type: ignore[attr-defined]
                return AcceptanceResult(
                    success=False,
                    error=f"Document not found: {document_id}",
                )

            # Check if already accepted
            if LegalAcceptance.has_user_accepted_document(user, document):
                existing = LegalAcceptance.objects.filter(user=user, document=document).first()  # type: ignore[attr-defined]
                return AcceptanceResult(
                    success=True,
                    acceptance=existing,
                    error=None,
                )

            acceptance = LegalAcceptance.record_acceptance(
                user=user,
                document=document,
                ip_address=ip_address,
                user_agent=user_agent,
                acceptance_method=acceptance_method,
                metadata=metadata,
            )

            logger.info(
                "User %s accepted document %s v%s",
                user.email,
                document.document_type,
                document.version,
            )

            return AcceptanceResult(
                success=True,
                acceptance=acceptance,
            )

    @classmethod
    def record_registration_acceptances(
        cls,
        user,
        document_ids: list[UUID],
        ip_address: str | None = None,
        user_agent: str = "",
        metadata: dict | None = None,
    ) -> list[AcceptanceResult]:
        """Record acceptance of multiple documents during registration.

        Args:
            user: User accepting the documents
            document_ids: List of document UUIDs being accepted
            ip_address: Optional IP address string
            user_agent: Optional browser user agent
            metadata: Optional additional context

        Returns:
            List of AcceptanceResult for each document
        """
        with transaction.atomic():  # type: ignore[attr-defined]
            results = []

            for doc_id in document_ids:
                result = cls.record_acceptance(
                    user=user,
                    document_id=doc_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    acceptance_method="checkbox",
                    metadata=metadata,
                )
                results.append(result)

            return results

    @classmethod
    def get_user_acceptances(cls, user) -> list[LegalAcceptance]:
        """Get all acceptance records for a user.

        Args:
            user: User to get acceptances for

        Returns:
            List of LegalAcceptance records ordered by acceptance date
        """
        return list(
            LegalAcceptance.objects.filter(user=user)  # type: ignore[attr-defined]
            .select_related("document")
            .order_by("-accepted_at")
        )

    @classmethod
    def get_active_documents(
        cls,
        organisation=None,
    ) -> dict[str, LegalDocument]:
        """Get all active documents.

        Args:
            organisation: Optional organisation for org-specific documents

        Returns:
            Dictionary mapping document types to active documents
        """
        documents = LegalDocument.objects.filter(  # type: ignore[attr-defined]
            is_active=True,
            organisation=organisation,
        )

        return {doc.document_type: doc for doc in documents}

    @classmethod
    def get_document_history(
        cls,
        document_type: str,
        organisation=None,
    ) -> list[LegalDocument]:
        """Get version history for a document type.

        Args:
            document_type: Type of document to get history for
            organisation: Optional organisation filter

        Returns:
            List of LegalDocuments ordered by version (newest first)
        """
        return list(
            LegalDocument.objects.filter(  # type: ignore[attr-defined]
                document_type=document_type,
                organisation=organisation,
            ).order_by("-effective_date", "-version")
        )

    @classmethod
    def get_acceptance_stats(
        cls,
        document: LegalDocument,
    ) -> dict:
        """Get acceptance statistics for a document.

        Args:
            document: Document to get stats for

        Returns:
            Dictionary with acceptance count and other stats
        """
        acceptances = LegalAcceptance.objects.filter(document=document)  # type: ignore[attr-defined]

        return {
            "document_id": str(document.id),
            "document_type": document.document_type,
            "version": document.version,
            "total_acceptances": acceptances.count(),
            "first_acceptance": acceptances.order_by("accepted_at")
            .values_list("accepted_at", flat=True)
            .first(),
            "latest_acceptance": acceptances.order_by("-accepted_at")
            .values_list("accepted_at", flat=True)
            .first(),
        }

    @classmethod
    def requires_acceptance_before_login(cls, user) -> bool:
        """Check if user must accept documents before proceeding.

        Used to block login until critical documents are accepted.

        Args:
            user: User to check

        Returns:
            True if user must accept documents before login
        """
        compliance = cls.check_user_compliance(user)

        # Check if any pending documents are critical (T&Cs or Privacy Policy)
        critical_types = {
            LegalDocument.DocumentType.TERMS_AND_CONDITIONS,
            LegalDocument.DocumentType.PRIVACY_POLICY,
        }

        return any(doc.document_type in critical_types for doc in compliance.pending_documents)
