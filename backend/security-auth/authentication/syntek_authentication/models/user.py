"""User model.

Custom user model with email authentication and multi-tenant support.
Implements security requirements from OWASP, NIST, and GDPR standards.
"""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models


class UserManager(models.Manager):
    """Custom user manager for email-based authentication.

    Handles user creation with proper email normalisation and password hashing.
    Implements Django's BaseUserManager pattern for custom user models.
    """

    def normalize_email(self, email: str) -> str:
        """Normalise email address by lowercasing the domain part.

        Preserves the case of the local part (before @) but lowercases
        the domain part (after @) as per RFC 5321.

        Args:
            email: The email address to normalise.

        Returns:
            Normalised email address with lowercase domain.

        Raises:
            ValueError: If email is not provided or invalid format.
        """
        if not email:
            raise ValueError("Email address is required")

        email = email.strip()

        if "@" not in email:
            raise ValueError("Email address must contain @")

        try:
            local_part, domain = email.rsplit("@", 1)
        except ValueError as e:
            raise ValueError("Invalid email format") from e

        return f"{local_part}@{domain.lower()}"

    def _create_user(self, email: str, password: str | None = None, **extra_fields) -> User:
        """Create and save a user with the given email and password.

        Internal method for creating users with common validation logic.

        Args:
            email: User email address.
            password: User password (optional).
            **extra_fields: Additional user fields.

        Returns:
            Created User instance.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields) -> User:
        """Create and return a regular user.

        Sets default values for is_staff and is_superuser to False.

        Args:
            email: User email address.
            password: User password (optional).
            **extra_fields: Additional user fields.

        Returns:
            Created User instance.

        Raises:
            ValueError: If is_staff or is_superuser are set to True.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        if extra_fields.get("is_staff") is True:
            raise ValueError("Regular users cannot have is_staff=True")
        if extra_fields.get("is_superuser") is True:
            raise ValueError("Regular users cannot have is_superuser=True")

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> User:
        """Create and return a superuser.

        Sets is_staff and is_superuser to True. Superusers have all permissions
        and can access the Django admin interface.

        Args:
            email: User email address.
            password: User password (required for superusers).
            **extra_fields: Additional user fields.

        Returns:
            Created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser are set to False or password not provided.
        """
        if password is None:
            raise ValueError("Superusers must have a password")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusers must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusers must have is_superuser=True")

        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email: str) -> User:
        """Get user by email (case-insensitive).

        Used by Django authentication system for looking up users.

        Args:
            email: User email address.

        Returns:
            User instance.

        Raises:
            User.DoesNotExist: If no user found with the given email.
        """
        return self.get(email__iexact=email)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email authentication.

    Uses email as the unique identifier instead of username.
    Supports multi-tenancy through organisation relationships.

    Attributes:
        id: UUID primary key
        email: Unique email address (used for authentication)
        first_name: User's first name
        last_name: User's last name
        organisation: Foreign key to Organisation (nullable for platform superusers)
        is_active: Account active status
        is_staff: Django admin access flag
        email_verified: Email verification status
        email_verified_at: Timestamp of email verification
        two_factor_enabled: 2FA enabled flag
        has_email_account: SaaS email service access flag
        has_vault_access: Password manager access flag
        last_login_ip: Encrypted IP address of last login
        password_changed_at: Timestamp of last password change (H11)
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")

    # Organisation FK - nullable for platform superusers
    organisation = models.ForeignKey(
        "syntek_authentication.Organisation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    # Status fields
    is_active = models.BooleanField(default=True)  # type: ignore[call-arg]
    is_staff = models.BooleanField(default=False)  # type: ignore[call-arg]

    # Email verification
    email_verified = models.BooleanField(default=False)  # type: ignore[call-arg]
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)  # type: ignore[call-arg]

    # SaaS feature flags
    has_email_account = models.BooleanField(default=False)  # type: ignore[call-arg]
    has_vault_access = models.BooleanField(default=False)  # type: ignore[call-arg]

    # Security tracking
    last_login_ip = models.BinaryField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    # Account lockout (P2-C7)
    failed_login_attempts = models.IntegerField(default=0)  # type: ignore[call-arg]
    account_locked_until = models.DateTimeField(null=True, blank=True)

    # Email verification token storage
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)
    email_verification_token_created = models.DateTimeField(null=True, blank=True)

    # GDPR compliance fields (Article 18 - Right to Restriction of Processing)
    processing_restricted = models.BooleanField(
        default=False,  # type: ignore[call-arg]
        help_text="User has restricted processing of their data (GDPR Article 18)",
    )
    restriction_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for processing restriction",
    )
    restricted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when processing was restricted",
    )
    deletion_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when account deletion was requested",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "core_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["organisation"]),
            # H1: Composite indexes for multi-tenant queries
            models.Index(fields=["organisation", "email"]),
            models.Index(fields=["organisation", "is_active"]),
            models.Index(fields=["organisation", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Return user email."""
        return str(self.email)

    def save(self, *args, **kwargs):
        """Save user with normalised email.

        Normalises email to lowercase for case-insensitive uniqueness.
        """
        if self.email:
            self.email = self.email.lower()  # type: ignore[attr-defined]
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        """Return first and last name with a space."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        """Return first name."""
        return str(self.first_name)
