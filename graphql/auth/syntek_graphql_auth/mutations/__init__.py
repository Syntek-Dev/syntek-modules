"""GraphQL mutations for authentication operations."""

from syntek_graphql_auth.mutations.auth import AuthMutations
from syntek_graphql_auth.mutations.session import SessionMutation
from syntek_graphql_auth.mutations.totp import TOTPMutations

__all__ = [
    "AuthMutations",
    "SessionMutation",
    "TOTPMutations",
]
