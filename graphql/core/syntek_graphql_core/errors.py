"""Standardised error codes and exceptions for GraphQL API.

This module defines error codes and custom exceptions for consistent
error handling across the GraphQL API (H4 requirement).

Each error includes:
- Unique error code (for client-side handling)
- User-friendly message
- HTTP status code equivalent
- Additional context data

Example:
    >>> raise AuthenticationError("INVALID_CREDENTIALS")
    >>> raise ValidationError("EMAIL_ALREADY_EXISTS", {"email": "test@example.com"})
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Standardised error codes for GraphQL API.

    Error codes follow the pattern: CATEGORY_SPECIFIC_ERROR
    Categories: AUTH, VALIDATION, PERMISSION, NOT_FOUND, RATE_LIMIT, SERVER
    """

    # Authentication errors (AUTH_*)
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TWO_FACTOR_REQUIRED = "TWO_FACTOR_REQUIRED"
    INVALID_TOTP_CODE = "INVALID_TOTP_CODE"
    INVALID_2FA_CODE = "INVALID_2FA_CODE"  # Alias for INVALID_TOTP_CODE
    CAPTCHA_FAILED = "CAPTCHA_FAILED"

    # OAuth/Social authentication errors
    INVALID_OAUTH_STATE = "INVALID_OAUTH_STATE"
    OAUTH_PROVIDER_ERROR = "OAUTH_PROVIDER_ERROR"
    SOCIAL_ACCOUNT_NOT_FOUND = "SOCIAL_ACCOUNT_NOT_FOUND"
    SOCIAL_ACCOUNT_ALREADY_LINKED = "SOCIAL_ACCOUNT_ALREADY_LINKED"
    LAST_AUTH_METHOD = "LAST_AUTH_METHOD"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"

    # Validation errors (VALIDATION_*)
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    INVALID_EMAIL_FORMAT = "INVALID_EMAIL_FORMAT"
    PASSWORD_TOO_WEAK = "PASSWORD_TOO_WEAK"  # pragma: allowlist secret
    PASSWORD_IN_HISTORY = "PASSWORD_IN_HISTORY"  # pragma: allowlist secret
    INVALID_INPUT = "INVALID_INPUT"
    ORGANISATION_NOT_FOUND = "ORGANISATION_NOT_FOUND"

    # Permission errors (PERMISSION_*)
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    NOT_ORGANISATION_OWNER = "NOT_ORGANISATION_OWNER"
    ORGANISATION_MISMATCH = "ORGANISATION_MISMATCH"

    # Not found errors (NOT_FOUND_*)
    USER_NOT_FOUND = "USER_NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Rate limit errors (RATE_LIMIT_*)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    PASSWORD_RESET_RATE_LIMIT_EXCEEDED = "PASSWORD_RESET_RATE_LIMIT_EXCEEDED"  # pragma: allowlist secret

    # Server errors (SERVER_*)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


