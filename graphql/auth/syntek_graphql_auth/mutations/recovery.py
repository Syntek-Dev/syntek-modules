"""GraphQL mutations for recovery key operations.

This module defines mutations for generating and using recovery keys
with versioning, expiry tracking, and security enhancements from Phase 2.2.

SECURITY FEATURES:
- Algorithm versioning (support for key format migrations)
- Expiry dates (keys valid for 90 days by default)
- Format options (base64, hex, words)
- One-time use enforcement
- Secure random generation (cryptographically secure)
- Audit logging

Implements requirements:
- IMPROVEMENT: Recovery key versioning and expiry tracking
- Security: One-time use, secure generation, constant-time comparison
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import strawberry
from django.db import transaction

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.recovery_key_service import RecoveryKeyService  # type: ignore[import]
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    ValidationError,
)
from syntek_graphql_core.utils.context import get_ip_address, get_request  # type: ignore[import]
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.recovery import (  # type: ignore[import]
    GenerateRecoveryKeysInput,
    GenerateRecoveryKeysPayload,
    LoginWithRecoveryKeyInput,
    RecoveryKeyType,
)
from syntek_graphql_auth.utils.converters import user_to_graphql_type  # type: ignore[import]

logger = logging.getLogger(__name__)


@strawberry.type
class RecoveryMutations:
    """GraphQL mutations for recovery key management."""

    @strawberry.mutation
    def generate_recovery_keys(
        self, info: Info, input: GenerateRecoveryKeysInput
    ) -> GenerateRecoveryKeysPayload:
        """Generate recovery keys for account recovery.

        Generates a set of one-time use recovery keys with algorithm versioning
        and expiry tracking. Keys can be used to access account if 2FA device lost.

        Security Features:
        - Cryptographically secure random generation
        - Algorithm versioning (v1, v2, etc.)
        - Configurable expiry (90 days default)
        - Multiple format options (base64, hex, words)
        - One-time use enforcement
        - Secure hashing (Argon2id)
        - Audit logging

        Format Options:
        - base64: e.g., "a7Kx-9mPq-W4nZ-Q2vC"
        - hex: e.g., "a7b3-4f8e-d1c9-2a6b"
        - words: e.g., "alpha-bravo-charlie-delta" (easier to write down)

        Args:
            info: GraphQL execution info with authenticated user
            input: Generation input (count, format, expiry_days)

        Returns:
            GenerateRecoveryKeysPayload with recovery keys

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If invalid parameters
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Validate count (max 10 keys)
        if input.count < 1 or input.count > 10:
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                "Recovery key count must be between 1 and 10",
            )

        # Validate format
        valid_formats = ["base64", "hex", "words"]
        if input.format not in valid_formats:
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                f"Format must be one of: {', '.join(valid_formats)}",
            )

        # Validate expiry days (30-365 days)
        if input.expiry_days < 30 or input.expiry_days > 365:
            raise ValidationError(
                ErrorCode.VALIDATION_ERROR,
                "Expiry days must be between 30 and 365",
            )

        with transaction.atomic():  # type: ignore[attr-defined]
            # Revoke existing unused keys
            RecoveryKeyService.revoke_unused_keys(user)

            # Generate new recovery keys
            keys, key_objects = RecoveryKeyService.generate_keys(
                user=user,
                count=input.count,
                format=input.format,
                expiry_days=input.expiry_days,
            )

            # Convert to GraphQL types
            recovery_keys = [
                RecoveryKeyType(
                    id=strawberry.ID(str(key_obj.id)),
                    algorithm_version=key_obj.algorithm_version,
                    created_at=key_obj.created_at.isoformat(),
                    expires_at=key_obj.expires_at.isoformat(),
                    is_expired=key_obj.is_expired(),
                    is_used=key_obj.is_used,
                    days_until_expiry=key_obj.days_until_expiry(),
                )
                for key_obj in key_objects
            ]

            # Log recovery key generation
            AuditService.log_event(
                action="recovery_keys_generated",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={
                    "count": input.count,
                    "format": input.format,
                    "expiry_days": input.expiry_days,
                    "algorithm_version": key_objects[0].algorithm_version,
                },
            )

            return GenerateRecoveryKeysPayload(
                success=True,
                message=f"Generated {input.count} recovery keys. Store them securely!",
                recovery_keys=keys,  # Plaintext keys (shown only once)
                recovery_key_objects=recovery_keys,  # Metadata (safe to expose)
            )

    @strawberry.mutation
    def login_with_recovery_key(
        self, info: Info, input: LoginWithRecoveryKeyInput
    ) -> AuthPayload:  # type: ignore[name-defined]
        """Login using a recovery key.

        Authenticates user with a one-time recovery key when 2FA device is lost.
        Marks key as used and issues JWT tokens.

        Security Features:
        - Constant-time key comparison
        - One-time use enforcement
        - Automatic key revocation after use
        - Expiry validation
        - Rate limiting (5/15min per IP)
        - Audit logging

        Args:
            info: GraphQL execution info
            input: Login input (email, recovery_key)

        Returns:
            AuthPayload with tokens and user data

        Raises:
            AuthenticationError: If key invalid or expired
        """
        from syntek_graphql_auth.types.auth import AuthPayload  # Avoid circular import

        ip_address = get_ip_address(info)

        with transaction.atomic():  # type: ignore[attr-defined]
            # Authenticate with recovery key
            user, token_pair = RecoveryKeyService.authenticate_with_recovery_key(
                email=input.email,
                recovery_key=input.recovery_key,
                ip_address=ip_address,
            )

            if not user:
                # Generic error message (prevent enumeration)
                raise AuthenticationError(
                    ErrorCode.INVALID_CREDENTIALS,
                    "Invalid email or recovery key",
                )

            # Log successful recovery key login
            AuditService.log_event(
                action="recovery_key_login",
                user=user,
                organisation=getattr(user, "organisation", None),
                ip_address=ip_address,
                metadata={"email": input.email},
            )

            # Convert user to GraphQL type
            graphql_user = user_to_graphql_type(user)

            return AuthPayload(
                success=True,
                message="Login successful with recovery key",
                access_token=token_pair["access"],
                refresh_token=token_pair["refresh"],
                user=graphql_user,
            )
