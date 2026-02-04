"""GraphQL queries for compliance operations."""

from syntek_graphql_compliance.queries.gdpr import GDPRQuery
from syntek_graphql_compliance.queries.legal import LegalQuery

__all__ = [
    "GDPRQuery",
    "LegalQuery",
]
