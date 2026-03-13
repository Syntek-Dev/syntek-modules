"""factory_boy factories for ``syntek-auth`` — US009.

Re-exports all public factory classes so that tests can import from the
stable path ``syntek_auth.factories``.

All factories were previously in the flat ``syntek_auth/factories.py`` module.
The public API is unchanged — existing imports continue to resolve correctly.
"""

from __future__ import annotations

from syntek_auth.factories.token import AccessTokenDenylistFactory, RefreshTokenFactory
from syntek_auth.factories.user import UserFactory
from syntek_auth.factories.verification import VerificationCodeFactory

__all__ = [
    "AccessTokenDenylistFactory",
    "RefreshTokenFactory",
    "UserFactory",
    "VerificationCodeFactory",
]
