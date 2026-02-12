"""GraphQL permission classes for access control.

Provides permission classes for protecting GraphQL queries and mutations.
Based on Strawberry's BasePermission class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from strawberry.permission import BasePermission

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_core.utils.context import get_request


class IsAuthenticated(BasePermission):
    """Permission class requiring user to be authenticated."""

    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        """Check if user is authenticated.

        Args:
            source: Source object
            info: GraphQL execution info
            **kwargs: Additional arguments

        Returns:
            True if authenticated, False otherwise
        """
        request = get_request(info)
        user = getattr(request, "user", None)
        return bool(getattr(user, "is_authenticated", False))


class HasPermission(BasePermission):
    """Permission class requiring specific Django permission."""

    def __init__(self, permission: str) -> None:
        """Initialize with required permission.

        Args:
            permission: Django permission string (e.g., 'core.view_user')
        """
        self.permission = permission
        self.message = f"User lacks required permission: {permission}"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        """Check if user has required permission.

        Args:
            source: Source object
            info: GraphQL execution info
            **kwargs: Additional arguments

        Returns:
            True if user has permission, False otherwise
        """
        request = get_request(info)
        user = getattr(request, "user", None)
        is_authenticated = getattr(user, "is_authenticated", False)
        has_perm = getattr(user, "has_perm", None)
        return is_authenticated and (has_perm(self.permission) if has_perm else False)


class IsOrganisationOwner(BasePermission):
    """Permission class requiring organisation owner role."""

    message = "User is not an organisation owner"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        """Check if user is organisation owner.

        Args:
            source: Source object
            info: GraphQL execution info
            **kwargs: Additional arguments

        Returns:
            True if organisation owner, False otherwise
        """
        request = get_request(info)
        user = getattr(request, "user", None)
        is_authenticated = getattr(user, "is_authenticated", False)
        if not is_authenticated:
            return False
        groups = getattr(user, "groups", None)
        if not groups:
            return False
        return groups.filter(name="Organisation Owner").exists()
