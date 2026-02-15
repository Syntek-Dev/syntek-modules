"""
Social account model for OAuth authentication.

Stores encrypted OAuth tokens and provider information.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class SocialAccount(models.Model):
    """
    Social account linked to a user via OAuth.

    Stores encrypted access tokens and refresh tokens for OAuth providers.
    Supports multiple providers per user (e.g., Google + GitHub).
    """

    PROVIDER_CHOICES = [
        ("google", "Google"),
        ("github", "GitHub"),
        ("microsoft", "Microsoft"),
        ("apple", "Apple"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("twitter", "Twitter/X"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
        help_text="User who owns this social account",
    )

    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text="OAuth provider name (e.g., google, github)",
        db_index=True,
    )

    provider_user_id = models.CharField(
        max_length=255,
        help_text="User ID from the OAuth provider",
        db_index=True,
    )

    access_token_encrypted = models.BinaryField(
        help_text="Encrypted OAuth access token (AES-256-GCM)"
    )

    refresh_token_encrypted = models.BinaryField(
        null=True,
        blank=True,
        help_text="Encrypted OAuth refresh token (if provided)",
    )

    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the access token expires",
    )

    scope = models.TextField(
        blank=True,
        help_text="OAuth scopes granted (space-separated)",
    )

    email = models.EmailField(
        blank=True,
        help_text="Email from OAuth provider (not encrypted, for display only)",
    )

    profile_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional profile data from provider (name, avatar, etc.)",
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the user's primary social login method",
    )

    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When this account was first linked"
    )

    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this social account was last used to log in",
    )

    class Meta:
        db_table = "auth_social_account"
        verbose_name = "Social Account"
        verbose_name_plural = "Social Accounts"
        unique_together = [("provider", "provider_user_id")]
        indexes = [
            models.Index(fields=["user", "provider"]),
            models.Index(fields=["provider", "provider_user_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.get_provider_display()}"

    def is_token_expired(self):
        """
        Check if the access token has expired.

        Returns:
            bool: True if token is expired or expiry unknown, False otherwise
        """
        if not self.token_expires_at:
            return True  # Assume expired if no expiry set
        return timezone.now() >= self.token_expires_at

    def mark_as_primary(self):
        """
        Mark this social account as primary.

        Unmarks any other social accounts for this user.
        """
        SocialAccount.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        self.is_primary = True
        self.save(update_fields=["is_primary"])

    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login_at = timezone.now()
        self.save(update_fields=["last_login_at"])


class OAuthState(models.Model):
    """
    OAuth state token for CSRF protection.

    Stores short-lived state tokens used during OAuth authorization flow
    to prevent CSRF attacks.
    """

    state = models.CharField(
        max_length=255,
        unique=True,
        help_text="Random state token (CSPRNG-generated)",
        db_index=True,
    )

    provider = models.CharField(
        max_length=20,
        help_text="OAuth provider name",
    )

    redirect_uri = models.CharField(
        max_length=500,
        help_text="Redirect URI after OAuth callback",
    )

    code_verifier = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="PKCE code verifier (for mobile OAuth)",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this state was created",
        db_index=True,
    )

    used = models.BooleanField(
        default=False,
        help_text="Whether this state has been used",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User initiating OAuth (if authenticated)",
    )

    class Meta:
        db_table = "auth_oauth_state"
        verbose_name = "OAuth State"
        verbose_name_plural = "OAuth States"
        indexes = [
            models.Index(fields=["state"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.provider} - {self.state[:10]}..."

    def is_expired(self):
        """
        Check if the state token has expired.

        State tokens expire after 10 minutes.

        Returns:
            bool: True if expired, False otherwise
        """
        from datetime import timedelta

        expiry_time = self.created_at + timedelta(minutes=10)
        return timezone.now() >= expiry_time

    def is_valid(self):
        """
        Check if the state token is valid (not used and not expired).

        Returns:
            bool: True if valid, False otherwise
        """
        return not self.used and not self.is_expired()

    def mark_as_used(self):
        """Mark this state token as used."""
        self.used = True
        self.save(update_fields=["used"])


class SocialLoginAttempt(models.Model):
    """
    Audit log for social login attempts.

    Tracks all OAuth login attempts for security monitoring and GDPR compliance.
    """

    STATUS_CHOICES = [
        ("success", "Success"),
        ("failed", "Failed"),
        ("email_conflict", "Email Conflict"),
        ("account_linked", "Account Linked"),
        ("invalid_state", "Invalid State"),
        ("provider_error", "Provider Error"),
    ]

    provider = models.CharField(
        max_length=20,
        help_text="OAuth provider name",
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Login attempt status",
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="social_login_attempts",
        help_text="User who attempted login (if successful or account exists)",
    )

    provider_user_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="User ID from OAuth provider",
    )

    email = models.EmailField(
        blank=True,
        help_text="Email from OAuth provider",
    )

    ip_address = models.GenericIPAddressField(help_text="IP address of the login attempt")

    user_agent = models.TextField(
        blank=True,
        help_text="User agent string from browser",
    )

    error_message = models.TextField(
        blank=True,
        help_text="Error message if login failed",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the login attempt occurred",
        db_index=True,
    )

    class Meta:
        db_table = "auth_social_login_attempt"
        verbose_name = "Social Login Attempt"
        verbose_name_plural = "Social Login Attempts"
        indexes = [
            models.Index(fields=["provider", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} - {self.status} - {self.created_at}"