# Error code to message mapping
ERROR_MESSAGES: dict[ErrorCode, str] = {
    # Authentication
    ErrorCode.INVALID_CREDENTIALS: "Invalid email or password",
    ErrorCode.EMAIL_NOT_VERIFIED: "Please verify your email address before logging in",
    ErrorCode.ACCOUNT_LOCKED: "Account is locked due to too many failed login attempts",
    ErrorCode.ACCOUNT_DISABLED: "Account has been disabled",
    ErrorCode.TOKEN_EXPIRED: "Authentication token has expired",
    ErrorCode.TOKEN_INVALID: "Invalid authentication token",
    ErrorCode.TWO_FACTOR_REQUIRED: "Two-factor authentication code required",
    ErrorCode.INVALID_TOTP_CODE: "Invalid two-factor authentication code",
    ErrorCode.INVALID_2FA_CODE: "Invalid two-factor authentication code",
    ErrorCode.CAPTCHA_FAILED: "CAPTCHA verification failed - please try again",
    # OAuth/Social authentication
    ErrorCode.INVALID_OAUTH_STATE: "Invalid or expired OAuth state token",
    ErrorCode.OAUTH_PROVIDER_ERROR: "OAuth provider returned an error",
    ErrorCode.SOCIAL_ACCOUNT_NOT_FOUND: "Social account not found",
    ErrorCode.SOCIAL_ACCOUNT_ALREADY_LINKED: "Social account already linked to another user",
    ErrorCode.LAST_AUTH_METHOD: "Cannot remove only authentication method",
    ErrorCode.CONSENT_REQUIRED: "User consent required for this operation",
    # Validation
    ErrorCode.EMAIL_ALREADY_EXISTS: "Email address is already registered",
    ErrorCode.INVALID_EMAIL_FORMAT: "Invalid email address format",
    ErrorCode.PASSWORD_TOO_WEAK: "Password does not meet security requirements",  # pragma: allowlist secret
    ErrorCode.PASSWORD_IN_HISTORY: "Cannot reuse a recent password",  # pragma: allowlist secret
    ErrorCode.INVALID_INPUT: "Invalid input data",
    ErrorCode.ORGANISATION_NOT_FOUND: "Organisation not found",
    # Permission
    ErrorCode.PERMISSION_DENIED: "You do not have permission to perform this action",
    ErrorCode.NOT_AUTHENTICATED: "Authentication required",
    ErrorCode.NOT_ORGANISATION_OWNER: "Organisation owner role required",
    ErrorCode.ORGANISATION_MISMATCH: "Cannot access resources from different organisation",
    # Not found
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.RESOURCE_NOT_FOUND: "Requested resource not found",
    # Rate limit
    ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded, please try again later",
    ErrorCode.TOO_MANY_REQUESTS: "Too many requests, please slow down",
    ErrorCode.PASSWORD_RESET_RATE_LIMIT_EXCEEDED: (
        "Too many password reset requests. Please try again in an hour."
    ),
    # Server
    ErrorCode.INTERNAL_ERROR: "An internal error occurred",
    ErrorCode.DATABASE_ERROR: "Database operation failed",
}


class GraphQLError(Exception):
    """Base exception for GraphQL API errors.

    All custom exceptions should inherit from this class.

    Attributes:
        code: Error code from ErrorCode enum
        message: User-friendly error message
        extensions: Additional error context data
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """Initialise GraphQL error.

        Args:
            code: Error code from ErrorCode enum
            message: Optional custom message (uses default if not provided)
            extensions: Optional additional context data
        """
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "An error occurred")
        self.extensions = extensions or {}
        self.extensions["code"] = code.value
        super().__init__(self.message)


class AuthenticationError(GraphQLError):
    """Exception for authentication failures."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        message: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """Initialise authentication error.

        Args:
            code: Error code (default: INVALID_CREDENTIALS)
            message: Optional custom message
            extensions: Optional additional context
        """
        super().__init__(code, message, extensions)


class ValidationError(GraphQLError):
    """Exception for input validation failures."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.INVALID_INPUT,
        message: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """Initialise validation error.

        Args:
            code: Error code (default: INVALID_INPUT)
            message: Optional custom message
            extensions: Optional additional context
        """
        super().__init__(code, message, extensions)


class PermissionError(GraphQLError):
    """Exception for permission/authorisation failures."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.PERMISSION_DENIED,
        message: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """Initialise permission error.

        Args:
            code: Error code (default: PERMISSION_DENIED)
            message: Optional custom message
            extensions: Optional additional context
        """
        super().__init__(code, message, extensions)


class NotFoundError(GraphQLError):
    """Exception for resource not found errors."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        message: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """Initialise not found error.

        Args:
            code: Error code (default: RESOURCE_NOT_FOUND)
            message: Optional custom message
            extensions: Optional additional context
        """
        super().__init__(code, message, extensions)


class RateLimitError(GraphQLError):
    """Exception for rate limit exceeded errors."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED,
        message: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """Initialise rate limit error.

        Args:
            code: Error code (default: RATE_LIMIT_EXCEEDED)
            message: Optional custom message
            extensions: Optional additional context
        """
        super().__init__(code, message, extensions)
