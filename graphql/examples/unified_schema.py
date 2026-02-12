"""Example: Creating a unified GraphQL schema with all modules.

This example shows how to compose all Syntek GraphQL modules into a single schema.
"""

import strawberry

# Import from syntek-graphql-audit
from syntek_graphql_audit.queries.audit import AuditQuery

# Import from syntek-graphql-auth
from syntek_graphql_auth.mutations.auth import AuthMutations
from syntek_graphql_auth.mutations.session import SessionMutations
from syntek_graphql_auth.mutations.totp import TOTPMutations
from syntek_graphql_auth.queries.user import UserQueries

# Import from syntek-graphql-compliance
from syntek_graphql_compliance.mutations.gdpr import GDPRMutations
from syntek_graphql_compliance.mutations.legal import LegalMutations
from syntek_graphql_compliance.queries.gdpr import GDPRQuery
from syntek_graphql_compliance.queries.legal import LegalQuery

# Import from syntek-graphql-core
from syntek_graphql_core.security import (
    IntrospectionControlExtension,
    QueryComplexityLimitExtension,
    QueryDepthLimitExtension,
)


# Compose all queries into a single Query type
@strawberry.type
class Query(UserQueries, AuditQuery, GDPRQuery, LegalQuery):
    """Root query type combining all module queries."""

    pass


# Compose all mutations into a single Mutation type
@strawberry.type
class Mutation(AuthMutations, SessionMutations, TOTPMutations, GDPRMutations, LegalMutations):
    """Root mutation type combining all module mutations."""

    pass


# Create the unified schema with security extensions
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimitExtension,
        QueryComplexityLimitExtension,
        IntrospectionControlExtension,
    ],
    scalar_overrides={
        # Add custom scalar overrides if needed
    },
)


# Django settings configuration
"""
Add to your Django settings.py:

# GraphQL Configuration
GRAPHQL_MAX_QUERY_DEPTH = 10
GRAPHQL_MAX_QUERY_COMPLEXITY = 1000
GRAPHQL_ENABLE_INTROSPECTION = False  # Disable in production

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'syntek_audit',           # Required for audit logs
    'syntek_sessions',        # Required for session management
    'syntek_compliance',      # Required for GDPR features
    'syntek_authentication',  # Required for auth
]

# Add GraphQL middleware
MIDDLEWARE = [
    # ... other middleware
    'syntek_graphql_core.middleware.GraphQLAuthenticationMiddleware',
]

# Configure your GraphQL endpoint (using Strawberry Django)
from django.urls import path
from strawberry.django.views import GraphQLView

urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
]
"""
