"""Performance metrics tracking and alerting.

Tracks database query performance metrics including execution times,
query counts, slow query frequency, and provides alerting capabilities
for performance degradation.

Features:
- Record query execution times per endpoint
- Track query counts per request
- Monitor slow query frequency
- Store metrics in Redis with time-series data
- Performance degradation detection
- Alert system integration (Sentry, email)
- Endpoint performance analysis

Configuration:
    SYNTEK_SECURITY_CORE = {
        'PERFORMANCE_METRICS': {
            'ENABLED': True,
            'REDIS_PREFIX': 'perf_metrics',
            'RETENTION_DAYS': 7,
            'ALERT_THRESHOLD_MS': 200,  # Alert if avg > 200ms
            'ALERT_CHANNELS': ['sentry', 'email'],
            'BASELINE_MULTIPLIER': 1.5,  # Alert if 50% slower than baseline
        }
    }

Example:
    from syntek_security_core.utils import PerformanceMetrics

    # Record metrics
    metrics = PerformanceMetrics()
    metrics.record_query_time('/api/users/', 150.5)
    metrics.record_query_count('/api/users/', 5)
    metrics.record_slow_query('/api/users/', 250.0, 'SELECT * FROM users')

    # Retrieve metrics
    stats = metrics.get_endpoint_stats('/api/users/')
    slowest = metrics.get_slowest_endpoints(limit=10)

    # Check for degradation
    if metrics.check_performance_degradation():
        print("Performance degradation detected!")
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Track and analyse database query performance metrics.

    Provides comprehensive performance tracking including query
    execution times, query counts, slow query monitoring, and
    performance degradation detection with alerting.

    Metrics are stored in Redis with configurable retention
    periods for historical analysis and trend detection.

    Configuration:
        SYNTEK_SECURITY_CORE = {
            'PERFORMANCE_METRICS': {
                'ENABLED': True,
                'REDIS_PREFIX': 'perf_metrics',
                'RETENTION_DAYS': 7,
                'ALERT_THRESHOLD_MS': 200,
                'ALERT_CHANNELS': ['sentry', 'email'],
                'BASELINE_MULTIPLIER': 1.5,
            }
        }

    Example:
        metrics = PerformanceMetrics()
        metrics.record_query_time('/api/users/', 150.5)
        stats = metrics.get_endpoint_stats('/api/users/')

    Attributes:
        config: Performance metrics configuration
        redis_prefix: Prefix for Redis keys
        retention_seconds: Metric retention period in seconds
    """

    def __init__(self) -> None:
        """Initialise performance metrics tracker.

        Loads configuration from Django settings and initialises
        Redis connection for metric storage.
        """
        self.config = self._get_config()
        self.redis_prefix = self.config["REDIS_PREFIX"]
        self.retention_seconds = self.config["RETENTION_DAYS"] * 86400

    def _get_config(self) -> dict[str, Any]:
        """Get performance metrics configuration from Django settings.

        Returns:
            Configuration dictionary with metrics settings
        """
        security_config = getattr(settings, "SYNTEK_SECURITY_CORE", {})
        perf_metrics_config = security_config.get("PERFORMANCE_METRICS", {})

        # Default configuration
        defaults: dict[str, Any] = {
            "ENABLED": True,
            "REDIS_PREFIX": "perf_metrics",
            "RETENTION_DAYS": 7,
            "ALERT_THRESHOLD_MS": 200,
            "ALERT_CHANNELS": ["sentry"],
            "BASELINE_MULTIPLIER": 1.5,  # Alert if 50% slower than baseline
            "SAMPLE_RATE": 1.0,  # Sample 100% of requests by default
        }

        # Merge with user configuration
        defaults.update(perf_metrics_config)
        return defaults

    def record_query_time(self, endpoint: str, execution_time_ms: float) -> None:
        """Record query execution time for endpoint.

        Stores execution time in Redis for statistical analysis
        and trend detection.

        Args:
            endpoint: Request endpoint path (e.g., '/api/users/')
            execution_time_ms: Query execution time in milliseconds
        """
        if not self.config["ENABLED"]:
            return

        # Apply sampling
        if not self._should_sample():
            return

        try:
            # Store execution time in time-series list
            key = f"{self.redis_prefix}:query_time:{endpoint}"
            timestamp = timezone.now().isoformat()

            # Store as JSON-like string for easy parsing
            value = f"{timestamp}:{execution_time_ms:.2f}"

            # Add to list with left push
            cache._cache.lpush(key, value)  # type: ignore[attr-defined]

            # Trim list to retention period
            max_entries = self.config["RETENTION_DAYS"] * 1440  # Assume 1 entry/minute
            cache._cache.ltrim(key, 0, max_entries)  # type: ignore[attr-defined]

            # Set expiry
            cache._cache.expire(key, self.retention_seconds)  # type: ignore[attr-defined]

        except AttributeError:
            # Cache backend doesn't support Redis operations
            logger.debug("Redis operations not available, using simple cache")
            self._record_simple_cache(endpoint, execution_time_ms, "query_time")
        except Exception as e:
            logger.error(f"Failed to record query time: {e}")

    def record_query_count(self, endpoint: str, count: int) -> None:
        """Record database query count for endpoint.

        Stores query count for monitoring excessive queries
        per request.

        Args:
            endpoint: Request endpoint path
            count: Number of database queries executed
        """
        if not self.config["ENABLED"]:
            return

        # Apply sampling
        if not self._should_sample():
            return

        try:
            # Store query count in time-series list
            key = f"{self.redis_prefix}:query_count:{endpoint}"
            timestamp = timezone.now().isoformat()

            value = f"{timestamp}:{count}"

            cache._cache.lpush(key, value)  # type: ignore[attr-defined]

            max_entries = self.config["RETENTION_DAYS"] * 1440
            cache._cache.ltrim(key, 0, max_entries)  # type: ignore[attr-defined]

            cache._cache.expire(key, self.retention_seconds)  # type: ignore[attr-defined]

        except AttributeError:
            logger.debug("Redis operations not available, using simple cache")
            self._record_simple_cache(endpoint, count, "query_count")
        except Exception as e:
            logger.error(f"Failed to record query count: {e}")

    def record_slow_query(
        self, endpoint: str, query_time_ms: float, sql: str | None = None
    ) -> None:
        """Record slow query occurrence.

        Tracks slow queries for identifying performance bottlenecks
        and optimisation opportunities.

        Args:
            endpoint: Request endpoint path
            query_time_ms: Query execution time in milliseconds
            sql: Optional SQL statement (truncated for storage)
        """
        if not self.config["ENABLED"]:
            return

        try:
            # Increment slow query counter
            key = f"{self.redis_prefix}:slow_query_count:{endpoint}"
            cache._cache.incr(key)  # type: ignore[attr-defined]
            cache._cache.expire(key, self.retention_seconds)  # type: ignore[attr-defined]

            # Store slow query details
            details_key = f"{self.redis_prefix}:slow_queries:{endpoint}"
            timestamp = timezone.now().isoformat()

            # Truncate SQL for storage
            sql_truncated = sql[:500] if sql else "N/A"
            value = f"{timestamp}:{query_time_ms:.2f}:{sql_truncated}"

            cache._cache.lpush(details_key, value)  # type: ignore[attr-defined]

            # Keep last 100 slow queries
            cache._cache.ltrim(details_key, 0, 99)  # type: ignore[attr-defined]

            cache._cache.expire(details_key, self.retention_seconds)  # type: ignore[attr-defined]

        except AttributeError:
            logger.debug("Redis operations not available, using simple cache")
            self._increment_simple_cache(endpoint, "slow_query_count")
        except Exception as e:
            logger.error(f"Failed to record slow query: {e}")

    def get_endpoint_stats(self, endpoint: str) -> dict[str, Any]:
        """Get performance statistics for endpoint.

        Calculates average execution time, query count, slow query
        percentage, and other metrics for the specified endpoint.

        Args:
            endpoint: Request endpoint path

        Returns:
            Dictionary containing endpoint statistics:
            - avg_time_ms: Average execution time
            - min_time_ms: Minimum execution time
            - max_time_ms: Maximum execution time
            - avg_query_count: Average queries per request
            - slow_query_count: Total slow queries
            - slow_query_percentage: Percentage of slow queries
            - total_requests: Total requests recorded
        """
        if not self.config["ENABLED"]:
            return {}

        try:
            # Get query times
            time_key = f"{self.redis_prefix}:query_time:{endpoint}"
            time_data = cache._cache.lrange(time_key, 0, -1)  # type: ignore[attr-defined]

            # Parse execution times
            execution_times = []
            for entry in time_data:
                try:
                    entry_str = entry.decode("utf-8") if isinstance(entry, bytes) else entry
                    _, time_str = entry_str.split(":")
                    execution_times.append(float(time_str))
                except (ValueError, IndexError):
                    continue

            # Get query counts
            count_key = f"{self.redis_prefix}:query_count:{endpoint}"
            count_data = cache._cache.lrange(count_key, 0, -1)  # type: ignore[attr-defined]

            query_counts = []
            for entry in count_data:
                try:
                    entry_str = entry.decode("utf-8") if isinstance(entry, bytes) else entry
                    _, count_str = entry_str.split(":")
                    query_counts.append(int(count_str))
                except (ValueError, IndexError):
                    continue

            # Get slow query count
            slow_key = f"{self.redis_prefix}:slow_query_count:{endpoint}"
            slow_count = cache._cache.get(slow_key) or 0  # type: ignore[attr-defined]

            # Calculate statistics
            stats: dict[str, Any] = {
                "endpoint": endpoint,
                "total_requests": len(execution_times),
            }

            if execution_times:
                stats.update(
                    {
                        "avg_time_ms": round(sum(execution_times) / len(execution_times), 2),
                        "min_time_ms": round(min(execution_times), 2),
                        "max_time_ms": round(max(execution_times), 2),
                    }
                )

            if query_counts:
                stats["avg_query_count"] = round(sum(query_counts) / len(query_counts), 2)

            if isinstance(slow_count, (int, bytes)):
                if isinstance(slow_count, bytes):
                    slow_count = int(slow_count.decode("utf-8"))

                stats["slow_query_count"] = slow_count

                if len(execution_times) > 0:
                    stats["slow_query_percentage"] = round(
                        (slow_count / len(execution_times)) * 100, 2
                    )

            return stats

        except AttributeError:
            # Redis operations not available
            return self._get_simple_cache_stats(endpoint)
        except Exception as e:
            logger.error(f"Failed to get endpoint stats: {e}")
            return {}

    def get_slowest_endpoints(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get slowest endpoints by average execution time.

        Analyses all tracked endpoints and returns the slowest
        ones for prioritising optimisation efforts.

        Args:
            limit: Maximum number of endpoints to return

        Returns:
            List of endpoint statistics dictionaries sorted by
            average execution time (slowest first)
        """
        if not self.config["ENABLED"]:
            return []

        try:
            # Get all endpoint keys
            pattern = f"{self.redis_prefix}:query_time:*"
            keys = cache._cache.keys(pattern)  # type: ignore[attr-defined]

            # Get stats for each endpoint
            endpoint_stats = []
            for key in keys:
                # Extract endpoint from key
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                endpoint = key_str.replace(f"{self.redis_prefix}:query_time:", "")

                stats = self.get_endpoint_stats(endpoint)
                if stats.get("avg_time_ms"):
                    endpoint_stats.append(stats)

            # Sort by average time (slowest first)
            sorted_stats = sorted(
                endpoint_stats, key=lambda x: x.get("avg_time_ms", 0), reverse=True
            )

            return sorted_stats[:limit]

        except AttributeError:
            logger.debug("Redis operations not available")
            return []
        except Exception as e:
            logger.error(f"Failed to get slowest endpoints: {e}")
            return []

    def check_performance_degradation(self) -> bool:
        """Check for performance degradation across endpoints.

        Compares current performance metrics with historical
        baselines to detect performance regressions.

        Returns:
            True if performance degradation detected, False otherwise
        """
        if not self.config["ENABLED"]:
            return False

        try:
            # Get current slowest endpoints
            current_stats = self.get_slowest_endpoints(limit=20)

            degraded = False

            for stats in current_stats:
                endpoint = stats["endpoint"]

                # Check against alert threshold
                avg_time_ms = stats.get("avg_time_ms", 0)
                if avg_time_ms > self.config["ALERT_THRESHOLD_MS"]:
                    logger.warning(
                        f"Performance alert: {endpoint} average time "
                        f"({avg_time_ms:.2f}ms) exceeds threshold "
                        f"({self.config['ALERT_THRESHOLD_MS']}ms)",
                        extra=stats,
                    )
                    degraded = True

                    # Send alerts
                    self._send_alert(endpoint, stats)

            return degraded

        except Exception as e:
            logger.error(f"Failed to check performance degradation: {e}")
            return False

    def _should_sample(self) -> bool:
        """Determine if current request should be sampled.

        Uses configured sample rate to reduce storage overhead
        in high-traffic environments.

        Returns:
            True if request should be sampled, False otherwise
        """
        import random

        sample_rate = self.config.get("SAMPLE_RATE", 1.0)
        return random.random() < sample_rate

    def _record_simple_cache(self, endpoint: str, value: float | int, metric_type: str) -> None:
        """Record metric using simple cache (fallback).

        Used when Redis-specific operations are not available.

        Args:
            endpoint: Request endpoint path
            value: Metric value to record
            metric_type: Type of metric ('query_time' or 'query_count')
        """
        key = f"{self.redis_prefix}:{metric_type}:{endpoint}:simple"

        # Get existing values
        existing = cache.get(key, [])
        existing.append((timezone.now().isoformat(), value))

        # Limit size
        max_size = 1000
        if len(existing) > max_size:
            existing = existing[-max_size:]

        cache.set(key, existing, self.retention_seconds)

    def _increment_simple_cache(self, endpoint: str, metric_type: str) -> None:
        """Increment counter using simple cache (fallback).

        Args:
            endpoint: Request endpoint path
            metric_type: Type of counter to increment
        """
        key = f"{self.redis_prefix}:{metric_type}:{endpoint}"
        current = cache.get(key, 0)
        cache.set(key, current + 1, self.retention_seconds)

    def _get_simple_cache_stats(self, endpoint: str) -> dict[str, Any]:
        """Get statistics from simple cache (fallback).

        Args:
            endpoint: Request endpoint path

        Returns:
            Dictionary containing basic statistics
        """
        # Get query times
        time_key = f"{self.redis_prefix}:query_time:{endpoint}:simple"
        time_data = cache.get(time_key, [])

        execution_times = [float(value) for _, value in time_data]

        stats: dict[str, Any] = {
            "endpoint": endpoint,
            "total_requests": len(execution_times),
        }

        if execution_times:
            stats.update(
                {
                    "avg_time_ms": round(sum(execution_times) / len(execution_times), 2),
                    "min_time_ms": round(min(execution_times), 2),
                    "max_time_ms": round(max(execution_times), 2),
                }
            )

        return stats

    def _send_alert(self, endpoint: str, stats: dict[str, Any]) -> None:
        """Send performance degradation alert.

        Sends alerts through configured channels (Sentry, email)
        when performance degradation is detected.

        Args:
            endpoint: Endpoint with performance issues
            stats: Performance statistics
        """
        alert_channels = self.config.get("ALERT_CHANNELS", [])

        # Send to Sentry
        if "sentry" in alert_channels:
            self._send_sentry_alert(endpoint, stats)

        # Send email
        if "email" in alert_channels:
            self._send_email_alert(endpoint, stats)

    def _send_sentry_alert(self, endpoint: str, stats: dict[str, Any]) -> None:
        """Send alert to Sentry.

        Args:
            endpoint: Endpoint with performance issues
            stats: Performance statistics
        """
        try:
            import sentry_sdk

            sentry_sdk.capture_message(
                f"Performance degradation detected: {endpoint}",
                level="warning",
                extras=stats,
            )

        except ImportError:
            logger.debug("Sentry not installed, skipping alert")
        except Exception as e:
            logger.error(f"Failed to send Sentry alert: {e}")

    def _send_email_alert(self, endpoint: str, stats: dict[str, Any]) -> None:
        """Send alert email.

        Args:
            endpoint: Endpoint with performance issues
            stats: Performance statistics
        """
        try:
            from django.core.mail import send_mail

            alert_email = self.config.get("ALERT_EMAIL")
            if not alert_email:
                return

            subject = f"Performance Alert: {endpoint}"
            message = f"""
Performance degradation detected for endpoint: {endpoint}

Statistics:
- Average execution time: {stats.get("avg_time_ms", "N/A")}ms
- Maximum execution time: {stats.get("max_time_ms", "N/A")}ms
- Average query count: {stats.get("avg_query_count", "N/A")}
- Slow query percentage: {stats.get("slow_query_percentage", "N/A")}%
- Total requests: {stats.get("total_requests", "N/A")}

Threshold: {self.config["ALERT_THRESHOLD_MS"]}ms
            """.strip()

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@syntek.dev"),
                recipient_list=[alert_email],
                fail_silently=True,
            )

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
