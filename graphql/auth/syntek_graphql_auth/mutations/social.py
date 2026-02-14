"""GraphQL mutations for social authentication - combined exports.

This module combines all social authentication mutations into a single
Strawberry type for use in the GraphQL schema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from syntek_graphql_auth.mutations import social_account_mgmt, social_auth
from syntek_graphql_auth.types.auth import AuthPayload
from syntek_graphql_auth.types.social import (
    HandleSocialCallbackInput,
    InitiateSocialLoginInput,
    LinkSocialAccountInput,
    SocialAccountType,
    SocialProviderType,
    UnlinkSocialAccountInput,
)


@strawberry.type
class SocialAuthMutations:
    """GraphQL mutations for social authentication operations.

    Provides OAuth-based authentication, account linking, and profile syncing
    with comprehensive security controls and GDPR compliance.
    """

    @strawberry.mutation
    def initiate_social_login(
        self, info: Info, input: InitiateSocialLoginInput
    ) -> SocialProviderType:
        """Generate OAuth authorization URL for social login.

        Delegates to social_auth.initiate_social_login for implementation.
        Rate limit: 10 OAuth initiations per IP per hour
        """
        return social_auth.initiate_social_login(info, input)

    @strawberry.mutation
    def handle_social_callback(
        self, info: Info, input: HandleSocialCallbackInput
    ) -> AuthPayload:
        """Handle OAuth callback and exchange code for tokens.

        Delegates to social_auth.handle_social_callback for implementation.
        Rate limit: 10 callbacks per IP per hour
        """
        return social_auth.handle_social_callback(info, input)

    @strawberry.mutation
    def link_social_account(
        self, info: Info, input: LinkSocialAccountInput
    ) -> SocialAccountType:
        """Link social account to authenticated user.

        Delegates to social_account_mgmt.link_social_account for implementation.
        Rate limit: 5 link operations per user per hour
        """
        return social_account_mgmt.link_social_account(info, input)

    @strawberry.mutation
    def unlink_social_account(
        self, info: Info, input: UnlinkSocialAccountInput
    ) -> bool:
        """Unlink social account from authenticated user.

        Delegates to social_account_mgmt.unlink_social_account for implementation.
        Rate limit: 5 unlink operations per user per hour
        """
        return social_account_mgmt.unlink_social_account(info, input)

    @strawberry.mutation
    def refresh_social_token(
        self, info: Info, provider: str
    ) -> SocialAccountType:
        """Manually refresh OAuth access token.

        Delegates to social_account_mgmt.refresh_social_token for implementation.
        """
        return social_account_mgmt.refresh_social_token(info, provider)

    @strawberry.mutation
    def set_social_account_primary(
        self, info: Info, provider: str
    ) -> SocialAccountType:
        """Set social account as primary login method.

        Delegates to social_account_mgmt.set_social_account_primary for implementation.
        """
        return social_account_mgmt.set_social_account_primary(info, provider)

    @strawberry.mutation
    def sync_social_profile(
        self, info: Info, provider: str
    ) -> SocialAccountType:
        """Sync profile photo and name from social account.

        Delegates to social_account_mgmt.sync_social_profile for implementation.
        GDPR: Requires user consent for profile sync
        """
        return social_account_mgmt.sync_social_profile(info, provider)
