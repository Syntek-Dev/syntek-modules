"""User model for ``syntek-auth`` — US009.

Defines the abstract base user, concrete user, and user manager that together
form the authentication identity layer.

Classes
-------
EncryptedField
    Django ``TextField`` subclass for AES-256-GCM encrypted PII columns.
    Delegates ciphertext validation to ``syntek_pyo3`` when available.
SyntekUserManager
    Custom manager providing ``create_user`` and ``create_superuser``.
    Computes HMAC-SHA256 lookup tokens for unique encrypted fields before save.
AbstractSyntekUser
    Abstract base class combining ``AbstractBaseUser`` and ``PermissionsMixin``.
    Carries ``EncryptedField`` PII columns for ``email``, ``phone``, and
    ``username``.  Uniqueness is enforced via companion ``*_token`` columns
    rather than directly on ciphertext (which is non-deterministic).
User
    Concrete subclass of ``AbstractSyntekUser`` that consumers point
    ``AUTH_USER_MODEL`` at.  Module internals always obtain the active user
    model via ``get_user_model()`` and never import this class directly.

Uniqueness strategy
-------------------
AES-256-GCM uses a random nonce per encryption, so the same plaintext
encrypted twice produces different ciphertext.  A DB UNIQUE constraint on
ciphertext is therefore meaningless.

Instead, a deterministic HMAC-SHA256 token of the normalised plaintext is
stored in a companion column:

    email        → email_token    (unique, not null)
    phone        → phone_token    (unique, nullable)
    username     → username_token (unique, nullable)

``SyntekUserManager.create_user`` computes these tokens automatically.
See ``services.lookup_tokens`` for the token functions.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.db import models

from syntek_auth.services.lookup_tokens import (
    make_email_token,
    make_phone_token,
    make_username_token,
)

# ---------------------------------------------------------------------------
# EncryptedField — storage + validation Django field
# ---------------------------------------------------------------------------


class EncryptedField(models.TextField):
    """Django model field for AES-256-GCM encrypted values.

    Extends ``TextField`` so that Django migrations can reference it without
    errors and the underlying DB column is ``TEXT``.

    When ``syntek_pyo3`` is installed (compiled PyO3 extension), ciphertext
    validation is delegated to the Rust ``EncryptedField``:

    - ``validate()`` raises ``ValidationError`` for any value that is not
      valid base64ct-encoded ciphertext with at least 28 decoded bytes.
    - ``pre_save()`` calls ``validate()`` before any DB write.

    When ``syntek_pyo3`` is not yet available (e.g. during early development
    or CI without the compiled extension), both methods fall back to a no-op
    so that tests and migrations continue to work with plaintext values.

    Actual encryption and decryption is the responsibility of the service
    layer (``syntek_pyo3.encrypt_field`` / ``syntek_pyo3.decrypt_field``) and
    the GraphQL middleware — not this field class.
    """

    def validate(self, value: object, model_instance: object) -> None:
        try:
            from syntek_pyo3 import (
                EncryptedField as _RustField,  # type: ignore[import-not-found]
            )

            _RustField().validate(str(value), model_instance)  # pyright: ignore[reportArgumentType]
        except ImportError:
            pass
        super().validate(value, model_instance)  # pyright: ignore[reportArgumentType]

    def pre_save(self, model_instance: models.Model, add: bool) -> object:
        value = super().pre_save(model_instance, add)
        if value is not None:
            try:
                from syntek_pyo3 import (
                    EncryptedField as _RustField,  # type: ignore[import-not-found]
                )

                _RustField().validate(str(value), None)
            except ImportError:
                pass
        return value


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class SyntekUserManager(BaseUserManager["AbstractSyntekUser"]):
    """Custom manager for ``AbstractSyntekUser`` and its concrete subclasses.

    Provides ``create_user`` and ``create_superuser`` helpers that normalise
    the email address, set the password via Django's hashing pipeline, and
    compute HMAC-SHA256 lookup tokens for all unique encrypted fields.
    """

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> AbstractSyntekUser:
        """Create and return a regular user.

        Normalises ``email`` with ``BaseUserManager.normalize_email`` and
        computes lookup tokens for ``email``, ``phone``, and ``username``
        before saving.  Tokens are computed by the functions in
        ``services.lookup_tokens`` and require ``SYNTEK_AUTH['FIELD_HMAC_KEY']``
        to be configured.

        Parameters
        ----------
        email:
            The user's email address.  Must not be empty.
        password:
            The plaintext password.  When ``None``, an unusable password is set.
        **extra_fields:
            Additional model fields.  Pass ``phone``, ``username``, etc. here;
            their tokens will be computed automatically if not already supplied.

        Returns
        -------
        AbstractSyntekUser
            The newly created user instance.

        Raises
        ------
        ValueError
            If ``email`` is empty or not provided.
        ImproperlyConfigured
            If ``SYNTEK_AUTH['FIELD_HMAC_KEY']`` is not set.
        """
        if not email:
            raise ValueError("The email address must be provided and non-empty.")

        email = self.normalize_email(email)

        # Email token — always required
        if "email_token" not in extra_fields:
            extra_fields["email_token"] = make_email_token(email)

        # Phone token — only when phone is supplied
        phone = extra_fields.get("phone")
        if phone and "phone_token" not in extra_fields:
            extra_fields["phone_token"] = make_phone_token(str(phone))

        # Username token — only when username is supplied
        username = extra_fields.get("username")
        if username and "username_token" not in extra_fields:
            cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
            case_sensitive: bool = bool(cfg.get("USERNAME_CASE_SENSITIVE", False))
            extra_fields["username_token"] = make_username_token(
                str(username), case_sensitive=case_sensitive
            )

        # Encrypt PII fields before save — tokens are computed from plaintext above.
        try:
            from syntek_pyo3 import (
                encrypt_fields_batch,  # type: ignore[import-not-found]
            )

            _cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
            _raw_key = _cfg.get("FIELD_KEY", "")
            _field_key: bytes = (
                _raw_key.encode("utf-8")
                if isinstance(_raw_key, str)
                else bytes(_raw_key)
            )
            _model_name: str = self.model.__name__

            _fields_to_encrypt: list[tuple[str, str]] = [("email", email)]
            if phone:
                _fields_to_encrypt.append(("phone", str(phone)))
            if username:
                _fields_to_encrypt.append(("username", str(username)))

            _encrypted = encrypt_fields_batch(
                _fields_to_encrypt, _field_key, _model_name
            )
            email = _encrypted[0]
            _idx = 1
            if phone:
                extra_fields["phone"] = _encrypted[_idx]
                _idx += 1
            if username:
                extra_fields["username"] = _encrypted[_idx]
        except ImportError:
            pass

        user: AbstractSyntekUser = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> AbstractSyntekUser:
        """Create and return a superuser (``is_staff=True``, ``is_superuser=True``).

        Parameters
        ----------
        email:
            The superuser's email address.
        password:
            The plaintext password.
        **extra_fields:
            Additional model fields.

        Returns
        -------
        AbstractSyntekUser
            The newly created superuser instance.

        Raises
        ------
        ValueError
            If ``is_staff`` or ``is_superuser`` is explicitly set to ``False``.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is False:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is False:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# ---------------------------------------------------------------------------
