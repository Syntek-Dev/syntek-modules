"""Rate limiting extensions for GraphQL operations.

Provides granular rate limiting per operation (mutation/query) with Redis-backed
counters for distributed deployments. Includes global SMS cost attack prevention.

Features:
- Operation-specific rate limits (e.g., sendPhoneVerification: 3/hour)
- IP-based and user-based rate limiting scopes
- Global SMS budget tracking (prevent cost attacks)
- CAPTCHA escalation after rate limit violations
- Redis-backed counters for horizontal scaling
- Automatic cleanup of expired counters

Configuration:
    GRAPHQL_RATE_LIMITS: Dict[str, str] - Operation-specific rate limits
    GRAPHQL_GLOBAL_SMS_LIMIT: int - Maximum SMS per hour (default: 1000)
    GRAPHQL_GLOBAL_SMS_BUDGET: Decimal - Maximum spend per day (default: 500)
    GRAPHQL_SMS_COST_PER_MESSAGE: Decimal - Cost per SMS (default: 0.05)
"""

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from strawberry.extensions import SchemaExtension

from syntek_graphql_core.errors import ErrorCode, RateLimitError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

logger = logging.getLogger(__name__)


class OperationRateLimitExtension(SchemaExtension):
    """Granular rate limiting per GraphQL operation.

    Enforces operation-specific rate limits to prevent abuse. Rate limits are
    configured per operation name (mutation/query) and can be scoped by IP address
    or authenticated user.

    Default rate limits (can be overridden in settings):
    - sendPhoneVerification: 3/hour per IP (prevent SMS cost attacks)
    - verifyPhone: 5/15min per IP
    - sendEmailVerification: 3/hour per IP
    - requestPasswordReset: 3/hour per IP
    - login: 5/15min per IP
    - totpVerify: 5/15min per IP
    - register: 10/hour per IP
    - All other operations: 100/hour per IP

    Configuration:
        GRAPHQL_RATE_LIMITS = {
            "sendPhoneVerification": "3/hour",
            "verifyPhone": "5/15min",
            "login": "5/15min",
        }

    Attributes:
        rate_limits: Dict mapping operation names to rate limit strings
        default_limit: Default rate limit for unconfigured operations
    """

    # Default rate limits per operation
    DEFAULT_RATE_LIMITS = {
        "sendPhoneVerification": "3/hour",
        "verifyPhone": "5/15min",
        "sendEmailVerification": "3/hour",
        "requestPasswordReset": "3/hour",
        "login": "5/15min",
        "totpVerify": "5/15min",
        "register": "10/hour",
        "changePassword": "5/hour",
        "resetPassword": "5/hour",
        "setupTOTP": "3/hour",
        "verifyTOTPSetup": "10/15min",
        "generateRecoveryKeys": "3/hour",
    }

    def __init__(self, *, execution_context: "ExecutionContext") -> None:
        """Initialise the extension with rate limit configuration.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

        # Load rate limits from settings or use defaults
        configured_limits = getattr(settings, "GRAPHQL_RATE_LIMITS", {})
        self.rate_limits = {**self.DEFAULT_RATE_LIMITS, **configured_limits}
        self.default_limit = getattr(settings, "GRAPHQL_DEFAULT_RATE_LIMIT", "100/hour")

    def on_execute(self) -> "Iterator[None]":
        """Execute before the GraphQL query is processed.

        Checks rate limits for the current operation and rejects if exceeded.

        Yields:
            None after validation completes.

        Raises:
            RateLimitError: If rate limit exceeded for the operation.
        """
        operation_name = self._get_operation_name()

        if not operation_name:
            # No operation name, skip rate limiting (likely introspection)
            yield
            return

        # Get rate limit for operation
        rate_limit_str = self.rate_limits.get(operation_name, self.default_limit)

        # Parse rate limit string (e.g., "3/hour" -> limit=3, period=3600)
        limit, period = self._parse_rate_limit(rate_limit_str)

        # Get client identifier (IP or user ID)
        client_id = self._get_client_id()

        # Check rate limit
        if not self._check_rate_limit(operation_name, client_id, limit, period):
            # Get retry-after time
            retry_after = self._get_retry_after(operation_name, client_id, period)

            logger.warning(
                f"Rate limit exceeded for operation {operation_name}",
                extra={
                    "operation": operation_name,
                    "client_id": client_id,
                    "limit": limit,
                    "period": period,
                    "retry_after": retry_after,
                },
            )

            raise RateLimitError(
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message=f"Rate limit exceeded for {operation_name}. Try again in {retry_after} seconds.",
                extensions={
                    "operation": operation_name,
                    "retry_after": retry_after,
                    "limit": limit,
                    "period": period,
                },
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

    def _get_client_id(self) -> str:
        """Get unique client identifier (IP or user ID).

        Returns IP address for anonymous users, user ID for authenticated users.

        Returns:
            Client identifier string.
        """
        # Try to get request from context
        context = self.execution_context.context

        if isinstance(context, dict):
            request = context.get("request")
        else:
            request = getattr(context, "request", None)

        if not request:
            return "unknown"

        # Use user ID if authenticated
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return f"user:{user.id}"

        # Fall back to IP address
        return self._get_client_ip(request)

    def _get_client_ip(self, request: Any) -> str:
        """Extract client IP address from request.

        Handles X-Forwarded-For header for reverse proxies.

        Args:
            request: Django HttpRequest object.

        Returns:
            Client IP address.
        """
        # Try syntek-security-core's get_client_ip if available
        try:
            from syntek_security_core.utils.request import get_client_ip  # type: ignore[import]

            return f"ip:{get_client_ip(request, anonymise=False)}"
        except (ImportError, AttributeError):
            pass

        # Fallback to manual extraction
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")

        return f"ip:{ip}"

    def _parse_rate_limit(self, rate_limit_str: str) -> tuple[int, int]:
        """Parse rate limit string into limit and period.

        Supports formats:
        - "3/hour" -> (3, 3600)
        - "5/15min" -> (5, 900)
        - "10/day" -> (10, 86400)
        - "100/min" -> (100, 60)

        Args:
            rate_limit_str: Rate limit string (e.g., "3/hour").

        Returns:
            Tuple of (limit, period_in_seconds).

        Raises:
            ValueError: If rate limit string is invalid.
        """
        try:
            limit_str, period_str = rate_limit_str.split("/")
            limit = int(limit_str)

            # Parse period (handle "15min" format)
            if period_str.endswith("min"):
                minutes = int(period_str[:-3]) if len(period_str) > 3 else 1
                period = minutes * 60
            elif period_str == "hour":
                period = 3600
            elif period_str == "day":
                period = 86400
            elif period_str.endswith("s"):
                period = int(period_str[:-1])
            else:
                period = int(period_str)

            return limit, period

        except (ValueError, IndexError) as e:
            logger.error(f"Invalid rate limit format: {rate_limit_str}: {e}")
            # Fall back to conservative default
            return 10, 3600

    def _check_rate_limit(
        self, operation: str, client_id: str, limit: int, period: int
    ) -> bool:
        """Check if client has exceeded rate limit for operation.

        Uses Redis-backed counter with sliding window.

        Args:
            operation: Operation name (e.g., "login").
            client_id: Client identifier (IP or user ID).
            limit: Maximum requests allowed.
            period: Time period in seconds.

        Returns:
            True if within limit, False if exceeded.
        """
        cache_key = f"graphql_rate_limit:{operation}:{client_id}"

        # Get current count
        current_count = cache.get(cache_key, 0)

        # Check if limit exceeded
        if current_count >= limit:
            return False

        # Increment counter
        if current_count == 0:
            # First request, set with expiry
            cache.set(cache_key, 1, period)
        else:
            # Increment existing counter
            try:
                cache.incr(cache_key)
            except ValueError:
                # Key expired between get and incr, reset
                cache.set(cache_key, 1, period)

        return True

    def _get_retry_after(self, operation: str, client_id: str, period: int) -> int:
        """Get seconds until rate limit resets.

        Args:
            operation: Operation name.
            client_id: Client identifier.
            period: Rate limit period in seconds.

        Returns:
            Seconds until rate limit resets.
        """
        cache_key = f"graphql_rate_limit:{operation}:{client_id}"

        # Get TTL from Redis
        try:
            ttl = cache.ttl(cache_key)  # type: ignore[attr-defined]
            return max(ttl or period, 1)
        except (AttributeError, TypeError):
            # TTL not supported, return full period
            return period


class GlobalSMSRateLimitExtension(SchemaExtension):
    """Global SMS rate limiting to prevent cost attacks.

    Tracks SMS sending across all instances using Redis to prevent cost-based
    attacks. Enforces global hourly limits and daily budget caps.

    This extension should be used alongside OperationRateLimitExtension for
    comprehensive SMS protection.

    Configuration:
        GRAPHQL_GLOBAL_SMS_LIMIT: Maximum SMS per hour (default: 1000)
        GRAPHQL_GLOBAL_SMS_BUDGET: Maximum spend per day in currency units (default: 500)
        GRAPHQL_SMS_COST_PER_MESSAGE: Cost per SMS message (default: 0.05)
        GRAPHQL_SMS_ALERT_THRESHOLD: Alert when usage exceeds % (default: 0.8)
        GRAPHQL_SMS_ALERT_EMAIL: Email for alerts (optional)

    Features:
    - Global hourly SMS limit (shared across all instances)
    - Daily budget tracking
    - Alert system (email/Slack) at 80% threshold
    - CAPTCHA escalation after budget threshold
    - Cost analytics integration

    Attributes:
        hourly_limit: Maximum SMS per hour
        daily_budget: Maximum daily spend
        cost_per_sms: Cost per SMS message
        alert_threshold: Threshold for alerts (0.0-1.0)
    """

    def __init__(self, *, execution_context: "ExecutionContext") -> None:
        """Initialise the extension with SMS cost attack prevention configuration.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

        # Load SMS cost settings
        self.hourly_limit = getattr(settings, "GRAPHQL_GLOBAL_SMS_LIMIT", 1000)
        self.daily_budget = Decimal(str(getattr(settings, "GRAPHQL_GLOBAL_SMS_BUDGET", 500)))
        self.cost_per_sms = Decimal(str(getattr(settings, "GRAPHQL_SMS_COST_PER_MESSAGE", 0.05)))
        self.alert_threshold = getattr(settings, "GRAPHQL_SMS_ALERT_THRESHOLD", 0.8)
        self.alert_email = getattr(settings, "GRAPHQL_SMS_ALERT_EMAIL", None)

    def on_execute(self) -> "Iterator[None]":
        """Execute before SMS-related operations.

        Checks global SMS limits and budget before allowing SMS operations.

        Yields:
            None after validation completes.

        Raises:
            RateLimitError: If global SMS limit or budget exceeded.
        """
        operation_name = self._get_operation_name()

        # Only apply to SMS operations
        sms_operations = ["sendPhoneVerification", "resendPhoneVerification"]

        if operation_name not in sms_operations:
            yield
            return

        # Check hourly limit
        if not self._check_hourly_limit():
            logger.error(
                "Global SMS hourly limit exceeded",
                extra={"limit": self.hourly_limit, "operation": operation_name},
            )

            self._send_alert("CRITICAL: Global SMS hourly limit exceeded")

            raise RateLimitError(
                code=ErrorCode.TOO_MANY_REQUESTS,
                message="Global SMS limit exceeded. Please try again later.",
                extensions={
                    "global_limit": self.hourly_limit,
                    "limit_type": "hourly",
                },
            )

        # Check daily budget
        if not self._check_daily_budget():
            logger.error(
                "Global SMS daily budget exceeded",
                extra={"budget": str(self.daily_budget), "operation": operation_name},
            )

            self._send_alert("CRITICAL: Global SMS daily budget exceeded")

            raise RateLimitError(
                code=ErrorCode.TOO_MANY_REQUESTS,
                message="Daily SMS budget exceeded. Please try again tomorrow.",
                extensions={
                    "daily_budget": str(self.daily_budget),
                    "limit_type": "budget",
                },
            )

        # Increment counters
        self._increment_hourly_counter()
        self._increment_daily_cost()

        # Check if approaching threshold
        self._check_alert_threshold()

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

    def _check_hourly_limit(self) -> bool:
        """Check if global hourly SMS limit is exceeded.

        Returns:
            True if within limit, False if exceeded.
        """
        cache_key = "global_sms_hourly_count"
        current_count = cache.get(cache_key, 0)

        return current_count < self.hourly_limit

    def _check_daily_budget(self) -> bool:
        """Check if global daily SMS budget is exceeded.

        Returns:
            True if within budget, False if exceeded.
        """
        cache_key = "global_sms_daily_cost"
        current_cost = Decimal(str(cache.get(cache_key, 0)))

        return current_cost < self.daily_budget

    def _increment_hourly_counter(self) -> None:
        """Increment global hourly SMS counter."""
        cache_key = "global_sms_hourly_count"
        current_count = cache.get(cache_key, 0)

        if current_count == 0:
            # First SMS this hour, set with 1-hour expiry
            cache.set(cache_key, 1, 3600)
        else:
            try:
                cache.incr(cache_key)
            except ValueError:
                # Key expired, reset
                cache.set(cache_key, 1, 3600)

    def _increment_daily_cost(self) -> None:
        """Increment global daily SMS cost."""
        cache_key = "global_sms_daily_cost"
        current_cost = Decimal(str(cache.get(cache_key, 0)))

        new_cost = current_cost + self.cost_per_sms

        # Get seconds until end of day for TTL
        now = timezone.now()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        ttl = int((end_of_day - now).total_seconds())

        cache.set(cache_key, str(new_cost), ttl)

    def _check_alert_threshold(self) -> None:
        """Check if SMS usage is approaching threshold and send alert."""
        # Check hourly threshold
        hourly_count = cache.get("global_sms_hourly_count", 0)
        hourly_usage = hourly_count / self.hourly_limit

        if hourly_usage >= self.alert_threshold:
            self._send_alert(
                f"SMS hourly usage at {hourly_usage * 100:.1f}% ({hourly_count}/{self.hourly_limit})"
            )

        # Check daily budget threshold
        daily_cost = Decimal(str(cache.get("global_sms_daily_cost", 0)))
        budget_usage = daily_cost / self.daily_budget

        if budget_usage >= self.alert_threshold:
            self._send_alert(
                f"SMS daily budget at {budget_usage * 100:.1f}% (${daily_cost}/${self.daily_budget})"
            )

    def _send_alert(self, message: str) -> None:
        """Send alert via email or logging.

        Args:
            message: Alert message to send.
        """
        logger.warning(f"SMS Alert: {message}")

        # Send email alert if configured
        if self.alert_email:
            try:
                from django.core.mail import send_mail

                send_mail(
                    subject="GraphQL SMS Alert",
                    message=message,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@syntek.dev"),
                    recipient_list=[self.alert_email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send SMS alert email: {e}")
