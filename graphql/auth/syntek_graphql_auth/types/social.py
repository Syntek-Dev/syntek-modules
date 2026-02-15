"""GraphQL types for social authentication operations.

This module defines input and output types for OAuth-based social authentication
including Google, GitHub, Microsoft, Apple, Facebook, LinkedIn, and Twitter/X.

Security Features:
- CSRF protection via state tokens
- PKCE support for mobile applications
- Encrypted token storage
- Audit logging of all login attempts

GDPR Compliance:
- User consent tracking for profile sync
- Data export includes social account data
- Account deletion revokes OAuth tokens
"""

from __future__ import annotations

from datetime import datetime

import strawberry


@strawberry.type
class SocialAccountType:
    """Social account linked to a user via OAuth.

    Represents a third-party OAuth account (Google, GitHub, etc.) that has been
    linked to a user's account for authentication or profile syncing.

    Attributes:
        id: Unique identifier for the social account
        provider: Provider name (google, github, microsoft, etc.)
        provider_display_name: Human-readable provider name
        email: Email address from OAuth provider
        profile_data: Additional profile information (name, avatar, etc.)
        is_primary: Whether this is the primary social login method
        created_at: When the account was first linked
        last_login_at: When this account was last used to log in
        is_token_expired: Whether the OAuth access token has expired
    """

    id: strawberry.ID
    provider: str
    provider_display_name: str
    email: str
    profile_data: strawberry.scalars.JSON
    is_primary: bool
    created_at: datetime
    last_login_at: datetime | None
    is_token_expired: bool


@strawberry.type
class SocialProviderType:
    """Available OAuth provider configuration.

    Represents an OAuth provider that can be used for authentication,
    including configuration and current enabled status.

    Attributes:
        provider: Provider identifier (google, github, microsoft, etc.)
        name: Human-readable provider name
        enabled: Whether the provider is configured and enabled
        scopes: OAuth scopes requested during authorization
        authorization_url: URL to redirect user for authorization (only if initiating login)
    """

    provider: str
    name: str
    enabled: bool
    scopes: list[str]
    authorization_url: str | None = None


@strawberry.type
class SocialLoginAttemptType:
    """Audit log entry for social login attempts.

    Tracks all OAuth login attempts for security monitoring and GDPR compliance.
    Includes both successful and failed attempts with detailed context.

    Attributes:
        id: Unique identifier for the login attempt
        provider: OAuth provider used
        status: Attempt status (success, failed, email_conflict, etc.)
        email: Email address from OAuth provider
        ip_address: IP address of the login attempt
        error_message: Error details if login failed
        created_at: When the login attempt occurred
    """

    id: strawberry.ID
    provider: str
    status: str
    email: str
    ip_address: str
    error_message: str | None
    created_at: datetime


@strawberry.input
class InitiateSocialLoginInput:
    """Input for initiating social login flow.

    Used to generate an OAuth authorization URL that the client should
    redirect the user to for authentication.

    Attributes:
        provider: OAuth provider to use (google, github, microsoft, etc.)
        redirect_uri: URL to redirect back to after OAuth authorization
        use_pkce: Enable PKCE flow for mobile applications (default: False)
    """

    provider: str
    redirect_uri: str
    use_pkce: bool = False


@strawberry.input
class HandleSocialCallbackInput:
    """Input for handling OAuth callback after authorization.

    Processes the OAuth callback after the user has authorized the application,
    exchanges the authorization code for tokens, and creates or logs in the user.

    Attributes:
        provider: OAuth provider name
        code: Authorization code from OAuth callback
        state: CSRF state token for validation
        code_verifier: PKCE code verifier for mobile flows (optional)
    """

    provider: str
    code: str
    state: str
    code_verifier: str | None = None


@strawberry.input
class LinkSocialAccountInput:
    """Input for linking social account to authenticated user.

    Allows an authenticated user to link an additional OAuth account
    without creating a new user account.

    Attributes:
        provider: OAuth provider to link
        code: Authorization code from OAuth callback
        state: CSRF state token for validation
    """

    provider: str
    code: str
    state: str


@strawberry.input
class UnlinkSocialAccountInput:
    """Input for unlinking social account from authenticated user.

    Removes a linked OAuth account. Requires password confirmation
    and ensures user has alternative authentication method.

    Attributes:
        provider: OAuth provider to unlink
        password: Current password for security verification
    """

    provider: str
    password: str
