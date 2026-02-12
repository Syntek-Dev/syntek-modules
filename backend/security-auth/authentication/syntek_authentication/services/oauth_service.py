"""
OAuth service for managing OAuth providers and authorization flows.

Handles OAuth 2.0 authorization code flow with PKCE support for multiple providers.
"""

from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone
from syntek_rust import generate_pkce_pair_py, generate_token_py

from ..models import OAuthState, SocialAccount, SocialLoginAttempt

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class OAuthService:
    """Service for managing OAuth providers and generating authorization URLs."""

    # Provider configuration (from settings)
    PROVIDER_CONFIG = {
        "google": {
            "name": "Google",
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"],
        },
        "github": {
            "name": "GitHub",
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "user_info_url": "https://api.github.com/user",
            "scopes": ["user:email"],
        },
        "microsoft": {
            "name": "Microsoft",
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "user_info_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile"],
        },
    }

    @staticmethod
    def get_provider_config(provider: str) -> dict:
        """
        Get configuration for an OAuth provider.

        Args:
            provider: Provider name (google, github, microsoft, etc.)

        Returns:
            dict: Provider configuration

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in OAuthService.PROVIDER_CONFIG:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        return OAuthService.PROVIDER_CONFIG[provider]

    @staticmethod
    def get_client_id(provider: str) -> str:
        """
        Get OAuth client ID from settings.

        Args:
            provider: Provider name

        Returns:
            str: Client ID

        Raises:
            ValueError: If client ID not configured
        """
        setting_name = f"SYNTEK_SOCIAL_AUTH_{provider.upper()}_CLIENT_ID"
        client_id = getattr(settings, setting_name, None)

        if not client_id:
            raise ValueError(
                f"OAuth client ID not configured for {provider}. "
                f"Set {setting_name} in settings."
            )

        return client_id

    @staticmethod
    def get_client_secret(provider: str) -> str:
        """
        Get OAuth client secret from settings.

        Args:
            provider: Provider name

        Returns:
            str: Client secret

        Raises:
            ValueError: If client secret not configured
        """
        setting_name = f"SYNTEK_SOCIAL_AUTH_{provider.upper()}_CLIENT_SECRET"
        client_secret = getattr(settings, setting_name, None)

        if not client_secret:
            raise ValueError(
                f"OAuth client secret not configured for {provider}. "
                f"Set {setting_name} in settings."
            )

        return client_secret

    @staticmethod
    def is_provider_enabled(provider: str) -> bool:
        """
        Check if an OAuth provider is enabled in settings.

        Args:
            provider: Provider name

        Returns:
            bool: True if enabled, False otherwise
        """
        setting_name = f"SYNTEK_SOCIAL_AUTH_{provider.upper()}_ENABLED"
        return getattr(settings, setting_name, False)

    @staticmethod
    def generate_authorization_url(
        provider: str,
        redirect_uri: str,
        user: Optional["User"] = None,
        use_pkce: bool = False,
    ) -> tuple[str, str]:
        """
        Generate OAuth authorization URL.

        Args:
            provider: OAuth provider name
            redirect_uri: Callback URL after authorization
            user: Authenticated user (if linking account), None for new registration
            use_pkce: Whether to use PKCE flow (required for mobile)

        Returns:
            tuple: (authorization_url, state_token)

        Raises:
            ValueError: If provider not enabled or configured
        """
        if not OAuthService.is_provider_enabled(provider):
            raise ValueError(f"OAuth provider {provider} is not enabled")

        config = OAuthService.get_provider_config(provider)
        client_id = OAuthService.get_client_id(provider)

        # Generate CSRF state token
        state = generate_token_py(32)

        # Generate PKCE pair if requested
        code_verifier = None
        if use_pkce:
            code_verifier, code_challenge = generate_pkce_pair_py()

        # Store state in database (expires after 10 minutes)
        OAuthState.objects.create(
            state=state,
            provider=provider,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
            user=user,
        )

        # Build authorization URL
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": state,
        }

        if use_pkce:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        auth_url = f"{config['auth_url']}?{urlencode(params)}"

        return auth_url, state

    @staticmethod
    def cleanup_expired_states():
        """
        Clean up expired OAuth state tokens.

        Should be run periodically (e.g., via cron or Celery task).
        """
        expiry_time = timezone.now() - timedelta(minutes=10)
        OAuthState.objects.filter(created_at__lt=expiry_time).delete()

    @staticmethod
    def log_login_attempt(
        provider: str,
        status: str,
        user: Optional["User"] = None,
        provider_user_id: str = "",
        email: str = "",
        ip_address: str = "",
        user_agent: str = "",
        error_message: str = "",
    ):
        """
        Log a social login attempt for audit purposes.

        Args:
            provider: OAuth provider name
            status: Login status (success, failed, email_conflict, etc.)
            user: User who attempted login (if successful)
            provider_user_id: User ID from OAuth provider
            email: Email from OAuth provider
            ip_address: IP address of the request
            user_agent: User agent string
            error_message: Error message if login failed
        """
        SocialLoginAttempt.objects.create(
            provider=provider,
            status=status,
            user=user,
            provider_user_id=provider_user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
        )

    @staticmethod
    def get_user_social_accounts(user: "User") -> list[SocialAccount]:
        """
        Get all social accounts linked to a user.

        Args:
            user: User to get social accounts for

        Returns:
            list: List of SocialAccount objects
        """
        return list(SocialAccount.objects.filter(user=user))

    @staticmethod
    def get_social_account(user: "User", provider: str) -> Optional[SocialAccount]:
        """
        Get a specific social account for a user.

        Args:
            user: User to get social account for
            provider: Provider name

        Returns:
            SocialAccount or None
        """
        return SocialAccount.objects.filter(user=user, provider=provider).first()

    @staticmethod
    def unlink_social_account(user: "User", provider: str) -> bool:
        """
        Unlink a social account from a user.

        Args:
            user: User to unlink from
            provider: Provider to unlink

        Returns:
            bool: True if account was unlinked, False if not found
        """
        social_account = OAuthService.get_social_account(user, provider)

        if social_account:
            social_account.delete()
            return True

        return False
