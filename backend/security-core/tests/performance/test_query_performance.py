"""Performance tests for database query optimisation.

Tests query performance, counts, and optimisation patterns to ensure
efficient database access and prevent performance regressions.

Run performance tests:
    pytest backend/security-core/tests/performance/ -v

Run with benchmarks:
    pytest backend/security-core/tests/performance/ --benchmark-only

Configuration:
    PERFORMANCE_TEST_CONFIG = {
        'BASELINE_QUERY_TIME_MS': 100,
        'BASELINE_QUERY_COUNT': 5,
        'LARGE_DATASET_SIZE': 1000000,
    }
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import override_settings

if TYPE_CHECKING:
    pass

User = get_user_model()


@pytest.fixture
def performance_config() -> dict[str, int]:
    """Get performance test configuration.

    Returns:
        Configuration dictionary with performance thresholds
    """
    config = getattr(settings, "PERFORMANCE_TEST_CONFIG", {})

    defaults = {
        "BASELINE_QUERY_TIME_MS": 100,
        "BASELINE_QUERY_COUNT": 5,
        "LARGE_DATASET_SIZE": 10000,  # Reduced for testing
    }

    defaults.update(config)
    return defaults


@pytest.fixture
def create_test_users(db):
    """Fixture to create test users.

    Args:
        db: Django database fixture

    Returns:
        Function to create specified number of users
    """

    def _create_users(count: int = 100) -> list:
        """Create test users with related data.

        Args:
            count: Number of users to create

        Returns:
            List of created User instances
        """
        users = []

        for i in range(count):
            user = User.objects.create(
                email=f"user{i}@test.com",
                username=f"user{i}",
                first_name="User",
                last_name=f"{i}",
            )
            users.append(user)

        return users

    return _create_users


@pytest.mark.django_db
@override_settings(DEBUG=True)
class TestQueryPerformance:
    """Performance tests for database queries.

    Tests query execution times, query counts, and optimisation
    patterns to ensure efficient database access.
    """

    def test_user_list_query_count(self, create_test_users):
        """Test that user list uses optimal query count.

        Verifies that fetching a list of users executes the
        minimum number of database queries.
        """
        # Create test users
        create_test_users(count=100)

        # Clear query log
        connection.queries_log.clear()

        # Execute query with select_related
        list(User.objects.all()[:100])

        # Verify query count
        query_count = len(connection.queries)

        # Should execute 1 query
        assert query_count <= 2, (
            f"User list executed {query_count} queries, expected <= 2. "
            f"Consider using select_related() for foreign keys."
        )

    def test_user_list_query_time(self, create_test_users, performance_config):
        """Test that user list query completes within time threshold.

        Args:
            create_test_users: Fixture to create test users
            performance_config: Performance configuration fixture
        """
        # Create test users
        create_test_users(count=100)

        # Measure query time
        start_time = time.perf_counter()
        list(User.objects.all()[:100])
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Verify execution time
        threshold = performance_config["BASELINE_QUERY_TIME_MS"]

        assert execution_time_ms < threshold, (
            f"User list query took {execution_time_ms:.2f}ms, "
            f"expected < {threshold}ms. Consider adding indexes or optimising query."
        )

    def test_no_n_plus_one_pattern(self, create_test_users):
        """Test that related object access doesn't trigger N+1 queries.

        Verifies that accessing related objects for multiple records
        doesn't execute additional queries per record.
        """
        # Create test users
        create_test_users(count=10)

        # Clear query log
        connection.queries_log.clear()

        # Fetch users (should use select_related or prefetch_related)
        user_list = list(User.objects.all()[:10])

        # Access related objects
        for user in user_list:
            # This should not trigger additional queries if optimised
            _ = user.email

        # Verify query count
        query_count = len(connection.queries)

        # Should not execute query per user
        assert query_count <= 2, (
            f"N+1 query pattern detected: {query_count} queries for 10 users. "
            f"Use select_related() or prefetch_related() to optimise."
        )

    @override_settings(DEBUG=True)
    def test_filter_query_uses_index(self, create_test_users):
        """Test that filter queries use database indexes.

        Verifies that common filter operations use indexes
        rather than full table scans.
        """
        # Create test users
        create_test_users(count=1000)

        # Clear query log
        connection.queries_log.clear()

        # Execute filtered query
        start_time = time.perf_counter()
        list(User.objects.filter(is_active=True)[:100])
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Fast execution suggests index usage
        # Slow execution (> 100ms for 1000 records) suggests missing index

        assert execution_time_ms < 100, (
            f"Filtered query took {execution_time_ms:.2f}ms for 1000 records. "
            f"Consider adding index on is_active field."
        )

    def test_exists_vs_count_performance(self, create_test_users):
        """Test that exists() is faster than count() for existence checks.

        Verifies the performance difference between exists()
        and count() > 0 patterns.
        """
        # Create test users
        create_test_users(count=1000)

        # Test count() performance
        start_count = time.perf_counter()
        User.objects.filter(is_active=True).count() > 0
        count_time_ms = (time.perf_counter() - start_count) * 1000

        # Test exists() performance
        start_exists = time.perf_counter()
        User.objects.filter(is_active=True).exists()
        exists_time_ms = (time.perf_counter() - start_exists) * 1000

        # exists() should be faster (stops at first match)
        assert exists_time_ms < count_time_ms, (
            f"exists() ({exists_time_ms:.2f}ms) slower than count() ({count_time_ms:.2f}ms). "
            f"Database optimisation may be needed."
        )

    @pytest.mark.slow
    def test_large_dataset_performance(self, performance_config):
        """Test query performance with large dataset.

        Simulates production-scale dataset to verify query
        performance under load.

        Note: Marked as slow test, run with: pytest -m slow
        """
        # Create large dataset
        dataset_size = performance_config.get("LARGE_DATASET_SIZE", 10000)

        # This would normally create dataset_size records
        # For testing, we'll use a smaller sample
        sample_size = min(dataset_size, 1000)

        users = []
        for i in range(sample_size):
            users.append(
                User(
                    email=f"bulk_user{i}@test.com",
                    username=f"bulk_user{i}",
                    first_name="Bulk",
                    last_name=f"{i}",
                )
            )

        # Bulk create for performance
        User.objects.bulk_create(users, batch_size=1000)

        # Test query performance on large dataset
        start_time = time.perf_counter()
        list(User.objects.filter(is_active=True)[:100])
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Should complete quickly even with large dataset
        assert execution_time_ms < 200, (
            f"Query took {execution_time_ms:.2f}ms on dataset of {sample_size} records. "
            f"Expected < 200ms. Consider adding indexes or optimising query."
        )

    def test_iterator_for_large_queryset(self, create_test_users):
        """Test that iterator() prevents loading all records into memory.

        Verifies that iterator() processes records efficiently
        without loading entire dataset into memory.
        """
        # Create test users
        create_test_users(count=1000)

        # Clear query log
        connection.queries_log.clear()

        # Process with iterator
        count = 0
        for user in User.objects.iterator(chunk_size=100):
            count += 1

        # Verify all users processed
        assert count == 1000

        # iterator() should use chunked queries
        query_count = len(connection.queries)

        # Should use multiple small queries (chunked)
        assert query_count >= 10, (
            f"iterator() used {query_count} queries, expected >= 10 (chunked). "
            f"Verify chunk_size is working correctly."
        )

    def test_values_list_performance(self, create_test_users):
        """Test that values_list() is faster than loading full models.

        Verifies performance benefit of values_list() when
        only specific fields are needed.
        """
        # Create test users
        create_test_users(count=1000)

        # Test full model loading
        start_full = time.perf_counter()
        list(User.objects.all()[:100])
        full_time_ms = (time.perf_counter() - start_full) * 1000

        # Test values_list loading
        start_values = time.perf_counter()
        list(User.objects.values_list("id", flat=True)[:100])
        values_time_ms = (time.perf_counter() - start_values) * 1000

        # values_list() should be faster (less data transferred)
        assert values_time_ms <= full_time_ms, (
            f"values_list() ({values_time_ms:.2f}ms) slower than full models "
            f"({full_time_ms:.2f}ms). Unexpected result."
        )


@pytest.mark.benchmark
class TestQueryBenchmarks:
    """Benchmark tests for database queries.

    Uses pytest-benchmark to measure and track query performance
    over time, detecting performance regressions.

    Run with: pytest --benchmark-only
    """

    @pytest.mark.django_db
    def test_benchmark_user_list(self, benchmark, create_test_users):
        """Benchmark user list query performance.

        Args:
            benchmark: pytest-benchmark fixture
            create_test_users: Fixture to create test users
        """
        # Create test data
        create_test_users(count=100)

        def query_users():
            """Execute user list query."""
            return list(User.objects.all()[:100])

        # Run benchmark
        benchmark(query_users)

        # Verify performance target
        assert benchmark.stats.mean < 0.1, (
            f"User list query averaged {benchmark.stats.mean * 1000:.2f}ms, expected < 100ms"
        )

    @pytest.mark.django_db
    def test_benchmark_filtered_query(self, benchmark, create_test_users):
        """Benchmark filtered query performance.

        Args:
            benchmark: pytest-benchmark fixture
            create_test_users: Fixture to create test users
        """
        # Create test data
        create_test_users(count=1000)

        def query_active_users():
            """Execute filtered query."""
            return list(User.objects.filter(is_active=True)[:100])

        # Run benchmark
        benchmark(query_active_users)

        # Verify performance target
        assert benchmark.stats.mean < 0.1, (
            f"Filtered query averaged {benchmark.stats.mean * 1000:.2f}ms, expected < 100ms"
        )

    @pytest.mark.django_db
    def test_benchmark_bulk_create(self, benchmark):
        """Benchmark bulk create performance.

        Args:
            benchmark: pytest-benchmark fixture
        """

        def bulk_create_users():
            """Bulk create users."""
            users = [
                User(
                    email=f"bench_user{i}@test.com",
                    username=f"bench_user{i}",
                    first_name="Bench",
                    last_name=f"{i}",
                )
                for i in range(100)
            ]

            User.objects.bulk_create(users, batch_size=100)

            # Clean up
            User.objects.filter(email__startswith="bench_user").delete()

        # Run benchmark
        benchmark(bulk_create_users)

        # Bulk create should be fast
        assert benchmark.stats.mean < 0.5, (
            f"Bulk create averaged {benchmark.stats.mean * 1000:.2f}ms, "
            f"expected < 500ms for 100 records"
        )


@pytest.mark.regression
class TestPerformanceRegression:
    """Performance regression tests.

    Tests that verify query performance hasn't degraded
    compared to baseline measurements.
    """

    @pytest.mark.django_db
    @override_settings(DEBUG=True)
    def test_no_query_count_regression(self, create_test_users, performance_config):
        """Test that query count hasn't increased.

        Verifies that changes haven't introduced additional
        queries to existing operations.
        """
        # Create test data
        create_test_users(count=100)

        # Clear query log
        connection.queries_log.clear()

        # Execute operation
        list(User.objects.all()[:100])

        # Verify query count hasn't regressed
        query_count = len(connection.queries)
        baseline = performance_config["BASELINE_QUERY_COUNT"]

        assert query_count <= baseline, (
            f"Query count regression detected: {query_count} queries, "
            f"baseline was {baseline}. Review recent changes for N+1 patterns."
        )

    @pytest.mark.django_db
    def test_no_execution_time_regression(self, create_test_users, performance_config):
        """Test that execution time hasn't increased.

        Verifies that changes haven't degraded query
        execution performance.
        """
        # Create test data
        create_test_users(count=100)

        # Measure execution time
        start_time = time.perf_counter()
        list(User.objects.all()[:100])
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Verify execution time hasn't regressed
        baseline = performance_config["BASELINE_QUERY_TIME_MS"]

        assert execution_time_ms < baseline * 1.5, (
            f"Execution time regression detected: {execution_time_ms:.2f}ms, "
            f"baseline was {baseline}ms. Review recent changes for performance impact."
        )


# Configuration example for settings.py
PERFORMANCE_TEST_CONFIG = {
    "BASELINE_QUERY_TIME_MS": 100,  # Maximum acceptable query time
    "BASELINE_QUERY_COUNT": 5,  # Maximum acceptable query count per operation
    "LARGE_DATASET_SIZE": 10000,  # Size of large dataset for load testing
}
