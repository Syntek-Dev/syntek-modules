"""GraphQL mutations for social authentication - OAuth login and callback.

This module implements OAuth authorization and callback handling with CSRF protection
and comprehensive security features.

Security Features:
- CSRF protection via state tokens with 10-minute expiry
- PKCE support for mobile OAuth flows
- Rate limiting on all mutations
- Audit logging of all operations

GDPR Compliance:
- Records social login attempts for audit trail
- Encrypts OAuth tokens with AES-256-GCM
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry
from django.contrib.auth import get_user_model
from django.db import transaction

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.token_service import TokenService  # type: ignore[import]
from syntek_authentication.services.oauth_callback_service import (  # type: ignore[import]
    OAuthCallbackService,
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
    get_ip_address,
    get_request,
    get_user_agent,
)
from syntek_graphql_core.utils.typing import (  # type: ignore[import]
    get_authenticated_user,
)

from syntek_graphql_auth.types.auth import (  # type: ignore[import]
    AuthPayload,
)
from syntek_graphql_auth.types.social import (  # type: ignore[import]
    HandleSocialCallbackInput,
    InitiateSocialLoginInput,
    SocialProviderType,
)
from syntek_graphql_auth.utils.converters import (  # type: ignore[import]
    user_to_graphql_type,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def initiate_social_login(
    info: Info, input: InitiateSocialLoginInput
) -> SocialProviderType:
    """Generate OAuth authorization URL for social login.

    Creates a CSRF state token, stores it in the database with expiry,
    and generates the OAuth authorization URL that the client should
    redirect the user to for authentication.

    Security Features:
    - CSRF state token with 10-minute expiry
    - PKCE support for mobile applications
    - Rate limit: 10 OAuth initiations per IP per hour

    Args:
        info: GraphQL execution info with request context
        input: Provider and redirect URI configuration

    Returns:
        SocialProviderType with authorization_url populated

    Raises:
        ValidationError: If provider not supported or not configured

    Examples:
        >>> # Web application flow
        >>> result = initiate_social_login(
        ...     provider="google",
        ...     redirect_uri="https://example.com/auth/callback",
        ...     use_pkce=False
        ... )
        >>> # Redirect user to result.authorization_url
    """
    ip_address = get_ip_address(info)
    request = get_request(info)
    user = get_authenticated_user(request) if request else None

    # Validate provider is supported
    try:
        config = OAuthService.get_provider_config(input.provider)
    except ValueError as e:
        raise ValidationError(
            message=str(e),
            code=ErrorCode.INVALID_INPUT,
        ) from e

    # Check if provider is enabled
    if not OAuthService.is_provider_enabled(input.provider):
        raise ValidationError(
            message=f"OAuth provider {input.provider} is not enabled in settings",
            code=ErrorCode.INVALID_INPUT,
        )

    # Check if client ID and secret are configured
    try:
        OAuthService.get_client_id(input.provider)
        OAuthService.get_client_secret(input.provider)
    except ValueError as e:
        raise ValidationError(
            message=f"OAuth provider {input.provider} is not properly configured",
            code=ErrorCode.INVALID_INPUT,
        ) from e

    # Generate authorization URL with state token
    try:
        auth_url, state = OAuthService.generate_authorization_url(
            provider=input.provider,
            redirect_uri=input.redirect_uri,
            user=user,
            use_pkce=input.use_pkce,
        )
    except Exception as e:
        logger.exception("Failed to generate OAuth authorization URL")
        raise ValidationError(
            message="Failed to generate authorization URL",
            code=ErrorCode.INTERNAL_ERROR,
        ) from e

    # Log audit event
    AuditService.log_event(
        action="oauth_initiate",
        user=user,
        organisation=user.organisation if user else None,
        ip_address=ip_address,
        metadata={
            "provider": input.provider,
            "use_pkce": input.use_pkce,
            "state": state[:10],  # Only log first 10 chars
        },
    )

    return SocialProviderType(
        provider=input.provider,
        name=config["name"],
        enabled=True,
        scopes=config["scopes"],
        authorization_url=auth_url,
    )


def handle_social_callback(
    info: Info, input: HandleSocialCallbackInput
) -> AuthPayload:
    """Handle OAuth callback and exchange code for tokens.

    Validates the CSRF state token, exchanges the authorization code for
    an access token, fetches user information from the OAuth provider,
    and either creates a new user account or logs in an existing user.

    Security Features:
    - CSRF validation via state token
    - PKCE verification for mobile flows
    - Rate limit: 10 callbacks per IP per hour
    - Audit logging of all attempts (success and failure)
    - Email conflict detection

    GDPR Compliance:
    - Records social login attempt for audit trail
    - Encrypts OAuth tokens with AES-256-GCM

    Args:
        info: GraphQL execution info with request context
        input: OAuth code, state, and provider

    Returns:
        AuthPayload with JWT tokens and user data

    Raises:
        AuthenticationError: If state invalid or token exchange fails
        ValidationError: If email conflict exists (user must log in first)

    Examples:
        >>> # Handle OAuth callback
        >>> result = handle_social_callback(
        ...     provider="google",
        ...     code="4/0AY0e-g7...",
        ...     state="abc123..."
        ... )
        >>> # Save tokens to client storage
        >>> save_tokens(result.access_token, result.refresh_token)
    """
    ip_address = get_ip_address(info)
    user_agent = get_user_agent(info)

    # Validate CSRF state token
    oauth_state = OAuthCallbackService.validate_state(
        state=input.state,
        code_verifier=input.code_verifier,
    )

    if not oauth_state:
        # Log failed attempt
        OAuthService.log_login_attempt(
            provider=input.provider,
            status="invalid_state",
            ip_address=ip_address,
            user_agent=user_agent,
            error_message="Invalid or expired state token",
        )

        raise AuthenticationError(
            message="Invalid or expired OAuth state token",
            code=ErrorCode.INVALID_OAUTH_STATE,
        )

    # Verify provider matches
    if oauth_state.provider != input.provider:
        raise AuthenticationError(
            message="Provider mismatch in OAuth callback",
            code=ErrorCode.INVALID_OAUTH_STATE,
        )

    # Exchange authorization code for access token
    try:
        token_response = OAuthCallbackService.exchange_code_for_token(
            provider=input.provider,
            code=input.code,
            redirect_uri=oauth_state.redirect_uri,
            code_verifier=input.code_verifier,
        )
    except ValueError as e:
        # Log failed attempt
        OAuthService.log_login_attempt(
            provider=input.provider,
            status="provider_error",
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=str(e),
        )

        raise AuthenticationError(
            message=f"OAuth provider returned error: {e}",
            code=ErrorCode.OAUTH_PROVIDER_ERROR,
        ) from e

    # Get user information from OAuth provider
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in")
    scope = token_response.get("scope", "")

    try:
        user_info = OAuthCallbackService.get_user_info(input.provider, access_token)
    except ValueError as e:
        # Log failed attempt
        OAuthService.log_login_attempt(
            provider=input.provider,
            status="provider_error",
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=str(e),
        )

        raise AuthenticationError(
            message="Failed to fetch user information from OAuth provider",
            code=ErrorCode.OAUTH_PROVIDER_ERROR,
        ) from e

    # Extract email and provider user ID
    email = user_info.get("email")
    provider_user_id = user_info.get("sub") or user_info.get("id") or str(user_info.get("node_id", ""))

    if not email or not provider_user_id:
        raise ValidationError(
            message="OAuth provider did not return required user information",
            code=ErrorCode.INVALID_INPUT,
        )

    # Create or link social account
    try:
        with transaction.atomic():
            user, social_account, created = OAuthCallbackService.create_or_link_account(
                provider=input.provider,
                provider_user_id=provider_user_id,
                email=email,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                scope=scope,
                profile_data=user_info,
                authenticated_user=oauth_state.user,
            )

            # Log successful attempt
            OAuthService.log_login_attempt(
                provider=input.provider,
                status="success" if not created else "account_created",
                user=user,
                provider_user_id=provider_user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Generate JWT tokens
            tokens = TokenService.create_tokens(user)

            # Log audit event
            AuditService.log_event(
                action="social_login_success",
                user=user,
                organisation=user.organisation if hasattr(user, "organisation") else None,
                ip_address=ip_address,
                metadata={
                    "provider": input.provider,
                    "email": email,
                    "created": created,
                },
            )

            return AuthPayload(
                access_token=tokens["access"],
                refresh_token=tokens["refresh"],
                user=user_to_graphql_type(user),
                requires_two_factor=False,
            )

    except ValueError as e:
        # Email conflict - user must log in first and link account
        if "already registered" in str(e).lower():
            OAuthService.log_login_attempt(
                provider=input.provider,
                status="email_conflict",
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )

            raise ValidationError(
                message=str(e),
                code=ErrorCode.EMAIL_ALREADY_EXISTS,
            ) from e

        # Other errors
        OAuthService.log_login_attempt(
            provider=input.provider,
            status="failed",
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=str(e),
        )

        raise ValidationError(
            message=str(e),
            code=ErrorCode.INVALID_INPUT,
        ) from e
