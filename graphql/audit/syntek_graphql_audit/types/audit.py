"""GraphQL types for audit logs and security monitoring.

This module provides GraphQL types for accessing audit logs and
session management with proper organisation boundary enforcement.
"""

from __future__ import annotations

import contextlib
from datetime import datetime  # noqa: TC003 - Required at runtime for Strawberry GraphQL
from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from django.db.models import Model  # Generic model type

# Type alias for audit log and session token models
AuditLog = Model
SessionToken = Model


@strawberry.type
class AuditLogType:
    """GraphQL type for audit log entries.

    Exposes audit log information with IP addresses remaining encrypted.
    Users can only view logs for their own organisation.
    Uses DataLoaders for user and organisation relationships to prevent N+1 queries.
    """

    id: strawberry.ID
    action: str
    user_id: strawberry.ID | None
    user_email: str | None
    organisation_id: strawberry.ID | None
    organisation_name: str | None
    user_agent: str
    device_fingerprint: str
    metadata: strawberry.scalars.JSON
    created_at: datetime

    # Private fields for DataLoader lookups
    _user_id_internal: strawberry.Private[int | None] = None
    _organisation_id_internal: strawberry.Private[int | None] = None
    _audit_log_instance: strawberry.Private[object | None] = None

    @staticmethod
    def from_model(audit_log: object) -> AuditLogType:
        """Convert AuditLog model to GraphQL type.

        Stores the audit log instance for potential DataLoader usage.
        If user/organisation are already loaded (via select_related),
        extracts their data immediately to avoid extra queries.

        Args:
            audit_log: AuditLog model instance.

        Returns:
            AuditLogType instance.
        """
        # Extract user data if available
        user_id = None
        user_email = None
        if audit_log.user_id:  # type: ignore[attr-defined]
            user_id = strawberry.ID(str(audit_log.user_id))  # type: ignore[attr-defined]
            # Try to get email from loaded user, otherwise will need DataLoader
            with contextlib.suppress(AttributeError):
                user = getattr(audit_log, "user", None)
                user_email = getattr(user, "email", None) if user else None

        # Extract organisation data if available
        organisation_id = None
        organisation_name = None
        if audit_log.organisation_id:  # type: ignore[attr-defined]
            organisation_id = strawberry.ID(str(audit_log.organisation_id))  # type: ignore[attr-defined]
            # Try to get name from loaded organisation
            with contextlib.suppress(AttributeError):
                organisation_name = audit_log.organisation.name if audit_log.organisation else None  # type: ignore[attr-defined]

        return AuditLogType(
            id=strawberry.ID(str(audit_log.id)),  # type: ignore[attr-defined]
            action=audit_log.action,  # type: ignore[attr-defined]
            user_id=user_id,
            user_email=user_email,
            organisation_id=organisation_id,
            organisation_name=organisation_name,
            user_agent=audit_log.user_agent,  # type: ignore[attr-defined]
            device_fingerprint=audit_log.device_fingerprint,  # type: ignore[attr-defined]
            metadata=audit_log.metadata,  # type: ignore[attr-defined]
            created_at=audit_log.created_at,  # type: ignore[attr-defined]
            _user_id_internal=audit_log.user_id,  # type: ignore[attr-defined]
            _organisation_id_internal=audit_log.organisation_id,  # type: ignore[attr-defined]
            _audit_log_instance=audit_log,
        )


@strawberry.type
class SessionTokenType:
    """GraphQL type for user session information.

    Provides session details for current user's active sessions.
    Sensitive information (token hashes) is not exposed.
    """

    id: strawberry.ID
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    device_fingerprint: str
    user_agent: str
    is_current: bool

    @staticmethod
    def from_model(session: object, is_current: bool = False) -> SessionTokenType:
        """Convert SessionToken model to GraphQL type.

        Args:
            session: SessionToken model instance.
            is_current: Whether this is the current session.

        Returns:
            SessionTokenType instance.
        """
        return SessionTokenType(
            id=strawberry.ID(str(session.id)),  # type: ignore[attr-defined]
            created_at=session.created_at,  # type: ignore[attr-defined]
            last_activity_at=session.last_activity_at,  # type: ignore[attr-defined]
            expires_at=session.expires_at,  # type: ignore[attr-defined]
            device_fingerprint=session.device_fingerprint,  # type: ignore[attr-defined]
            user_agent=session.user_agent,  # type: ignore[attr-defined]
            is_current=is_current,
        )


@strawberry.type
class AuditLogConnection:
    """Paginated connection for audit logs."""

    items: list[AuditLogType]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@strawberry.type
class SessionManagementInfo:
    """Information about user's session management status."""

    active_sessions: list[SessionTokenType]
    total_sessions: int
    max_sessions: int
    can_create_new_session: bool


@strawberry.input
class AuditLogFilterInput:
    """Filter options for audit log queries."""

    action: str | None = None
    user_id: strawberry.ID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


@strawberry.input
class PaginationInput:
    """Pagination parameters."""

    limit: int = 20
    offset: int = 0
