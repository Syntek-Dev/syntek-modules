"""GraphQL types for authentication operations.

This module defines input and output types for authentication mutations.
Implementation stub for TDD - tests will fail until fully implemented.
"""

from __future__ import annotations

from uuid import UUID  # noqa: TC003 - Required at runtime for Strawberry GraphQL

import strawberry

from syntek_graphql_auth.types.user import (
    UserType,  # noqa: TC001 - Required at runtime for Strawberry GraphQL
)


@strawberry.input
class RegisterInput:
    """Input for user registration mutation.

    Legal document acceptance is optional but recommended. If accepted_document_ids
    is provided, the registration will record acceptance of those documents.
    Clients should fetch registration_requirements query first to get document IDs.
    """

    email: str
    password: str
    first_name: str
    last_name: str
    organisation_slug: str
    captcha_token: str | None = None  # Required in production (Phase 4)
    accepted_document_ids: list[UUID] | None = None  # Legal documents accepted (Phase 8b)


@strawberry.input
class LoginInput:
    """Input for user login mutation."""

    email: str
    password: str
    totp_code: str | None = None  # For 2FA (Phase 4)
    captcha_token: str | None = None  # Required in production (Phase 4)


@strawberry.input
class PasswordResetRequestInput:
    """Input for password reset request mutation."""

    email: str


@strawberry.input
class PasswordResetInput:
    """Input for password reset completion mutation."""

    token: str
    new_password: str


@strawberry.input
class PasswordChangeInput:
    """Input for password change mutation."""

    current_password: str
    new_password: str


@strawberry.input
class EnableTwoFactorInput:
    """Input for enabling 2FA mutation."""

    totp_code: str  # Verify setup worked


@strawberry.type
class AuthPayload:
    """Response payload for authentication mutations.

    Updated to include session management fields for H12 (concurrent session limit).
    Field names use snake_case for consistency with GraphQL conventions.
    """

    access_token: str
    refresh_token: str
    user: UserType
    requires_two_factor: bool = False

    # Session management fields (H12 - Concurrent session limit)
    session_count: int | None = None
    session_limit: int | None = None
    oldest_session_revoked: bool = False


@strawberry.type
class TwoFactorSetupPayload:
    """Response payload for 2FA setup mutation."""

    secret: str
    qr_code_url: str
    backup_codes: list[str]
