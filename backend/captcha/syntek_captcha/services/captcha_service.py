"""reCAPTCHA v3 verification service.

This module provides Google reCAPTCHA v3 integration with score-based verification,
action-specific thresholds, and fail-open behavior for service unavailability.
"""

import logging

import requests  # type: ignore[import]
from django.conf import settings

logger = logging.getLogger(__name__)


class CaptchaService:
    """Service for verifying reCAPTCHA v3 tokens.

    Provides score-based verification (0.0-1.0) with action-specific thresholds
    and graceful degradation when the reCAPTCHA service is unavailable.

    Example:
        >>> is_valid, score, error = CaptchaService.verify_token(
        ...     token='token-from-frontend',
        ...     action='register'
        ... )
        >>> if not is_valid:
        ...     return JsonResponse({'error': f'CAPTCHA failed: {error}'})
    """

    RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
    TIMEOUT = 5  # seconds

    @classmethod
    def get_config(cls) -> dict:
        """Get CAPTCHA configuration from Django settings.

        Returns:
            dict: CAPTCHA configuration dictionary with keys:
                - SECRET_KEY: reCAPTCHA secret key
                - SITE_KEY: reCAPTCHA site key (public)
                - ENABLED: Whether verification is enabled
                - FAIL_OPEN: Allow users through if service is down
                - THRESHOLDS: Action-specific score thresholds
        """
        return getattr(
            settings,
            "SYNTEK_CAPTCHA",
            {
                "SECRET_KEY": "",
                "SITE_KEY": "",
                "ENABLED": True,
                "FAIL_OPEN": True,
                "THRESHOLDS": {
                    "register": 0.5,
                    "login": 0.3,
                    "password_reset": 0.5,
                    "contact": 0.5,
                    "default": 0.5,
                },
            },
        )

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if CAPTCHA verification is enabled.

        Returns:
            bool: True if CAPTCHA is enabled in settings
        """
        config = cls.get_config()
        return config.get("ENABLED", True)

    @classmethod
    def get_threshold(cls, action: str) -> float:
        """Get score threshold for a specific action.

        Args:
            action: Action name (e.g., 'register', 'login', 'password_reset')

        Returns:
            float: Score threshold (0.0-1.0). Scores below this are rejected.
        """
        config = cls.get_config()
        thresholds = config.get("THRESHOLDS", {})
        return thresholds.get(action, thresholds.get("default", 0.5))

    @classmethod
    def verify_token(
        cls, token: str, action: str, remote_ip: str | None = None
    ) -> tuple[bool, float | None, str | None]:
        """Verify a reCAPTCHA token from the frontend.

        Args:
            token: reCAPTCHA response token from frontend
            action: Action name for threshold lookup
            remote_ip: Optional client IP address for additional verification

        Returns:
            Tuple of (is_valid, score, error_message):
                - is_valid (bool): True if token passed verification
                - score (float|None): reCAPTCHA score (0.0-1.0), or None on error
                - error_message (str|None): Error description if verification failed

        Examples:
            >>> # Successful verification
            >>> is_valid, score, error = CaptchaService.verify_token(
            ...     token='valid-token',
            ...     action='register'
            ... )
            >>> assert is_valid is True
            >>> assert 0.0 <= score <= 1.0
            >>> assert error is None

            >>> # Failed verification (low score)
            >>> is_valid, score, error = CaptchaService.verify_token(
            ...     token='bot-token',
            ...     action='register'
            ... )
            >>> assert is_valid is False
            >>> assert error == 'Score 0.1 below threshold 0.5'

            >>> # Service unavailable (fail-open mode)
            >>> is_valid, score, error = CaptchaService.verify_token(
            ...     token='any-token',
            ...     action='register'
            ... )
            >>> assert is_valid is True  # Allows user through
            >>> assert error == 'Service unavailable (fail-open)'
        """
        # Check if CAPTCHA is enabled
        if not cls.is_enabled():
            logger.info("CAPTCHA verification is disabled")
            return True, None, "CAPTCHA disabled"

        config = cls.get_config()
        secret_key = config.get("SECRET_KEY", "")
        fail_open = config.get("FAIL_OPEN", True)

        # Validate secret key exists
        if not secret_key:
            logger.error("CAPTCHA SECRET_KEY not configured")
            if fail_open:
                return True, None, "Configuration error (fail-open)"
            return False, None, "CAPTCHA not configured"

        # Validate token exists
        if not token:
            logger.warning("Empty CAPTCHA token received")
            return False, None, "No CAPTCHA token provided"

        # Build verification request
        payload = {
            "secret": secret_key,
            "response": token,
        }

        if remote_ip:
            payload["remoteip"] = remote_ip

        try:
            # Call reCAPTCHA verification API
            response = requests.post(cls.RECAPTCHA_VERIFY_URL, data=payload, timeout=cls.TIMEOUT)
            response.raise_for_status()
            result = response.json()

        except requests.exceptions.Timeout:
            logger.error("CAPTCHA verification timeout")
            if fail_open:
                return True, None, "Service timeout (fail-open)"
            return False, None, "CAPTCHA service timeout"

        except requests.exceptions.RequestException as e:
            logger.error(f"CAPTCHA verification request failed: {e}")
            if fail_open:
                return True, None, "Service unavailable (fail-open)"
            return False, None, "CAPTCHA service unavailable"

        except ValueError as e:
            logger.error(f"CAPTCHA verification response parsing failed: {e}")
            if fail_open:
                return True, None, "Invalid response (fail-open)"
            return False, None, "CAPTCHA service error"

        # Check if verification succeeded
        success = result.get("success", False)
        if not success:
            error_codes = result.get("error-codes", [])
            logger.warning(f"CAPTCHA verification failed: {error_codes}")

            # Configuration errors should not fail-open
            if "invalid-input-secret" in error_codes or "missing-input-secret" in error_codes:
                return False, None, "Invalid CAPTCHA configuration"

            # Other errors can fail-open
            if fail_open:
                return True, None, f"Verification failed (fail-open): {error_codes}"
            return False, None, f"Verification failed: {error_codes}"

        # Get score and validate against threshold
        score = result.get("score", 0.0)
        threshold = cls.get_threshold(action)

        # Verify action matches (optional but recommended)
        result_action = result.get("action", "")
        if result_action != action:
            logger.warning(f"CAPTCHA action mismatch: expected '{action}', got '{result_action}'")

        # Check score against threshold
        if score < threshold:
            logger.warning(
                f"CAPTCHA score {score} below threshold {threshold} for action '{action}'"
            )
            return False, score, f"Score {score} below threshold {threshold}"

        # Success
        logger.info(f"CAPTCHA verification successful: score={score}, action={action}")
        return True, score, None

    @classmethod
    def get_site_key(cls) -> str:
        """Get the public reCAPTCHA site key for frontend use.

        Returns:
            str: reCAPTCHA site key (safe to expose in frontend)
        """
        config = cls.get_config()
        return config.get("SITE_KEY", "")
