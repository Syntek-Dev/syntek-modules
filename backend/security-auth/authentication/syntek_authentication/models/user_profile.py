"""UserProfile model for user personalisation.

Stores additional user information including contact details,
avatar, localisation preferences, and biographical information.
"""

import uuid

from django.db import models


class UserProfile(models.Model):
    """User profile with additional personalisation information.

    Extends the User model with profile-specific data including
    localisation preferences, contact details, and avatar information.

    Attributes:
        id: UUID primary key
        user: One-to-one relationship with User model
        phone: Contact phone number (optional, max 20 chars)
        avatar: URL to user's avatar image (optional)
        timezone: User's timezone preference (default: UTC)
        language: User's language preference (default: en)
        bio: User biography text (optional)
        created_at: Profile creation timestamp
        updated_at: Last modification timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        "syntek_authentication.User",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=20, blank=True, default="")
    avatar = models.URLField(max_length=500, blank=True, default="")
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")
    bio = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self) -> str:
        """Return user email for profile."""
        return f"Profile for {getattr(self.user, 'email', 'Unknown')}"
