"""
OAuth callback service for handling token exchange and user creation.

Handles the OAuth callback after user authorizes the application.
"""

import requests
from datetime import timedelta
from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from syntek_rust import (
    encrypt_oauth_token_py,
    decrypt_oauth_token_py,
    hash_email_py,
)

from ..models import EncryptedEmail, OAuthState, SocialAccount
from .oauth_service import OAuthService

User = get_user_model()


class OAuthCallbackService:
    """Service for handling OAuth callbacks and token exchange."""

    @staticmethod
    def _get_encryption_key() -> bytes:
        """Get encryption key from settings or file."""
        from django.conf import settings
        import os

        key_path = getattr(settings, "ENCRYPTION_KEY_PATH", None)
        if key_path and os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()

        raise ValueError("Encryption key not configured")

    @staticmethod
    def _get_hmac_key() -> bytes:
        """Get HMAC key from settings or file."""
        from django.conf import settings
        import os

        key_path = getattr(settings, "HMAC_KEY_PATH", None)
        if key_path and os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()

        raise ValueError("HMAC key not configured")

    @staticmethod
    def validate_state(state: str, code_verifier: Optional[str] = None) -> Optional[OAuthState]:
        """
        Validate OAuth state token.

        Args:
            state: State token from OAuth callback
            code_verifier: PKCE code verifier (for mobile flows)

        Returns:
            OAuthState object if valid, None otherwise
        """
        try:
            oauth_state = OAuthState.objects.get(state=state)
        except OAuthState.DoesNotExist:
            return None

        # Check if state is valid (not used and not expired)
        if not oauth_state.is_valid():
            return None

        # Verify PKCE code verifier matches (if using PKCE)
        if code_verifier and oauth_state.code_verifier != code_verifier:
            return None

        # Mark state as used
        oauth_state.mark_as_used()

        return oauth_state

    @staticmethod
    def exchange_code_for_token(
        provider: str, code: str, redirect_uri: str, code_verifier: Optional[str] = None
    ) -> dict:
        """
        Exchange authorization code for access token.

        Args:
            provider: OAuth provider name
            code: Authorization code from OAuth callback
            redirect_uri: Redirect URI used in authorization request
            code_verifier: PKCE code verifier (for mobile flows)

        Returns:
            dict: Token response from provider

        Raises:
            ValueError: If token exchange fails
        """
        config = OAuthService.get_provider_config(provider)
        client_id = OAuthService.get_client_id(provider)
        client_secret = OAuthService.get_client_secret(provider)

        # Build token request
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        # Add PKCE code verifier if used
        if code_verifier:
            data["code_verifier"] = code_verifier

        # Exchange code for token
        response = requests.post(
            config["token_url"],
            data=data,
            headers={"Accept": "application/json"},
            timeout=10,
        )

        if response.status_code != 200:
            raise ValueError(
                f"Token exchange failed: {response.status_code} {response.text}"
            )

        return response.json()

    @staticmethod
    def get_user_info(provider: str, access_token: str) -> dict:
        """
        Get user information from OAuth provider.

        Args:
            provider: OAuth provider name
            access_token: Access token from token exchange

        Returns:
            dict: User information from provider

        Raises:
            ValueError: If user info request fails
        """
        config = OAuthService.get_provider_config(provider)

        # Get user info from provider
        response = requests.get(
            config["user_info_url"],
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

        if response.status_code != 200:
            raise ValueError(
                f"User info request failed: {response.status_code} {response.text}"
            )

        return response.json()

    @staticmethod
    @transaction.atomic
    def create_or_link_account(
        provider: str,
        provider_user_id: str,
        email: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: Optional[int],
        scope: str,
        profile_data: dict,
        authenticated_user: Optional[User] = None,
    ) -> Tuple[User, SocialAccount, bool]:
        """
        Create a new user or link social account to existing user.

        Args:
            provider: OAuth provider name
            provider_user_id: User ID from OAuth provider
            email: Email from OAuth provider
            access_token: OAuth access token
            refresh_token: OAuth refresh token (if provided)
            expires_in: Token expiry in seconds
            scope: OAuth scopes granted
            profile_data: Additional profile data from provider
            authenticated_user: Currently authenticated user (if linking)

        Returns:
            tuple: (User, SocialAccount, created)
                - User: The user object
                - SocialAccount: The social account object
                - created: True if new user was created

        Raises:
            ValueError: If email conflict occurs
        """
        encryption_key = OAuthCallbackService._get_encryption_key()
        hmac_key = OAuthCallbackService._get_hmac_key()

        # Check if social account already exists
        existing_account = SocialAccount.objects.filter(
            provider=provider, provider_user_id=provider_user_id
        ).first()

        if existing_account:
            # Update existing account
            OAuthCallbackService._update_social_account(
                existing_account,
                access_token,
                refresh_token,
                expires_in,
                scope,
                profile_data,
                encryption_key,
            )
            existing_account.update_last_login()
            return existing_account.user, existing_account, False

        # If linking to authenticated user
        if authenticated_user:
            # Check if user already has this provider linked
            if SocialAccount.objects.filter(
                user=authenticated_user, provider=provider
            ).exists():
                raise ValueError(
                    f"User already has a {provider} account linked"
                )

            # Create social account for authenticated user
            social_account = OAuthCallbackService._create_social_account(
                user=authenticated_user,
                provider=provider,
                provider_user_id=provider_user_id,
                email=email,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                scope=scope,
                profile_data=profile_data,
                encryption_key=encryption_key,
            )

            return authenticated_user, social_account, False

        # Check if email is already in use
        email_hash = hash_email_py(email.lower(), hmac_key)
        existing_user = EncryptedEmail.objects.filter(email_hash=email_hash).first()

        if existing_user:
            # Email conflict: Don't auto-create user
            # Frontend should handle this by prompting user to log in
            raise ValueError(
                f"Email {email} is already registered. "
                "Please log in and link your account."
            )

        # Create new user with social account
        user = OAuthCallbackService._create_user_from_social(
            email=email,
            provider=provider,
            profile_data=profile_data,
        )

        # Store encrypted email
        from .email_encryption_service import EmailEncryptionService

        EmailEncryptionService.encrypt_and_save(user, email)

        # Create social account
        social_account = OAuthCallbackService._create_social_account(
            user=user,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scope=scope,
            profile_data=profile_data,
            encryption_key=encryption_key,
        )

        return user, social_account, True

    @staticmethod
    def _create_user_from_social(
        email: str, provider: str, profile_data: dict
    ) -> User:
        """Create a new user from social account data."""
        # Extract name from profile data
        name = profile_data.get("name", "")
        first_name = profile_data.get("given_name", name.split()[0] if name else "")
        last_name = profile_data.get("family_name", name.split()[-1] if name and len(name.split()) > 1 else "")

        # Generate unique username from email
        username = email.split("@")[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        # Set unusable password (user logs in via OAuth only)
        user.set_unusable_password()
        user.save()

        return user

    @staticmethod
    def _create_social_account(
        user: User,
        provider: str,
        provider_user_id: str,
        email: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: Optional[int],
        scope: str,
        profile_data: dict,
        encryption_key: bytes,
    ) -> SocialAccount:
        """Create a new social account."""
        # Encrypt tokens
        access_token_encrypted = encrypt_oauth_token_py(access_token, encryption_key)
        refresh_token_encrypted = (
            encrypt_oauth_token_py(refresh_token, encryption_key)
            if refresh_token
            else None
        )

        # Calculate token expiry
        token_expires_at = None
        if expires_in:
            token_expires_at = timezone.now() + timedelta(seconds=expires_in)

        return SocialAccount.objects.create(
            user=user,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            token_expires_at=token_expires_at,
            scope=scope,
            email=email,
            profile_data=profile_data,
        )

    @staticmethod
    def _update_social_account(
        social_account: SocialAccount,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: Optional[int],
        scope: str,
        profile_data: dict,
        encryption_key: bytes,
    ):
        """Update an existing social account with new tokens."""
        # Encrypt new tokens
        social_account.access_token_encrypted = encrypt_oauth_token_py(
            access_token, encryption_key
        )

        if refresh_token:
            social_account.refresh_token_encrypted = encrypt_oauth_token_py(
                refresh_token, encryption_key
            )

        # Update expiry
        if expires_in:
            social_account.token_expires_at = timezone.now() + timedelta(
                seconds=expires_in
            )

        social_account.scope = scope
        social_account.profile_data = profile_data
        social_account.save()

    @staticmethod
    def decrypt_access_token(social_account: SocialAccount) -> str:
        """
        Decrypt OAuth access token.

        Args:
            social_account: SocialAccount to decrypt token from

        Returns:
            str: Decrypted access token
        """
        encryption_key = OAuthCallbackService._get_encryption_key()
        return decrypt_oauth_token_py(
            social_account.access_token_encrypted, encryption_key
        )
