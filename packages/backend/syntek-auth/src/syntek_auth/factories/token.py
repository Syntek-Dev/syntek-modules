"""factory_boy factories for token models — ``syntek-auth`` / US009.

Provides ``RefreshTokenFactory`` and ``AccessTokenDenylistFactory`` for
building token model instances in tests.
"""

from __future__ import annotations

import secrets
from datetime import timedelta

import factory
from django.utils import timezone

from syntek_auth.factories.user import UserFactory
from syntek_auth.models.tokens import RefreshToken
from syntek_auth.models.verification import AccessTokenDenylist


class RefreshTokenFactory(factory.django.DjangoModelFactory):
    """Factory for the ``RefreshToken`` model.

    Generates a unique random JTI and sets a 7-day expiry by default.

    Examples
    --------
    Create a refresh token for a specific user::

        token = RefreshTokenFactory.create(user=some_user)
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = RefreshToken

    user = factory.SubFactory(UserFactory)  # type: ignore[attr-defined]
    jti: factory.LazyFunction = factory.LazyFunction(  # type: ignore[assignment]
        lambda: secrets.token_hex(16)
    )
    expires_at: factory.LazyFunction = factory.LazyFunction(  # type: ignore[assignment]
        lambda: timezone.now() + timedelta(days=7)
    )


class AccessTokenDenylistFactory(factory.django.DjangoModelFactory):
    """Factory for the ``AccessTokenDenylist`` model.

    Generates a unique random JTI and sets a 15-minute expiry by default.

    Examples
    --------
    Create a denylist entry::

        entry = AccessTokenDenylistFactory.create()
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = AccessTokenDenylist

    jti: factory.LazyFunction = factory.LazyFunction(  # type: ignore[assignment]
        lambda: secrets.token_hex(16)
    )
    expires_at: factory.LazyFunction = factory.LazyFunction(  # type: ignore[assignment]
        lambda: timezone.now() + timedelta(minutes=15)
    )
