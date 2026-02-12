"""LegalDocument model for Terms & Conditions, Privacy Policy, and DPAs.

This module implements legal document version management for GDPR compliance.
Stores versioned legal documents with content hashes to prove what users agreed to.

GDPR Compliance:
- Article 13/14: Privacy Policy transparency requirements
- Article 28: Data Processing Agreement requirements
- Article 7(1): Demonstrate consent was given
"""

from __future__ import annotations

import hashlib
import uuid
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    pass


class LegalDocument(models.Model):
    """Store versioned legal documents for compliance tracking.

    Maintains a complete history of all legal document versions to prove
    exactly what terms users accepted. Documents are never deleted, only
    superseded by newer versions.

    Attributes:
        id: UUID primary key
        document_type: Type of legal document (T&Cs, Privacy Policy, DPA, etc.)
        version: Semantic version number (e.g., "1.0.0", "2.1.0")
        title: Human-readable document title
        content_hash: SHA-256 hash of document content for integrity verification
        content_url: URL to the full document (internal or external)
        effective_date: Date when this version becomes/became active
        summary_of_changes: Description of what changed from previous version
        requires_re_acceptance: Whether existing users must re-accept this version
        is_active: Whether this is the currently active version for its type
        organisation: Optional organisation for organisation-specific DPAs
        created_at: Timestamp when this version was created
        created_by: User who created this version (admin)
    """

    class DocumentType(models.TextChoices):
        """Types of legal documents supported by the system."""

        TERMS_AND_CONDITIONS = "terms_and_conditions", "Terms and Conditions"  # type: ignore[assignment]
        PRIVACY_POLICY = "privacy_policy", "Privacy Policy"  # type: ignore[assignment]
        COOKIE_POLICY = "cookie_policy", "Cookie Policy"  # type: ignore[assignment]
        ACCEPTABLE_USE = "acceptable_use", "Acceptable Use Policy"  # type: ignore[assignment]
        DATA_PROCESSING_AGREEMENT = "dpa", "Data Processing Agreement"  # type: ignore[assignment]
        SUB_PROCESSOR_LIST = "sub_processor_list", "Sub-Processor List"  # type: ignore[assignment]
        SLA = "sla", "Service Level Agreement"  # type: ignore[assignment]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        help_text="Type of legal document",
    )

    version = models.CharField(
        max_length=20,
        help_text="Semantic version number (e.g., 1.0.0, 2.1.0)",
    )

    title = models.CharField(
        max_length=255,
        help_text="Human-readable document title",
    )

    content_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of document content for integrity verification",
    )

    content_url = models.URLField(
        max_length=500,
        help_text="URL to the full document content",
    )

    effective_date = models.DateTimeField(
        help_text="Date when this version becomes/became active",
    )

    summary_of_changes = models.TextField(
        blank=True,
        default="",
        help_text="Summary of changes from previous version",
    )

    requires_re_acceptance = models.BooleanField(
        default=False,  # type: ignore[call-arg]
        help_text="Whether existing users must re-accept this version (material changes)",
    )

    is_active = models.BooleanField(
        default=False,  # type: ignore[call-arg]
        help_text="Whether this is the currently active version for its type",
    )

    # Organisation-specific documents (for DPAs with specific customers)
    organisation = models.ForeignKey(
        "syntek_authentication.Organisation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="legal_documents",
        help_text="Organisation for organisation-specific DPAs (null for platform-wide)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_legal_documents",
        help_text="Admin user who created this version",
    )

    class Meta:
        db_table = "legal_documents"
        verbose_name = "Legal Document"
        verbose_name_plural = "Legal Documents"
        ordering = ["-effective_date", "-version"]
        indexes = [
            models.Index(fields=["document_type", "is_active"]),
            models.Index(fields=["document_type", "-effective_date"]),
            models.Index(fields=["organisation", "document_type"]),
            models.Index(fields=["content_hash"]),
        ]
        constraints = [
            # Only one active version per document type per organisation scope
            models.UniqueConstraint(
                fields=["document_type", "organisation"],
                condition=models.Q(is_active=True),
                name="unique_active_document_per_type_org",
            ),
            # Unique version numbers per document type per organisation scope
            models.UniqueConstraint(
                fields=["document_type", "version", "organisation"],
                name="unique_version_per_document_type_org",
            ),
        ]

    def __str__(self) -> str:
        """Return document description."""
        org_suffix = f" ({self.organisation.name})" if self.organisation else ""
        active_suffix = " [ACTIVE]" if self.is_active else ""
        return f"{self.get_document_type_display()} v{self.version}{org_suffix}{active_suffix}"  # type: ignore[attr-defined]

    def save(self, *args, **kwargs):
        """Save document with validation.

        Ensures only one active document per type/organisation combination.
        """
        if self.is_active:
            # Deactivate other versions of same type and organisation scope
            LegalDocument.objects.filter(  # type: ignore[attr-defined]
                document_type=self.document_type,
                organisation=self.organisation,
                is_active=True,
            ).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA-256 hash of document content.

        Args:
            content: Document content to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def get_active_document(
        cls,
        document_type: str,
        organisation=None,
    ) -> LegalDocument | None:
        """Get the currently active document of a given type.

        Args:
            document_type: Type of document to retrieve
            organisation: Optional organisation for org-specific documents

        Returns:
            Active LegalDocument or None if not found
        """
        return cls.objects.filter(  # type: ignore[attr-defined]
            document_type=document_type,
            organisation=organisation,
            is_active=True,
        ).first()

    @classmethod
    def get_required_documents_for_registration(cls) -> list[LegalDocument]:
        """Get all documents required for user registration.

        Returns:
            List of active LegalDocuments that must be accepted at registration
        """
        required_types = [
            cls.DocumentType.TERMS_AND_CONDITIONS,
            cls.DocumentType.PRIVACY_POLICY,
        ]
        return list(
            cls.objects.filter(  # type: ignore[attr-defined]
                document_type__in=required_types,
                organisation__isnull=True,
                is_active=True,
            )
        )

    @classmethod
    def get_pending_acceptances_for_user(cls, user) -> list[LegalDocument]:
        """Get documents that require user acceptance.

        Returns documents that:
        1. User has never accepted, OR
        2. Have been updated with requires_re_acceptance=True since last acceptance

        Args:
            user: User to check pending acceptances for

        Returns:
            List of LegalDocuments requiring acceptance
        """
        # Import here to avoid circular import at module level
        from syntek_legal.models.legal_acceptance import LegalAcceptance

        pending = []
        required_types = [
            cls.DocumentType.TERMS_AND_CONDITIONS,
            cls.DocumentType.PRIVACY_POLICY,
            cls.DocumentType.COOKIE_POLICY,
        ]

        for doc_type in required_types:
            active_doc = cls.get_active_document(doc_type)
            if not active_doc:
                continue

            # Check if user has accepted this specific version
            has_accepted = LegalAcceptance.objects.filter(  # type: ignore[attr-defined]
                user=user,
                document=active_doc,
            ).exists()

            if not has_accepted:
                # Check if this version requires re-acceptance
                if active_doc.requires_re_acceptance:
                    pending.append(active_doc)
                else:
                    # Check if user has accepted any version of this document type
                    has_any_acceptance = LegalAcceptance.objects.filter(  # type: ignore[attr-defined]
                        user=user,
                        document__document_type=doc_type,
                    ).exists()

                    if not has_any_acceptance:
                        pending.append(active_doc)

        return pending

    def verify_content_hash(self, content: str) -> bool:
        """Verify that content matches stored hash.

        Args:
            content: Content to verify

        Returns:
            True if content matches stored hash
        """
        return self.content_hash == self.compute_content_hash(content)
