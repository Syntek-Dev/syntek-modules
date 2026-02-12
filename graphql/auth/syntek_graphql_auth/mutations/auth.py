"""GraphQL mutations for authentication operations.

This module defines all authentication-related mutations with full implementation
for Phase 3 including security requirements C4, C5, H2, H4, H10, M1.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import strawberry
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone as tz

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.models import EmailVerificationToken, Organisation  # type: ignore[import]
from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.auth_service import AuthService  # type: ignore[import]
from apps.core.services.captcha_service import captcha_service  # type: ignore[import]
from apps.core.services.email_service import EmailService  # type: ignore[import]
from apps.core.services.legal_document_service import LegalDocumentService  # type: ignore[import]
from apps.core.services.password_reset_service import PasswordResetService  # type: ignore[import]
from apps.core.services.token_service import TokenService  # type: ignore[import]
from apps.core.utils.token_hasher import TokenHasher  # type: ignore[import]
from syntek_graphql_core.errors import (  # type: ignore[import]
    AuthenticationError,
    ErrorCode,
    ValidationError,
)
from syntek_graphql_core.utils.context import (  # type: ignore[import]
    get_bearer_token,
    get_ip_address,
    get_request,
    get_user_agent,
)
from syntek_graphql_core.utils.typing import get_authenticated_user  # type: ignore[import]

from syntek_graphql_auth.types.auth import (  # type: ignore[import]
    AuthPayload,
    EnableTwoFactorInput,
    LoginInput,
    PasswordChangeInput,
    PasswordResetInput,
    PasswordResetRequestInput,
    RegisterInput,
    TwoFactorSetupPayload,
)
from syntek_graphql_auth.utils.converters import user_to_graphql_type  # type: ignore[import]

User = get_user_model()


@strawberry.type
class AuthMutations:
    """GraphQL mutations for authentication."""

    @strawberry.mutation
    def register(self, info: Info, input: RegisterInput) -> AuthPayload:
        """Register a new user account.

        Creates user, sends verification email, and returns auth tokens.
        Implements error code standardisation (H4) and CAPTCHA protection (M001).

        Args:
            info: GraphQL execution info
            input: Registration input data

        Returns:
            AuthPayload with token and user data

        Raises:
            ValidationError: If email exists or organisation not found (H4)
            AuthenticationError: If CAPTCHA validation fails (M001)
        """
        # Get client IP for audit logging
        ip_address = get_ip_address(info)

        # Verify CAPTCHA (M001 - Phase 4 requirement)
        is_valid, score, error = captcha_service.verify_token(
            token=input.captcha_token,
            action="register",
            remote_ip=ip_address,
        )

        if not is_valid:
            # Log CAPTCHA failure
            AuditService.log_event(
                action="captcha_failed",
                user=None,
                organisation=None,
                ip_address=ip_address,
                metadata={
                    "action": "register",
                    "score": score,
                    "error": error,
                },
            )
            raise AuthenticationError(
                ErrorCode.CAPTCHA_FAILED,
                error or "CAPTCHA verification failed",
            )

        # Log CAPTCHA score for monitoring
        AuditService.log_event(
            action="captcha_verified",
            user=None,
            organisation=None,
            ip_address=ip_address,
            metadata={
                "action": "register",
                "score": score,
            },
        )

        # Find organisation by slug
        try:
            organisation = Organisation.objects.get(slug=input.organisation_slug)
        except Organisation.DoesNotExist as err:
            raise ValidationError(
                ErrorCode.ORGANISATION_NOT_FOUND,
                f"Organisation with slug '{input.organisation_slug}' not found",
            ) from err

        # Register user (raises ValueError if email exists)
        try:
            with transaction.atomic():  # type: ignore[attr-defined]
                user = AuthService.register_user(
                    email=input.email,
                    password=input.password,
                    first_name=input.first_name,
                    last_name=input.last_name,
                    organisation=organisation,
                )

                # Create email verification token (expires in 24 hours)
                token = TokenHasher.generate_token()
                token_hash = TokenHasher.hash_token(token)
                EmailVerificationToken.objects.create(
                    user=user,
                    token_hash=token_hash,
                    expires_at=tz.now() + timedelta(hours=24),
                )

                # Send verification email
                EmailService.send_verification_email(user, token)

                # Record legal document acceptances if provided (Phase 8b)
                user_agent = get_user_agent(info)
                if input.accepted_document_ids:
                    LegalDocumentService.record_registration_acceptances(
                        user=user,
                        document_ids=input.accepted_document_ids,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            "registration": True,
                            "organisation_slug": input.organisation_slug,
                        },
                    )

                # Create session tokens
                tokens = TokenService.create_tokens(user)

                # Log registration
                AuditService.log_event(
                    action="user_registered",
                    user=user,
                    organisation=organisation,
                    ip_address=ip_address,
                    metadata={
                        "legal_documents_accepted": len(input.accepted_document_ids or []),
                    },
                )

                # Get session count for user (should be 1 for new registration)
                from apps.core.models import SessionToken  # type: ignore[import]

                session_count = SessionToken.objects.filter(
                    user=user, is_revoked=False, expires_at__gt=tz.now()
                ).count()

                return AuthPayload(
                    access_token=tokens["access_token"],
                    refresh_token=tokens["refresh_token"],
                    user=user_to_graphql_type(user),
                    requires_two_factor=False,
                    session_count=session_count,
                    session_limit=5,  # H12 requirement
                    oldest_session_revoked=tokens.get("oldest_session_revoked", False),
                )

        except ValueError as e:
            # Convert to standardised error (H4)
            # TODO (Phase 4): Improve service layer exception handling by creating
            # custom exception types (EmailAlreadyExistsError, InvalidInputError, etc.)
            # in apps/core/services/exceptions.py to avoid string matching.
            # This will allow more precise error handling without parsing error messages.
            if "already registered" in str(e):
                raise ValidationError(ErrorCode.EMAIL_ALREADY_EXISTS, str(e)) from e
            raise ValidationError(ErrorCode.INVALID_INPUT, str(e)) from e

    @strawberry.mutation
    def login(self, info: Info, input: LoginInput) -> AuthPayload:
        """Login with email and password.

        Enforces email verification (C5), implements standardised errors (H4),
        and CAPTCHA protection (M001).

        Args:
            info: GraphQL execution info
            input: Login credentials

        Returns:
            AuthPayload with token and user data

        Raises:
            AuthenticationError: If credentials invalid, email not verified, or CAPTCHA fails
        """
        # Get client IP and device fingerprint
        ip_address = get_ip_address(info)
        user_agent = get_user_agent(info)

        # Verify CAPTCHA (M001 - Phase 4 requirement)
        is_valid, score, error = captcha_service.verify_token(
            token=input.captcha_token,
            action="login",
            remote_ip=ip_address,
        )

        if not is_valid:
            # Log CAPTCHA failure
            AuditService.log_event(
                action="captcha_failed",
                user=None,
                organisation=None,
                ip_address=ip_address,
                metadata={
                    "action": "login",
                    "score": score,
                    "error": error,
                    "email": input.email,
                },
            )
            raise AuthenticationError(
                ErrorCode.CAPTCHA_FAILED,
                error or "CAPTCHA verification failed",
            )

        # Log CAPTCHA score for monitoring
        AuditService.log_event(
            action="captcha_verified",
            user=None,
            organisation=None,
            ip_address=ip_address,
            metadata={
                "action": "login",
                "score": score,
            },
        )

        # Authenticate user
        result = AuthService.login(
            email=input.email,
            password=input.password,
            device_fingerprint=user_agent[:200],  # Truncate user agent
            ip_address=ip_address,
        )

        if not result:
            # Log failed attempt
            AuditService.log_event(
                action="login_failed",
                user=None,
                organisation=None,
                ip_address=ip_address,
                metadata={"email": input.email, "reason": "invalid_credentials"},
            )
            raise AuthenticationError(ErrorCode.INVALID_CREDENTIALS, "Invalid email or password")

        user = result["user"]

        # Enforce email verification (C5 requirement)
        if not user.email_verified:
            AuditService.log_event(
                action="login_blocked_unverified",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
            )
            raise AuthenticationError(
                ErrorCode.EMAIL_NOT_VERIFIED,
                "Please verify your email address before logging in",
            )

        # Check if account is locked
        if not user.is_active:
            raise AuthenticationError(ErrorCode.ACCOUNT_DISABLED, "Your account has been disabled")

        # Check if 2FA is required (Phase 5 implementation)
        from apps.core.services.totp_service import TOTPService  # type: ignore[import]

        has_2fa = TOTPService.has_confirmed_device(user)

        # If user has 2FA enabled but didn't provide a code, require it
        if has_2fa and not input.totp_code:
            return AuthPayload(
                access_token="",  # No token until 2FA verified
                refresh_token="",
                user=user_to_graphql_type(user),
                requires_two_factor=True,
                session_count=None,
                session_limit=5,
                oldest_session_revoked=False,
            )

        # If user provided a 2FA code, verify it
        if has_2fa and input.totp_code:
            # Try TOTP token first
            verified = False

            # Get user's confirmed devices
            devices = list(user.totp_devices.filter(is_confirmed=True))

            # Try each device until one verifies
            for device in devices:
                if TOTPService.verify_token(device, input.totp_code):
                    verified = True
                    break

            # If TOTP failed, try backup code
            if not verified:
                verified = TOTPService.verify_backup_code(user, input.totp_code)  # type: ignore[arg-type]

                if verified:
                    # Log backup code usage
                    AuditService.log_event(
                        action="2fa_backup_code_used",
                        user=user,
                        organisation=user.organisation,
                        ip_address=ip_address,
                    )

            if not verified:
                # Log failed 2FA attempt
                AuditService.log_event(
                    action="2fa_verification_failed",
                    user=user,
                    organisation=user.organisation,
                    ip_address=ip_address,
                )
                raise AuthenticationError(
                    ErrorCode.INVALID_2FA_CODE,
                    "Invalid two-factor authentication code",
                )

        # Log successful login
        AuditService.log_event(
            action="login_success",
            user=user,
            organisation=user.organisation,
            ip_address=ip_address,
        )

        # Get session count for user
        from apps.core.models import SessionToken  # type: ignore[import]

        session_count = SessionToken.objects.filter(
            user=user, is_revoked=False, expires_at__gt=tz.now()
        ).count()

        return AuthPayload(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=user_to_graphql_type(user),
            requires_two_factor=False,
            session_count=session_count,
            session_limit=5,  # H12 requirement
            oldest_session_revoked=result.get("oldest_session_revoked", False),
        )

    @strawberry.mutation
    def logout(self, info: Info) -> bool:
        """Logout and revoke current session.

        Implements proper token revocation (H10 requirement).

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            True if logout successful

        Raises:
            AuthenticationError: If user not authenticated
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        # Get access token from request headers
        token = get_bearer_token(info)

        # Revoke current session token (H10 requirement)
        if token:
            AuthService.logout(user, token)

        # Log logout
        ip_address = get_ip_address(info)
        AuditService.log_event(
            action="logout",
            user=user,
            organisation=user.organisation,
            ip_address=ip_address,
        )

        return True

    @strawberry.mutation
    def refresh_token(self, info: Info, refresh_token: str) -> AuthPayload:
        """Refresh access token using refresh token.

        Implements replay detection (H9) and standardised errors (H4).

        Args:
            info: GraphQL execution info
            refresh_token: Valid refresh token

        Returns:
            AuthPayload with new tokens

        Raises:
            AuthenticationError: If refresh token invalid, expired, or replayed
        """
        user_agent = get_user_agent(info)

        # Get session token to find user
        token_hash = TokenHasher.hash_token(refresh_token)
        try:
            from apps.core.models import SessionToken  # type: ignore[import]

            session = SessionToken.objects.select_related("user").get(refresh_token_hash=token_hash)
            user = session.user
        except SessionToken.DoesNotExist as err:
            raise AuthenticationError(
                ErrorCode.TOKEN_INVALID, "Invalid or expired refresh token"
            ) from err

        # Refresh tokens with replay detection (H9)
        tokens = TokenService.refresh_tokens(
            refresh_token=refresh_token,
            device_fingerprint=user_agent[:200],
        )

        if not tokens:
            raise AuthenticationError(ErrorCode.TOKEN_INVALID, "Invalid or expired refresh token")

        # Get session count for user
        from apps.core.models import SessionToken  # type: ignore[import]

        session_count = SessionToken.objects.filter(
            user=user, is_revoked=False, expires_at__gt=tz.now()
        ).count()

        return AuthPayload(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user=user_to_graphql_type(user),
            requires_two_factor=False,
            session_count=session_count,
            session_limit=5,
            oldest_session_revoked=tokens.get("oldest_session_revoked", False),
        )

    @strawberry.mutation
    def request_password_reset(self, info: Info, input: PasswordResetRequestInput) -> bool:
        """Request password reset email.

        Always returns True to prevent user enumeration (M7).
        Implements dual-layer rate limiting (M008):
        - PRIMARY: 3 requests per hour per email
        - SECONDARY: 10 requests per hour per IP

        Args:
            info: GraphQL execution info
            input: Email to send reset link

        Returns:
            True (always, to prevent user enumeration - M7)

        Raises:
            ValidationError: If IP-based rate limit exceeded (applies to all requests)
        """
        ip_address = get_ip_address(info)

        # SECONDARY rate limit check: Per-IP (applies before checking if user exists)
        # This prevents user enumeration through rate limit differences
        if not PasswordResetService.check_ip_rate_limit(ip_address):
            # Log IP rate limit violation (no user context to avoid enumeration)
            AuditService.log_event(
                action="password_reset_ip_rate_limit_exceeded",
                user=None,
                organisation=None,
                ip_address=ip_address,
                metadata={"email_attempted": input.email},
            )
            raise ValidationError(
                ErrorCode.PASSWORD_RESET_RATE_LIMIT_EXCEEDED,
                "Too many password reset requests. Please try again later.",
            )

        try:
            user = User.objects.get(email=input.email)

            # PRIMARY rate limit check: Per-email (M008)
            # Check BEFORE creating token to avoid database writes on rate limit
            if not PasswordResetService.check_rate_limit(user):
                # Rate limit exceeded - log but STILL return True (prevent enumeration)
                AuditService.log_event(
                    action="password_reset_rate_limit_exceeded",
                    user=user,
                    organisation=user.organisation,
                    ip_address=ip_address,
                )
                # Return True (do not raise error) to prevent user enumeration
                return True

            # Create password reset token (hashed - C3)
            token = PasswordResetService.create_reset_token(user, ip_address)

            # Send reset email
            EmailService.send_password_reset_email(user, token)

            # Log reset request
            AuditService.log_event(
                action="password_reset_requested",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
            )

        except User.DoesNotExist:
            # Return True anyway to prevent user enumeration (M7)
            # Also log the attempt for security monitoring
            AuditService.log_event(
                action="password_reset_nonexistent_user",
                user=None,
                organisation=None,
                ip_address=ip_address,
                metadata={"email_attempted": input.email},
            )

        return True

    @strawberry.mutation
    def reset_password(self, info: Info, input: PasswordResetInput) -> bool:
        """Complete password reset with token.

        Revokes all sessions after reset (H8), uses hash comparison (C3),
        and sends confirmation email (US-003 Phase 3).

        Args:
            info: GraphQL execution info
            input: Reset token and new password

        Returns:
            True if reset successful

        Raises:
            AuthenticationError: If token invalid or expired
            ValidationError: If password weak
        """
        ip_address = get_ip_address(info)

        # Verify reset token (C3 - hash comparison)
        user = PasswordResetService.verify_reset_token(input.token)
        if not user:
            raise AuthenticationError(ErrorCode.TOKEN_INVALID, "Invalid or expired reset token")

        try:
            # Reset password and revoke all sessions (H8)
            PasswordResetService.reset_password(user, input.token, input.new_password)

            # Send confirmation email (US-003 Phase 3 requirement)
            EmailService.send_password_reset_confirmation_email(user)

            # Log password reset
            AuditService.log_event(
                action="password_reset_completed",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
            )

            return True

        except ValueError as e:
            raise ValidationError(ErrorCode.PASSWORD_TOO_WEAK, str(e)) from e

    @strawberry.mutation
    def change_password(self, info: Info, input: PasswordChangeInput) -> bool:
        """Change password for authenticated user.

        Revokes all other sessions (H8) and validates password strength.

        Args:
            info: GraphQL execution info with authenticated user
            input: Current and new password

        Returns:
            True if change successful

        Raises:
            AuthenticationError: If user not authenticated or current password wrong
            ValidationError: If new password weak or in history
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        ip_address = get_ip_address(info)

        # Change password (validates and revokes sessions)
        success = AuthService.change_password(user, input.current_password, input.new_password)

        if not success:
            raise AuthenticationError(
                ErrorCode.INVALID_CREDENTIALS, "Current password is incorrect"
            )

        # Log password change
        AuditService.log_event(
            action="password_changed",
            user=user,
            organisation=user.organisation,
            ip_address=ip_address,
        )

        return True

    @strawberry.mutation
    def verify_email(self, info: Info, token: str) -> bool:
        """Verify email address with token.

        Uses hash comparison for token validation (C3).

        Args:
            info: GraphQL execution info
            token: Email verification token from email

        Returns:
            True if verification successful

        Raises:
            AuthenticationError: If token invalid or expired
        """
        ip_address = get_ip_address(info)

        # Hash token for lookup (C3)
        token_hash = TokenHasher.hash_token(token)

        try:
            verification_token = EmailVerificationToken.objects.select_related("user").get(
                token_hash=token_hash
            )

            # Check if token is valid
            if not verification_token.is_valid():
                raise AuthenticationError(ErrorCode.TOKEN_EXPIRED, "Verification token has expired")

            # Mark email as verified
            user = verification_token.user
            user.email_verified = True
            user.save(update_fields=["email_verified"])

            # Mark token as used
            verification_token.mark_used()

            # Log verification
            AuditService.log_event(
                action="email_verified",
                user=user,
                organisation=user.organisation,
                ip_address=ip_address,
            )

            return True

        except EmailVerificationToken.DoesNotExist as err:
            raise AuthenticationError(
                ErrorCode.TOKEN_INVALID, "Invalid verification token"
            ) from err

    @strawberry.mutation
    def resend_verification_email(self, info: Info) -> bool:
        """Resend email verification for current user.

        Invalidates old tokens before creating new one.

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            True if email sent

        Raises:
            AuthenticationError: If user not authenticated
            ValidationError: If email already verified
        """
        request = get_request(info)
        user = get_authenticated_user(request)

        if not user:
            raise AuthenticationError(ErrorCode.NOT_AUTHENTICATED, "Authentication required")

        if user.email_verified:
            raise ValidationError(ErrorCode.INVALID_INPUT, "Email address is already verified")

        # Invalidate old verification tokens
        EmailVerificationToken.objects.filter(user=user, used=False).update(used=True)

        # Create new verification token (expires in 24 hours)
        token = TokenHasher.generate_token()
        token_hash = TokenHasher.hash_token(token)
        EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=tz.now() + timedelta(hours=24),
        )

        # Send verification email
        EmailService.send_verification_email(user, token)

        return True

    @strawberry.mutation
    def enable_two_factor(self, info: Info, input: EnableTwoFactorInput) -> bool:
        """Enable two-factor authentication (Phase 4).

        Args:
            info: GraphQL execution info with authenticated user
            input: TOTP code to verify setup

        Returns:
            True if 2FA enabled

        Raises:
            PermissionError: If user not authenticated
            ValueError: If TOTP code invalid
        """
        # TODO: Implement 2FA enable (Phase 4)
        raise NotImplementedError("Enable 2FA not implemented yet - Phase 4")

    @strawberry.mutation
    def disable_two_factor(self, info: Info, password: str) -> bool:
        """Disable two-factor authentication (Phase 4).

        Args:
            info: GraphQL execution info with authenticated user
            password: User password to confirm

        Returns:
            True if 2FA disabled

        Raises:
            PermissionError: If user not authenticated
            ValueError: If password invalid
        """
        # TODO: Implement 2FA disable (Phase 4)
        raise NotImplementedError("Disable 2FA not implemented yet - Phase 4")

    @strawberry.mutation
    def generate_two_factor_setup(self, info: Info) -> TwoFactorSetupPayload:
        """Generate 2FA setup data (QR code, secret, backup codes) - Phase 4.

        Args:
            info: GraphQL execution info with authenticated user

        Returns:
            TwoFactorSetupPayload with secret and QR code

        Raises:
            PermissionError: If user not authenticated
        """
        # TODO: Implement 2FA setup generation (Phase 4)
        raise NotImplementedError("Generate 2FA setup not implemented yet - Phase 4")
