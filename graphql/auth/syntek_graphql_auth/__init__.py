"""Syntek GraphQL Auth - Authentication & Session Management.

Production-ready authentication mutations and queries with JWT, TOTP 2FA,
and session management.

Features:
- User registration and login with email verification
- JWT access and refresh tokens with rotation
- TOTP two-factor authentication with backup codes
- Session management with concurrent session limiting
- Password reset with secure token hashing
- Comprehensive audit logging
- Rate limiting and CAPTCHA protection
"""

__version__ = "2.0.0"

from syntek_graphql_auth.mutations import AuthMutations, SessionMutation, TOTPMutations
from syntek_graphql_auth.queries import UserQueries
from syntek_graphql_auth.schema import create_auth_schema

__all__ = [
    # Version
    "__version__",
    # Mutations
    "AuthMutations",
    "SessionMutation",
    "TOTPMutations",
    # Queries
    "UserQueries",
    # Schema
    "create_auth_schema",
]
