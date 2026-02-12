"""Converter utilities for transforming Django models to GraphQL types.

This module provides functions to convert Django model instances to their
corresponding Strawberry GraphQL types for the auth module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

    from syntek_graphql_auth.types.user import UserType


def user_to_graphql_type(user: AbstractBaseUser) -> UserType:
    """Convert a Django User model instance to GraphQL UserType.

    This converter transforms a Django User model (or custom user model) into
    the Strawberry GraphQL UserType, preserving the user instance for lazy
    loading of relationships via DataLoaders.

    Args:
        user: Django User model instance (or custom user model)

    Returns:
        UserType: Strawberry GraphQL type representing the user

    Example:
        >>> from django.contrib.auth import get_user_model
        >>> User = get_user_model()
        >>> user = User.objects.get(email="user@example.com")
        >>> graphql_user = user_to_graphql_type(user)
    """
    from syntek_graphql_auth.types.user import UserType

    return UserType(
        id=strawberry.ID(str(user.id)),  # type: ignore[attr-defined]
        email=user.email,  # type: ignore[attr-defined]
        first_name=user.first_name,  # type: ignore[attr-defined]
        last_name=user.last_name,  # type: ignore[attr-defined]
        email_verified=getattr(user, "email_verified", False),
        two_factor_enabled=getattr(user, "two_factor_enabled", False),
        is_active=user.is_active,
        created_at=getattr(user, "created_at", user.date_joined),  # type: ignore[attr-defined]
        updated_at=getattr(user, "updated_at", user.date_joined),  # type: ignore[attr-defined]
        # Store private fields for lazy loading
        _organisation_id=getattr(user, "organisation_id", None),
        _user_instance=user,
    )
