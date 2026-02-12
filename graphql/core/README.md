# Syntek GraphQL Core

Security foundation for Syntek GraphQL modules providing core security components, error handling, and utilities shared across all GraphQL implementations.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Error Code Reference](#error-code-reference)
- [Security Considerations](#security-considerations)
- [Development](#development)
- [Testing](#testing)
- [License](#license)

---

## Overview

**syntek-graphql-core** provides the foundational security layer for all Syntek GraphQL modules. It includes:

- **Standardised Error Handling**: Consistent error codes and exceptions across GraphQL APIs
- **Permission Classes**: Authentication and authorization checks for queries/mutations
- **Security Extensions**: Query depth limiting, complexity analysis, and introspection control
- **Authentication Middleware**: JWT token extraction and verification
- **Context Utilities**: Request data access from GraphQL context
- **Type Guards**: Type-safe user authentication checks

This package is designed as a dependency for other Syntek GraphQL modules (auth, compliance, audit) and should be installed first.

## Features

- **10+ Error Codes**: Standardised error codes for authentication, validation, permissions, rate limiting, and server errors
- **Type-Safe Exceptions**: Custom exception classes with error codes and context data
- **Permission Classes**: `IsAuthenticated`, `HasPermission`, `IsOrganisationOwner`
- **Query Depth Limiting**: Prevent deeply nested queries (configurable, default 10 levels)
- **Query Complexity Analysis**: Detect expensive queries (configurable, default 1000)
- **Introspection Control**: Disable GraphQL schema introspection in production
- **JWT Authentication Middleware**: Automatic Bearer token extraction and verification
- **Request Context Utilities**: Easy access to IP address, user agent, tokens from GraphQL context
- **Type Utilities**: Type guards for authenticated users with proper mypy/pyright support
- **Production-Ready**: Tested, documented, with comprehensive error handling

## Installation

### Using uv (Recommended)

```bash
uv pip install syntek-graphql-core
```

### Using pip

```bash
pip install syntek-graphql-core
```

### Poetry

```toml
[tool.poetry.dependencies]
syntek-graphql-core = "^1.0.0"
```

## Quick Start

### 1. Add to Django Settings

```python
# settings.py

INSTALLED_APPS = [
    # Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # Strawberry GraphQL
    'strawberry.django',
    # Syntek modules (in order)
    'syntek_graphql_core',
    'syntek_graphql_auth',  # Other GraphQL modules
]

# GraphQL configuration
GRAPHQL_MAX_QUERY_DEPTH = 10  # Maximum nesting levels
GRAPHQL_MAX_QUERY_COMPLEXITY = 1000  # Maximum complexity score
GRAPHQL_ENABLE_INTROSPECTION = DEBUG  # Disable in production
```

### 2. Add Middleware

```python
# settings.py

MIDDLEWARE = [
    # Django middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Syntek GraphQL authentication
    'syntek_graphql_core.middleware.GraphQLAuthenticationMiddleware',
]
```

### 3. Configure GraphQL Schema

```python
# schema.py
import strawberry
from syntek_graphql_core import (
    QueryDepthLimitExtension,
    QueryComplexityLimitExtension,
    IntrospectionControlExtension,
    IsAuthenticated,
)

@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def current_user(self, info) -> str:
        """Get currently authenticated user."""
        request = info.context["request"]
        return request.user.username

schema = strawberry.Schema(
    query=Query,
    extensions=[
        QueryDepthLimitExtension,
        QueryComplexityLimitExtension,
        IntrospectionControlExtension,
    ],
)
```

### 4. Add to URLs

```python
# urls.py
from django.urls import path
from strawberry.django.views import GraphQLView
from myapp.schema import schema

urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
]
```

---

## Configuration Reference

All configuration uses Django settings with `GRAPHQL_` prefix.

| Setting                        | Type | Default | Description                                                 |
| ------------------------------ | ---- | ------- | ----------------------------------------------------------- |
| `GRAPHQL_MAX_QUERY_DEPTH`      | int  | 10      | Maximum nesting depth for GraphQL queries                   |
| `GRAPHQL_MAX_QUERY_COMPLEXITY` | int  | 1000    | Maximum complexity score for queries                        |
| `GRAPHQL_ENABLE_INTROSPECTION` | bool | False   | Enable GraphQL schema introspection (auto-enabled in DEBUG) |

### Example Configuration

```python
# settings.py

# Strict security settings for production
if not DEBUG:
    GRAPHQL_MAX_QUERY_DEPTH = 8
    GRAPHQL_MAX_QUERY_COMPLEXITY = 500
    GRAPHQL_ENABLE_INTROSPECTION = False
else:
    # Relaxed for development
    GRAPHQL_MAX_QUERY_DEPTH = 15
    GRAPHQL_MAX_QUERY_COMPLEXITY = 2000
    GRAPHQL_ENABLE_INTROSPECTION = True
```

---

## Usage Examples

### Using Error Classes

Raise standardised errors with consistent error codes:

```python
from syntek_graphql_core import (
    AuthenticationError,
    ValidationError,
    PermissionError,
    NotFoundError,
    RateLimitError,
    ErrorCode,
)

# Authentication error
raise AuthenticationError(
    code=ErrorCode.INVALID_CREDENTIALS,
    message="Invalid email or password"
)

# Validation error with context
raise ValidationError(
    code=ErrorCode.EMAIL_ALREADY_EXISTS,
    extensions={"email": "user@example.com"}
)

# Permission error
raise PermissionError(
    code=ErrorCode.NOT_AUTHENTICATED,
    message="You must be logged in to access this resource"
)

# Not found error
raise NotFoundError(
    code=ErrorCode.USER_NOT_FOUND,
    message="User with ID 123 not found"
)

# Rate limit error
raise RateLimitError(
    code=ErrorCode.PASSWORD_RESET_RATE_LIMIT_EXCEEDED,
    message="Please try again in 1 hour"
)
```

### Using Permission Classes

Protect queries and mutations with permission classes:

```python
import strawberry
from syntek_graphql_core import (
    IsAuthenticated,
    HasPermission,
    IsOrganisationOwner,
)

@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def profile(self, info) -> str:
        """Get authenticated user's profile (requires login)."""
        request = info.context["request"]
        return f"Profile: {request.user.username}"

    @strawberry.field(permission_classes=[HasPermission("users.view_user")])
    def users(self, info) -> list[str]:
        """List users (requires specific permission)."""
        return ["alice", "bob", "charlie"]

    @strawberry.field(permission_classes=[IsOrganisationOwner])
    def organisation_settings(self, info) -> dict:
        """Get organisation settings (requires org owner role)."""
        return {"theme": "dark", "language": "en"}
```

### Using Security Extensions

Security extensions are automatically applied when added to the schema:

```python
import strawberry
from syntek_graphql_core import (
    QueryDepthLimitExtension,
    QueryComplexityLimitExtension,
    IntrospectionControlExtension,
)

schema = strawberry.Schema(
    query=Query,
    extensions=[
        QueryDepthLimitExtension,
        QueryComplexityLimitExtension,
        IntrospectionControlExtension,
    ],
)
```

**Result**: Queries will be automatically validated before execution:

```graphql
# ✅ Valid: depth = 2
query {
  user {
    posts {
      title
    }
  }
}

# ❌ Blocked: depth > max (exceeds limit)
query {
  user {
    posts {
      comments {
        author {
          posts {
            comments {
              author {
                posts {
                  # ... infinitely nested
                }
              }
            }
          }
        }
      }
    }
  }
}

# ❌ Blocked in production: introspection query
query {
  __schema {
    types {
      name
    }
  }
}
```

### Using Context Utilities

Access request data safely from GraphQL context:

```python
import strawberry
from syntek_graphql_core.utils import (
    get_request,
    get_ip_address,
    get_user_agent,
    get_authorization_header,
    get_bearer_token,
)

@strawberry.type
class Query:
    @strawberry.field
    def debug_info(self, info) -> str:
        """Get request debug information."""
        request = get_request(info)
        ip = get_ip_address(info)
        user_agent = get_user_agent(info)
        token = get_bearer_token(info)

        return f"IP: {ip}, User-Agent: {user_agent}, Token: {token[:20]}..."
```

### Using Type Guards

Safely access authenticated user with proper type checking:

```python
from django.http import HttpRequest
from syntek_graphql_core.utils import (
    is_authenticated_user,
    get_authenticated_user,
    require_authenticated_user,
)

def process_user(request: HttpRequest) -> None:
    # Type guard: narrows type from generic to concrete User
    if is_authenticated_user(request.user):
        print(f"User email: {request.user.email}")  # Type-safe
        print(f"User groups: {request.user.groups.all()}")

    # Optional retrieval
    user = get_authenticated_user(request)
    if user:
        print(f"Authenticated: {user.username}")

    # Required retrieval (raises if not authenticated)
    try:
        user = require_authenticated_user(request)
        print(f"User: {user.email}")
    except ValueError:
        print("No authenticated user")
```

### Custom Permission Classes

Extend permission classes for custom logic:

```python
from typing import Any
from strawberry.permission import BasePermission
from strawberry.types import Info
from syntek_graphql_core.utils.context import get_request

class IsPremiumUser(BasePermission):
    """Custom permission: user has premium subscription."""

    message = "Premium subscription required"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        request = get_request(info)
        user = request.user
        if not user.is_authenticated:
            return False
        return hasattr(user, 'profile') and user.profile.is_premium

# Usage in schema
@strawberry.field(permission_classes=[IsPremiumUser])
def premium_feature(self, info) -> str:
    return "Premium content"
```

---

## API Reference

### Error Classes

#### `ErrorCode` (Enum)

Standardised error codes for all GraphQL operations.

**Authentication Errors:**

- `INVALID_CREDENTIALS` - Invalid email or password
- `EMAIL_NOT_VERIFIED` - Email address not verified
- `ACCOUNT_LOCKED` - Account locked due to too many failed attempts
- `ACCOUNT_DISABLED` - Account has been disabled
- `TOKEN_EXPIRED` - Authentication token expired
- `TOKEN_INVALID` - Invalid authentication token
- `TWO_FACTOR_REQUIRED` - Two-factor authentication required
- `INVALID_TOTP_CODE` - Invalid 2FA code
- `CAPTCHA_FAILED` - CAPTCHA verification failed

**Validation Errors:**

- `INVALID_INPUT` - Invalid input data
- `EMAIL_ALREADY_EXISTS` - Email already registered
- `INVALID_EMAIL_FORMAT` - Invalid email format
- `PASSWORD_TOO_WEAK` - Password doesn't meet requirements
- `PASSWORD_IN_HISTORY` - Cannot reuse recent password
- `ORGANISATION_NOT_FOUND` - Organisation not found

**Permission Errors:**

- `PERMISSION_DENIED` - Access denied
- `NOT_AUTHENTICATED` - Authentication required
- `NOT_ORGANISATION_OWNER` - Organisation owner role required
- `ORGANISATION_MISMATCH` - Cross-organisation access denied

**Not Found Errors:**

- `USER_NOT_FOUND` - User not found
- `RESOURCE_NOT_FOUND` - Resource not found

**Rate Limit Errors:**

- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded
- `TOO_MANY_REQUESTS` - Too many requests
- `PASSWORD_RESET_RATE_LIMIT_EXCEEDED` - Password reset rate limited

**Server Errors:**

- `INTERNAL_ERROR` - Internal server error
- `DATABASE_ERROR` - Database operation failed

#### `GraphQLError` (Base Exception)

Base exception for all GraphQL errors.

```python
class GraphQLError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """
        Args:
            code: Error code from ErrorCode enum
            message: Optional custom message (uses default if not provided)
            extensions: Optional context data to include in response
        """
```

#### `AuthenticationError`

Exception for authentication failures.

```python
raise AuthenticationError(
    code=ErrorCode.TOKEN_EXPIRED,
    extensions={"expires_in": 3600}
)
```

#### `ValidationError`

Exception for input validation failures.

```python
raise ValidationError(
    code=ErrorCode.EMAIL_ALREADY_EXISTS,
    extensions={"field": "email", "value": "user@example.com"}
)
```

#### `PermissionError`

Exception for authorization failures.

```python
raise PermissionError(
    code=ErrorCode.NOT_ORGANISATION_OWNER
)
```

#### `NotFoundError`

Exception for resource not found errors.

```python
raise NotFoundError(
    code=ErrorCode.USER_NOT_FOUND,
    extensions={"user_id": 123}
)
```

#### `RateLimitError`

Exception for rate limit exceeded errors.

```python
raise RateLimitError(
    code=ErrorCode.TOO_MANY_REQUESTS,
    extensions={"retry_after": 60}
)
```

### Permission Classes

#### `IsAuthenticated`

Requires user to be authenticated.

```python
@strawberry.field(permission_classes=[IsAuthenticated])
def protected_query(self, info) -> str:
    return "Only authenticated users can see this"
```

#### `HasPermission(permission: str)`

Requires specific Django permission.

```python
@strawberry.field(permission_classes=[HasPermission("users.view_user")])
def users_list(self, info) -> list[str]:
    return ["alice", "bob"]
```

#### `IsOrganisationOwner`

Requires user to be in "Organisation Owner" group.

```python
@strawberry.field(permission_classes=[IsOrganisationOwner])
def org_settings(self, info) -> dict:
    return {"name": "Acme Corp"}
```

### Security Extensions

#### `QueryDepthLimitExtension`

Prevents deeply nested queries. Configured via `GRAPHQL_MAX_QUERY_DEPTH` (default: 10).

```python
# Configuration
GRAPHQL_MAX_QUERY_DEPTH = 10  # Maximum nesting levels

# Add to schema
extensions=[QueryDepthLimitExtension]
```

#### `QueryComplexityLimitExtension`

Detects expensive queries by complexity scoring. Configured via `GRAPHQL_MAX_QUERY_COMPLEXITY` (default: 1000).

Complexity calculation:

- Each field = 1 complexity
- List fields (e.g., `users`) = 1 × 10 multiplier
- Nested complexity = parent complexity × field multiplier

```python
# Configuration
GRAPHQL_MAX_QUERY_COMPLEXITY = 1000

# Add to schema
extensions=[QueryComplexityLimitExtension]
```

#### `IntrospectionControlExtension`

Disables GraphQL introspection in production. Always enabled in DEBUG mode or if `GRAPHQL_ENABLE_INTROSPECTION = True`.

```python
# Configuration
GRAPHQL_ENABLE_INTROSPECTION = DEBUG

# Add to schema
extensions=[IntrospectionControlExtension]
```

### Authentication Middleware

#### `GraphQLAuthenticationMiddleware`

Extracts Bearer token from Authorization header and authenticates user via JWT.

**Prerequisites:**

- `syntek-security-auth` package must be installed
- TokenService must be available from `syntek_security_auth.jwt.services`

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'syntek_graphql_core.middleware.GraphQLAuthenticationMiddleware',
]
```

**How it works:**

1. Extracts Authorization header
2. Verifies Bearer token using TokenService
3. Sets `request.user` to authenticated user or AnonymousUser
4. Passes request to next middleware

### Context Utilities

#### `get_request(info: Info) -> HttpRequest`

Extract Django request from GraphQL Info context.

```python
from syntek_graphql_core.utils import get_request

@strawberry.field
def my_field(self, info) -> str:
    request = get_request(info)
    return request.user.username
```

#### `get_ip_address(info: Info) -> str`

Get client IP address, handling reverse proxies (X-Forwarded-For header).

```python
from syntek_graphql_core.utils import get_ip_address

@strawberry.field
def debug_ip(self, info) -> str:
    ip = get_ip_address(info)
    return f"Your IP: {ip}"
```

#### `get_user_agent(info: Info) -> str`

Get User-Agent string from request headers.

```python
from syntek_graphql_core.utils import get_user_agent

@strawberry.field
def debug_agent(self, info) -> str:
    ua = get_user_agent(info)
    return f"Your browser: {ua}"
```

#### `get_authorization_header(info: Info) -> str`

Get full Authorization header value.

```python
from syntek_graphql_core.utils import get_authorization_header

@strawberry.field
def debug_auth(self, info) -> str:
    auth = get_authorization_header(info)
    return f"Auth header present: {bool(auth)}"
```

#### `get_bearer_token(info: Info) -> str`

Extract Bearer token from Authorization header (removes "Bearer " prefix).

```python
from syntek_graphql_core.utils import get_bearer_token

@strawberry.field
def debug_token(self, info) -> str:
    token = get_bearer_token(info)
    return f"Token (first 20 chars): {token[:20]}"
```

### Type Utilities

#### `is_authenticated_user(user: object) -> TypeGuard[AbstractBaseUser]`

Type guard to check if user is an authenticated User instance (not AnonymousUser).

```python
from syntek_graphql_core.utils import is_authenticated_user

user = request.user
if is_authenticated_user(user):
    # user is now typed as authenticated user
    print(user.email)  # type-safe
```

#### `get_authenticated_user(request: HttpRequest) -> AbstractBaseUser | None`

Get authenticated user from request with proper typing.

```python
from syntek_graphql_core.utils import get_authenticated_user

user = get_authenticated_user(request)
if user:
    print(user.email)
```

#### `require_authenticated_user(request: HttpRequest) -> AbstractBaseUser`

Get authenticated user or raise ValueError.

```python
from syntek_graphql_core.utils import require_authenticated_user

try:
    user = require_authenticated_user(request)
    print(user.email)
except ValueError:
    print("User not authenticated")
```

---

## Error Code Reference

### Complete Error Code Mapping

| Code                                 | Message                                     | Category   | HTTP Status |
| ------------------------------------ | ------------------------------------------- | ---------- | ----------- |
| `INVALID_CREDENTIALS`                | Invalid email or password                   | Auth       | 401         |
| `EMAIL_NOT_VERIFIED`                 | Please verify email before login            | Auth       | 401         |
| `ACCOUNT_LOCKED`                     | Account locked due to failed attempts       | Auth       | 401         |
| `ACCOUNT_DISABLED`                   | Account has been disabled                   | Auth       | 401         |
| `TOKEN_EXPIRED`                      | Authentication token has expired            | Auth       | 401         |
| `TOKEN_INVALID`                      | Invalid authentication token                | Auth       | 401         |
| `TWO_FACTOR_REQUIRED`                | Two-factor authentication code required     | Auth       | 401         |
| `INVALID_TOTP_CODE`                  | Invalid two-factor authentication code      | Auth       | 401         |
| `CAPTCHA_FAILED`                     | CAPTCHA verification failed                 | Auth       | 400         |
| `EMAIL_ALREADY_EXISTS`               | Email address is already registered         | Validation | 400         |
| `INVALID_EMAIL_FORMAT`               | Invalid email address format                | Validation | 400         |
| `PASSWORD_TOO_WEAK`                  | Password doesn't meet security requirements | Validation | 400         |
| `PASSWORD_IN_HISTORY`                | Cannot reuse a recent password              | Validation | 400         |
| `INVALID_INPUT`                      | Invalid input data                          | Validation | 400         |
| `ORGANISATION_NOT_FOUND`             | Organisation not found                      | Validation | 404         |
| `PERMISSION_DENIED`                  | You do not have permission                  | Permission | 403         |
| `NOT_AUTHENTICATED`                  | Authentication required                     | Permission | 401         |
| `NOT_ORGANISATION_OWNER`             | Organisation owner role required            | Permission | 403         |
| `ORGANISATION_MISMATCH`              | Cannot access from different org            | Permission | 403         |
| `USER_NOT_FOUND`                     | User not found                              | Not Found  | 404         |
| `RESOURCE_NOT_FOUND`                 | Requested resource not found                | Not Found  | 404         |
| `RATE_LIMIT_EXCEEDED`                | Rate limit exceeded, try later              | Rate Limit | 429         |
| `TOO_MANY_REQUESTS`                  | Too many requests, please slow down         | Rate Limit | 429         |
| `PASSWORD_RESET_RATE_LIMIT_EXCEEDED` | Too many resets, try in 1 hour              | Rate Limit | 429         |
| `INTERNAL_ERROR`                     | An internal error occurred                  | Server     | 500         |
| `DATABASE_ERROR`                     | Database operation failed                   | Server     | 500         |

### Handling Errors in Client Code

```python
from syntek_graphql_core import ErrorCode

try:
    # Some GraphQL operation
    pass
except Exception as e:
    if hasattr(e, 'code'):
        if e.code == ErrorCode.NOT_AUTHENTICATED:
            # Handle auth required
            redirect_to_login()
        elif e.code == ErrorCode.RATE_LIMIT_EXCEEDED:
            # Handle rate limit
            show_retry_message()
        elif e.code == ErrorCode.PERMISSION_DENIED:
            # Handle permission denied
            show_forbidden_message()
```

---

## Security Considerations

### 1. Query Depth Limiting

Prevent Denial-of-Service attacks through deeply nested queries:

```python
# Configure appropriate limits
GRAPHQL_MAX_QUERY_DEPTH = 10  # Adjust based on schema complexity
```

### 2. Query Complexity Analysis

Detect expensive queries that could impact performance:

```python
# Set complexity limits based on database load capacity
GRAPHQL_MAX_QUERY_COMPLEXITY = 1000
```

### 3. Introspection Control

Disable schema introspection in production to prevent information disclosure:

```python
# Production environment
GRAPHQL_ENABLE_INTROSPECTION = False

# Development environment (auto-enabled in DEBUG mode)
DEBUG = True
```

### 4. Authentication Middleware

Always enable JWT authentication middleware for GraphQL endpoints:

```python
MIDDLEWARE = [
    'syntek_graphql_core.middleware.GraphQLAuthenticationMiddleware',
]
```

### 5. Permission Checks

Always use permission classes on sensitive fields:

```python
@strawberry.field(permission_classes=[IsAuthenticated, HasPermission("users.edit_user")])
def edit_user(self, info) -> bool:
    return True
```

### 6. Error Messages

Avoid exposing sensitive information in error messages:

```python
# Good: Generic error message
raise AuthenticationError(ErrorCode.INVALID_CREDENTIALS)

# Bad: Leaks information
raise AuthenticationError(message="Email 'admin@example.com' not found")
```

### 7. Rate Limiting

Combine with rate limiting middleware to protect mutations:

```python
# Add rate limiting middleware
MIDDLEWARE = [
    'syntek_security_core.middleware.RateLimitingMiddleware',
]
```

### 8. Logging

All security events are logged with context but without sensitive data:

```python
import logging

logger = logging.getLogger('syntek_graphql_core')

# Logs include query depth/complexity violations with details
# but not user credentials or tokens
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules/graphql/core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=syntek_graphql_core

# Run specific test file
pytest tests/test_errors.py

# Run specific test
pytest tests/test_errors.py::test_authentication_error
```

### Code Quality

```bash
# Type checking with mypy
mypy syntek_graphql_core

# Linting with ruff
ruff check syntek_graphql_core

# Format code with ruff
ruff format syntek_graphql_core

# Check imports
ruff check --select I syntek_graphql_core
```

### Project Structure

```
graphql/core/
├── syntek_graphql_core/
│   ├── __init__.py              # Public API exports
│   ├── errors.py                # Error codes and exceptions
│   ├── permissions.py           # Permission classes
│   ├── security.py              # Security extensions
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py              # JWT authentication middleware
│   └── utils/
│       ├── __init__.py
│       ├── context.py           # Request context helpers
│       └── typing.py            # Type guards for authentication
├── tests/
│   ├── conftest.py              # Pytest configuration
│   └── test_*.py                # Test files
├── README.md                    # This file
├── LICENSE                      # MIT License
├── pyproject.toml               # Project metadata
└── MANIFEST.in                  # Package manifest
```

---

## Testing

### Test Coverage

All modules have comprehensive test coverage including:

- Error code enumeration and messages
- Permission class checks
- Security extension validation
- Authentication middleware
- Context utility functions
- Type guard validation

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=syntek_graphql_core --cov-report=html

# Run tests matching pattern
pytest -k "test_error" -v

# Run specific test file
pytest tests/test_permissions.py -v
```

### Example Test

```python
import pytest
from syntek_graphql_core import ErrorCode, AuthenticationError

def test_authentication_error():
    """Test AuthenticationError with error code."""
    error = AuthenticationError(
        code=ErrorCode.INVALID_CREDENTIALS,
        extensions={"attempt": 1}
    )
    assert error.code == ErrorCode.INVALID_CREDENTIALS
    assert error.extensions["code"] == "INVALID_CREDENTIALS"
    assert error.extensions["attempt"] == 1
```

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues, questions, or contributions:

- **Issues**: [GitHub Issues](https://github.com/syntek/syntek-modules/issues)
- **Documentation**: [Syntek Docs](https://docs.syntek.dev/graphql/core)
- **Repository**: [GitHub Repository](https://github.com/syntek/syntek-modules)

---

## Related Packages

- **syntek-graphql-auth**: Authentication and authorization queries/mutations
- **syntek-graphql-compliance**: GDPR and legal compliance features
- **syntek-graphql-audit**: Audit logging and compliance tracking
- **syntek-security-auth**: JWT and token management (required by middleware)
- **syntek-security-core**: HTTP security headers and rate limiting

---

**Last Updated**: 2025-02-04
**Version**: 1.0.0
**Maintainer**: Syntek Development Team
