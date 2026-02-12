"""GraphQL mutations for session management.

This module provides mutations for managing user sessions including
revoking sessions and enforcing session limits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from apps.core.models import User  # type: ignore[import]
    from strawberry.types import Info

from syntek_graphql_core.permissions import IsAuthenticated  # type: ignore[import]


@strawberry.type
class RevokeSessionPayload:
    """Response for session revocation mutation."""

    success: bool
    message: str


@strawberry.type
class RevokeAllSessionsPayload:
    """Response for revoking all sessions mutation."""

    success: bool
    sessions_revoked: int
    message: str


@strawberry.type
class SessionMutation:
    """GraphQL mutations for session management."""

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def revoke_session(
        self,
        info: Info,
        session_id: strawberry.ID,
    ) -> RevokeSessionPayload:
        """Revoke a specific session.

        Users can only revoke their own sessions.
        Useful for "log out this device" functionality.

        Args:
            info: GraphQL resolver info containing request context.
            session_id: ID of the session to revoke.

        Returns:
            RevokeSessionPayload with success status.
        """
        from apps.core.services.session_management_service import (  # type: ignore[import]
            SessionManagementService,
        )

        user: User = info.context.request.user

        success = SessionManagementService.revoke_session(
            session_id=str(session_id),
            user=user,
        )

        if success:
            return RevokeSessionPayload(
                success=True,
                message="Session revoked successfully",
            )
        else:
            return RevokeSessionPayload(
                success=False,
                message="Session not found or already revoked",
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def revoke_all_sessions(
        self,
        info: Info,
        except_current: bool = True,
    ) -> RevokeAllSessionsPayload:
        """Revoke all sessions for the current user.

        Useful for "log out all devices" functionality.

        Args:
            info: GraphQL resolver info containing request context.
            except_current: Whether to keep the current session active.

        Returns:
            RevokeAllSessionsPayload with number of sessions revoked.
        """
        from apps.core.services.session_management_service import (  # type: ignore[import]
            SessionManagementService,
        )

        user: User = info.context.request.user

        # Get current session ID if we should keep it
        current_session_id = None
        if except_current:
            current_session_id = getattr(info.context.request, "session_token_id", None)

        sessions_revoked = SessionManagementService.revoke_all_user_sessions(
            user=user,
            except_session_id=current_session_id,
        )

        return RevokeAllSessionsPayload(
            success=True,
            sessions_revoked=sessions_revoked,
            message=f"Successfully revoked {sessions_revoked} session(s)",
        )
