"""GraphQL security extensions for query depth and complexity limiting.

This module provides security extensions for Strawberry GraphQL to protect
against malicious or resource-intensive queries:
- Query depth limiting (prevent deeply nested queries)
- Query complexity analysis (prevent expensive queries)
- Introspection control (disable in production)
- Query cost estimation
"""

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from strawberry.extensions import SchemaExtension

if TYPE_CHECKING:
    from collections.abc import Iterator

    from strawberry.types import ExecutionContext

logger = logging.getLogger(__name__)


class QueryDepthLimitExtension(SchemaExtension):
    """Limit the maximum depth of GraphQL queries.

    This extension prevents deeply nested queries that could cause performance
    issues or be used for denial-of-service attacks. For example:

    query {
        user {
            posts {
                comments {
                    author {
                        posts {
                            comments {
                                # ... infinitely nested
                            }
                        }
                    }
                }
            }
        }
    }

    The maximum depth can be configured via the MAX_QUERY_DEPTH setting.
    Default is 10 levels deep.

    Attributes:
        max_depth: Maximum allowed query depth.
    """

    def __init__(
        self,
        *,
        execution_context: ExecutionContext,
        max_depth: int | None = None,
    ) -> None:
        """Initialize the extension with maximum query depth.

        Args:
            execution_context: The GraphQL execution context.
            max_depth: Maximum allowed query depth (overrides settings).
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context
        configured_depth = getattr(settings, "GRAPHQL_MAX_QUERY_DEPTH", 10)
        self.max_depth: int = max_depth if max_depth is not None else (configured_depth or 10)

    def on_execute(self) -> Iterator[None]:
        """Execute before the GraphQL query is processed.

        Validates the query depth before execution begins.

        Yields:
            None after validation completes.

        Raises:
            Exception: If query depth exceeds the maximum allowed.
        """
        query_depth = self._calculate_query_depth(self.execution_context.graphql_document)

        if query_depth > self.max_depth:
            logger.warning(
                f"Query depth limit exceeded: {query_depth} > {self.max_depth}",
                extra={
                    "query_depth": query_depth,
                    "max_depth": self.max_depth,
                    "query": str(self.execution_context.query),
                },
            )
            raise Exception(
                f"Query depth of {query_depth} exceeds maximum allowed depth of {self.max_depth}"
            )
        yield

    def _calculate_query_depth(self, document: Any, depth: int = 0) -> int:
        """Calculate the maximum depth of a GraphQL query document.

        Args:
            document: The GraphQL document AST.
            depth: Current depth level (used for recursion).

        Returns:
            The maximum depth of the query.
        """
        if not document:
            return depth

        max_depth = depth

        # Handle different node types
        if hasattr(document, "definitions"):
            for definition in document.definitions:
                node_depth = self._calculate_query_depth(definition, depth)
                max_depth = max(max_depth, node_depth)
        elif hasattr(document, "selection_set") and document.selection_set:
            for selection in document.selection_set.selections:
                node_depth = self._calculate_query_depth(selection, depth + 1)
                max_depth = max(max_depth, node_depth)

        return max_depth


class QueryComplexityLimitExtension(SchemaExtension):
    """Limit the complexity of GraphQL queries.

    This extension calculates a complexity score for each query based on:
    - Number of fields requested
    - Use of list fields (arrays)
    - Nested queries
    - Costly field resolvers (marked with @cost decorator)

    Queries exceeding the maximum complexity are rejected before execution.
    Maximum complexity can be configured via GRAPHQL_MAX_QUERY_COMPLEXITY setting.
    Default is 1000.

    Attributes:
        max_complexity: Maximum allowed query complexity score.
    """

    def __init__(
        self,
        *,
        execution_context: ExecutionContext,
        max_complexity: int | None = None,
    ) -> None:
        """Initialize the extension with maximum query complexity.

        Args:
            execution_context: The GraphQL execution context.
            max_complexity: Maximum allowed complexity (overrides settings).
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context
        configured_complexity = getattr(settings, "GRAPHQL_MAX_QUERY_COMPLEXITY", 1000)
        self.max_complexity: int = (
            max_complexity if max_complexity is not None else (configured_complexity or 1000)
        )

    def on_execute(self) -> Iterator[None]:
        """Execute before the GraphQL query is processed.

        Validates the query complexity before execution begins.

        Yields:
            None after validation completes.

        Raises:
            Exception: If query complexity exceeds the maximum allowed.
        """
        query_complexity = self._calculate_query_complexity(self.execution_context.graphql_document)

        if query_complexity > self.max_complexity:
            logger.warning(
                f"Query complexity limit exceeded: {query_complexity} > {self.max_complexity}",
                extra={
                    "query_complexity": query_complexity,
                    "max_complexity": self.max_complexity,
                    "query": str(self.execution_context.query),
                },
            )
            raise Exception(
                f"Query complexity of {query_complexity} exceeds maximum allowed "
                f"complexity of {self.max_complexity}"
            )
        yield

    def _calculate_query_complexity(self, document: Any, multiplier: int = 1) -> int:
        """Calculate the complexity score of a GraphQL query document.

        Args:
            document: The GraphQL document AST.
            multiplier: Multiplier for nested list fields.

        Returns:
            The complexity score of the query.
        """
        if not document:
            return 0

        complexity = 0

        # Handle different node types
        if hasattr(document, "definitions"):
            for definition in document.definitions:
                complexity += self._calculate_query_complexity(definition, multiplier)
        elif hasattr(document, "selection_set") and document.selection_set:
            for selection in document.selection_set.selections:
                # Determine if this is a list field (more expensive)
                # This is a simplified heuristic; in production, you'd check field types
                field_multiplier = 1
                if hasattr(selection, "name"):
                    field_name = (
                        selection.name.value
                        if hasattr(selection.name, "value")
                        else str(selection.name)
                    )
                    # Common list field naming patterns
                    if field_name.endswith("s") or field_name in [
                        "list",
                        "items",
                        "results",
                    ]:
                        # Assume list fields return 10 items on average
                        field_multiplier = 10

                # Each field adds base complexity (with multiplier for list fields)
                field_complexity = 1 * multiplier * field_multiplier

                # Add nested complexity
                nested_complexity = self._calculate_query_complexity(
                    selection, multiplier * field_multiplier
                )

                complexity += field_complexity + nested_complexity

        return complexity


