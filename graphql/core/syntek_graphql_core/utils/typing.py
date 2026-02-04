"""Type utilities for GraphQL layer.

Provides type guards and utilities for working with Django's authentication
types in a type-safe manner with pyright/mypy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeGuard

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

# Get the actual User model class
UserModel = get_user_model()


def is_authenticated_user(user: object) -> TypeGuard[AbstractBaseUser]:
    """Type guard to check if user is an authenticated User instance.

    Use this to narrow the type from Django's generic user types
    (_AnyUser, _UserModel, AbstractBaseUser) to our concrete User model.

    Args:
        user: Object to check (typically from request.user)

    Returns:
        True if user is authenticated and is our User model instance

    Example:
        >>> user = request.user
        >>> if is_authenticated_user(user):
        ...     # user is now typed as authenticated user
        ...     print(user.email)
    """
    return (
        user is not None
        and not isinstance(user, AnonymousUser)
        and isinstance(user, UserModel)
        and getattr(user, "is_authenticated", False)
    )


def get_authenticated_user(request) -> AbstractBaseUser | None:
    """Get authenticated user from request with proper typing.

    Args:
        request: Django HTTP request object

    Returns:
        User instance if authenticated, None otherwise

    Example:
        >>> user = get_authenticated_user(request)
        >>> if user:
        ...     print(user.email)
    """
    user = getattr(request, "user", None)
    if is_authenticated_user(user):
        return user  # type: ignore[return-value]
    return None


def require_authenticated_user(request) -> AbstractBaseUser:
    """Get authenticated user or raise error.

    Args:
        request: Django HTTP request object

    Returns:
        User instance

    Raises:
        ValueError: If user is not authenticated

    Example:
        >>> user = require_authenticated_user(request)
        >>> print(user.email)  # Guaranteed to be User
    """
    user = get_authenticated_user(request)
    if user is None:
        raise ValueError("Authentication required")
    return user
