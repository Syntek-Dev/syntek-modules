"""GraphQL queries for user data.

Implements organisation boundary enforcement and uses DataLoaders (H2).
All queries respect multi-tenancy isolation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry
from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.errors import AuthenticationError, ErrorCode  # type: ignore[import]
from syntek_graphql_core.utils.context import get_request  # type: ignore[import]

from syntek_graphql_auth.types.user import UserType  # type: ignore[import]
from syntek_graphql_auth.utils.converters import user_to_graphql_type  # type: ignore[import]

User = get_user_model()


@strawberry.type
class UserQueries:
    """GraphQL queries for user-related data with organisation boundaries."""

    @strawberry.field
    def me(self, info: Info) -> UserType | None:
        """Get current authenticated user.

        Returns:
            Current user or None if not authenticated
        """
        request = get_request(info)
        user = request.user

        if not user.is_authenticated:
            return None

        return user_to_graphql_type(user)

    @strawberry.field
    def user(self, info: Info, id: strawberry.ID) -> UserType | None:
        """Get user by ID (organisation-scoped).

        Enforces organisation boundary - users can only query users from
        their own organisation.

        Args:
            info: GraphQL execution info
            id: User ID

        Returns:
            User if in same organisation, None otherwise
        """
        request = get_request(info)
        current_user = request.user

        if not current_user.is_authenticated:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        try:
            # Query with organisation boundary enforcement
            # User IDs are UUIDs, so use str(id) directly
            user = User.objects.select_related("organisation").get(
                id=str(id), organisation=current_user.organisation
            )
            return user_to_graphql_type(user)

        except (User.DoesNotExist, ValueError):
            return None

    @strawberry.field
    def users(self, info: Info, limit: int = 10, offset: int = 0) -> list[UserType]:
        """Get all users in current user's organisation.

        Enforces organisation boundary - only returns users from the same
        organisation as the authenticated user.

        Args:
            info: GraphQL execution info
            limit: Maximum users to return (default: 10, max: 100)
            offset: Pagination offset

        Returns:
            List of users from same organisation

        Raises:
            AuthenticationError: If user not authenticated
        """
        request = get_request(info)
        current_user = request.user

        if not current_user.is_authenticated:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Limit maximum page size
        if limit > 100:
            limit = 100

        # Query users from same organisation only
        users = (
            User.objects.filter(organisation=current_user.organisation)
            .select_related("organisation")
            .order_by("email")[offset : offset + limit]
        )

        return [user_to_graphql_type(u) for u in users]
