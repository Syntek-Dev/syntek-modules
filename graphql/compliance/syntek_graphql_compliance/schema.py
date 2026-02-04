"""GraphQL schema for compliance operations.

This module provides a standalone schema creation function for
GDPR compliance and legal document management.
"""

import strawberry

from syntek_graphql_compliance.mutations import GDPRMutations, LegalMutations
from syntek_graphql_compliance.queries import GDPRQuery, LegalQuery
from syntek_graphql_core.security import (  # type: ignore[import]
    IntrospectionControlExtension,
    QueryComplexityLimitExtension,
    QueryDepthLimitExtension,
)


@strawberry.type
class ComplianceQuery(GDPRQuery, LegalQuery):
    """Combined compliance query root."""

    pass


@strawberry.type
class ComplianceMutation(GDPRMutations, LegalMutations):
    """Combined compliance mutation root."""

    pass


def create_compliance_schema() -> strawberry.Schema:
    """Create a standalone compliance schema.

    Returns:
        Strawberry schema with GDPR and legal document operations.
    """
    return strawberry.Schema(
        query=ComplianceQuery,
        mutation=ComplianceMutation,
        extensions=[
            QueryDepthLimitExtension,
            QueryComplexityLimitExtension,
            IntrospectionControlExtension,
        ],
    )
