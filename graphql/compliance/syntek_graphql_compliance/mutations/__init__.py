"""GraphQL mutations for compliance operations."""

from syntek_graphql_compliance.mutations.gdpr import GDPRMutations
from syntek_graphql_compliance.mutations.legal import LegalMutations

__all__ = [
    "GDPRMutations",
    "LegalMutations",
]
