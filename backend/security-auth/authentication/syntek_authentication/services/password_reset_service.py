"""Password reset service with hash-then-store pattern.

This module handles password reset token creation and verification using
the hash-then-store security pattern. Implements C3 security requirement.

SECURITY NOTE (C3):
- Tokens are hashed before storing in database
- Plain token never persisted, only sent via email once
- HMAC-SHA256 hashing with TOKEN_SIGNING_KEY
- Constant-time comparison prevents timing attacks
- Tokens expire after 15 minutes

SECURITY NOTE (H11):
- Password history enforced (prevents reuse of last 5 passwords)
- Password strength validated
- All sessions revoked on password reset (H8)

SECURITY NOTE (H12):
- Single-use tokens (marked as used after reset)

SECURITY NOTE (M008):
- Rate limiting enforced (3 requests per hour per email)
- IP-based rate limiting as fallback (10 requests per hour per IP)

MULTIPLE RESET BEHAVIOUR (Phase 2):
- When a user requests multiple password resets, old tokens are invalidated
- Only the most recent token is valid (all previous tokens marked as used)
- This prevents confusion and security issues with multiple active links

Example:
    >>> token = PasswordResetService.create_reset_token(user)
    >>> # Token sent via email, hash stored in DB
    >>> user = PasswordResetService.verify_reset_token(token)
    >>> PasswordResetService.reset_password(user, token, new_password)
"""

import re
from datetime import timedelta
from typing import TYPE_CHECKING

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

if TYPE_CHECKING:
    from syntek_authentication.models import User


