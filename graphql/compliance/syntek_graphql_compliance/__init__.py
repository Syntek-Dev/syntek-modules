"""Syntek GraphQL Compliance - GDPR & Legal Document Management.

This package provides GraphQL operations for GDPR compliance
and legal document management.

Features:
- GDPR Article 15: Data export requests
- GDPR Article 17: Account deletion
- GDPR Article 18: Processing restrictions
- Consent management
- Legal document versioning and acceptance tracking
"""

from syntek_graphql_compliance.mutations import GDPRMutations, LegalMutations
from syntek_graphql_compliance.queries import GDPRQuery, LegalQuery

__version__ = "1.0.0"

__all__ = [
    "GDPRMutations",
    "LegalMutations",
    "GDPRQuery",
    "LegalQuery",
]