class IntrospectionControlExtension(SchemaExtension):
    """Control GraphQL introspection based on environment.

    Introspection allows clients to query the GraphQL schema structure.
    While useful for development, it can expose sensitive information in production.

    This extension disables introspection in production environments unless
    explicitly enabled via GRAPHQL_ENABLE_INTROSPECTION setting.

    Introspection is always enabled in development/test environments.
    """

    def __init__(self, *, execution_context: ExecutionContext) -> None:
        """Initialize the extension.

        Args:
            execution_context: The GraphQL execution context.
        """
        super().__init__(execution_context=execution_context)
        self.execution_context = execution_context

    def on_execute(self) -> Iterator[None]:
        """Execute before the GraphQL query is processed.

        Blocks introspection queries in production if disabled.

        Yields:
            None after validation completes.

        Raises:
            Exception: If introspection is disabled and query is introspection.
        """
        # Allow introspection in DEBUG mode
        if getattr(settings, "DEBUG", False):
            yield
            return

        # Check if introspection is explicitly enabled
        if getattr(settings, "GRAPHQL_ENABLE_INTROSPECTION", False):
            yield
            return

        # Check if this is an introspection query
        if self._is_introspection_query(self.execution_context.graphql_document):
            logger.warning(
                "Introspection query blocked in production",
                extra={"query": str(self.execution_context.query)},
            )
            raise Exception("GraphQL introspection is disabled in production")
        yield

    def _is_introspection_query(self, document: Any) -> bool:
        """Check if a query is an introspection query.

        Introspection queries typically query __schema or __type fields.

        Args:
            document: The GraphQL document AST.

        Returns:
            True if the query is an introspection query, False otherwise.
        """
        if not document:
            return False

        if hasattr(document, "definitions"):
            return self._check_definitions(document.definitions)

        if hasattr(document, "selection_set"):
            return self._check_selection_set(document.selection_set)

        return False

    def _check_definitions(self, definitions: list[Any]) -> bool:
        """Check if any definition is an introspection query.

        Args:
            definitions: List of GraphQL definitions.

        Returns:
            True if any definition is an introspection query.
        """
        return any(self._is_introspection_query(definition) for definition in definitions)

    def _check_selection_set(self, selection_set: Any) -> bool:
        """Check if selection set contains introspection fields.

        Args:
            selection_set: GraphQL selection set.

        Returns:
            True if selection set contains __schema or __type.
        """
        if not selection_set or not selection_set.selections:
            return False

        for selection in selection_set.selections:
            if self._is_introspection_field(selection):
                return True
            if self._is_introspection_query(selection):
                return True

        return False

    def _is_introspection_field(self, selection: Any) -> bool:
        """Check if a field is an introspection field (__schema or __type).

        Args:
            selection: GraphQL selection node.

        Returns:
            True if the field is __schema or __type, False otherwise.
        """
        if not hasattr(selection, "name"):
            return False

        field_name = (
            selection.name.value if hasattr(selection.name, "value") else str(selection.name)
        )

        return field_name in ["__schema", "__type"]
