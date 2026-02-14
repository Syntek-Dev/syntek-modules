"""N+1 query detection extension for GraphQL.

Detects N+1 query patterns where resolvers execute excessive
database queries in loops, suggesting optimisation opportunities
using DataLoader, select_related, or prefetch_related.

Features:
- Detect resolvers generating > N queries (configurable threshold)
- Log warnings with resolver path and query count
- Suggest DataLoader usage in warnings
- Optional strict mode (raise exception in development)
- Track queries per resolver using on_resolve hook
- Performance impact tracking

Configuration:
    GRAPHQL_N_PLUS_ONE_DETECTION = {
        'ENABLED': True,  # Default: True in dev, False in prod
        'QUERY_THRESHOLD': 10,  # Warn if resolver executes > N queries
        'STRICT_MODE': False,  # Raise exception in dev mode
        'SUGGEST_DATALOADER': True,  # Include DataLoader suggestions
        'LOG_SQL': False,  # Log SQL statements from N+1 patterns
    }

Example:
    # In schema.py
    from syntek_graphql_core.extensions import NPlusOneDetectionExtension

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[
            NPlusOneDetectionExtension(),
        ],
    )
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import connection

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

try:
    from strawberry.extensions import SchemaExtension
except ImportError:
    # Graceful fallback if Strawberry not installed
    SchemaExtension = object  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


class NPlusOneQueryError(Exception):
    """Exception raised when N+1 query pattern detected in strict mode.

    Attributes:
        resolver_path: Path to resolver with N+1 pattern
        query_count: Number of queries executed by resolver
        message: Error message with optimisation suggestions
    """

    def __init__(self, resolver_path: str, query_count: int, message: str) -> None:
        """Initialise N+1 query error.

        Args:
            resolver_path: Path to resolver with N+1 pattern
            query_count: Number of queries executed
            message: Error message with details
        """
        self.resolver_path = resolver_path
        self.query_count = query_count
        super().__init__(message)


class NPlusOneDetectionExtension(SchemaExtension):
    """Detect N+1 query patterns in GraphQL resolvers.

    Monitors database queries executed by individual resolvers
    and warns when a resolver generates excessive queries,
    indicating a potential N+1 query problem.

    N+1 Query Pattern:
        When a resolver fetches a list of items (1 query), then
        fetches related data for each item individually (N queries),
        resulting in N+1 total queries instead of 2 queries with
        proper eager loading.

    Example N+1 Pattern:
        # BAD - Executes N+1 queries
        @strawberry.type
        class User:
            @strawberry.field
            def posts(self) -> list[Post]:
                return self.posts.all()  # Query per user

        # GOOD - Executes 2 queries using prefetch_related
        users = User.objects.prefetch_related('posts').all()

        # BETTER - Executes batched queries using DataLoader
        posts_loader = DataLoader(load_fn=load_posts_batch)

    Configuration:
        GRAPHQL_N_PLUS_ONE_DETECTION = {
            'ENABLED': True,
            'QUERY_THRESHOLD': 10,
            'STRICT_MODE': False,
            'SUGGEST_DATALOADER': True,
            'LOG_SQL': False,
        }

    Attributes:
        config: N+1 detection configuration
        resolver_query_counts: Track query counts per resolver
        current_resolver_path: Current resolver being tracked
        current_query_start: Query count at resolver start
    """

    def __init__(self, *, execution_context: ExecutionContext) -> None:
        """Initialise N+1 detection extension.

        Loads configuration and initialises tracking state for
        detecting N+1 query patterns.

        Args:
            execution_context: GraphQL execution context from Strawberry
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context
        self.config = self._get_config()

        # Tracking state
        self.resolver_query_counts: dict[str, int] = {}
        self.current_resolver_path: str | None = None
        self.current_query_start: int = 0

    def _get_config(self) -> dict[str, Any]:
        """Get N+1 detection configuration from Django settings.

        Loads configuration from GRAPHQL_N_PLUS_ONE_DETECTION setting
        with sensible defaults for development and production.

        Returns:
            Configuration dictionary with detection settings
        """
        n_plus_one_config = getattr(settings, "GRAPHQL_N_PLUS_ONE_DETECTION", {})

        # Default configuration
        defaults: dict[str, Any] = {
            "ENABLED": settings.DEBUG,  # Enabled in dev by default
            "QUERY_THRESHOLD": 10,  # Warn if > 10 queries per resolver
            "STRICT_MODE": False,  # Don't raise exceptions by default
            "SUGGEST_DATALOADER": True,  # Include DataLoader suggestions
            "LOG_SQL": False,  # Don't log SQL by default
            "EXCLUDE_PATHS": [],  # Resolver paths to exclude from checking
        }

        # Merge with user configuration
        defaults.update(n_plus_one_config)
        return defaults

    def on_resolve(self) -> Iterator[None]:
        """Track queries executed per resolver.

        Monitors database query count before and after resolver
        execution to detect N+1 patterns.

        Yields:
            None after resolver completes

        Raises:
            NPlusOneQueryError: If strict mode enabled and N+1 detected
        """
        if not self.config["ENABLED"]:
            yield
            return

        # Get resolver path
        resolver_path = self._get_resolver_path()

        # Skip excluded paths
        if self._is_excluded_path(resolver_path):
            yield
            return

        # Track query count at resolver start
        start_query_count = len(connection.queries)

        # Execute resolver
        yield

        # Calculate queries executed by this resolver
        queries_executed = len(connection.queries) - start_query_count

        # Store query count for this resolver
        self.resolver_query_counts[resolver_path] = (
            self.resolver_query_counts.get(resolver_path, 0) + queries_executed
        )

        # Check if threshold exceeded
        if queries_executed > self.config["QUERY_THRESHOLD"]:
            self._handle_n_plus_one(resolver_path, queries_executed, start_query_count)

    def _get_resolver_path(self) -> str:
        """Get current resolver path for tracking.

        Constructs a path string representing the resolver hierarchy
        for detailed N+1 pattern tracking.

        Returns:
            Resolver path string (e.g., "Query.users.posts")
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

    def _is_excluded_path(self, resolver_path: str) -> bool:
        """Check if resolver path is excluded from N+1 detection.

        Some resolvers may legitimately execute many queries
        and can be excluded from checking.

        Args:
            resolver_path: Resolver path to check

        Returns:
            True if path should be excluded, False otherwise
        """
        exclude_paths = self.config.get("EXCLUDE_PATHS", [])

        for exclude_pattern in exclude_paths:
            if exclude_pattern in resolver_path:
                return True

        return False

    def _handle_n_plus_one(
        self, resolver_path: str, query_count: int, start_query_count: int
    ) -> None:
        """Handle detected N+1 query pattern.

        Logs warning with optimisation suggestions and optionally
        raises exception in strict mode.

        Args:
            resolver_path: Path to resolver with N+1 pattern
            query_count: Number of queries executed
            start_query_count: Starting query count for SQL retrieval

        Raises:
            NPlusOneQueryError: If strict mode enabled
        """
        # Build warning message
        message = self._build_warning_message(resolver_path, query_count)

        # Get SQL queries if configured
        sql_queries = []
        if self.config["LOG_SQL"]:
            sql_queries = self._get_resolver_sql_queries(start_query_count, query_count)

        # Log warning
        logger.warning(
            f"N+1 query pattern detected: {resolver_path}",
            extra={
                "resolver_path": resolver_path,
                "query_count": query_count,
                "threshold": self.config["QUERY_THRESHOLD"],
                "sql_queries": sql_queries if sql_queries else None,
            },
        )

        # Raise exception in strict mode
        if self.config["STRICT_MODE"] and settings.DEBUG:
            raise NPlusOneQueryError(resolver_path, query_count, message)

    def _build_warning_message(self, resolver_path: str, query_count: int) -> str:
        """Build warning message with optimisation suggestions.

        Creates a detailed message explaining the N+1 pattern
        and suggesting solutions.

        Args:
            resolver_path: Path to resolver with N+1 pattern
            query_count: Number of queries executed

        Returns:
            Formatted warning message with suggestions
        """
        message_parts = [
            f"N+1 query pattern detected in resolver: {resolver_path}",
            f"Executed {query_count} queries (threshold: {self.config['QUERY_THRESHOLD']})",
        ]

        # Add optimisation suggestions if enabled
        if self.config["SUGGEST_DATALOADER"]:
            message_parts.extend(
                [
                    "",
                    "Optimisation suggestions:",
                    "1. Use DataLoader for batched loading:",
                    "   from strawberry.dataloader import DataLoader",
                    "   loader = DataLoader(load_fn=batch_load_function)",
                    "",
                    "2. Use select_related() for foreign keys:",
                    "   Model.objects.select_related('foreign_key_field')",
                    "",
                    "3. Use prefetch_related() for many-to-many:",
                    "   Model.objects.prefetch_related('many_to_many_field')",
                    "",
                    "4. Use only() or defer() to limit fields:",
                    "   Model.objects.only('field1', 'field2')",
                ]
            )

        return "\n".join(message_parts)

    def _get_resolver_sql_queries(
        self, start_count: int, query_count: int
    ) -> list[dict[str, Any]]:
        """Get SQL queries executed by resolver.

        Retrieves the SQL statements executed by the resolver
        for debugging N+1 patterns.

        Args:
            start_count: Query count at resolver start
            query_count: Number of queries executed

        Returns:
            List of query dictionaries with SQL and execution time
        """
        # Get queries executed by this resolver
        resolver_queries = connection.queries[start_count : start_count + query_count]

        return [
            {
                "sql": query.get("sql", "")[:500],  # Truncate long SQL
                "time_ms": round(float(query.get("time", 0)) * 1000, 2),
            }
            for query in resolver_queries
        ]


class DataLoaderExample:
    """Example DataLoader implementation for reference.

    This class demonstrates proper DataLoader usage to prevent
    N+1 query patterns in GraphQL resolvers.

    Example usage:
        # Define batch loading function
        async def load_users_batch(keys: list[int]) -> list[User | None]:
            users = await User.objects.filter(id__in=keys)
            user_map = {user.id: user for user in users}
            return [user_map.get(key) for key in keys]

        # Create DataLoader
        user_loader = DataLoader(load_fn=load_users_batch)

        # Use in resolver
        @strawberry.field
        async def user(self, info: Info, id: int) -> User | None:
            return await info.context.user_loader.load(id)

    Benefits:
        - Batches multiple load() calls into single database query
        - Caches results within single request
        - Prevents N+1 query patterns automatically
        - Reduces database load and improves performance
    """

    @staticmethod
    def example_batch_load_function() -> str:
        """Return example batch loading function code.

        Returns:
            Python code string with DataLoader example
        """
        return """
