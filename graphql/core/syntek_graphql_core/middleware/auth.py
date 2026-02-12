"""Authentication middleware for GraphQL API.

Extracts JWT tokens from Authorization header and authenticates users
for GraphQL requests. Integrates with syntek-security-auth TokenService.

Note: This middleware requires syntek-security-auth to be installed and configured.
"""

from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest

User = get_user_model()


class GraphQLAuthenticationMiddleware:
    """JWT authentication middleware for GraphQL.

    Extracts Bearer token from Authorization header and authenticates
    the user using TokenService from syntek-security-auth. Sets request.user
    to authenticated user or AnonymousUser.

    Example Authorization header:
        Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

    Prerequisites:
        - syntek-security-auth must be installed
        - TokenService must be available from syntek_security_auth.jwt.services
    """

    def __init__(self, get_response: Callable) -> None:
        """Initialize middleware.

        Args:
            get_response: Next middleware/view in chain
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> Any:
        """Process request to authenticate user.

        Extracts JWT token from Authorization header, verifies it,
        and sets request.user to the authenticated user.

        Args:
            request: HTTP request

        Returns:
            HTTP response from next middleware/view
        """
        # Only process GraphQL requests
        if not request.path.startswith("/graphql"):
            return self.get_response(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")  # type: ignore[attr-defined]

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

            # Import TokenService dynamically to avoid circular imports
            try:
                from syntek_security_auth.jwt.services import TokenService  # type: ignore[import]

                # Verify token and get user
                user = TokenService.verify_access_token(token)

                if user:
                    request.user = user  # type: ignore[attr-defined]
                else:
                    request.user = AnonymousUser()  # type: ignore[attr-defined]
            except (ImportError, AttributeError):
                # TokenService not available, fallback to anonymous
                request.user = AnonymousUser()  # type: ignore[attr-defined]
        else:
            # No token provided, user is anonymous
            request.user = AnonymousUser()  # type: ignore[attr-defined]

        return self.get_response(request)
