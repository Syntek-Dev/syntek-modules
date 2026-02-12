"""
GraphQL schema for minimal authentication example.

This schema provides user authentication, session management,
JWT tokens, and TOTP 2FA capabilities using Syntek GraphQL modules.
"""

import strawberry
from syntek_graphql_auth.mutations.auth import AuthMutations
from syntek_graphql_auth.mutations.session import SessionMutations
from syntek_graphql_auth.mutations.totp import TOTPMutations
from syntek_graphql_auth.queries.user import UserQueries
from syntek_graphql_core.security import (
    IntrospectionControlExtension,
    QueryComplexityLimitExtension,
    QueryDepthLimitExtension,
)


@strawberry.type
class Query(UserQueries):
    """
    Root query type for authentication operations.

    Provides queries for:
    - Current user information (me)
    - User lookup by ID
    - User listing
    """

    @strawberry.field
    def health_check(self) -> bool:
        """
        Health check endpoint for monitoring.

        Returns True if the API is operational.
        """
        return True

    @strawberry.field
    def api_version(self) -> str:
        """
        Return the API version.

        Returns:
            str: The current API version string
        """
        return "1.0.0"


@strawberry.type
class Mutation(AuthMutations, TOTPMutations, SessionMutations):
    """
    Root mutation type for authentication operations.

    Provides mutations for:
    - User registration
    - Login/logout
    - Password management (change, reset)
    - JWT token refresh
    - TOTP 2FA (enable, verify, disable)
    - Session management
    """

    pass


# Create schema with security extensions
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        # Prevent deeply nested queries (max 10 levels)
        QueryDepthLimitExtension(max_depth=10),
        # Prevent expensive queries (max 1000 complexity)
        QueryComplexityLimitExtension(max_complexity=1000),
        # Control introspection based on DEBUG setting
        IntrospectionControlExtension(),
    ],
)
