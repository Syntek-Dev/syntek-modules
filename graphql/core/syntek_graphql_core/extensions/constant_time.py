"""Constant-time response extension to prevent timing attacks.

Ensures authentication-related operations take a fixed amount of time regardless
of success or failure, preventing timing-based attacks that could leak information
about valid usernames, passwords, or other sensitive data.

Features:
- Fixed response time for auth operations
- Configurable minimum duration
- Timing anomaly detection and logging
- Applies to sensitive operations only

Configuration:
    GRAPHQL_CONSTANT_TIME_DURATION: Minimum response time in seconds (default: 0.2)
    GRAPHQL_CONSTANT_TIME_OPERATIONS: List of operations to protect (default: auth ops)
"""

import logging
import time
from typing import TYPE_CHECKING

from django.conf import settings
from strawberry.extensions import SchemaExtension

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

logger = logging.getLogger(__name__)


class ConstantTimeResponseExtension(SchemaExtension):
    """Enforce constant-time responses for authentication operations.

    Timing attacks can reveal information by measuring response times. For example,
    a failed login that immediately returns "invalid email" is faster than one that
    checks a valid email but has wrong password. This extension ensures all
    authentication operations take a minimum fixed duration.

    Protected operations (default):
    - login
    - verifyEmail
    - verifyPhone
    - totpVerify
    - verifyTOTPSetup
    - resetPassword
    - changePassword
    - loginWithRecoveryKey

    The extension measures execution time and sleeps for the remaining duration
    to reach the configured minimum time. Unusually fast or slow responses are
    logged for security analysis.

    Configuration:
        GRAPHQL_CONSTANT_TIME_DURATION: Minimum response time in seconds (default: 0.2)
        GRAPHQL_CONSTANT_TIME_OPERATIONS: List of operations to protect
        GRAPHQL_CONSTANT_TIME_ENABLED: Enable/disable extension (default: True)

    Attributes:
        target_duration: Minimum response time in seconds
        protected_operations: Set of operation names to protect
        enabled: Whether the extension is enabled
    """

    # Default operations to protect with constant-time responses
    DEFAULT_PROTECTED_OPERATIONS = {
        "login",
        "verifyEmail",
        "verifyPhone",
        "totpVerify",
        "verifyTOTPSetup",
        "resetPassword",
        "changePassword",
        "loginWithRecoveryKey",
        "register",  # Prevent username enumeration
        "requestPasswordReset",  # Prevent email enumeration
    }

    def __init__(self, *, execution_context: "ExecutionContext") -> None:
        """Initialise the extension with constant-time configuration.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

        # Load configuration
        self.target_duration = getattr(settings, "GRAPHQL_CONSTANT_TIME_DURATION", 0.2)
        configured_ops = getattr(settings, "GRAPHQL_CONSTANT_TIME_OPERATIONS", None)
        self.protected_operations = (
            set(configured_ops) if configured_ops else self.DEFAULT_PROTECTED_OPERATIONS
        )
        self.enabled = getattr(settings, "GRAPHQL_CONSTANT_TIME_ENABLED", True)

        # Track start time
        self.start_time = None

    def on_execute(self) -> "Iterator[None]":
        """Execute with constant-time guarantee.

        Measures execution time and adds delay to reach target duration.

        Yields:
            None after execution completes.
        """
        if not self.enabled:
            yield
            return

        operation_name = self._get_operation_name()

        # Only apply to protected operations
        if operation_name not in self.protected_operations:
            yield
            return

        # Record start time
        self.start_time = time.perf_counter()

        # Execute the operation
        yield

        # Calculate elapsed time
        elapsed = time.perf_counter() - self.start_time

        # Calculate sleep duration
        sleep_duration = max(0, self.target_duration - elapsed)

        # Log timing anomalies
        if elapsed < (self.target_duration * 0.5):
            # Unusually fast (potential attack or bypass)
            logger.warning(
                f"Unusually fast response for {operation_name}: {elapsed:.3f}s",
                extra={
                    "operation": operation_name,
                    "elapsed": elapsed,
                    "target": self.target_duration,
                },
            )
        elif elapsed > (self.target_duration * 2):
            # Unusually slow (potential DoS or performance issue)
            logger.warning(
                f"Unusually slow response for {operation_name}: {elapsed:.3f}s",
                extra={
                    "operation": operation_name,
                    "elapsed": elapsed,
                    "target": self.target_duration,
                },
            )

        # Sleep to reach target duration
        if sleep_duration > 0:
            time.sleep(sleep_duration)

        logger.debug(
            f"Constant-time response for {operation_name}: {elapsed:.3f}s + {sleep_duration:.3f}s sleep",
            extra={
                "operation": operation_name,
                "elapsed": elapsed,
                "sleep": sleep_duration,
                "total": elapsed + sleep_duration,
            },
        )

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