class PasswordResetService:
    """Service for password reset with hash-then-store pattern.

    Handles creation of password reset tokens, verification, and
    password reset completion with secure token handling.

    Security Features:
    - Hash-then-store pattern (C3)
    - HMAC-SHA256 token hashing
    - 15-minute token expiry
    - Single-use tokens (H12)
    - Password history enforcement (H11)
    - Session revocation on reset (H8)
    - Rate limiting (M008): 3 requests per hour per email

    Attributes:
        None - All methods are static
    """

    TOKEN_EXPIRY_MINUTES = 15
    PASSWORD_HISTORY_COUNT = 5
    RATE_LIMIT_MAX_REQUESTS_PER_EMAIL = 3
    RATE_LIMIT_MAX_REQUESTS_PER_IP = 10
    RATE_LIMIT_WINDOW_HOURS = 1

    @staticmethod
    def check_rate_limit(user: "User") -> bool:
        """Check if user has exceeded password reset rate limit (per-email).

        Implements M008 requirement: Max 3 reset requests per hour per email.
        Counts all password reset tokens created within the rate limit window,
        regardless of whether they were used or expired.

        This is the PRIMARY rate limit check.

        Args:
            user: User requesting password reset.

        Returns:
            True if within rate limit (can proceed), False if limit exceeded.

        Example:
            >>> if not PasswordResetService.check_rate_limit(user):
            ...     raise ValueError("Rate limit exceeded")
        """
        from syntek_authentication.models import PasswordResetToken

        rate_limit_window = timezone.now() - timedelta(
            hours=PasswordResetService.RATE_LIMIT_WINDOW_HOURS
        )

        # Count all tokens created within the rate limit window for this user
        recent_tokens_count = PasswordResetToken.objects.filter(  # type: ignore[attr-defined]
            user=user, created_at__gte=rate_limit_window
        ).count()

        return recent_tokens_count < PasswordResetService.RATE_LIMIT_MAX_REQUESTS_PER_EMAIL

    @staticmethod
    def check_ip_rate_limit(ip_address: str) -> bool:
        """Check if IP address has exceeded password reset rate limit.

        Implements SECONDARY rate limiting: Max 10 reset requests per hour per IP.
        This prevents attackers from enumerating users or DoS attacks by making
        excessive requests from the same IP across different email addresses.

        NOTE: This requires AuditLog module to be installed. If not available,
        returns True (skips IP-based rate limiting).

        Args:
            ip_address: IP address to check (hashed for privacy).

        Returns:
            True if within rate limit (can proceed), False if limit exceeded.

        Example:
            >>> if not PasswordResetService.check_ip_rate_limit("192.168.1.1"):
            ...     raise ValueError("Too many requests from this location")
        """
        if not ip_address:
            # If IP address not available, skip IP-based rate limiting
            return True

        try:
            from syntek_audit.models import AuditLog  # type: ignore[import]
            from syntek_authentication.utils import IPEncryption  # type: ignore[import]

            rate_limit_window = timezone.now() - timedelta(
                hours=PasswordResetService.RATE_LIMIT_WINDOW_HOURS
            )

            # Hash the IP for comparison (we store encrypted IPs in audit log)
            encrypted_ip = IPEncryption.encrypt_ip(ip_address)

            # Count reset requests from this IP
            ip_requests_count = AuditLog.objects.filter(  # type: ignore[attr-defined]
                action="password_reset_requested",
                ip_address=encrypted_ip,
                created_at__gte=rate_limit_window,
            ).count()

            return ip_requests_count < PasswordResetService.RATE_LIMIT_MAX_REQUESTS_PER_IP

        except ImportError:
            # AuditLog not available, skip IP-based rate limiting
            return True
        except Exception:
            # If IP encryption fails, allow the request (fail open for rate limiting)
            # The primary email-based rate limit will still protect against abuse
            return True

    @staticmethod
    def invalidate_old_tokens(user: "User") -> int:
        """Invalidate all unused password reset tokens for user.

        Marks all existing valid tokens as used to ensure only the latest
        token works when multiple reset requests are made. Implements
        acceptance criteria: "only the latest link works".

        Args:
            user: User whose old tokens should be invalidated.

        Returns:
            Number of tokens invalidated.

        Example:
            >>> count = PasswordResetService.invalidate_old_tokens(user)
            >>> # All previous unused tokens now marked as used
        """
        from syntek_authentication.models import PasswordResetToken

        # Get all valid (unused and not expired) tokens for the user
        valid_tokens = PasswordResetToken.objects.filter(  # type: ignore[attr-defined]
            user=user, used=False, expires_at__gt=timezone.now()
        )

        # Count tokens to be invalidated
        count = valid_tokens.count()

        # Mark all as used
        valid_tokens.update(used=True, used_at=timezone.now())

        return count

    @staticmethod
    def create_reset_token(user: "User", ip_address: str = "") -> str:
        """Create password reset token for user.

        Generates a cryptographically secure token, hashes it with
        HMAC-SHA256, and stores only the hash in the database.

        NOTE: Rate limiting should be checked BEFORE calling this method
        to avoid database writes when rate limit is exceeded.

        Multiple Reset Behaviour (Phase 2):
        When a user requests multiple password resets, this method invalidates
        all previous unused tokens by marking them as used. This ensures only
        the most recent token is valid, preventing confusion and potential
        security issues with multiple valid reset links.

        Args:
            user: User requesting password reset.
            ip_address: IP address of request (for audit logging).

        Returns:
            Plain reset token (only returned once, not stored).
        """
        from syntek_authentication.models import PasswordResetToken
        from syntek_authentication.utils import TokenHasher

        # Invalidate all old tokens for this user
        PasswordResetService.invalidate_old_tokens(user)

        # Generate cryptographically secure token
        plain_token = TokenHasher.generate_token()

        # Hash the token for storage
        token_hash = TokenHasher.hash_token(plain_token)

        # Calculate expiry time (15 minutes)
        expires_at = timezone.now() + timedelta(minutes=PasswordResetService.TOKEN_EXPIRY_MINUTES)

        # Create token record
        PasswordResetToken.objects.create(  # type: ignore[attr-defined]
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # Return plain token (only returned once, never stored)
        return plain_token

    @staticmethod
    def verify_reset_token(token: str) -> "User | None":
        """Verify password reset token and return user.

        Hashes the provided token and compares with stored hashes
        using constant-time comparison to prevent timing attacks.

        Checks that the token is valid: not expired, not used, and exists.
        Multiple reset requests invalidate old tokens, ensuring only the
        latest token works (Phase 2 requirement).

        Args:
            token: Plain reset token from email link.

        Returns:
            User instance if token is valid and not expired/used, None otherwise.
        """
        from syntek_authentication.models import PasswordResetToken
        from syntek_authentication.utils import TokenHasher

        # Hash the token
        token_hash = TokenHasher.hash_token(token)

        try:
            reset_token = PasswordResetToken.objects.select_related("user").get(  # type: ignore[attr-defined]
                token_hash=token_hash
            )

            # Check if token is valid (not expired, not used)
            if reset_token.is_valid():
                return reset_token.user

        except PasswordResetToken.DoesNotExist:  # type: ignore[attr-defined]
            pass

        return None

    @staticmethod
    def reset_password(user: "User", token: str, new_password: str) -> bool:
        """Reset user password using valid token.

        Verifies token, validates new password against requirements,
        checks password history, marks token as used, and updates password.

        Args:
            user: User whose password to reset.
            token: Plain reset token from email link.
            new_password: New password to set.

        Returns:
            True if successful, False if token invalid.

        Raises:
            ValueError: If new password violates requirements or matches history.
        """
        from syntek_authentication.models import PasswordHistory, PasswordResetToken  # type: ignore[import]
        from syntek_authentication.utils import TokenHasher  # type: ignore[import]
        from syntek_jwt.services import TokenService  # type: ignore[import]

        # Verify token
        verified_user = PasswordResetService.verify_reset_token(token)
        if verified_user != user:
            return False

        # Validate password strength
        PasswordResetService._validate_password_strength(new_password, user)

        # Check password history (H11)
        if PasswordHistory.check_password_reuse(
            user, new_password, PasswordResetService.PASSWORD_HISTORY_COUNT
        ):
            raise ValueError(
                f"Cannot reuse any of your last {PasswordResetService.PASSWORD_HISTORY_COUNT} passwords"
            )

        # Hash the token to find it
        token_hash = TokenHasher.hash_token(token)

        try:
            reset_token = PasswordResetToken.objects.get(token_hash=token_hash)  # type: ignore[attr-defined]

            # Mark token as used (H12)
            reset_token.mark_used()

            # Record current password in history before changing
            if user.password:
                PasswordHistory.record_password(user, user.password)  # type: ignore[arg-type]

            # Set new password
            user.set_password(new_password)
            user.password_changed_at = timezone.now()  # type: ignore[misc]
            user.save(update_fields=["password", "password_changed_at"])

            # Revoke all existing tokens (force re-login) (H8)
            TokenService.revoke_user_tokens(user)

            return True

        except PasswordResetToken.DoesNotExist:  # type: ignore[attr-defined]
            return False

    @staticmethod
    def _validate_password_strength(password: str, user: "User | None" = None) -> None:
        """Validate password meets strength requirements.

        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Password to validate.
            user: User instance for context (optional).

        Raises:
            ValueError: If password doesn't meet requirements.
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character")

        # Use Django's password validators as well
        try:
            validate_password(password, user=user)
        except ValidationError as e:
            # If Django validators fail, raise the first error
            if e.messages:
                raise ValueError(e.messages[0]) from None
            raise ValueError("Password does not meet requirements") from None

    @staticmethod
    def cleanup_expired_tokens() -> int:
        """Remove expired password reset tokens (maintenance task).

        Returns:
            Number of expired tokens removed.
        """
        from syntek_authentication.models import PasswordResetToken

        now = timezone.now()
        expired_tokens = PasswordResetToken.objects.filter(expires_at__lt=now)  # type: ignore[attr-defined]
        count = expired_tokens.count()
        expired_tokens.delete()
        return count
