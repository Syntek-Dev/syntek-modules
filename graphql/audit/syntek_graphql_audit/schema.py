"""GraphQL schema for audit logging operations.

This module provides a standalone schema creation function for
audit log queries and session management.
"""

import strawberry
from syntek_graphql_core.security import (  # type: ignore[import]
    IntrospectionControlExtension,
    QueryComplexityLimitExtension,
    QueryDepthLimitExtension,
)

from syntek_graphql_audit.queries import AuditQuery


def create_audit_schema() -> strawberry.Schema:
    """Create a standalone audit logging schema.

    Returns:
        Strawberry schema with audit log query operations.

    Example:
        >>> from syntek_graphql_audit.schema import create_audit_schema
        >>> schema = create_audit_schema()
    """
    return strawberry.Schema(
        query=AuditQuery,
        extensions=[
            QueryDepthLimitExtension,
            QueryComplexityLimitExtension,
            IntrospectionControlExtension,
        ],
    )
