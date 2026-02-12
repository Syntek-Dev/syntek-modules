"""GraphQL queries for GDPR compliance operations.

This module provides GraphQL queries for accessing GDPR-related data
including data export requests, account deletion requests, consent
records, and processing restriction status.

All queries require authentication and return only data belonging
to the authenticated user.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.models import (  # type: ignore[import]
    AccountDeletionRequest,
    ConsentRecord,
    DataExportRequest,
)
from apps.core.services.processing_restriction_service import (  # type: ignore[import]
    ProcessingRestrictionService,
)

from syntek_graphql_compliance.types.gdpr import (  # type: ignore[import]
    AccountDeletionRequestType,
    ConsentRecordType,
    DataExportRequestType,
    ProcessingRestrictionType,
)


@strawberry.type
class GDPRQuery:
    """GraphQL queries for GDPR compliance.

    Provides access to user's GDPR-related data including export requests,
    deletion requests, consent records, and processing restriction status.
    """

    @strawberry.field
    def my_data_exports(
        self,
        info: Info,
        limit: int = 10,
    ) -> list[DataExportRequestType]:
        """Get current user's data export requests.

        Returns a list of the user's data export requests, ordered by
        most recent first.

        Args:
            info: GraphQL resolver info containing request context.
            limit: Maximum number of exports to return (default: 10, max: 50).

        Returns:
            List of DataExportRequestType instances.

        Raises:
            PermissionError: If user is not authenticated.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            raise PermissionError("Authentication required.")

        # Clamp limit
        limit = min(max(1, limit), 50)

        exports = DataExportRequest.objects.filter(user=user).order_by("-created_at")[:limit]

        return [DataExportRequestType.from_model(export) for export in exports]

    @strawberry.field
    def my_data_export(
        self,
        info: Info,
        request_id: strawberry.ID,
    ) -> DataExportRequestType | None:
        """Get a specific data export request.

        Args:
            info: GraphQL resolver info containing request context.
            request_id: UUID of the export request.

        Returns:
            DataExportRequestType if found, None otherwise.

        Raises:
            PermissionError: If user is not authenticated.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            raise PermissionError("Authentication required.")

        try:
            export = DataExportRequest.objects.get(id=UUID(str(request_id)), user=user)
            return DataExportRequestType.from_model(export)
        except (DataExportRequest.DoesNotExist, ValueError):
            return None

    @strawberry.field
    def my_deletion_requests(
        self,
        info: Info,
        limit: int = 10,
    ) -> list[AccountDeletionRequestType]:
        """Get current user's account deletion requests.

        Returns a list of the user's deletion requests, ordered by
        most recent first.

        Args:
            info: GraphQL resolver info containing request context.
            limit: Maximum number of requests to return (default: 10, max: 50).

        Returns:
            List of AccountDeletionRequestType instances.

        Raises:
            PermissionError: If user is not authenticated.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            raise PermissionError("Authentication required.")

        # Clamp limit
        limit = min(max(1, limit), 50)

        requests = AccountDeletionRequest.objects.filter(user=user).order_by("-created_at")[:limit]

        return [AccountDeletionRequestType.from_model(req) for req in requests]

    @strawberry.field
    def my_processing_restriction(
        self,
        info: Info,
    ) -> ProcessingRestrictionType:
        """Get current user's processing restriction status.

        Returns the current processing restriction status including
        what processing is allowed and restricted.

        Args:
            info: GraphQL resolver info containing request context.

        Returns:
            ProcessingRestrictionType with current status.

        Raises:
            PermissionError: If user is not authenticated.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            raise PermissionError("Authentication required.")

        details = ProcessingRestrictionService.get_restriction_details(user)

        return ProcessingRestrictionType(
            processing_restricted=details["processing_restricted"],
            restriction_reason=details["restriction_reason"],
            restricted_at=user.restricted_at if user.processing_restricted else None,
            allowed_processing=details["allowed_processing"],
            restricted_processing=details["restricted_processing"],
        )

    @strawberry.field
    def my_consents(
        self,
        info: Info,
    ) -> list[ConsentRecordType]:
        """Get current user's consent records.

        Returns a list of the user's active consent records.

        Args:
            info: GraphQL resolver info containing request context.

        Returns:
            List of ConsentRecordType instances.

        Raises:
            PermissionError: If user is not authenticated.
        """
        user = info.context.request.user
        if not user.is_authenticated:
            raise PermissionError("Authentication required.")

        # Get most recent consent record for each type
        consents = (
            ConsentRecord.objects.filter(user=user)
            .order_by("consent_type", "-granted_at")
            .distinct("consent_type")
        )

        return [ConsentRecordType.from_model(consent) for consent in consents]
