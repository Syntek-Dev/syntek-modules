"""Database query profiling middleware for Django.

Profiles database queries per HTTP request, detecting slow queries
and excessive query counts. Logs warnings for performance issues
with request context for debugging.

Features:
- Track total query count per request
- Identify slow queries (configurable threshold)
- Log SQL statements for slow queries
- Track request execution time
- Include user and IP context in logs
- Integration with Sentry/GlitchTip

Configuration:
    SYNTEK_SECURITY_CORE = {
        'QUERY_PROFILING': {
            'ENABLED': True,  # Default: True in dev, False in prod
            'SLOW_QUERY_THRESHOLD_MS': 100,  # Queries slower than this trigger logs
            'LOG_SQL': True,  # Log full SQL for slow queries
            'LOG_BACKEND': 'console',  # 'console' or 'sentry'
            'EXCESSIVE_QUERY_COUNT': 50,  # Warn if request exceeds this many queries
            'TRACK_DUPLICATE_QUERIES': True,  # Detect duplicate queries
        }
    }

Example:
    # In settings.py
    MIDDLEWARE = [
        ...
        'syntek_security_core.middleware.DatabaseQueryProfilingMiddleware',
        ...
    ]
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Any, Callable

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class DatabaseQueryProfilingMiddleware:
    """Profile database queries and detect slow operations.

    Monitors database queries executed during each HTTP request,
    logging warnings for slow queries and excessive query counts
    to help identify performance bottlenecks.

    Measurements:
    - Total request execution time
    - Total database query count
    - Individual query execution times
    - Duplicate query detection
    - Slow query identification

    Configuration:
        SYNTEK_SECURITY_CORE = {
            'QUERY_PROFILING': {
                'ENABLED': True,
                'SLOW_QUERY_THRESHOLD_MS': 100,
                'LOG_SQL': True,
                'LOG_BACKEND': 'console',
                'EXCESSIVE_QUERY_COUNT': 50,
                'TRACK_DUPLICATE_QUERIES': True,
            }
        }

    Example:
        MIDDLEWARE = [
            'syntek_security_core.middleware.DatabaseQueryProfilingMiddleware',
        ]

    Attributes:
        get_response: Next middleware or view in chain
        config: Query profiling configuration
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialise query profiling middleware.

        Args:
            get_response: Next middleware or view in the chain
        """
        self.get_response = get_response
        self.config = self._get_config()

    def _get_config(self) -> dict[str, Any]:
        """Get query profiling configuration from Django settings.

        Loads configuration from SYNTEK_SECURITY_CORE.QUERY_PROFILING
        with sensible defaults for development and production.

        Returns:
            Configuration dictionary with profiling settings
        """
        security_config = getattr(settings, "SYNTEK_SECURITY_CORE", {})
        query_profiling_config = security_config.get("QUERY_PROFILING", {})

        # Default configuration
        defaults: dict[str, Any] = {
            "ENABLED": settings.DEBUG,  # Enabled in dev by default
            "SLOW_QUERY_THRESHOLD_MS": 100,
            "LOG_SQL": True,
            "LOG_BACKEND": "console",
            "EXCESSIVE_QUERY_COUNT": 50,
            "TRACK_DUPLICATE_QUERIES": True,
            "EXCLUDE_PATHS": ["/health/", "/metrics/", "/static/"],
        }

        # Merge with user configuration
        defaults.update(query_profiling_config)
        return defaults

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and profile database queries.

        Args:
            request: Django HTTP request

        Returns:
            HttpResponse from view or next middleware
        """
        if not self.config["ENABLED"]:
            return self.get_response(request)

        # Skip excluded paths
        if self._is_excluded_path(request.path):
            return self.get_response(request)

        # Reset query log and track start time
        connection.queries_log.clear()
        start_query_count = len(connection.queries)
        start_time = time.perf_counter()

        # Process request
        response = self.get_response(request)

        # Calculate metrics
        execution_time_ms = (time.perf_counter() - start_time) * 1000
        query_count = len(connection.queries) - start_query_count

        # Profile queries
        self._profile_queries(request, execution_time_ms, query_count)

        return response

    def _is_excluded_path(self, path: str) -> bool:
        """Check if request path is excluded from profiling.

        Health checks and static files are typically excluded
        to reduce log noise.

        Args:
            path: Request path to check

        Returns:
            True if path should be excluded, False otherwise
        """
        exclude_paths = self.config.get("EXCLUDE_PATHS", [])

        for exclude_pattern in exclude_paths:
            if path.startswith(exclude_pattern):
                return True

        return False

    def _profile_queries(
        self, request: HttpRequest, execution_time_ms: float, query_count: int
    ) -> None:
        """Profile queries executed during request.

        Analyses database queries to identify performance issues
        including slow queries, excessive query counts, and
        duplicate queries.

        Args:
            request: Django HTTP request
            execution_time_ms: Total request execution time
            query_count: Number of queries executed
        """
        if query_count == 0:
            return

        # Get recent queries
        recent_queries = connection.queries[-query_count:] if query_count > 0 else []

        # Find slow queries
        slow_queries = self._find_slow_queries(recent_queries)

        # Check for excessive query count
        excessive_queries = query_count > self.config["EXCESSIVE_QUERY_COUNT"]

        # Detect duplicate queries
        duplicate_queries: list[dict[str, Any]] = []
        if self.config["TRACK_DUPLICATE_QUERIES"]:
            duplicate_queries = self._find_duplicate_queries(recent_queries)

        # Log if performance issues detected
        if slow_queries or excessive_queries or duplicate_queries:
            self._log_performance_issues(
                request,
                execution_time_ms,
                query_count,
                slow_queries,
                excessive_queries,
                duplicate_queries,
            )

    def _find_slow_queries(self, queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find queries exceeding slow query threshold.

        Args:
            queries: List of query dictionaries from Django connection

        Returns:
            List of slow query details
        """
        threshold_ms = self.config["SLOW_QUERY_THRESHOLD_MS"]
        slow_queries = []

        for query in queries:
            query_time_ms = float(query.get("time", 0)) * 1000

            if query_time_ms > threshold_ms:
                slow_query_data = {
                    "time_ms": round(query_time_ms, 2),
                }

                # Include SQL if configured
                if self.config["LOG_SQL"]:
                    slow_query_data["sql"] = query.get("sql", "")[:1000]  # Truncate

                slow_queries.append(slow_query_data)

        return slow_queries

    def _find_duplicate_queries(self, queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find duplicate SQL queries in request.

        Duplicate queries often indicate missing prefetch_related
        or select_related optimisations.

        Args:
            queries: List of query dictionaries from Django connection

        Returns:
            List of duplicate query details
        """
        # Count SQL statements
        sql_statements = [query.get("sql", "") for query in queries]
        sql_counts = Counter(sql_statements)

        # Find duplicates (executed more than once)
        duplicates = []
        for sql, count in sql_counts.items():
            if count > 1:
                duplicate_data = {
                    "count": count,
                    "sql": sql[:500] if self.config["LOG_SQL"] else None,  # Truncate
                }
                duplicates.append(duplicate_data)

        return duplicates

    def _log_performance_issues(
        self,
        request: HttpRequest,
        execution_time_ms: float,
        query_count: int,
        slow_queries: list[dict[str, Any]],
        excessive_queries: bool,
        duplicate_queries: list[dict[str, Any]],
    ) -> None:
        """Log database performance issues with request context.

        Args:
            request: Django HTTP request
            execution_time_ms: Total request execution time
            query_count: Total query count
            slow_queries: List of slow query details
            excessive_queries: Whether query count is excessive
            duplicate_queries: List of duplicate query details
        """
        # Build log context
        log_data = {
            "path": request.path,
            "method": request.method,
            "execution_time_ms": round(execution_time_ms, 2),
            "query_count": query_count,
            "slow_query_count": len(slow_queries),
            "duplicate_query_count": len(duplicate_queries),
            **self._get_request_context(request),
        }

        # Add slow queries if present
        if slow_queries:
            log_data["slow_queries"] = slow_queries

        # Add duplicate queries if present
        if duplicate_queries:
            log_data["duplicate_queries"] = duplicate_queries

        # Build message
        issues = []
        if slow_queries:
            issues.append(f"{len(slow_queries)} slow queries")
        if excessive_queries:
            issues.append(
                f"excessive query count ({query_count} > {self.config['EXCESSIVE_QUERY_COUNT']})"
            )
        if duplicate_queries:
            issues.append(f"{len(duplicate_queries)} duplicate queries")

        message = (
            f"Database performance issues detected on {request.method} {request.path}: "
            f"{', '.join(issues)}"
        )

        logger.warning(message, extra=log_data)

        # Send to Sentry if configured
        if self.config["LOG_BACKEND"] == "sentry":
            self._send_to_sentry(request, log_data)

    def _get_request_context(self, request: HttpRequest) -> dict[str, Any]:
        """Extract request context for logging.

        Args:
            request: Django HTTP request

        Returns:
            Dictionary containing request context data
        """
        context: dict[str, Any] = {}

        # Extract user information
        user = getattr(request, "user", None)
        if user and hasattr(user, "is_authenticated") and user.is_authenticated:
            context["user_id"] = getattr(user, "id", None)
            context["user_email"] = getattr(user, "email", None)

        # Extract IP address
        context["ip_address"] = self._get_client_ip(request)

        return context

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request.

        Handles X-Forwarded-For headers for proxy/load balancer
        deployments.

        Args:
            request: Django HTTP request

        Returns:
            Client IP address string
        """
        # Check X-Forwarded-For header (proxy/load balancer)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip.strip()

        # Fallback to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR", "unknown")

    def _send_to_sentry(self, request: HttpRequest, log_data: dict[str, Any]) -> None:
        """Send performance data to Sentry.

        Integrates with Sentry performance monitoring to track
        database performance issues over time.

        Args:
            request: Django HTTP request
            log_data: Performance data for Sentry
        """
        try:
            import sentry_sdk

            # Create transaction
            with sentry_sdk.start_transaction(
                op="http.server", name=f"{request.method} {request.path}"
            ) as transaction:
                # Add tags
                transaction.set_tag("has_slow_queries", log_data["slow_query_count"] > 0)
                transaction.set_tag("has_duplicate_queries", log_data["duplicate_query_count"] > 0)

                # Add measurements
                transaction.set_measurement(
                    "execution_time_ms", log_data["execution_time_ms"], "millisecond"
                )
                transaction.set_measurement("query_count", log_data["query_count"], "count")
                transaction.set_measurement(
                    "slow_query_count", log_data["slow_query_count"], "count"
                )

                # Add slow queries as spans
                for i, slow_query in enumerate(log_data.get("slow_queries", [])):
                    with sentry_sdk.start_span(
                        op="db.sql.query", description=f"slow_query_{i}"
                    ) as span:
                        span.set_measurement("time_ms", slow_query["time_ms"], "millisecond")
                        if "sql" in slow_query:
                            span.set_data("sql", slow_query["sql"])

        except ImportError:
            # Sentry not installed, skip
            logger.debug("Sentry not installed, skipping performance tracking")
        except Exception as e:
            # Don't break request on Sentry errors
            logger.error(f"Failed to send performance data to Sentry: {e}")
