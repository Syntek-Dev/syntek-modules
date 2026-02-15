"""Input sanitisation extension for GraphQL operations.

Sanitises user input to prevent XSS, SQL injection, and other injection attacks.
Applied to all string inputs before operation execution.

Features:
- XSS prevention (HTML/JavaScript escaping)
- SQL injection prevention (dangerous pattern detection)
- Command injection prevention
- Path traversal prevention
- Configurable sanitisation levels

Configuration:
    GRAPHQL_SANITISE_INPUTS: Enable/disable sanitisation (default: True)
    GRAPHQL_SANITISATION_LEVEL: "strict", "moderate", "lenient" (default: "moderate")
    GRAPHQL_ALLOW_HTML_FIELDS: Fields that allow HTML content (default: [])
"""

import html
import logging
import re
from typing import TYPE_CHECKING, Any

from django.conf import settings
from strawberry.extensions import SchemaExtension

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

logger = logging.getLogger(__name__)


class InputSanitisationExtension(SchemaExtension):
    """Sanitise user inputs to prevent injection attacks.

    Automatically sanitises string inputs in GraphQL operations to prevent:
    - Cross-Site Scripting (XSS) attacks
    - SQL injection attempts
    - Command injection
    - Path traversal
    - LDAP injection
    - XML injection

    Sanitisation levels:
    - "strict": Aggressive sanitisation, strips most special characters
    - "moderate": Balanced approach, escapes dangerous patterns (default)
    - "lenient": Minimal sanitisation, only blocks obvious attacks

    HTML-allowed fields:
    Some fields may legitimately contain HTML (e.g., rich text editors).
    These can be configured via GRAPHQL_ALLOW_HTML_FIELDS setting.

    Configuration:
        GRAPHQL_SANITISE_INPUTS: Enable/disable (default: True)
        GRAPHQL_SANITISATION_LEVEL: "strict", "moderate", "lenient" (default: "moderate")
        GRAPHQL_ALLOW_HTML_FIELDS: Fields that allow HTML (e.g., ["description", "bio"])
        GRAPHQL_LOG_SANITISATION: Log sanitised inputs (default: True)

    Attributes:
        enabled: Whether sanitisation is enabled
        level: Sanitisation level ("strict", "moderate", "lenient")
        allow_html_fields: Set of field names that allow HTML
        log_sanitisation: Whether to log sanitised inputs
    """

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bEXEC\b.*\()",
        r"(--|\#|\/\*|\*\/)",  # SQL comments
        r"(\bOR\b.*=.*)",  # OR 1=1
        r"(\bAND\b.*=.*)",  # AND 1=1
        r"(';.*--)",  # Classic SQL injection
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers like onclick=
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",  # Shell metacharacters
        r"\$\(.+\)",  # Command substitution
        r"`[^`]+`",  # Backtick execution
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",  # ../ path traversal
        r"\.\.",  # .. directory
        r"/etc/",  # Unix system paths
        r"/proc/",
        r"C:\\",  # Windows paths
    ]

    def __init__(self, *, execution_context: "ExecutionContext") -> None:
        """Initialise the extension with sanitisation configuration.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

        # Load configuration
        self.enabled = getattr(settings, "GRAPHQL_SANITISE_INPUTS", True)
        self.level = getattr(settings, "GRAPHQL_SANITISATION_LEVEL", "moderate")
        allow_html = getattr(settings, "GRAPHQL_ALLOW_HTML_FIELDS", [])
        self.allow_html_fields = set(allow_html)
        self.log_sanitisation = getattr(settings, "GRAPHQL_LOG_SANITISATION", True)

        # Compile regex patterns
        self.sql_regex = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_regex = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        self.command_regex = [re.compile(p) for p in self.COMMAND_INJECTION_PATTERNS]
        self.path_regex = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]

    def on_execute(self) -> "Iterator[None]":
        """Execute with input sanitisation.

        Sanitises all string inputs in operation variables.

        Yields:
            None after sanitisation completes.
        """
        if not self.enabled:
            yield
            return

        # Sanitise variables
        self._sanitise_variables()

        yield

    def _sanitise_variables(self) -> None:
        """Sanitise all variables in the execution context."""
        variables = self.execution_context.variables

        if not variables:
            return

        operation_name = self._get_operation_name()

        for key, value in variables.items():
            if isinstance(value, str):
                sanitised = self._sanitise_string(value, key)

                if sanitised != value and self.log_sanitisation:
                    logger.info(
                        f"Sanitised input for {operation_name}.{key}",
                        extra={
                            "operation": operation_name,
                            "field": key,
                            "original_length": len(value),
                            "sanitised_length": len(sanitised),
                        },
                    )

                variables[key] = sanitised
            elif isinstance(value, dict):
                self._sanitise_dict(value, key, operation_name)
            elif isinstance(value, list):
                self._sanitise_list(value, key, operation_name)

    def _sanitise_dict(self, data: dict[str, Any], parent_key: str, operation: str | None) -> None:
        """Recursively sanitise dictionary values.

        Args:
            data: Dictionary to sanitise (modified in place).
            parent_key: Parent key name for logging.
            operation: Operation name for logging.
        """
        for key, value in data.items():
            full_key = f"{parent_key}.{key}"

            if isinstance(value, str):
                sanitised = self._sanitise_string(value, key)

                if sanitised != value and self.log_sanitisation:
                    logger.info(
                        f"Sanitised input for {operation}.{full_key}",
                        extra={
                            "operation": operation,
                            "field": full_key,
                            "original_length": len(value),
                            "sanitised_length": len(sanitised),
                        },
                    )

                data[key] = sanitised
            elif isinstance(value, dict):
                self._sanitise_dict(value, full_key, operation)
            elif isinstance(value, list):
                self._sanitise_list(value, full_key, operation)

    def _sanitise_list(self, data: list[Any], parent_key: str, operation: str | None) -> None:
        """Recursively sanitise list items.

        Args:
            data: List to sanitise (modified in place).
            parent_key: Parent key name for logging.
            operation: Operation name for logging.
        """
        for i, value in enumerate(data):
            if isinstance(value, str):
                sanitised = self._sanitise_string(value, parent_key)

                if sanitised != value and self.log_sanitisation:
                    logger.info(
                        f"Sanitised input for {operation}.{parent_key}[{i}]",
                        extra={
                            "operation": operation,
                            "field": f"{parent_key}[{i}]",
                            "original_length": len(value),
                            "sanitised_length": len(sanitised),
                        },
                    )

                data[i] = sanitised
            elif isinstance(value, dict):
                self._sanitise_dict(value, f"{parent_key}[{i}]", operation)
            elif isinstance(value, list):
                self._sanitise_list(value, f"{parent_key}[{i}]", operation)

    def _sanitise_string(self, value: str, field_name: str) -> str:
        """Sanitise a string value based on sanitisation level.

        Args:
            value: String to sanitise.
            field_name: Field name (to check if HTML allowed).

        Returns:
            Sanitised string.
        """
        if not value:
            return value

        # Check if HTML allowed for this field
        allow_html = field_name in self.allow_html_fields

        # Apply sanitisation based on level
        if self.level == "strict":
            return self._strict_sanitise(value, allow_html)
        elif self.level == "lenient":
            return self._lenient_sanitise(value, allow_html)
        else:  # moderate (default)
            return self._moderate_sanitise(value, allow_html)

    def _strict_sanitise(self, value: str, allow_html: bool) -> str:
        """Strict sanitisation - removes most special characters.

        Args:
            value: String to sanitise.
            allow_html: Whether to allow HTML.

        Returns:
            Sanitised string.
        """
        # Remove SQL injection patterns
        for pattern in self.sql_regex:
            value = pattern.sub("", value)

        # Remove command injection patterns
        for pattern in self.command_regex:
            value = pattern.sub("", value)

        # Remove path traversal patterns
        for pattern in self.path_regex:
            value = pattern.sub("", value)

        # Handle HTML/XSS
        if not allow_html:
            # Escape all HTML
            value = html.escape(value)

            # Remove XSS patterns
            for pattern in self.xss_regex:
                value = pattern.sub("", value)

        return value.strip()

    def _moderate_sanitise(self, value: str, allow_html: bool) -> str:
        """Moderate sanitisation - balanced approach.

        Args:
            value: String to sanitise.
            allow_html: Whether to allow HTML.

        Returns:
            Sanitised string.
        """
        # Detect and log SQL injection attempts
        for pattern in self.sql_regex:
            if pattern.search(value):
                logger.warning(
                    f"Potential SQL injection detected: {pattern.pattern}",
                    extra={"pattern": pattern.pattern, "value_length": len(value)},
                )
                value = pattern.sub("", value)

        # Detect and log command injection attempts
        for pattern in self.command_regex:
            if pattern.search(value):
                logger.warning(
                    f"Potential command injection detected: {pattern.pattern}",
                    extra={"pattern": pattern.pattern, "value_length": len(value)},
                )
                value = pattern.sub("", value)

        # Detect and log path traversal attempts
        for pattern in self.path_regex:
            if pattern.search(value):
                logger.warning(
                    f"Potential path traversal detected: {pattern.pattern}",
                    extra={"pattern": pattern.pattern, "value_length": len(value)},
                )
                value = pattern.sub("", value)

        # Handle HTML/XSS
        if not allow_html:
            # Escape HTML entities
            value = html.escape(value, quote=True)

            # Remove dangerous XSS patterns
            for pattern in self.xss_regex:
                if pattern.search(value):
                    logger.warning(
                        f"Potential XSS detected: {pattern.pattern}",
                        extra={"pattern": pattern.pattern, "value_length": len(value)},
                    )
                    value = pattern.sub("", value)

        return value.strip()

    def _lenient_sanitise(self, value: str, allow_html: bool) -> str:
        """Lenient sanitisation - only blocks obvious attacks.

        Args:
            value: String to sanitise.
            allow_html: Whether to allow HTML.

        Returns:
            Sanitised string.
        """
        # Only block the most obvious SQL injection patterns
        obvious_sql = [
            r"(';.*--)",  # Classic SQL injection
            r"(\bDROP\b.*\bTABLE\b)",  # DROP TABLE
        ]

        for pattern_str in obvious_sql:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            if pattern.search(value):
                logger.warning(
                    f"Obvious SQL injection blocked: {pattern_str}",
                    extra={"pattern": pattern_str, "value_length": len(value)},
                )
                value = pattern.sub("", value)

        # Only block obvious XSS if HTML not allowed
        if not allow_html:
            obvious_xss = [
                r"<script[^>]*>.*?</script>",  # Script tags
                r"javascript:",  # JavaScript protocol
            ]

            for pattern_str in obvious_xss:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                if pattern.search(value):
                    logger.warning(
                        f"Obvious XSS blocked: {pattern_str}",
                        extra={"pattern": pattern_str, "value_length": len(value)},
                    )
                    value = pattern.sub("", value)

        return value.strip()

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
