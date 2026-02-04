"""GraphQL mutations for legal document acceptance.

This module provides mutations for users to accept legal documents
and for admins to create new document versions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.legal_document_service import LegalDocumentService  # type: ignore[import]

from syntek_graphql_compliance.types.legal import (  # type: ignore[import]
    AcceptDocumentInput,
    AcceptDocumentPayload,
    AcceptMultipleDocumentsInput,
    AcceptMultipleDocumentsPayload,
    CreateLegalDocumentInput,
    CreateLegalDocumentPayload,
    LegalAcceptanceType,
    LegalDocumentType,
)


def get_client_ip(request) -> str | None:
    """Extract client IP address from request.

    Args:
        request: Django HTTP request

    Returns:
        IP address string or None
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_user_agent(request) -> str:
    """Extract user agent from request.

    Args:
        request: Django HTTP request

    Returns:
        User agent string
    """
    return request.META.get("HTTP_USER_AGENT", "")


@strawberry.type
class LegalMutations:
    """GraphQL mutations for legal document acceptance."""

    @strawberry.mutation
    def accept_legal_document(
        self,
        info: Info,
        input: AcceptDocumentInput,
    ) -> AcceptDocumentPayload:
        """Accept a legal document.

        Records user acceptance of a specific document version.
        Requires authentication.

        Args:
            info: Strawberry request info
            input: AcceptDocumentInput with document ID

        Returns:
            AcceptDocumentPayload with result
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return AcceptDocumentPayload(
                success=False,
                error="Authentication required",
            )

        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        result = LegalDocumentService.record_acceptance(
            user=user,
            document_id=input.document_id,
            ip_address=ip_address,
            user_agent=user_agent,
            acceptance_method=input.acceptance_method.value,
        )

        if not result.success:
            return AcceptDocumentPayload(
                success=False,
                error=result.error,
            )

        return AcceptDocumentPayload(
            success=True,
            acceptance=LegalAcceptanceType.from_model(result.acceptance),
        )

    @strawberry.mutation
    def accept_multiple_legal_documents(
        self,
        info: Info,
        input: AcceptMultipleDocumentsInput,
    ) -> AcceptMultipleDocumentsPayload:
        """Accept multiple legal documents at once.

        Used during registration to accept T&Cs and Privacy Policy together.
        Requires authentication.

        Args:
            info: Strawberry request info
            input: AcceptMultipleDocumentsInput with document IDs

        Returns:
            AcceptMultipleDocumentsPayload with results
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return AcceptMultipleDocumentsPayload(
                success=False,
                acceptances=[],
                errors=["Authentication required"],
            )

        request = info.context.request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        results = LegalDocumentService.record_registration_acceptances(
            user=user,
            document_ids=input.document_ids,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        acceptances = []
        errors = []

        for result in results:
            if result.success and result.acceptance:
                acceptances.append(LegalAcceptanceType.from_model(result.acceptance))
            elif result.error:
                errors.append(result.error)

        return AcceptMultipleDocumentsPayload(
            success=len(errors) == 0,
            acceptances=acceptances,
            errors=errors,
        )

    @strawberry.mutation
    def create_legal_document(
        self,
        info: Info,
        input: CreateLegalDocumentInput,
    ) -> CreateLegalDocumentPayload:
        """Create a new legal document version (admin only).

        Creates a new version of a legal document. Only staff users
        can create documents.

        Args:
            info: Strawberry request info
            input: CreateLegalDocumentInput with document details

        Returns:
            CreateLegalDocumentPayload with result
        """
        user = info.context.request.user
        if not user.is_authenticated:
            return CreateLegalDocumentPayload(
                success=False,
                error="Authentication required",
            )

        if not user.is_staff:
            return CreateLegalDocumentPayload(
                success=False,
                error="Staff access required",
            )

        try:
            document = LegalDocumentService.create_document(
                document_type=input.document_type.value,
                version=input.version,
                title=input.title,
                content_url=input.content_url,
                content=input.content,
                effective_date=input.effective_date,
                summary_of_changes=input.summary_of_changes,
                requires_re_acceptance=input.requires_re_acceptance,
                is_active=input.is_active,
                created_by=user,
            )

            return CreateLegalDocumentPayload(
                success=True,
                document=LegalDocumentType.from_model(document),
            )
        except Exception as e:
            return CreateLegalDocumentPayload(
                success=False,
                error=str(e),
            )
