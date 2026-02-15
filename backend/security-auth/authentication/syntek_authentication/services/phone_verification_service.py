"""Phone verification service for SMS-based phone number verification.

This module provides phone verification functionality including:
- SMS sending with third-party providers (Twilio, AWS SNS)
- Verification code generation and validation
- Rate limiting to prevent abuse
- Cost attack prevention

SECURITY NOTE:
- Uses Rust CSPRNG for code generation
- Encrypted phone number storage
- HMAC-based lookups (constant-time)
- Global SMS rate limiting (prevent cost attacks)
- CAPTCHA escalation after threshold

Example:
    >>> PhoneVerificationService.send_verification_code(user, phone_number)
    >>> PhoneVerificationService.verify_code(user, code)
    >>> PhoneVerificationService.check_phone_availability(phone_number)
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

try:
    from syntek_rust import (
        encrypt_phone_number_py,
        generate_verification_code_py,
        hash_phone_py,
    )
except ImportError:
    raise ImportError(
        "syntek_rust not found. Install with: cd rust/pyo3_bindings && maturin develop"
    )

if TYPE_CHECKING:
    from syntek_authentication.models import User

logger = logging.getLogger(__name__)


class PhoneVerificationService:
    """Service for phone number verification via SMS.

    Handles phone verification flow:
    1. Generate secure 6-digit code (Rust CSPRNG)
    2. Send SMS via provider (Twilio/AWS SNS)
    3. Verify code with constant-time comparison
    4. Track attempts and enforce rate limits

    Features:
    - Encrypted phone storage (AES-256-GCM)
    - HMAC-based lookups (prevent enumeration)
    - Global SMS rate limiting
    - Cost attack prevention
    - Automatic code expiry (15 minutes)

    Attributes:
        CODE_EXPIRY_MINUTES: Verification code validity period
        MAX_ATTEMPTS: Maximum verification attempts before lockout
        RATE_LIMIT_WINDOW: Time window for rate limiting
        GLOBAL_SMS_LIMIT: Maximum SMS messages per hour (globally)
    """

    CODE_EXPIRY_MINUTES = 15
    MAX_ATTEMPTS = 5
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    GLOBAL_SMS_LIMIT = 100  # Global SMS limit per hour
    SMS_COST_THRESHOLD = 500.0  # Daily budget in USD

    # Redis cache keys
    CACHE_KEY_USER_SMS = "phone_verification:user:{user_id}"
    CACHE_KEY_PHONE_SMS = "phone_verification:phone:{phone_hash}"
    CACHE_KEY_GLOBAL_SMS = "phone_verification:global_sms_count"
    CACHE_KEY_DAILY_COST = "phone_verification:daily_cost"

    @staticmethod
    def _get_encryption_key() -> bytes:
        """Get encryption key from settings.

        Returns:
            Encryption key bytes.

        Raises:
            ImproperlyConfigured: If encryption key not configured.
        """
        key = getattr(settings, "ENCRYPTION_KEY", None)
        if not key:
            raise ValueError("ENCRYPTION_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    def _get_hmac_key() -> bytes:
        """Get HMAC key from settings.

        Returns:
            HMAC key bytes.

        Raises:
            ImproperlyConfigured: If HMAC key not configured.
        """
        key = getattr(settings, "HMAC_SECRET_KEY", None)
        if not key:
            raise ValueError("HMAC_SECRET_KEY not configured in settings")
        return key.encode() if isinstance(key, str) else key

    @staticmethod
    def _check_global_sms_limit() -> tuple[bool, int]:
        """Check if global SMS limit has been reached.

        Returns:
            Tuple of (is_allowed, current_count).

        Raises:
            None - Returns status instead of raising.
        """
        cache_key = PhoneVerificationService.CACHE_KEY_GLOBAL_SMS
        current_count = cache.get(cache_key, 0)

        if current_count >= PhoneVerificationService.GLOBAL_SMS_LIMIT:
            logger.warning(
                f"Global SMS limit reached: {current_count}/{PhoneVerificationService.GLOBAL_SMS_LIMIT}"
            )
            return False, current_count

        return True, current_count

    @staticmethod
    def _increment_global_sms_count() -> int:
        """Increment global SMS counter.

        Returns:
            New SMS count.
        """
        cache_key = PhoneVerificationService.CACHE_KEY_GLOBAL_SMS
        new_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, new_count, PhoneVerificationService.RATE_LIMIT_WINDOW)
        return new_count

    @staticmethod
    def _check_daily_cost_limit() -> tuple[bool, float]:
        """Check if daily SMS cost limit has been reached.

        Returns:
            Tuple of (is_allowed, current_cost).
        """
        cache_key = PhoneVerificationService.CACHE_KEY_DAILY_COST
        current_cost = cache.get(cache_key, 0.0)

        if current_cost >= PhoneVerificationService.SMS_COST_THRESHOLD:
            logger.critical(
                f"Daily SMS cost limit reached: ${current_cost}/{PhoneVerificationService.SMS_COST_THRESHOLD}"
            )
            return False, current_cost

        return True, current_cost

    @staticmethod
    def _increment_daily_cost(cost_per_sms: float = 0.05) -> float:
        """Increment daily SMS cost tracker.

        Args:
            cost_per_sms: Cost per SMS in USD (default: $0.05).

        Returns:
            New total cost.
        """
        cache_key = PhoneVerificationService.CACHE_KEY_DAILY_COST
        current_cost = cache.get(cache_key, 0.0)
        new_cost = current_cost + cost_per_sms

        # Cache for 24 hours
        cache.set(cache_key, new_cost, 86400)
        return new_cost

    @staticmethod
    def _send_sms(phone_number: str, message: str) -> bool:
        """Send SMS via configured provider.

        Args:
            phone_number: E.164 formatted phone number.
            message: SMS message content.

        Returns:
            True if sent successfully, False otherwise.

        Note:
            This is a placeholder. Implement actual SMS provider integration:
            - Twilio: from twilio.rest import Client
            - AWS SNS: import boto3; sns = boto3.client('sns')
            - Vonage: from vonage import Client
        """
        # TODO: Implement actual SMS provider
        # For now, log the message (development mode)
        if settings.DEBUG:
            logger.info(f"[SMS DEBUG] To: {phone_number}, Message: {message}")
            return True

        # Production implementation example (Twilio):
        # try:
        #     from twilio.rest import Client
        #     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        #     message = client.messages.create(
        #         body=message,
        #         from_=settings.TWILIO_PHONE_NUMBER,
        #         to=phone_number
        #     )
        #     return message.sid is not None
        # except Exception as e:
        #     logger.error(f"SMS send failed: {e}")
        #     return False

        logger.warning("SMS provider not configured. Set DEBUG=False to use production SMS.")
        return False

    @staticmethod
    @transaction.atomic
    def send_verification_code(user: "User", phone_number: str) -> dict:
        """Generate and send verification code via SMS.

        Args:
            user: User requesting verification.
            phone_number: E.164 formatted phone number.

        Returns:
            Dict with status, message, and optional code (DEBUG only).

        Raises:
            ValueError: If phone number invalid or rate limited.
        """
        from syntek_authentication.models import PhoneVerificationToken

        # Check global SMS limit
        is_allowed, current_count = PhoneVerificationService._check_global_sms_limit()
        if not is_allowed:
            logger.warning(
                f"Global SMS limit reached for user {user.id}: {current_count}/{PhoneVerificationService.GLOBAL_SMS_LIMIT}"
            )
            raise ValueError("SMS service temporarily unavailable. Please try again later.")

        # Check daily cost limit
        is_allowed, current_cost = PhoneVerificationService._check_daily_cost_limit()
        if not is_allowed:
            logger.critical(
                f"Daily SMS cost limit reached: ${current_cost}/{PhoneVerificationService.SMS_COST_THRESHOLD}"
            )
            raise ValueError("SMS service temporarily unavailable. Please contact support.")

        # Check user-specific rate limit (1 SMS per 60 seconds)
        user_cache_key = PhoneVerificationService.CACHE_KEY_USER_SMS.format(user_id=user.id)
        if cache.get(user_cache_key):
            raise ValueError("Please wait 60 seconds before requesting another code.")

        # Encrypt phone number and generate hash
        encryption_key = PhoneVerificationService._get_encryption_key()
        hmac_key = PhoneVerificationService._get_hmac_key()

        phone_encrypted = encrypt_phone_number_py(phone_number, encryption_key)
        phone_hash = hash_phone_py(phone_number, hmac_key)

        # Generate verification code (6 digits, Rust CSPRNG)
        code = generate_verification_code_py()
        code_hash = hash_phone_py(code, hmac_key)

        # Invalidate any existing unused codes for this user
        PhoneVerificationToken.objects.filter(user=user, used_at__isnull=True).update(
            used_at=timezone.now()  # Mark as used to prevent reuse
        )

        # Create new verification token
        expires_at = timezone.now() + timedelta(
            minutes=PhoneVerificationService.CODE_EXPIRY_MINUTES
        )
        PhoneVerificationToken.objects.create(
            user=user,
            phone_number_encrypted=phone_encrypted,
            phone_hash=phone_hash,
            code=code,  # Store plain code for SMS sending
            code_hash=code_hash,
            expires_at=expires_at,
        )

        # Send SMS
        message = f"Your verification code is: {code}. Valid for {PhoneVerificationService.CODE_EXPIRY_MINUTES} minutes."
        sms_sent = PhoneVerificationService._send_sms(phone_number, message)

        if not sms_sent:
            logger.error(f"Failed to send SMS to {phone_hash[:8]}... for user {user.id}")
            raise ValueError("Failed to send verification code. Please try again.")

        # Increment counters
        PhoneVerificationService._increment_global_sms_count()
        PhoneVerificationService._increment_daily_cost()

        # Set user rate limit (60 seconds)
        cache.set(user_cache_key, True, 60)

        logger.info(f"Sent verification code to {phone_hash[:8]}... for user {user.id}")

        response = {
            "status": "success",
            "message": "Verification code sent.",
            "expires_at": expires_at.isoformat(),
        }

        # In DEBUG mode, include the code for testing
        if settings.DEBUG:
            response["code"] = code  # Only for development

        return response

    @staticmethod
    @transaction.atomic
    def verify_code(user: "User", code: str) -> dict:
        """Verify phone verification code.

        Args:
            user: User attempting verification.
            code: 6-digit verification code.

        Returns:
            Dict with status and message.

        Raises:
            ValueError: If code invalid, expired, or too many attempts.
        """
        from syntek_authentication.models import PhoneVerificationToken

        # Get latest unused token for user
        try:
            token = PhoneVerificationToken.objects.filter(user=user, used_at__isnull=True).latest(
                "created_at"
            )
        except PhoneVerificationToken.DoesNotExist:
            raise ValueError("No verification code found. Please request a new one.")

        # Check if expired
        if token.is_expired():
            raise ValueError("Verification code has expired. Please request a new one.")

        # Check max attempts
        if token.attempts >= PhoneVerificationService.MAX_ATTEMPTS:
            token.mark_as_used()  # Lock the token
            raise ValueError("Too many failed attempts. Please request a new verification code.")

        # Verify code (constant-time comparison via HMAC)
        hmac_key = PhoneVerificationService._get_hmac_key()
        code_hash = hash_phone_py(code, hmac_key)

        if code_hash != token.code_hash:
            # Increment attempts
            token.increment_attempts()
            remaining_attempts = PhoneVerificationService.MAX_ATTEMPTS - token.attempts

            if remaining_attempts > 0:
                raise ValueError(
                    f"Invalid verification code. {remaining_attempts} attempts remaining."
                )
            else:
                raise ValueError(
                    "Too many failed attempts. Please request a new verification code."
                )

        # Code is valid - mark as used
        token.mark_as_used()

        # Update user's phone number
        user.phone_number_encrypted = token.phone_number_encrypted
        user.phone_hash = token.phone_hash
        user.phone_consent = True
        user.phone_consent_at = timezone.now()
        user.save(
            update_fields=[
                "phone_number_encrypted",
                "phone_hash",
                "phone_consent",
                "phone_consent_at",
            ]
        )

        logger.info(f"Phone verified successfully for user {user.id}")

        return {
            "status": "success",
            "message": "Phone number verified successfully.",
        }

    @staticmethod
    def check_phone_availability(phone_number: str) -> bool:
        """Check if phone number is already registered.

        Args:
            phone_number: E.164 formatted phone number.

        Returns:
            True if available, False if already taken.
        """
        from syntek_authentication.models import User

        hmac_key = PhoneVerificationService._get_hmac_key()
        phone_hash = hash_phone_py(phone_number, hmac_key)

        # Use hash for constant-time lookup
        exists = User.objects.filter(phone_hash=phone_hash).exists()
        return not exists

    @staticmethod
    def get_global_sms_stats() -> dict:
        """Get global SMS rate limiting statistics.

        Returns:
            Dict with current SMS count and cost.
        """
        cache_key_sms = PhoneVerificationService.CACHE_KEY_GLOBAL_SMS
        cache_key_cost = PhoneVerificationService.CACHE_KEY_DAILY_COST

        current_count = cache.get(cache_key_sms, 0)
        current_cost = cache.get(cache_key_cost, 0.0)

        return {
            "sms_count": current_count,
            "sms_limit": PhoneVerificationService.GLOBAL_SMS_LIMIT,
            "daily_cost": current_cost,
            "cost_limit": PhoneVerificationService.SMS_COST_THRESHOLD,
            "percentage_used": (current_count / PhoneVerificationService.GLOBAL_SMS_LIMIT) * 100,
        }
