"""GraphQL types for User model.

This module defines Strawberry GraphQL types for User-related data.
Implements H2 requirement for N+1 query prevention using DataLoaders.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Required at runtime for Strawberry GraphQL
from typing import TYPE_CHECKING, Any
from uuid import UUID

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info


@strawberry.type
class OrganisationType:
    """GraphQL type representing an Organisation.

    Maps to apps.core.models.Organisation model.
    """

    id: strawberry.ID
    name: str
    slug: str
    industry: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@strawberry.type
class UserProfileType:
    """GraphQL type representing a UserProfile.

    Maps to apps.core.models.UserProfile model.
    """

    id: strawberry.ID
    phone: str | None
    avatar: str | None
    timezone: str
    language: str
    bio: str | None


@strawberry.type
class UserType:
    """GraphQL type representing a User.

    Maps to apps.core.models.User model.
    Uses DataLoaders for relationship fields to prevent N+1 queries (H2).
    """

    id: strawberry.ID
    email: str
    first_name: str
    last_name: str
    email_verified: bool
    two_factor_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Store organisation_id for lazy loading (Private fields are not exposed in schema)
    _organisation_id: strawberry.Private[UUID | None] = None
    _organisation_data: strawberry.Private[OrganisationType | None] = None
    _user_instance: strawberry.Private[Any] = None

    @strawberry.field
    async def organisation(self, info: Info) -> OrganisationType | None:
        """Get organisation for the user using DataLoader.

        Uses DataLoader to batch organisation lookups, preventing N+1 queries
        when accessing organisations for multiple users (H2 requirement).

        If organisation data is pre-loaded (from select_related), returns it
        directly. Otherwise uses DataLoader to batch the lookup.

        Args:
            info: GraphQL resolver info containing request context

        Returns:
            OrganisationType for the user's organisation or None
        """
        # Return pre-loaded organisation data if available
        if self._organisation_data is not None:
            return self._organisation_data

        # If organisation_id is not available, try to get from user instance
        organisation_id = self._organisation_id
        if organisation_id is None and self._user_instance is not None:
            try:
                org = getattr(self._user_instance, "organisation", None)
                if org is not None:
                    # Organisation is already loaded, return it directly
                    return OrganisationType(
                        id=strawberry.ID(str(org.id)),
                        name=org.name,
                        slug=org.slug,
                        industry=org.industry,
                        is_active=org.is_active,
                        created_at=org.created_at,
                        updated_at=org.updated_at,
                    )
                # Try to get organisation_id
                organisation_id = getattr(self._user_instance, "organisation_id", None)
            except (AttributeError, Exception) as e:
                # Log the exception for debugging
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get organisation for user: {e}")

        # If no organisation_id available, return None
        if organisation_id is None:
            return None

        # Use DataLoader to batch organisation lookup
        from api.dataloaders import get_dataloaders  # type: ignore[import]

        loaders = get_dataloaders(info.context)
        org = await loaders.organisation.load(organisation_id)

        if org is None:
            return None

        return OrganisationType(
            id=strawberry.ID(str(org.id)),
            name=org.name,
            slug=org.slug,
            industry=org.industry,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )

    @strawberry.field
    async def profile(self, info: Info) -> UserProfileType | None:
        """Load user profile using DataLoader.

        Uses DataLoader to batch profile lookups, preventing N+1 queries
        when accessing profiles for multiple users.

        Args:
            info: GraphQL resolver info containing request context

        Returns:
            UserProfileType for the user's profile or None
        """
        # Try to get user_id
        user_id = None
        if self._user_instance is not None:
            try:
                # Check if profile is already loaded
                profile = getattr(self._user_instance, "profile", None)
                if profile is not None:
                    # Profile is already loaded, return it directly
                    return UserProfileType(
                        id=strawberry.ID(str(profile.id)),
                        phone=profile.phone,
                        avatar=str(profile.avatar) if profile.avatar else None,
                        timezone=profile.timezone,
                        language=profile.language,
                        bio=profile.bio,
                    )
                # Get user_id for DataLoader lookup
                user_id = getattr(self._user_instance, "id", None)
            except (AttributeError, Exception) as e:
                # Log the exception for debugging
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get profile for user: {e}")

        # If no user_id, try to extract from self.id
        if user_id is None:
            try:
                user_id = UUID(str(self.id))
            except (ValueError, TypeError):
                return None

        # Use DataLoader to batch profile lookup
        from api.dataloaders import get_dataloaders  # type: ignore[import]

        loaders = get_dataloaders(info.context)
        profile = await loaders.user_profile.load(user_id)

        if profile is None:
            return None

        return UserProfileType(
            id=strawberry.ID(str(profile.id)),
            phone=profile.phone,
            avatar=str(profile.avatar) if profile.avatar else None,
            timezone=profile.timezone,
            language=profile.language,
            bio=profile.bio,
        )
