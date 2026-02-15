"""GraphQL queries for social authentication.

This module provides queries for viewing linked social accounts,
available OAuth providers, and social login history.

Security Features:
- Authentication required for personal data queries
- Rate limiting on history queries
- Provider availability checking

GDPR Compliance:
- Social login history included in DSAR exports
- User can view all linked accounts
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_authentication.models import (  # type: ignore[import]
    SocialAccount,
    SocialLoginAttempt,
)
from syntek_authentication.services.oauth_service import (  # type: ignore[import]
    OAuthService,
)
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    ValidationError,
)
from syntek_graphql_core.utils.context import (  # type: ignore[import]
    get_request,
)
from syntek_graphql_core.utils.typing import (  # type: ignore[import]
    get_authenticated_user,
)

from syntek_graphql_auth.types.social import (  # type: ignore[import]
    SocialAccountType,
    SocialLoginAttemptType,
    SocialProviderType,
)


@strawberry.type
class SocialAuthQueries:
    """GraphQL queries for social authentication.

    Provides read-only access to social accounts, providers, and login history.
    """

    @strawberry.field
    def social_accounts(self, info: Info) -> list[SocialAccountType]:
        """List all social accounts linked to authenticated user.

        Returns all OAuth accounts (Google, GitHub, etc.) that the user
        has linked to their account for authentication.

        Security Features:
        - Requires user authentication
        - Only returns accounts for authenticated user

        Returns:
            list[SocialAccountType]: User's linked social accounts

        Raises:
            AuthenticationError: If not authenticated

        Examples:
            >>> # Query linked accounts
            >>> query {
            ...     socialAccounts {
            ...         provider
            ...         email
            ...         isPrimary
            ...         lastLoginAt
            ...     }
            ... }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(
                message="Authentication required",
                code=ErrorCode.NOT_AUTHENTICATED,
            )

        # Fetch all social accounts for user
        accounts = SocialAccount.objects.filter(user=user).order_by("-created_at")

        return [
            SocialAccountType(
                id=strawberry.ID(str(account.id)),
                provider=account.provider,
                provider_display_name=account.get_provider_display(),
                email=account.email,
                profile_data=account.profile_data,
                is_primary=account.is_primary,
                created_at=account.created_at,
                last_login_at=account.last_login_at,
                is_token_expired=account.is_token_expired(),
            )
            for account in accounts
        ]

    @strawberry.field
    def available_social_providers(self, info: Info) -> list[SocialProviderType]:
        """List all enabled OAuth providers with UI configuration.

        Returns information about all OAuth providers that are configured
        and enabled in settings. Used to display login buttons and check
        which providers are available.

        Security Features:
        - Public endpoint (no authentication required)
        - Does not expose client secrets
        - Only returns enabled providers

        Returns:
            list[SocialProviderType]: Available OAuth providers

        Examples:
            >>> # Query available providers
            >>> query {
            ...     availableSocialProviders {
            ...         provider
            ...         name
            ...         enabled
            ...         scopes
            ...     }
            ... }
        """
        providers = []

        for provider_key, config in OAuthService.PROVIDER_CONFIG.items():
            # Check if provider is enabled in settings
            enabled = OAuthService.is_provider_enabled(provider_key)

            # Check if client ID and secret are configured
            if enabled:
                try:
                    OAuthService.get_client_id(provider_key)
                    OAuthService.get_client_secret(provider_key)
                except ValueError:
                    # Not properly configured, mark as disabled
                    enabled = False

            providers.append(
                SocialProviderType(
                    provider=provider_key,
                    name=config["name"],
                    enabled=enabled,
                    scopes=config["scopes"],
                    authorization_url=None,  # Don't expose URLs in list query
                )
            )

        return providers

    @strawberry.field
    def social_login_history(
        self,
        info: Info,
        provider: str | None = None,
        limit: int = 50,
    ) -> list[SocialLoginAttemptType]:
        """View social login attempt history for authenticated user.

        Returns a paginated list of social login attempts (both successful
        and failed) for security monitoring and audit purposes.

        Security Features:
        - Requires user authentication
        - Rate limit: Applied via GraphQL query complexity
        - Maximum 100 results per query

        GDPR Compliance:
        - Included in DSAR exports
        - User has right to access (Art. 15)

        Args:
            info: GraphQL execution info with authenticated user
            provider: Filter by provider (optional)
            limit: Maximum results (default 50, max 100)

        Returns:
            list[SocialLoginAttemptType]: Login attempt history

        Raises:
            AuthenticationError: If not authenticated
            ValidationError: If limit > 100

        Examples:
            >>> # Query recent login attempts
            >>> query {
            ...     socialLoginHistory(limit: 20) {
            ...         provider
            ...         status
            ...         email
            ...         ipAddress
            ...         createdAt
            ...     }
            ... }

            >>> # Filter by provider
            >>> query {
            ...     socialLoginHistory(provider: "google", limit: 10) {
            ...         status
            ...         createdAt
            ...     }
            ... }
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(
                message="Authentication required",
                code=ErrorCode.NOT_AUTHENTICATED,
            )

        # Validate limit
        if limit > 100:
            raise ValidationError(
                message="Maximum limit is 100 results",
                code=ErrorCode.INVALID_INPUT,
            )

        # Build query
        query = SocialLoginAttempt.objects.filter(user=user)

        # Filter by provider if specified
        if provider:
            query = query.filter(provider=provider)

        # Order by most recent first and limit
        attempts = query.order_by("-created_at")[:limit]

        return [
            SocialLoginAttemptType(
                id=strawberry.ID(str(attempt.id)),
                provider=attempt.provider,
                status=attempt.status,
                email=attempt.email,
                ip_address=attempt.ip_address,
                error_message=attempt.error_message,
                created_at=attempt.created_at,
            )
            for attempt in attempts
        ]
