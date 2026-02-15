"""GraphQL queries for authentication operations."""

from syntek_graphql_auth.queries.config import AuthConfigQueries
from syntek_graphql_auth.queries.user import UserQueries

__all__ = [
    "AuthConfigQueries",
    "UserQueries",
]
