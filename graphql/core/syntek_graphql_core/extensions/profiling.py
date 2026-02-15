"""GraphQL query profiling extension.

Tracks execution time, database queries, and resolver performance
for GraphQL operations. Integrates with GlitchTip/Sentry for
performance monitoring and detects slow queries that exceed
configurable thresholds.

Features:
- Track overall operation execution time
- Count database queries per GraphQL operation
- Track per-resolver execution times
- Identify slow queries (configurable threshold)
- Log query details with request context
- Integration with Sentry/GlitchTip for performance monitoring

Configuration:
    GRAPHQL_PROFILING = {
        'ENABLED': True,  # Default: True in dev, False in prod
        'SLOW_QUERY_THRESHOLD_MS': 100,  # Queries slower than this trigger logs
        'LOG_BACKEND': 'console',  # 'console' or 'sentry'
        'TRACK_RESOLVER_TIMING': True,  # Track individual resolver performance
        'TRACK_DB_QUERIES': True,  # Track database query counts
        'LOG_SQL_ON_SLOW': False,  # Log SQL statements for slow queries
    }

Example:
    # In schema.py
    from syntek_graphql_core.extensions import QueryProfilingExtension

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[
            QueryProfilingExtension(),
        ],
    )
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import connection

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.extensions import LifecycleStep
    from strawberry.types import ExecutionContext

try:
    from strawberry.extensions import SchemaExtension
except ImportError:
    # Graceful fallback if Strawberry not installed
    SchemaExtension = object  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


class QueryProfilingExtension(SchemaExtension):
    """Profile GraphQL query execution and detect slow queries.

    Tracks execution time, database query counts, and integrates
    with performance monitoring systems to identify bottlenecks.

    Measurements:
    - Total operation execution time (milliseconds)
    - Database query count per operation
    - Individual resolver execution times (optional)
    - SQL statement logging for slow queries (optional)

    Configuration:
        GRAPHQL_PROFILING = {
            'ENABLED': True,
            'SLOW_QUERY_THRESHOLD_MS': 100,
            'LOG_BACKEND': 'console',
            'TRACK_RESOLVER_TIMING': True,
            'TRACK_DB_QUERIES': True,
            'LOG_SQL_ON_SLOW': False,
        }

    Example:
        schema = strawberry.Schema(
            query=Query,
            extensions=[QueryProfilingExtension()],
        )

    Attributes:
        config: Profiling configuration dictionary
        start_time: Operation start timestamp (perf_counter)
        start_query_count: Database query count at operation start
        resolver_timings: Dictionary mapping resolver paths to execution times
    """

    def __init__(self, *, execution_context: ExecutionContext) -> None:
        """Initialise profiling extension.

        Loads configuration from Django settings and initialises
        tracking state for the current operation.

        Args:
            execution_context: GraphQL execution context from Strawberry
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context
        self.config = self._get_config()

        # Tracking state
        self.start_time: float | None = None
        self.start_query_count: int = 0
        self.resolver_timings: dict[str, float] = {}
        self.resolver_query_counts: dict[str, int] = {}

    def _get_config(self) -> dict[str, Any]:
        """Get profiling configuration from Django settings.

        Loads configuration from GRAPHQL_PROFILING setting with
        sensible defaults for development and production environments.

        Returns:
            Configuration dictionary with profiling settings
        """
        graphql_profiling = getattr(settings, "GRAPHQL_PROFILING", {})

        # Default configuration
        defaults: dict[str, Any] = {
            "ENABLED": settings.DEBUG,  # Enabled in dev by default
            "SLOW_QUERY_THRESHOLD_MS": 100,
            "LOG_BACKEND": "console",
            "TRACK_RESOLVER_TIMING": True,
            "TRACK_DB_QUERIES": True,
            "LOG_SQL_ON_SLOW": False,
            "MAX_RESOLVERS_LOGGED": 20,  # Limit resolver timing logs
        }

        # Merge with user configuration
        defaults.update(graphql_profiling)
        return defaults

    def on_execute(self) -> Iterator[None]:
        """Track execution time and database queries for operation.

        Measures total operation execution time and database query
        count, logging warnings for operations that exceed the
        configured slow query threshold.

        Yields:
            None after operation completes
        """
        if not self.config["ENABLED"]:
            yield
            return

        # Track start time and query count
        self.start_time = time.perf_counter()

        if self.config["TRACK_DB_QUERIES"]:
            self.start_query_count = len(connection.queries)

        # Execute operation
        yield

        # Calculate metrics
        execution_time_ms = (time.perf_counter() - self.start_time) * 1000

        query_count = 0
        if self.config["TRACK_DB_QUERIES"]:
            query_count = len(connection.queries) - self.start_query_count

        # Log if slow query
        if execution_time_ms > self.config["SLOW_QUERY_THRESHOLD_MS"]:
            self._log_slow_query(execution_time_ms, query_count)
        else:
            # Log all queries in debug mode
            if settings.DEBUG:
                self._log_query_debug(execution_time_ms, query_count)

    def on_resolve(self) -> Iterator[None]:
        """Track per-resolver execution time and database queries.

        Measures execution time and query count for individual
        resolvers when TRACK_RESOLVER_TIMING is enabled.

        Yields:
            None after resolver completes
        """
        if not self.config["ENABLED"] or not self.config["TRACK_RESOLVER_TIMING"]:
            yield
            return

        # Get resolver path
        resolver_path = self._get_resolver_path()

        # Track start time and query count
        resolver_start_time = time.perf_counter()
        resolver_start_query_count = 0

        if self.config["TRACK_DB_QUERIES"]:
            resolver_start_query_count = len(connection.queries)

        # Execute resolver
        yield

        # Calculate resolver metrics
        resolver_time_ms = (time.perf_counter() - resolver_start_time) * 1000
        resolver_query_count = 0

        if self.config["TRACK_DB_QUERIES"]:
            resolver_query_count = len(connection.queries) - resolver_start_query_count

        # Store resolver timing
        self.resolver_timings[resolver_path] = resolver_time_ms
        self.resolver_query_counts[resolver_path] = resolver_query_count

    def _get_operation_name(self) -> str | None:
        """Extract operation name from GraphQL document.

        Parses the GraphQL document to find the operation name
        for logging and identification purposes.

        Returns:
            Operation name string, or None if not found
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

    def _get_resolver_path(self) -> str:
        """Get current resolver path for tracking.

        Constructs a path string representing the resolver hierarchy
        for detailed performance tracking.

        Returns:
            Resolver path string (e.g., "Query.user.profile")
        """
        # Get path info from execution context
        path_info = getattr(self.execution_context, "path", None)

        if not path_info:
            return "unknown"

        # Build path string from path segments
        path_segments = []
        current = path_info

        while current:
            if hasattr(current, "key"):
                key = current.key
                if isinstance(key, str):
                    path_segments.append(key)

            current = getattr(current, "prev", None)

        # Reverse to get correct order
        path_segments.reverse()

        return ".".join(path_segments) if path_segments else "unknown"

    def _get_request_context(self) -> dict[str, Any]:
        """Extract request context for logging.

        Retrieves user ID, IP address, and other context information
        from the execution context for inclusion in logs.

        Returns:
            Dictionary containing request context data
        """
        context_data: dict[str, Any] = {}

        # Get request from context
        context = self.execution_context.context

        if isinstance(context, dict):
            request = context.get("request")
        else:
            request = getattr(context, "request", None)

        if not request:
            return context_data

        # Extract user information
        user = getattr(request, "user", None)
        if user and hasattr(user, "is_authenticated") and user.is_authenticated:
            context_data["user_id"] = getattr(user, "id", None)
            context_data["user_email"] = getattr(user, "email", None)

        # Extract IP address
        context_data["ip_address"] = self._get_client_ip(request)

        # Extract request method and path
        context_data["method"] = getattr(request, "method", None)
        context_data["path"] = getattr(request, "path", None)

        return context_data

    def _get_client_ip(self, request: Any) -> str:
        """Extract client IP address from request.

        Handles X-Forwarded-For headers for proxy/load balancer
        deployments.

        Args:
            request: Django HttpRequest object

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

    def _log_slow_query(self, execution_time_ms: float, query_count: int) -> None:
        """Log slow query details with context.

        Logs comprehensive information about slow queries including
        execution time, query count, resolver timings, and request
        context. Integrates with Sentry if configured.

        Args:
            execution_time_ms: Total execution time in milliseconds
            query_count: Number of database queries executed
        """
        operation_name = self._get_operation_name() or "unknown"
        context = self._get_request_context()

        # Build log message
        log_data = {
            "operation": operation_name,
            "execution_time_ms": round(execution_time_ms, 2),
            "db_query_count": query_count,
            **context,
        }

        # Add resolver timings if available
        if self.resolver_timings:
            # Get slowest resolvers (limit to avoid log spam)
            sorted_resolvers = sorted(
                self.resolver_timings.items(), key=lambda x: x[1], reverse=True
            )
            max_resolvers = self.config.get("MAX_RESOLVERS_LOGGED", 20)
            slowest_resolvers = sorted_resolvers[:max_resolvers]

            resolver_details = [
                {
                    "path": path,
                    "time_ms": round(time_ms, 2),
                    "queries": self.resolver_query_counts.get(path, 0),
                }
                for path, time_ms in slowest_resolvers
            ]

            log_data["slowest_resolvers"] = resolver_details

        # Log SQL statements if configured
        if self.config["LOG_SQL_ON_SLOW"] and query_count > 0:
            sql_queries = self._get_recent_sql_queries(query_count)
            log_data["sql_queries"] = sql_queries

        logger.warning(
            f"Slow GraphQL query detected: {operation_name} "
            f"({execution_time_ms:.2f}ms, {query_count} queries)",
            extra=log_data,
        )

        # Send to Sentry if configured
        if self.config["LOG_BACKEND"] == "sentry":
            self._send_to_sentry(operation_name, execution_time_ms, log_data)

    def _log_query_debug(self, execution_time_ms: float, query_count: int) -> None:
        """Log query debug information in development mode.

        Logs all GraphQL operations in debug mode for performance
        analysis during development.

        Args:
            execution_time_ms: Total execution time in milliseconds
            query_count: Number of database queries executed
        """
        operation_name = self._get_operation_name() or "unknown"

        logger.debug(
            f"GraphQL query: {operation_name} "
            f"({execution_time_ms:.2f}ms, {query_count} queries)",
            extra={
                "operation": operation_name,
                "execution_time_ms": round(execution_time_ms, 2),
                "db_query_count": query_count,
            },
        )

    def _get_recent_sql_queries(self, count: int) -> list[dict[str, Any]]:
        """Get recent SQL queries from Django connection.

        Retrieves the most recent SQL queries executed during
        the operation for debugging slow queries.

        Args:
            count: Number of recent queries to retrieve

        Returns:
            List of query dictionaries with SQL and execution time
        """
        recent_queries = connection.queries[-count:] if count > 0 else []

        return [
            {
                "sql": query.get("sql", "")[:500],  # Truncate long SQL
                "time_ms": round(float(query.get("time", 0)) * 1000, 2),
            }
            for query in recent_queries
        ]

    def _send_to_sentry(
        self, operation_name: str, execution_time_ms: float, log_data: dict[str, Any]
    ) -> None:
        """Send performance data to Sentry.

        Integrates with Sentry performance monitoring to track
        slow queries and performance trends over time.

        Args:
            operation_name: GraphQL operation name
            execution_time_ms: Total execution time in milliseconds
            log_data: Additional context data for Sentry
        """
        try:
            import sentry_sdk

            # Start transaction if not exists
            with sentry_sdk.start_transaction(
                op="graphql.query", name=operation_name
            ) as transaction:
                # Add context
                transaction.set_tag("operation", operation_name)
                transaction.set_tag("slow_query", True)
                transaction.set_measurement(
                    "execution_time_ms", execution_time_ms, "millisecond"
                )
                transaction.set_measurement(
                    "db_query_count", log_data.get("db_query_count", 0), "count"
                )

                # Add resolver timings as spans
                if self.resolver_timings:
                    for resolver_path, time_ms in self.resolver_timings.items():
                        with sentry_sdk.start_span(
                            op="graphql.resolver", description=resolver_path
                        ) as span:
                            span.set_measurement("time_ms", time_ms, "millisecond")
                            span.set_measurement(
                                "queries",
                                self.resolver_query_counts.get(resolver_path, 0),
                                "count",
                            )

        except ImportError:
            # Sentry not installed, skip
            logger.debug("Sentry not installed, skipping performance tracking")
        except Exception as e:
            # Don't break request on Sentry errors
            logger.error(f"Failed to send performance data to Sentry: {e}")
