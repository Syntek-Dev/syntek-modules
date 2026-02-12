"""GraphQL schema for authentication operations.

This module provides a standalone schema creation function for
authentication, TOTP 2FA, and session management.
"""

import strawberry
from syntek_graphql_core.security import (  # type: ignore[import]
    IntrospectionControlExtension,
    QueryComplexityLimitExtension,
    QueryDepthLimitExtension,
)

from syntek_graphql_auth.mutations import AuthMutations, SessionMutation, TOTPMutations
from syntek_graphql_auth.mutations.totp import TOTPQueries
from syntek_graphql_auth.queries import UserQueries


@strawberry.type
class AuthQuery(UserQueries, TOTPQueries):
    """Combined authentication query root."""

    pass


@strawberry.type
class AuthMutation(AuthMutations, TOTPMutations, SessionMutation):
    """Combined authentication mutation root."""

    pass


def create_auth_schema() -> strawberry.Schema:
    """Create a standalone authentication schema.

    Returns:
        Strawberry schema with authentication and session operations.
    """
    return strawberry.Schema(
        query=AuthQuery,
        mutation=AuthMutation,
        extensions=[
            QueryDepthLimitExtension,
            QueryComplexityLimitExtension,
            IntrospectionControlExtension,
        ],
    )
