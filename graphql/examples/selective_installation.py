"""Example: Selective module installation and usage.

This example shows different installation scenarios and schema compositions.
"""

import strawberry

# Scenario 1: Minimal installation (Auth only)
"""
Install only core and auth:
    uv pip install syntek-graphql-core syntek-graphql-auth

Use in your project:
"""


def minimal_auth_schema():
    """Create a minimal schema with authentication only."""
    from syntek_graphql_auth.mutations.auth import AuthMutations
    from syntek_graphql_auth.queries.user import UserQueries
    from syntek_graphql_core.security import (
        IntrospectionControlExtension,
        QueryComplexityLimitExtension,
        QueryDepthLimitExtension,
    )

    @strawberry.type
    class Query(UserQueries):
        pass

    @strawberry.type
    class Mutation(AuthMutations):
        pass

    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[
            QueryDepthLimitExtension,
            QueryComplexityLimitExtension,
            IntrospectionControlExtension,
        ],
    )


# Scenario 2: Auth + Audit (no GDPR/Legal)
"""
Install core, auth, and audit:
    uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-audit

Use in your project:
"""


def auth_audit_schema():
    """Create schema with authentication and audit logging."""
    from syntek_graphql_audit.queries.audit import AuditQuery
    from syntek_graphql_auth.mutations.auth import AuthMutations
    from syntek_graphql_auth.queries.user import UserQueries
    from syntek_graphql_core.security import (
        IntrospectionControlExtension,
        QueryComplexityLimitExtension,
        QueryDepthLimitExtension,
    )

    @strawberry.type
    class Query(UserQueries, AuditQuery):
        pass

    @strawberry.type
    class Mutation(AuthMutations):
        pass

    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[
            QueryDepthLimitExtension,
            QueryComplexityLimitExtension,
            IntrospectionControlExtension,
        ],
    )


# Scenario 3: GDPR compliance only (with auth)
"""
Install core, auth, and compliance:
    uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-compliance

Use in your project:
"""


def compliance_schema():
    """Create schema with GDPR compliance features."""
    from syntek_graphql_auth.mutations.auth import AuthMutations
    from syntek_graphql_auth.queries.user import UserQueries
    from syntek_graphql_compliance.mutations.gdpr import GDPRMutations
    from syntek_graphql_compliance.queries.gdpr import GDPRQuery
    from syntek_graphql_core.security import (
        IntrospectionControlExtension,
        QueryComplexityLimitExtension,
        QueryDepthLimitExtension,
    )

    @strawberry.type
    class Query(UserQueries, GDPRQuery):
        pass

    @strawberry.type
    class Mutation(AuthMutations, GDPRMutations):
        pass

    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[
            QueryDepthLimitExtension,
            QueryComplexityLimitExtension,
            IntrospectionControlExtension,
        ],
    )


# Scenario 4: Custom selection (Auth + specific features)
"""
Pick and choose specific features:
    uv pip install syntek-graphql-core syntek-graphql-auth

Then import only what you need:
"""


def custom_schema():
    """Create schema with custom feature selection."""
    from syntek_graphql_auth.mutations.auth import AuthMutations
    from syntek_graphql_auth.mutations.totp import TOTPMutations  # Only 2FA
    from syntek_graphql_auth.queries.user import UserQueries
    from syntek_graphql_core.security import QueryDepthLimitExtension

    @strawberry.type
    class Query(UserQueries):
        pass

    @strawberry.type
    class Mutation(AuthMutations, TOTPMutations):
        # Only auth and 2FA mutations, no session management
        pass

    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[QueryDepthLimitExtension],  # Only depth limiting
    )


# Using standalone schema creation functions
"""
Each module provides a create_*_schema() function for quick setup:
"""


def using_standalone_schemas():
    """Use pre-configured schemas from individual modules."""
    # Auth-only schema
    from syntek_graphql_auth.schema import create_auth_schema

    auth_schema = create_auth_schema()

    # Other schema options available (choose based on your needs):
    # Audit-only schema (requires auth):
    #   from syntek_graphql_audit.schema import create_audit_schema
    #   return create_audit_schema()
    #
    # Compliance-only schema (requires auth):
    #   from syntek_graphql_compliance.schema import create_compliance_schema
    #   return create_compliance_schema()
    #
    # Core-only schema (just security extensions, no queries/mutations):
    #   from syntek_graphql_core.schema import create_core_schema
    #   return create_core_schema()

    return auth_schema  # Default to auth schema


# Installation commands for different scenarios
INSTALLATION_GUIDE = """
# Scenario 1: Minimal (Auth only)
uv pip install syntek-graphql-core syntek-graphql-auth

# Scenario 2: Auth + Audit
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-audit

# Scenario 3: Auth + GDPR/Legal
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-compliance

# Scenario 4: Full installation (all modules)
uv pip install syntek-graphql-core \\
               syntek-graphql-auth \\
               syntek-graphql-audit \\
               syntek-graphql-compliance

# Scenario 5: Development installation (with dev dependencies)
uv pip install syntek-graphql-core[dev] \\
               syntek-graphql-auth[dev] \\
               syntek-graphql-audit[dev] \\
               syntek-graphql-compliance[dev]
"""
