"""factory_boy factories for ``VerificationCode`` — ``syntek-auth`` / US009.

Provides ``VerificationCodeFactory`` for building verification code instances
in tests.  Defaults to an ``email_verify`` code type with a 24-hour expiry.
"""

from __future__ import annotations

from datetime import timedelta

import factory
from django.utils import timezone

from syntek_auth.factories.user import UserFactory
from syntek_auth.models.verification import VerificationCode


class VerificationCodeFactory(factory.django.DjangoModelFactory):
    """Factory for the ``VerificationCode`` model.

    Generates a URL-safe token, sets expiry 24 hours in the future, and
    defaults to ``code_type=EMAIL_VERIFY``.

    Examples
    --------
    Create an email verification code::

        code = VerificationCodeFactory.create(user=some_user)

    Create an expired phone OTP::

        code = VerificationCodeFactory.create(
            code_type=VerificationCode.CodeType.PHONE_VERIFY,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
    """

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = VerificationCode

    user = factory.SubFactory(UserFactory)  # type: ignore[attr-defined]
    code_type = VerificationCode.CodeType.EMAIL_VERIFY
    token: factory.LazyAttribute = factory.Sequence(  # type: ignore[assignment]
        lambda n: f"test-token-{n:06d}"
    )
    expires_at: factory.LazyFunction = factory.LazyFunction(  # type: ignore[assignment]
        lambda: timezone.now() + timedelta(hours=24)
    )
    used_at = None
    attempt_count = 0