# Example DataLoader implementation for User model
from strawberry.dataloader import DataLoader
from typing import List, Optional
from myapp.models import User

async def load_users_batch(keys: List[int]) -> List[Optional[User]]:
    '''Batch load users by ID.

    Args:
        keys: List of user IDs to load

    Returns:
        List of User instances in same order as keys
    '''
    # Fetch all users in single query
    users = await User.objects.filter(id__in=keys)

    # Create mapping of ID to user
    user_map = {user.id: user for user in users}

    # Return users in same order as keys (None if not found)
    return [user_map.get(key) for key in keys]

# Create DataLoader instance
user_loader = DataLoader(load_fn=load_users_batch)

# Use in resolver
@strawberry.type
class Query:
    @strawberry.field
    async def user(self, info: Info, id: int) -> Optional[User]:
        # Load user using DataLoader (batched automatically)
        return await info.context.user_loader.load(id)

    @strawberry.field
    async def users(self, info: Info, ids: List[int]) -> List[Optional[User]]:
        # Load multiple users (single batched query)
        return await info.context.user_loader.load_many(ids)
"""

    @staticmethod
    def example_prefetch_related() -> str:
        """Return example prefetch_related usage code.

        Returns:
            Python code string with Django ORM example
        """
        return """
# Example Django ORM optimisation with prefetch_related
from django.db.models import Prefetch
from myapp.models import User, Post

# BAD - N+1 query pattern
users = User.objects.all()
for user in users:
    posts = user.posts.all()  # Executes query per user (N+1)

# GOOD - Prefetch related objects
users = User.objects.prefetch_related('posts').all()
for user in users:
    posts = user.posts.all()  # No additional queries (cached)

# BETTER - Custom prefetch with filtering
posts_prefetch = Prefetch(
    'posts',
    queryset=Post.objects.filter(published=True).order_by('-created_at')
)
users = User.objects.prefetch_related(posts_prefetch).all()

# BEST - Combine select_related and prefetch_related
users = (
    User.objects
    .select_related('profile')  # Foreign key (JOIN)
    .prefetch_related('posts')  # Many-to-many (separate query)
    .all()
)
"""
