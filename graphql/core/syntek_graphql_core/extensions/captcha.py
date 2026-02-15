"""CAPTCHA validation extension for GraphQL operations.

Validates CAPTCHA tokens (reCAPTCHA v2/v3, hCaptcha) for sensitive operations
to prevent automated attacks. Can be applied after rate limit violations or
as a default requirement for high-risk operations.

Features:
- Support for reCAPTCHA v2, v3, and hCaptcha
- Score-based validation for reCAPTCHA v3
- Automatic escalation after rate limit violations
- Configurable per-operation requirements

Configuration:
    RECAPTCHA_SECRET_KEY: reCAPTCHA secret key
    RECAPTCHA_VERSION: Version to use ("v2", "v3", default: "v3")
    RECAPTCHA_V3_MIN_SCORE: Minimum score for v3 (default: 0.5)
    HCAPTCHA_SECRET_KEY: hCaptcha secret key (optional)
    GRAPHQL_CAPTCHA_OPERATIONS: Operations requiring CAPTCHA
"""

import logging
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from strawberry.extensions import SchemaExtension

from syntek_graphql_core.errors import AuthenticationError, ErrorCode

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

logger = logging.getLogger(__name__)


class CaptchaValidationExtension(SchemaExtension):
    """Validate CAPTCHA tokens for protected GraphQL operations.

    Prevents automated attacks by requiring CAPTCHA verification for sensitive
    operations like registration, password reset, and login (after rate limit).

    Supports multiple CAPTCHA providers:
    - Google reCAPTCHA v2 (checkbox)
    - Google reCAPTCHA v3 (score-based, invisible)
    - hCaptcha (privacy-focused alternative)

    Operations requiring CAPTCHA (default):
    - register
    - requestPasswordReset
    - changePassword
    - login (after rate limit violation)

    The extension extracts the CAPTCHA token from operation variables and
    validates it with the configured provider. For reCAPTCHA v3, scores below
    the threshold (default: 0.5) are rejected.

    Configuration:
        RECAPTCHA_SECRET_KEY: Secret key from reCAPTCHA admin console
        RECAPTCHA_VERSION: "v2" or "v3" (default: "v3")
        RECAPTCHA_V3_MIN_SCORE: Minimum score for v3 (0.0-1.0, default: 0.5)
        HCAPTCHA_SECRET_KEY: hCaptcha secret key (optional)
        GRAPHQL_CAPTCHA_REQUIRED: Operations requiring CAPTCHA
        GRAPHQL_CAPTCHA_ENABLED: Enable/disable extension (default: True)

    Attributes:
        recaptcha_secret: reCAPTCHA secret key
        recaptcha_version: reCAPTCHA version ("v2" or "v3")
        min_score: Minimum reCAPTCHA v3 score
        hcaptcha_secret: hCaptcha secret key (optional)
        required_operations: Set of operations requiring CAPTCHA
        enabled: Whether the extension is enabled
    """

    # Default operations requiring CAPTCHA
    DEFAULT_REQUIRED_OPERATIONS = {
        "register",
        "requestPasswordReset",
        "changePassword",
    }

    # reCAPTCHA verification URLs
    RECAPTCHA_V2_URL = "https://www.google.com/recaptcha/api/siteverify"
    RECAPTCHA_V3_URL = "https://www.google.com/recaptcha/api/siteverify"
    HCAPTCHA_URL = "https://hcaptcha.com/siteverify"

    def __init__(self, *, execution_context: "ExecutionContext") -> None:
        """Initialise the extension with CAPTCHA configuration.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

        # Load configuration
        self.recaptcha_secret = getattr(settings, "RECAPTCHA_SECRET_KEY", None)
        self.recaptcha_version = getattr(settings, "RECAPTCHA_VERSION", "v3")
        self.min_score = getattr(settings, "RECAPTCHA_V3_MIN_SCORE", 0.5)
        self.hcaptcha_secret = getattr(settings, "HCAPTCHA_SECRET_KEY", None)
        configured_ops = getattr(settings, "GRAPHQL_CAPTCHA_REQUIRED", None)
        self.required_operations = (
            set(configured_ops) if configured_ops else self.DEFAULT_REQUIRED_OPERATIONS
        )
        self.enabled = getattr(settings, "GRAPHQL_CAPTCHA_ENABLED", True)

    def on_execute(self) -> "Iterator[None]":
        """Execute with CAPTCHA validation.

        Validates CAPTCHA token for required operations.

        Yields:
            None after validation completes.

        Raises:
            AuthenticationError: If CAPTCHA validation fails.
        """
        if not self.enabled:
            yield
            return

        operation_name = self._get_operation_name()

        # Only apply to required operations
        if operation_name not in self.required_operations:
            yield
            return

        # Extract CAPTCHA token from variables
        captcha_token = self._get_captcha_token()

        if not captcha_token:
            logger.warning(
                f"CAPTCHA token missing for {operation_name}",
                extra={"operation": operation_name},
            )

            raise AuthenticationError(
                code=ErrorCode.CAPTCHA_FAILED,
                message="CAPTCHA verification required. Please complete the CAPTCHA challenge.",
                extensions={"operation": operation_name, "reason": "missing_token"},
            )

        # Validate CAPTCHA
        is_valid, error_message = self._validate_captcha(captcha_token, operation_name)

        if not is_valid:
            logger.warning(
                f"CAPTCHA validation failed for {operation_name}: {error_message}",
                extra={
                    "operation": operation_name,
                    "error": error_message,
                },
            )

            raise AuthenticationError(
                code=ErrorCode.CAPTCHA_FAILED,
                message=f"CAPTCHA verification failed: {error_message}",
                extensions={"operation": operation_name, "reason": error_message},
            )

        logger.info(
            f"CAPTCHA validated for {operation_name}",
            extra={"operation": operation_name},
        )

        yield

    def _get_operation_name(self) -> str | None:
        """Extract operation name from GraphQL document.

        Returns:
            Operation name or None if not found.
        """
        document = self.execution_context.graphql_document

        if not document or not hasattr(document, "definitions"):
            return None

        for definition in document.definitions:
            if hasattr(definition, "selection_set") and definition.selection_set:
                for selection in definition.selection_set.selections:
                    if hasattr(selection, "name"):
                        name = selection.name
                        return name.value if hasattr(name, "value") else str(name)

        return None

    def _get_captcha_token(self) -> str | None:
        """Extract CAPTCHA token from operation variables.

        Looks for "captchaToken" or "captcha" in variable values.

        Returns:
            CAPTCHA token or None if not found.
        """
        variables = self.execution_context.variables

        if not variables:
            return None

        # Check common variable names
        return variables.get("captchaToken") or variables.get("captcha")

    def _validate_captcha(self, token: str, operation: str) -> tuple[bool, str]:
        """Validate CAPTCHA token with provider.

        Args:
            token: CAPTCHA token from client.
            operation: Operation name (used for action in reCAPTCHA v3).

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Determine provider
        if self.recaptcha_secret:
            return self._validate_recaptcha(token, operation)
        elif self.hcaptcha_secret:
            return self._validate_hcaptcha(token)
        else:
            logger.error("No CAPTCHA provider configured")
            return False, "CAPTCHA not configured"

    def _validate_recaptcha(self, token: str, operation: str) -> tuple[bool, str]:
        """Validate reCAPTCHA token.

        Args:
            token: reCAPTCHA response token.
            operation: Operation name (used for action in v3).

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            # Send verification request
            response = requests.post(
                self.RECAPTCHA_V3_URL,
                data={"secret": self.recaptcha_secret, "response": token},
                timeout=5,
            )

            response.raise_for_status()
            result = response.json()

            # Check success
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                return False, f"Verification failed: {', '.join(error_codes)}"

            # For v3, check score
            if self.recaptcha_version == "v3":
                score = result.get("score", 0.0)

                if score < self.min_score:
                    return False, f"Score too low: {score} < {self.min_score}"

                # Optionally check action matches
                action = result.get("action")
                if action != operation:
                    logger.warning(
                        f"reCAPTCHA action mismatch: expected {operation}, got {action}"
                    )

            return True, ""

        except requests.RequestException as e:
            logger.error(f"reCAPTCHA validation request failed: {e}")
            return False, "Verification service unavailable"
        except Exception as e:
            logger.error(f"Unexpected error validating reCAPTCHA: {e}")
            return False, "Verification error"

    def _validate_hcaptcha(self, token: str) -> tuple[bool, str]:
        """Validate hCaptcha token.

        Args:
            token: hCaptcha response token.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            # Send verification request
            response = requests.post(
                self.HCAPTCHA_URL,
                data={"secret": self.hcaptcha_secret, "response": token},
                timeout=5,
            )

            response.raise_for_status()
            result = response.json()

            # Check success
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                return False, f"Verification failed: {', '.join(error_codes)}"

            return True, ""

        except requests.RequestException as e:
            logger.error(f"hCaptcha validation request failed: {e}")
            return False, "Verification service unavailable"
        except Exception as e:
            logger.error(f"Unexpected error validating hCaptcha: {e}")
            return False, "Verification error"