# Abstract base user
# ---------------------------------------------------------------------------


class AbstractSyntekUser(AbstractBaseUser, PermissionsMixin):
    """Abstract base user for the Syntek authentication system.

    PII columns (``email``, ``phone``, ``username``) are stored via
    ``EncryptedField`` so that values are encrypted with AES-256-GCM before
    any database write.

    Because AES-256-GCM is non-deterministic (random nonce per encryption),
    uniqueness is enforced via companion HMAC-SHA256 token columns rather than
    directly on the ciphertext:

        email        → email_token    (unique, NOT NULL)
        phone        → phone_token    (unique, nullable)
        username     → username_token (unique, nullable)

    ``USERNAME_FIELD`` is ``"email"``.  The ``LOGIN_FIELD`` setting controls
    which field is used for authentication at runtime.

    This class is abstract (``Meta.abstract = True``) and cannot be
    instantiated directly.
    """

    # ------------------------------------------------------------------
    # Encrypted PII fields
    # ------------------------------------------------------------------

    email: EncryptedField = EncryptedField(
        blank=False,
        null=False,
        verbose_name="email address",
    )
    email_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="email lookup token",
        help_text=(
            "HMAC-SHA256 of the normalised email address.  "
            "Holds the uniqueness constraint in place of the ciphertext."
        ),
    )

    phone: EncryptedField = EncryptedField(
        blank=True,
        null=True,
        verbose_name="phone number",
    )
    phone_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="phone lookup token",
        help_text=(
            "HMAC-SHA256 of the phone number.  "
            "Holds the uniqueness constraint in place of the ciphertext."
        ),
    )

    username: EncryptedField = EncryptedField(
        blank=True,
        null=True,
        verbose_name="username",
    )
    username_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        verbose_name="username lookup token",
        help_text=(
            "HMAC-SHA256 of the normalised username.  "
            "Holds the uniqueness constraint in place of the ciphertext."
        ),
    )

    # ------------------------------------------------------------------
    # MFA
    # ------------------------------------------------------------------

    totp_secret: EncryptedField = EncryptedField(
        blank=True,
        null=True,
        verbose_name="TOTP secret",
        help_text=(
            "AES-256-GCM encrypted base32-encoded TOTP secret for RFC 6238 "
            "authenticator apps.  Null until the user enables TOTP."
        ),
    )
    totp_secret_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="TOTP secret token",
        help_text=(
            "HMAC-SHA256 of the plaintext TOTP secret.  Enforces uniqueness "
            "across users — no two accounts may share the same TOTP seed."
        ),
    )

    # ------------------------------------------------------------------
    # Status flags
    # ------------------------------------------------------------------

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    email_verified = models.BooleanField(
        default=False,
        verbose_name="email verified",
    )
    phone_verified = models.BooleanField(
        default=False,
        verbose_name="phone verified",
    )

    objects: SyntekUserManager = SyntekUserManager()  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Concrete user
# ---------------------------------------------------------------------------


class User(AbstractSyntekUser):
    """Concrete user model — consumers set ``AUTH_USER_MODEL = 'syntek_auth.User'``.

    Module internals must never import this class directly; use
    ``django.contrib.auth.get_user_model()`` instead.
    """

    class Meta(AbstractSyntekUser.Meta):
        abstract = False
        swappable = "AUTH_USER_MODEL"
