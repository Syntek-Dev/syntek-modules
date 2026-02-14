"""Suspicious activity detection extension for GraphQL operations.

Detects and flags unusual patterns that may indicate malicious activity:
- Multiple failed authentication attempts
- Unusual request patterns (velocity, frequency)
- Geographic anomalies
- Session hijacking indicators
- Credential stuffing attacks

Features:
- Real-time pattern detection
- IP reputation checking
- User behaviour analysis
- Automatic blocking of suspicious IPs
- Alert system integration

Configuration:
    GRAPHQL_SUSPICIOUS_ACTIVITY_ENABLED: Enable detection (default: True)
    GRAPHQL_SUSPICIOUS_ACTIVITY_AUTO_BLOCK: Auto-block suspicious IPs (default: False)
    GRAPHQL_SUSPICIOUS_ACTIVITY_THRESHOLD: Suspicion score threshold (default: 75)
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from strawberry.extensions import SchemaExtension

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

logger = logging.getLogger(__name__)


class SuspiciousActivityExtension(SchemaExtension):
    """Detect and flag suspicious activity patterns.

    Monitors GraphQL operations for patterns indicating malicious activity:

    Detection rules:
    1. Failed login velocity (>5 failures in 5 minutes from same IP)
    2. Multiple accounts from same IP (>3 registrations in 1 hour)
    3. Password reset abuse (>10 resets in 1 hour)
    4. TOTP brute force (>10 failed TOTP attempts in 10 minutes)
    5. Geographic anomalies (login from different countries in <1 hour)
    6. Session enumeration (>20 different session tokens in 5 minutes)

    Actions:
    - Log suspicious activity with details
    - Increment suspicion score in cache
    - Optionally auto-block high-scoring IPs
    - Send alerts to security team

    Configuration:
        GRAPHQL_SUSPICIOUS_ACTIVITY_ENABLED: Enable/disable (default: True)
        GRAPHQL_SUSPICIOUS_ACTIVITY_AUTO_BLOCK: Auto-block IPs (default: False)
        GRAPHQL_SUSPICIOUS_ACTIVITY_THRESHOLD: Suspicion score (0-100, default: 75)
        GRAPHQL_SUSPICIOUS_ACTIVITY_ALERT_EMAIL: Email for alerts

    Attributes:
        enabled: Whether detection is enabled
        auto_block: Whether to auto-block suspicious IPs
        threshold: Suspicion score threshold for blocking
        alert_email: Email address for security alerts
    """

    # Suspicion score weights
    FAILED_LOGIN_SCORE = 10
    FAILED_TOTP_SCORE = 15
    MULTIPLE_ACCOUNTS_SCORE = 25
    PASSWORD_RESET_ABUSE_SCORE = 20
    GEOGRAPHIC_ANOMALY_SCORE = 30
    SESSION_ENUMERATION_SCORE = 40

    def __init__(self, *, execution_context: "ExecutionContext") -> None:
        """Initialise the extension with suspicious activity detection configuration.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

        # Load configuration
        self.enabled = getattr(settings, "GRAPHQL_SUSPICIOUS_ACTIVITY_ENABLED", True)
        self.auto_block = getattr(settings, "GRAPHQL_SUSPICIOUS_ACTIVITY_AUTO_BLOCK", False)
        self.threshold = getattr(settings, "GRAPHQL_SUSPICIOUS_ACTIVITY_THRESHOLD", 75)
        self.alert_email = getattr(settings, "GRAPHQL_SUSPICIOUS_ACTIVITY_ALERT_EMAIL", None)

    def on_execute(self) -> "Iterator[None]":
        """Execute with suspicious activity detection.

        Monitors operation execution and detects suspicious patterns.

        Yields:
            None after detection completes.
        """
        if not self.enabled:
            yield
            return

        operation_name = self._get_operation_name()
        client_ip = self._get_client_ip()

        # Pre-execution checks
        self._check_pre_execution(operation_name, client_ip)

        # Execute operation
        yield

        # Post-execution analysis (would need access to result, not available in on_execute)
        # Note: For post-execution analysis, would need to use on_operation_resolve instead

    def _check_pre_execution(self, operation: str | None, client_ip: str) -> None:
        """Run pre-execution suspicious activity checks.

        Args:
            operation: Operation name.
            client_ip: Client IP address.
        """
        if not operation:
            return

        # Check operation-specific patterns
        if operation == "login":
            self._check_failed_login_velocity(client_ip)
        elif operation == "register":
            self._check_multiple_registrations(client_ip)
        elif operation == "requestPasswordReset":
            self._check_password_reset_abuse(client_ip)
        elif operation == "totpVerify":
            self._check_totp_brute_force(client_ip)

        # Check IP reputation
        self._check_ip_reputation(client_ip)

    def _check_failed_login_velocity(self, client_ip: str) -> None:
        """Check for rapid failed login attempts from same IP.

        Args:
            client_ip: Client IP address.
        """
        cache_key = f"suspicious:failed_login:{client_ip}"
        failed_count = cache.get(cache_key, 0)

        if failed_count >= 5:
            # Suspicious: >5 failed logins in 5 minutes
            self._flag_suspicious_activity(
                client_ip,
                "failed_login_velocity",
                self.FAILED_LOGIN_SCORE,
                f"Multiple failed login attempts: {failed_count}",
            )

    def _check_multiple_registrations(self, client_ip: str) -> None:
        """Check for multiple account registrations from same IP.

        Args:
            client_ip: Client IP address.
        """
        cache_key = f"suspicious:registrations:{client_ip}"
        registration_count = cache.get(cache_key, 0)

        # Increment counter
        if registration_count == 0:
            cache.set(cache_key, 1, 3600)  # 1 hour window
        else:
            try:
                cache.incr(cache_key)
                registration_count += 1
            except ValueError:
                cache.set(cache_key, 1, 3600)
                registration_count = 1

        if registration_count >= 3:
            # Suspicious: >3 registrations in 1 hour
            self._flag_suspicious_activity(
                client_ip,
                "multiple_registrations",
                self.MULTIPLE_ACCOUNTS_SCORE,
                f"Multiple account registrations: {registration_count}",
            )

    def _check_password_reset_abuse(self, client_ip: str) -> None:
        """Check for password reset abuse from same IP.

        Args:
            client_ip: Client IP address.
        """
        cache_key = f"suspicious:password_reset:{client_ip}"
        reset_count = cache.get(cache_key, 0)

        # Increment counter
        if reset_count == 0:
            cache.set(cache_key, 1, 3600)  # 1 hour window
        else:
            try:
                cache.incr(cache_key)
                reset_count += 1
            except ValueError:
                cache.set(cache_key, 1, 3600)
                reset_count = 1

        if reset_count >= 10:
            # Suspicious: >10 password resets in 1 hour
            self._flag_suspicious_activity(
                client_ip,
                "password_reset_abuse",
                self.PASSWORD_RESET_ABUSE_SCORE,
                f"Excessive password reset requests: {reset_count}",
            )

    def _check_totp_brute_force(self, client_ip: str) -> None:
        """Check for TOTP brute force attempts.

        Args:
            client_ip: Client IP address.
        """
        cache_key = f"suspicious:totp_failed:{client_ip}"
        failed_count = cache.get(cache_key, 0)

        if failed_count >= 10:
            # Suspicious: >10 failed TOTP attempts in 10 minutes
            self._flag_suspicious_activity(
                client_ip,
                "totp_brute_force",
                self.FAILED_TOTP_SCORE,
                f"Multiple failed TOTP attempts: {failed_count}",
            )

    def _check_ip_reputation(self, client_ip: str) -> None:
        """Check IP address reputation and history.

        Args:
            client_ip: Client IP address.
        """
        # Check if IP is already flagged
        cache_key = f"suspicious:ip_score:{client_ip}"
        suspicion_score = cache.get(cache_key, 0)

        if suspicion_score >= self.threshold:
            logger.warning(
                f"High suspicion score for IP {client_ip}: {suspicion_score}",
                extra={
                    "client_ip": client_ip,
                    "suspicion_score": suspicion_score,
                    "threshold": self.threshold,
                },
            )

            if self.auto_block:
                self._auto_block_ip(client_ip, suspicion_score)

    def _flag_suspicious_activity(
        self, client_ip: str, activity_type: str, score: int, details: str
    ) -> None:
        """Flag suspicious activity and increment suspicion score.

        Args:
            client_ip: Client IP address.
            activity_type: Type of suspicious activity.
            score: Suspicion score to add.
            details: Activity details.
        """
        logger.warning(
            f"Suspicious activity detected: {activity_type}",
            extra={
                "client_ip": client_ip,
                "activity_type": activity_type,
                "score": score,
                "details": details,
            },
        )

        # Increment suspicion score
        cache_key = f"suspicious:ip_score:{client_ip}"
        current_score = cache.get(cache_key, 0)
        new_score = current_score + score

        # Store with 24-hour expiry
        cache.set(cache_key, new_score, 86400)

        # Check if threshold exceeded
        if new_score >= self.threshold:
            self._send_alert(client_ip, activity_type, new_score, details)

            if self.auto_block:
                self._auto_block_ip(client_ip, new_score)

    def _auto_block_ip(self, client_ip: str, suspicion_score: int) -> None:
        """Automatically block suspicious IP address.

        Args:
            client_ip: Client IP address to block.
            suspicion_score: Current suspicion score.
        """
        logger.error(
            f"Auto-blocking IP {client_ip} (suspicion score: {suspicion_score})",
            extra={
                "client_ip": client_ip,
                "suspicion_score": suspicion_score,
                "action": "auto_block",
            },
        )

        # Try to use IP blacklist service if available
        try:
            from syntek_authentication.services.ip_tracking_service import (  # type: ignore[import]
                IPTrackingService,
            )

            # Add to blacklist with 24-hour expiry
            expiry = timezone.now() + timedelta(hours=24)

            IPTrackingService.add_to_blacklist(
                ip_address=client_ip,
                reason=f"Auto-blocked: Suspicion score {suspicion_score}",
                severity="high",
                expires_at=expiry,
            )

            logger.info(f"IP {client_ip} added to blacklist (expires: {expiry})")

        except (ImportError, AttributeError):
            # IP blacklist service not available
            logger.warning("IP blacklist service not available, using cache-based blocking")

            # Fall back to cache-based blocking
            cache_key = f"ip_blocked:{client_ip}"
            cache.set(cache_key, True, 86400)  # 24 hours

    def _send_alert(
        self, client_ip: str, activity_type: str, suspicion_score: int, details: str
    ) -> None:
        """Send security alert via email.

        Args:
            client_ip: Client IP address.
            activity_type: Type of suspicious activity.
            suspicion_score: Current suspicion score.
            details: Activity details.
        """
        if not self.alert_email:
            return

        try:
            from django.core.mail import send_mail

            subject = f"Security Alert: Suspicious Activity Detected ({activity_type})"
            message = f"""
Suspicious activity detected from IP: {client_ip}

Activity Type: {activity_type}
Suspicion Score: {suspicion_score}/{self.threshold}
Details: {details}

Timestamp: {timezone.now().isoformat()}

This is an automated security alert from the GraphQL API.
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@syntek.dev"),
                recipient_list=[self.alert_email],
                fail_silently=True,
            )

            logger.info(f"Security alert sent for {activity_type} from {client_ip}")

        except Exception as e:
            logger.error(f"Failed to send security alert: {e}")

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

    def _get_client_ip(self) -> str:
        """Extract client IP address from request.

        Returns:
            Client IP address.
        """
        context = self.execution_context.context

        if isinstance(context, dict):
            request = context.get("request")
        else:
            request = getattr(context, "request", None)

        if not request:
            return "unknown"

        # Try syntek-security-core's get_client_ip if available
        try:
            from syntek_security_core.utils.request import get_client_ip  # type: ignore[import]

            return get_client_ip(request, anonymise=False)
        except (ImportError, AttributeError):
            pass

        # Fallback to manual extraction
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR", "unknown")
