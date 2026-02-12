"""Syntek GraphQL Audit - Audit logging queries for GraphQL.

Provides GraphQL queries for accessing audit logs and session management.
"""

__version__ = "1.0.0"

from syntek_graphql_audit.queries import AuditQuery
from syntek_graphql_audit.schema import create_audit_schema
from syntek_graphql_audit.types import (
    AuditLogConnection,
    AuditLogFilterInput,
    AuditLogType,
    PaginationInput,
    SessionManagementInfo,
    SessionTokenType,
)

__all__ = [
    # Version
    "__version__",
    # Queries
    "AuditQuery",
    # Schema
    "create_audit_schema",
    # Types
    "AuditLogConnection",
    "AuditLogFilterInput",
    "AuditLogType",
    "PaginationInput",
    "SessionManagementInfo",
    "SessionTokenType",
]
