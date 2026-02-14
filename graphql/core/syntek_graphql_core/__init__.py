"""Syntek GraphQL Core - Security foundation for GraphQL modules.

Provides core security components, error handling, and utilities
shared across all Syntek GraphQL modules.
"""

__version__ = "1.0.0"

from syntek_graphql_core.errors import (
    AuthenticationError,
    ErrorCode,
    GraphQLError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ValidationError,
)
from syntek_graphql_core.extensions import (
    CaptchaValidationExtension,
    ConstantTimeResponseExtension,
    GlobalSMSRateLimitExtension,
    InputSanitisationExtension,
    OperationRateLimitExtension,
    SessionFingerprintExtension,
    SuspiciousActivityExtension,
)
from syntek_graphql_core.middleware import GraphQLAuthenticationMiddleware
from syntek_graphql_core.permissions import (
    HasPermission,
    IsAuthenticated,
    IsOrganisationOwner,
)
from syntek_graphql_core.security import (
    IntrospectionControlExtension,
    QueryComplexityLimitExtension,
    QueryDepthLimitExtension,
)
from syntek_graphql_core.utils import (
    get_authenticated_user,
    get_authorization_header,
    get_bearer_token,
    get_ip_address,
    get_request,
    get_user_agent,
    is_authenticated_user,
    require_authenticated_user,
)

__all__ = [
    # Version
    "__version__",
    # Errors
    "AuthenticationError",
    "ErrorCode",
    "GraphQLError",
    "NotFoundError",
    "PermissionError",
    "RateLimitError",
    "ValidationError",
    # Middleware
    "GraphQLAuthenticationMiddleware",
    # Permissions
    "HasPermission",
    "IsAuthenticated",
    "IsOrganisationOwner",
    # Security extensions (query structure)
    "IntrospectionControlExtension",
    "QueryComplexityLimitExtension",
    "QueryDepthLimitExtension",
    # Security extensions (operation-level)
    "CaptchaValidationExtension",
    "ConstantTimeResponseExtension",
    "GlobalSMSRateLimitExtension",
    "InputSanitisationExtension",
    "OperationRateLimitExtension",
    "SessionFingerprintExtension",
    "SuspiciousActivityExtension",
    # Utilities
    "get_authenticated_user",
    "get_authorization_header",
    "get_bearer_token",
    "get_ip_address",
    "get_request",
    "get_user_agent",
    "is_authenticated_user",
    "require_authenticated_user",
]
