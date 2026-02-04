"""GraphQL queries for audit logs and security monitoring.

This module provides queries for accessing audit logs and managing
user sessions with proper permission checks.

Prerequisites:
    - syntek-graphql-core must be installed for permissions
    - syntek-audit must be installed for AuditLog model
    - syntek-sessions must be installed for SessionManagementService
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.permissions import IsAuthenticated  # type: ignore[import]

from syntek_graphql_audit.types import (  # type: ignore[import]
    AuditLogConnection,
    AuditLogFilterInput,
    AuditLogType,
    PaginationInput,
    SessionManagementInfo,
    SessionTokenType,
)


@strawberry.type
class AuditQuery:
    """GraphQL queries for audit logs and session management."""

    @strawberry.field(permission_classes=[IsAuthenticated])
    def my_audit_logs(
        self,
        info: Info,
        filters: AuditLogFilterInput | None = None,
        pagination: PaginationInput | None = None,
    ) -> AuditLogConnection:
        """Get audit logs for the current user.

        Only returns logs for the authenticated user.
        Respects organisation boundaries.

        Args:
            info: GraphQL resolver info containing request context.
            filters: Optional filters for the query.
            pagination: Pagination parameters.

        Returns:
            Paginated connection of audit logs.
        """
        # Import dynamically to avoid circular imports
        try:
            from syntek_audit.models import AuditLog  # type: ignore[import]
        except ImportError as e:
            raise ImportError(
                "syntek-audit package is required for audit log queries. "
                "Install it with: uv pip install syntek-audit"
            ) from e

        user = info.context.request.user

        # Base query: current user only
        queryset = AuditLog.objects.filter(user=user).order_by("-created_at")

        # Apply filters if provided
        if filters:
            if filters.action:
                queryset = queryset.filter(action=filters.action)

            if filters.date_from:
                queryset = queryset.filter(created_at__gte=filters.date_from)

            if filters.date_to:
                queryset = queryset.filter(created_at__lte=filters.date_to)

        # Get total count before pagination
        total_count = queryset.count()

        # Apply pagination
        if pagination is None:
            pagination = PaginationInput()

        limit = min(pagination.limit, 100)  # Max 100 per page
        offset = pagination.offset

        has_previous_page = offset > 0
        has_next_page = (offset + limit) < total_count

        # Get paginated results
        logs = queryset[offset : offset + limit]

        return AuditLogConnection(
            items=[AuditLogType.from_model(log) for log in logs],
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    @strawberry.field(permission_classes=[IsAuthenticated])
    def organisation_audit_logs(
        self,
        info: Info,
        filters: AuditLogFilterInput | None = None,
        pagination: PaginationInput | None = None,
    ) -> AuditLogConnection:
        """Get audit logs for the current user's organisation.

        Requires appropriate permissions to view organisation logs.
        Returns all logs for the organisation.

        Args:
            info: GraphQL resolver info containing request context.
            filters: Optional filters for the query.
            pagination: Pagination parameters.

        Returns:
            Paginated connection of audit logs.

        Raises:
            PermissionError: If user lacks permission to view organisation logs.
        """
        # Import dynamically to avoid circular imports
        try:
            from syntek_audit.models import AuditLog  # type: ignore[import]
        except ImportError as e:
            raise ImportError(
                "syntek-audit package is required for audit log queries. "
                "Install it with: uv pip install syntek-audit"
            ) from e

        user = info.context.request.user

        # Check permission (adjust permission string to match your setup)
        if not user.has_perm("audit.view_auditlog"):
            from syntek_graphql_core.errors import (  # type: ignore[import]
                PermissionError as GraphQLPermissionError,
            )

            raise GraphQLPermissionError(
                message="You do not have permission to view organisation audit logs"
            )

        # Base query: current organisation
        queryset = AuditLog.objects.filter(organisation=user.organisation).order_by("-created_at")

        # Apply filters if provided
        if filters:
            if filters.action:
                queryset = queryset.filter(action=filters.action)

            if filters.user_id:
                queryset = queryset.filter(user__id=filters.user_id)

            if filters.date_from:
                queryset = queryset.filter(created_at__gte=filters.date_from)

            if filters.date_to:
                queryset = queryset.filter(created_at__lte=filters.date_to)

        # Get total count before pagination
        total_count = queryset.count()

        # Apply pagination
        if pagination is None:
            pagination = PaginationInput()

        limit = min(pagination.limit, 100)  # Max 100 per page
        offset = pagination.offset

        has_previous_page = offset > 0
        has_next_page = (offset + limit) < total_count

        # Get paginated results
        logs = queryset.select_related("user", "organisation")[offset : offset + limit]

        return AuditLogConnection(
            items=[AuditLogType.from_model(log) for log in logs],
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    @strawberry.field(permission_classes=[IsAuthenticated])
    def my_sessions(self, info: Info) -> SessionManagementInfo:
        """Get active sessions for the current user.

        Returns information about all active sessions and
        session management limits.

        Args:
            info: GraphQL resolver info containing request context.

        Returns:
            Session management information with active sessions.
        """
        # Import dynamically to avoid circular imports
        try:
            from syntek_sessions.services import SessionManagementService  # type: ignore[import]
        except ImportError as e:
            raise ImportError(
                "syntek-sessions package is required for session queries. "
                "Install it with: uv pip install syntek-sessions"
            ) from e

        user = info.context.request.user

        # Get active sessions
        active_sessions = SessionManagementService.get_active_sessions(user)
        max_sessions = SessionManagementService.get_max_sessions_per_user()

        # Determine if user can create new session
        can_create_new_session = len(active_sessions) < max_sessions

        # Try to identify current session (from request)
        # This requires the session token to be in the request context
        current_session_id = getattr(info.context.request, "session_token_id", None)

        return SessionManagementInfo(
            active_sessions=[
                SessionTokenType.from_model(
                    session,
                    is_current=(str(session.id) == current_session_id),
                )
                for session in active_sessions
            ],
            total_sessions=len(active_sessions),
            max_sessions=max_sessions,
            can_create_new_session=can_create_new_session,
        )

    @strawberry.field(permission_classes=[IsAuthenticated])
    def available_audit_actions(self) -> list[str]:
        """Get list of available audit log action types.

        Returns:
            List of action type strings.
        """
        # Import dynamically to avoid circular imports
        try:
            from syntek_audit.models import AuditLog  # type: ignore[import]
        except ImportError as e:
            raise ImportError(
                "syntek-audit package is required for audit log queries. "
                "Install it with: uv pip install syntek-audit"
            ) from e

        return [choice[0] for choice in AuditLog.ActionType.choices]
