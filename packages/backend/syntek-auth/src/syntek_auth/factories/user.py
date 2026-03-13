"""factory_boy factories for the ``User`` model — ``syntek-auth`` / US009.

Provides ``UserFactory`` for building ``User`` instances in tests without
hitting the database (``build()``) or with database persistence (``create()``).

The factory computes HMAC-SHA256 lookup tokens (``email_token``,
``phone_token``, ``username_token``) automatically via ``LazyAttribute`` so
that test users satisfy the DB uniqueness constraints on those columns.
Tests must have ``SYNTEK_AUTH['FIELD_HMAC_KEY']`` configured (the project
``conftest.py`` sets a safe test key).
"""

from __future__ import annotations

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser

from syntek_auth.services.lookup_tokens import (
    make_email_token,
    make_phone_token,
    make_username_token,
)


def _email_token(email: str) -> str:
    return make_email_token(email)


def _username_token(username: str) -> str:
    return make_username_token(username)


def _phone_token(phone: str) -> str:
    return make_phone_token(phone)


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for the concrete ``User`` model.

    Uses ``factory.Sequence`` to generate a unique email address per instance.
    Lookup tokens are derived automatically from the corresponding plaintext
    fields via ``LazyAttribute``.

    Examples
    --------
    Build a User without touching the database::

        user = UserFactory.build()

    Create a User with a custom email::

        user = UserFactory.create(email="alice@example.com")

    Create a User with a username::

        user = UserFactory.create(username="alice", username_token=None)
        # username_token is computed automatically when username is set
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = get_user_model()
        skip_postgeneration_save = True

    email: factory.LazyAttribute = factory.Sequence(  # type: ignore[assignment]
        lambda n: f"user{n}@example.com"
    )
    email_token = factory.LazyAttribute(lambda obj: _email_token(obj.email))  # type: ignore[reportPrivateImportUsage]

    username: str | None = None
    username_token = factory.LazyAttribute(  # type: ignore[reportPrivateImportUsage]
        lambda obj: _username_token(obj.username) if obj.username else None
    )

    phone: str | None = None
    phone_token = factory.LazyAttribute(  # type: ignore[reportPrivateImportUsage]
        lambda obj: _phone_token(obj.phone) if obj.phone else None
    )

    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    email_verified: bool = False
    phone_verified: bool = False

    @classmethod
    def _create(
        cls,
        model_class: type,
        *_args: object,
        **kwargs: object,
    ) -> object:
        """Delegate to ``create_user`` so PII fields are encrypted before DB write."""
        # Tokens are recomputed from plaintext inside create_user
        kwargs.pop("email_token", None)
        kwargs.pop("phone_token", None)
        kwargs.pop("username_token", None)
        email = str(kwargs.pop("email"))
        # Password is handled by the @factory.post_generation hook after creation
        manager = model_class._default_manager
        return manager.create_user(email=email, password=None, **kwargs)  # type: ignore[return-value]

    @factory.post_generation  # type: ignore[misc]
    def password(
        self: object,  # type: ignore[misc]
        create: bool,
        extracted: str | None,
        **kwargs: object,  # noqa: ARG002
    ) -> None:
        """Set the password on the user instance after generation.

        When ``extracted`` is provided it is used as the plaintext password.
        Otherwise ``"testpassword123"`` is used as the default.

        Explicitly saves the instance when ``create=True`` because
        ``skip_postgeneration_save = True`` suppresses the automatic re-save
        that factory_boy used to perform after post-generation hooks.
        """
        if isinstance(self, AbstractBaseUser):
            password_value = extracted if extracted is not None else "testpassword123"
            self.set_password(password_value)  # type: ignore[union-attr]
            if create:
                self.save(update_fields=["password"])  # type: ignore[union-attr]
