"""LegalAcceptance model for tracking user acceptance of legal documents.

This module records when users accept Terms & Conditions, Privacy Policy,
Cookie Policy, and DPAs. Records are retained for legal compliance even
after user account deletion.

GDPR Compliance:
- Article 7(1): Controller must demonstrate consent was given
- Article 17(3)(b): Retention for legal claims defence
- Recital 42: Consent must be demonstrable
"""

from __future__ import annotations

import hashlib
import uuid
from typing import TYPE_CHECKING

from django.db import models

# Import encryption utilities if available
try:
    from syntek_authentication.utils.encryption import IPEncryption  # type: ignore[import]
except ImportError:
    IPEncryption = None  # type: ignore[assignment, misc]

if TYPE_CHECKING:
    pass


class LegalAcceptance(models.Model):
    """Record user acceptance of legal documents.

    Tracks when users accept legal documents with full audit trail.
    Records are preserved for legal compliance even after user deletion
    by storing a hashed email for identification.

    Retention: 7 years after account deletion (legal compliance)

    Attributes:
        id: UUID primary key
        user: Foreign key to User (SET_NULL on deletion for retention)
        document: Foreign key to LegalDocument (PROTECT - never delete accepted docs)
        accepted_at: Timestamp when acceptance occurred
        ip_address: Encrypted IP address at time of acceptance
        user_agent: Browser user agent string
        user_email_hash: SHA-256 hash of user email (for audit after deletion)
        acceptance_method: How acceptance was given (checkbox, click, etc.)
        metadata: Additional acceptance context (JSON)
    """

    class AcceptanceMethod(models.TextChoices):
        """Methods by which user can accept legal documents."""

        CHECKBOX = "checkbox", "Checkbox Agreement"  # type: ignore[assignment]
        CLICK_WRAP = "click_wrap", "Click-Wrap Agreement"  # type: ignore[assignment]
        BROWSE_WRAP = "browse_wrap", "Browse-Wrap Agreement"  # type: ignore[assignment]
        SIGNED = "signed", "Signed Agreement"  # type: ignore[assignment]
        API = "api", "API Acceptance"  # type: ignore[assignment]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        "syntek_authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="legal_acceptances",
        help_text="User who accepted (null after account deletion)",
    )

    document = models.ForeignKey(
        "syntek_legal.LegalDocument",
        on_delete=models.PROTECT,
        related_name="acceptances",
        help_text="Legal document that was accepted (never deleted)",
    )

    accepted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when document was accepted",
    )

    ip_address = models.BinaryField(
        null=True,
        blank=True,
        help_text="Encrypted IP address at time of acceptance",
    )

    user_agent = models.TextField(
        blank=True,
        default="",
        help_text="Browser user agent string at time of acceptance",
    )

    user_email_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of user email (for audit after account deletion)",
    )

    acceptance_method = models.CharField(
        max_length=20,
        choices=AcceptanceMethod.choices,
        default=AcceptanceMethod.CHECKBOX,
        help_text="Method by which acceptance was given",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional acceptance context (referrer, language, etc.)",
    )

    class Meta:
        db_table = "legal_acceptances"
        verbose_name = "Legal Acceptance"
        verbose_name_plural = "Legal Acceptances"
        ordering = ["-accepted_at"]
        indexes = [
            models.Index(fields=["user", "document"]),
            models.Index(fields=["user", "-accepted_at"]),
            models.Index(fields=["document", "-accepted_at"]),
            models.Index(fields=["user_email_hash"]),
            models.Index(fields=["accepted_at"]),
        ]

    def __str__(self) -> str:
        """Return acceptance description."""
        email_hash: str = self.user_email_hash  # type: ignore[assignment]
        user_email = getattr(self.user, "email", "Unknown") if self.user else "Unknown"
        user_desc = user_email if user_email != "Unknown" else f"[Deleted: {email_hash[:8]}...]"
        return f"{user_desc} accepted {self.document} at {self.accepted_at}"

    def save(self, *args, **kwargs):
        """Save acceptance record with email hash computation.

        Automatically computes user_email_hash if user is set and hash is empty.
        """
        if self.user and not self.user_email_hash:
            user_email = getattr(self.user, "email", None)
            if user_email:
                self.user_email_hash = self.compute_email_hash(user_email)

        super().save(*args, **kwargs)

    @staticmethod
    def compute_email_hash(email: str) -> str:
        """Compute SHA-256 hash of email address.

        Args:
            email: Email address to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(email.lower().encode("utf-8")).hexdigest()

    def get_ip_address(self) -> str | None:
        """Get decrypted IP address.

        Returns:
            Decrypted IP address string or None if not set
        """
        if not self.ip_address or not IPEncryption:
            return None
        return IPEncryption.decrypt_ip(self.ip_address)

    def set_ip_address(self, ip_address: str) -> None:
        """Set encrypted IP address.

        Args:
            ip_address: IP address string to encrypt and store
        """
        if IPEncryption:
            self.ip_address = IPEncryption.encrypt_ip(ip_address)

    @classmethod
    def record_acceptance(
        cls,
        user,
        document,
        ip_address: str | None = None,
        user_agent: str = "",
        acceptance_method: str = "checkbox",
        metadata: dict | None = None,
    ) -> LegalAcceptance:
        """Record user acceptance of a legal document.

        Args:
            user: User accepting the document
            document: LegalDocument being accepted
            ip_address: Optional IP address string
            user_agent: Optional browser user agent
            acceptance_method: Method of acceptance
            metadata: Optional additional context

        Returns:
            Created LegalAcceptance record
        """
        acceptance = cls(
            user=user,
            document=document,
            user_email_hash=cls.compute_email_hash(user.email),
            user_agent=user_agent,
            acceptance_method=acceptance_method,
            metadata=metadata or {},
        )

        if ip_address:
            acceptance.set_ip_address(ip_address)

        acceptance.save()
        return acceptance

    @classmethod
    def has_user_accepted_document(cls, user, document) -> bool:
        """Check if user has accepted a specific document version.

        Args:
            user: User to check
            document: LegalDocument to check acceptance for

        Returns:
            True if user has accepted this document version
        """
        return cls.objects.filter(user=user, document=document).exists()  # type: ignore[attr-defined]

    @classmethod
    def has_user_accepted_document_type(cls, user, document_type: str) -> bool:
        """Check if user has accepted any version of a document type.

        Args:
            user: User to check
            document_type: Document type to check (e.g., "terms_and_conditions")

        Returns:
            True if user has accepted any version of this document type
        """
        return cls.objects.filter(  # type: ignore[attr-defined]
            user=user,
            document__document_type=document_type,
        ).exists()

    @classmethod
    def get_user_acceptances(cls, user):
        """Get all acceptance records for a user.

        Args:
            user: User to get acceptances for

        Returns:
            QuerySet of LegalAcceptance records
        """
        return cls.objects.filter(user=user).select_related("document")  # type: ignore[attr-defined]

    @classmethod
    def get_latest_acceptance_for_type(
        cls,
        user,
        document_type: str,
    ) -> LegalAcceptance | None:
        """Get the most recent acceptance for a document type.

        Args:
            user: User to check
            document_type: Document type to get acceptance for

        Returns:
            Most recent LegalAcceptance or None
        """
        return (
            cls.objects.filter(  # type: ignore[attr-defined]
                user=user,
                document__document_type=document_type,
            )
            .select_related("document")
            .order_by("-accepted_at")
            .first()
        )
