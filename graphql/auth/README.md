# Syntek GraphQL Auth

GraphQL authentication and authorization layer for Syntek applications with JWT, sessions, TOTP/2FA, and advanced security features.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Security Considerations](#security-considerations)
- [Development](#development)
- [Testing](#testing)
- [Migration from v1.x](#migration-from-v1x)
- [License](#license)

---

## Overview

**syntek-graphql-auth** provides a complete authentication and authorization GraphQL API layer for Django applications. Built on Strawberry GraphQL, it integrates seamlessly with Syntek's backend authentication modules to provide:

- **User Registration**: Email verification, password strength validation, organisation assignment
- **Authentication**: JWT-based login with refresh tokens, session management
- **Two-Factor Authentication**: TOTP (Time-based One-Time Password) with backup codes
- **Password Management**: Reset, change, history tracking
- **Session Control**: Concurrent session limiting, device tracking, session termination
- **User Queries**: Profile access, session listing, organisation-aware queries

This module is part of Syntek's modular GraphQL architecture and depends on `syntek-graphql-core` for error handling, permissions, and security extensions.

## Features

### Authentication

- ✅ Email + password registration with verification
- ✅ JWT access and refresh tokens
- ✅ Email verification workflow
- ✅ Password strength validation
- ✅ Password history tracking (prevent reuse)
- ✅ Login attempt rate limiting
- ✅ Account lockout protection
- ✅ CAPTCHA support

### Two-Factor Authentication

- ✅ TOTP setup with QR code generation
- ✅ Backup code generation (10 single-use codes)
- ✅ 2FA enforcement policies
- ✅ Device remember functionality
- ✅ 2FA disable with password confirmation

### Session Management

- ✅ Concurrent session limiting
- ✅ Device and location tracking
- ✅ Session listing and termination
- ✅ Automatic token rotation
- ✅ Session timeout configuration

### Password Management

- ✅ Secure password reset via email
- ✅ Password change with old password verification
- ✅ Password history enforcement
- ✅ Common password checking
- ✅ Configurable complexity requirements

### User Queries

- ✅ Current user profile
- ✅ Active sessions listing
- ✅ Organisation-scoped queries
- ✅ Permission-based access control

## Installation

### Using uv (Recommended)

```bash
uv pip install syntek-graphql-core syntek-graphql-auth
```

### Using pip

```bash
pip install syntek-graphql-core syntek-graphql-auth
```

### Poetry

```toml
[tool.poetry.dependencies]
syntek-graphql-core = "^1.0.0"
syntek-graphql-auth = "^2.0.0"
```

## Quick Start

### 1. Install Backend Dependencies

This GraphQL module requires backend authentication modules:

```bash
uv pip install syntek-authentication syntek-sessions syntek-jwt syntek-mfa
```

### 2. Add to Django Settings

```python
# settings.py

INSTALLED_APPS = [
    # Django core
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    # Strawberry GraphQL
    'strawberry.django',

    # Syntek backend modules (required)
    'syntek_authentication',
    'syntek_sessions',
    'syntek_jwt',
    'syntek_mfa',

    # Syntek GraphQL modules
    'syntek_graphql_core',
    'syntek_graphql_auth',
]

# Authentication middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'syntek_graphql_core.middleware.GraphQLAuthenticationMiddleware',
]
```

### 3. Configure Authentication

```python
# settings.py

# GraphQL Core Configuration
GRAPHQL_MAX_QUERY_DEPTH = 10
GRAPHQL_MAX_QUERY_COMPLEXITY = 1000
GRAPHQL_ENABLE_INTROSPECTION = DEBUG

# Authentication Configuration
SYNTEK_AUTHENTICATION = {
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_NUMBERS': True,
    'PASSWORD_REQUIRE_SPECIAL': True,
    'PASSWORD_HISTORY_COUNT': 5,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 minutes
}

# Session Configuration
SYNTEK_SESSIONS = {
    'MAX_CONCURRENT_SESSIONS': 3,
    'SESSION_TIMEOUT': 1800,  # 30 minutes
    'TRACK_DEVICE_INFO': True,
}

# JWT Configuration
SYNTEK_JWT = {
    'ACCESS_TOKEN_LIFETIME': 900,   # 15 minutes
    'REFRESH_TOKEN_LIFETIME': 86400,  # 24 hours
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
}

# MFA Configuration
SYNTEK_MFA = {
    'TOTP_ISSUER': 'Syntek Platform',
    'TOTP_DIGITS': 6,
    'BACKUP_CODE_COUNT': 10,
}
```

### 4. Create GraphQL Schema

```python
# schema.py
import strawberry
from syntek_graphql_core import (
    QueryDepthLimitExtension,
    QueryComplexityLimitExtension,
    IntrospectionControlExtension,
)
from syntek_graphql_auth.mutations.auth import AuthMutations
from syntek_graphql_auth.mutations.totp import TOTPMutations
from syntek_graphql_auth.mutations.session import SessionMutations
from syntek_graphql_auth.queries.user import UserQueries

@strawberry.type
class Query(UserQueries):
    """GraphQL query root."""
    pass

@strawberry.type
class Mutation(AuthMutations, TOTPMutations, SessionMutations):
    """GraphQL mutation root."""
    pass

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimitExtension,
        QueryComplexityLimitExtension,
        IntrospectionControlExtension,
    ],
)
```

### 5. Add GraphQL Endpoint

```python
# urls.py
from django.urls import path
from strawberry.django.views import GraphQLView
from myapp.schema import schema

urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
]
```

### 6. Run Migrations

```bash
python manage.py migrate
```

---

## Configuration Reference

### Authentication Settings

Configure via `SYNTEK_AUTHENTICATION` in Django settings:

| Setting                       | Type | Default | Description                             |
| ----------------------------- | ---- | ------- | --------------------------------------- |
| `PASSWORD_MIN_LENGTH`         | int  | 12      | Minimum password length                 |
| `PASSWORD_REQUIRE_UPPERCASE`  | bool | True    | Require uppercase letters               |
| `PASSWORD_REQUIRE_LOWERCASE`  | bool | True    | Require lowercase letters               |
| `PASSWORD_REQUIRE_NUMBERS`    | bool | True    | Require numeric digits                  |
| `PASSWORD_REQUIRE_SPECIAL`    | bool | True    | Require special characters              |
| `PASSWORD_HISTORY_COUNT`      | int  | 5       | Number of previous passwords to check   |
| `CHECK_COMMON_PASSWORDS`      | bool | True    | Check against common password list      |
| `MAX_LOGIN_ATTEMPTS`          | int  | 5       | Failed login attempts before lockout    |
| `LOCKOUT_DURATION`            | int  | 300     | Account lockout duration in seconds     |
| `EMAIL_VERIFICATION_REQUIRED` | bool | True    | Require email verification before login |
| `CAPTCHA_ENABLED`             | bool | False   | Enable CAPTCHA on registration/login    |

### Session Settings

Configure via `SYNTEK_SESSIONS` in Django settings:

| Setting                        | Type | Default | Description                            |
| ------------------------------ | ---- | ------- | -------------------------------------- |
| `MAX_CONCURRENT_SESSIONS`      | int  | 3       | Maximum concurrent active sessions     |
| `SESSION_TIMEOUT`              | int  | 1800    | Inactivity timeout in seconds (30 min) |
| `SESSION_ABSOLUTE_TIMEOUT`     | int  | 43200   | Absolute timeout in seconds (12 hours) |
| `TRACK_DEVICE_INFO`            | bool | True    | Track device and browser information   |
| `TRACK_LOCATION`               | bool | True    | Track IP-based location                |
| `TERMINATE_ON_PASSWORD_CHANGE` | bool | True    | End other sessions on password change  |

### JWT Settings

Configure via `SYNTEK_JWT` in Django settings:

| Setting                  | Type | Default | Description                                  |
| ------------------------ | ---- | ------- | -------------------------------------------- |
| `ACCESS_TOKEN_LIFETIME`  | int  | 900     | Access token lifetime in seconds (15 min)    |
| `REFRESH_TOKEN_LIFETIME` | int  | 86400   | Refresh token lifetime in seconds (24 hours) |
| `ROTATE_REFRESH_TOKENS`  | bool | True    | Issue new refresh token on refresh           |
| `ALGORITHM`              | str  | 'HS256' | JWT signing algorithm                        |
| `AUDIENCE`               | str  | None    | JWT audience claim                           |
| `ISSUER`                 | str  | None    | JWT issuer claim                             |

### MFA Settings

Configure via `SYNTEK_MFA` in Django settings:

| Setting              | Type | Default  | Description                               |
| -------------------- | ---- | -------- | ----------------------------------------- |
| `TOTP_ISSUER`        | str  | 'Syntek' | TOTP issuer name (shown in authenticator) |
| `TOTP_DIGITS`        | int  | 6        | TOTP code length                          |
| `TOTP_INTERVAL`      | int  | 30       | TOTP time step in seconds                 |
| `BACKUP_CODE_COUNT`  | int  | 10       | Number of backup codes to generate        |
| `BACKUP_CODE_LENGTH` | int  | 8        | Backup code length                        |
| `ENFORCE_2FA`        | bool | False    | Require 2FA for all users                 |

---

## Usage Examples

### Registration

```graphql
mutation Register {
  register(
    email: "user@example.com"
    password: "SecureP@ssw0rd123"
    firstName: "John"
    lastName: "Doe"
    organisationId: "org_123"
  ) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      emailVerified
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "register": {
      "success": true,
      "message": "Registration successful. Please check your email to verify your account.",
      "user": {
        "id": "user_456",
        "email": "user@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "emailVerified": false
      }
    }
  }
}
```

### Login

```graphql
mutation Login {
  login(email: "user@example.com", password: "SecureP@ssw0rd123") {
    success
    accessToken
    refreshToken
    user {
      id
      email
      emailVerified
      totpEnabled
    }
  }
}
```

**Response (without 2FA):**

```json
{
  "data": {
    "login": {
      "success": true,
      "accessToken": "eyJhbGc...",
      "refreshToken": "eyJhbGc...",
      "user": {
        "id": "user_456",
        "email": "user@example.com",
        "emailVerified": true,
        "totpEnabled": false
      }
    }
  }
}
```

**Response (2FA required):**

```json
{
  "data": {
    "login": {
      "success": false,
      "accessToken": null,
      "refreshToken": null,
      "user": null
    }
  },
  "errors": [
    {
      "message": "Two-factor authentication code required",
      "extensions": {
        "code": "TWO_FACTOR_REQUIRED"
      }
    }
  ]
}
```

### Login with 2FA

```graphql
mutation LoginWith2FA {
  login(
    email: "user@example.com"
    password: "SecureP@ssw0rd123"
    totpCode: "123456"
  ) {
    success
    accessToken
    refreshToken
  }
}
```

### Setup TOTP (2FA)

```graphql
mutation SetupTOTP {
  setupTotp {
    success
    secret
    qrCodeUrl
    backupCodes
  }
}
```

**Response:**

```json
{
  "data": {
    "setupTotp": {
      "success": true,
      "secret": "JBSWY3DPEHPK3PXP",
      "qrCodeUrl": "otpauth://totp/Syntek:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Syntek",
      "backupCodes": [
        "a8f3-9d2e",
        "b7c1-4e8f",
        "c9d2-5a6b",
        ...
      ]
    }
  }
}
```

### Verify TOTP

```graphql
mutation VerifyTOTP {
  verifyTotp(code: "123456") {
    success
    message
  }
}
```

### Password Reset Request

```graphql
mutation RequestPasswordReset {
  requestPasswordReset(email: "user@example.com") {
    success
    message
  }
}
```

### Password Reset Confirm

```graphql
mutation ResetPassword {
  resetPassword(
    token: "reset_token_here"
    newPassword: "NewSecureP@ssw0rd456"
  ) {
    success
    message
  }
}
```

### Change Password

```graphql
mutation ChangePassword {
  changePassword(
    oldPassword: "SecureP@ssw0rd123"
    newPassword: "NewSecureP@ssw0rd456"
  ) {
    success
    message
  }
}
```

### Get Current User

```graphql
query CurrentUser {
  currentUser {
    id
    email
    firstName
    lastName
    emailVerified
    totpEnabled
    organisation {
      id
      name
    }
  }
}
```

### List Active Sessions

```graphql
query ActiveSessions {
  activeSessions {
    id
    deviceName
    browser
    location
    ipAddress
    lastActivity
    isCurrent
  }
}
```

### Terminate Session

```graphql
mutation TerminateSession {
  terminateSession(sessionId: "session_789") {
    success
    message
  }
}
```

### Refresh Token

```graphql
mutation RefreshToken {
  refreshToken(refreshToken: "eyJhbGc...") {
    success
    accessToken
    refreshToken
  }
}
```

### Logout

```graphql
mutation Logout {
  logout {
    success
    message
  }
}
```

---

## API Reference

### Mutations

#### `register`

Register a new user account.

**Arguments:**

- `email: String!` - User email address (must be unique)
- `password: String!` - User password (must meet strength requirements)
- `firstName: String!` - User first name
- `lastName: String!` - User last name
- `organisationId: ID` - Optional organisation ID to assign user

**Returns:** `RegisterPayload`

- `success: Boolean!`
- `message: String`
- `user: UserType`

**Errors:**

- `EMAIL_ALREADY_EXISTS` - Email already registered
- `PASSWORD_TOO_WEAK` - Password doesn't meet requirements
- `INVALID_EMAIL_FORMAT` - Invalid email format
- `ORGANISATION_NOT_FOUND` - Organisation ID not found

---

#### `login`

Authenticate user and return JWT tokens.

**Arguments:**

- `email: String!` - User email
- `password: String!` - User password
- `totpCode: String` - Optional TOTP code (required if 2FA enabled)

**Returns:** `LoginPayload`

- `success: Boolean!`
- `accessToken: String`
- `refreshToken: String`
- `user: UserType`

**Errors:**

- `INVALID_CREDENTIALS` - Wrong email or password
- `EMAIL_NOT_VERIFIED` - Email not verified
- `ACCOUNT_LOCKED` - Too many failed attempts
- `ACCOUNT_DISABLED` - Account disabled by admin
- `TWO_FACTOR_REQUIRED` - TOTP code required
- `INVALID_TOTP_CODE` - Invalid 2FA code

---

#### `refreshToken`

Refresh access token using refresh token.

**Arguments:**

- `refreshToken: String!` - Valid refresh token

**Returns:** `RefreshTokenPayload`

- `success: Boolean!`
- `accessToken: String`
- `refreshToken: String`

**Errors:**

- `TOKEN_EXPIRED` - Refresh token expired
- `TOKEN_INVALID` - Invalid or revoked token

---

#### `logout`

End current session and revoke tokens.

**Returns:** `LogoutPayload`

- `success: Boolean!`
- `message: String`

**Requires:** Authenticated user

---

#### `requestPasswordReset`

Send password reset email.

**Arguments:**

- `email: String!` - User email

**Returns:** `PasswordResetRequestPayload`

- `success: Boolean!`
- `message: String`

**Note:** Always returns success to prevent email enumeration

---

#### `resetPassword`

Reset password using token from email.

**Arguments:**

- `token: String!` - Reset token from email
- `newPassword: String!` - New password

**Returns:** `PasswordResetPayload`

- `success: Boolean!`
- `message: String`

**Errors:**

- `TOKEN_INVALID` - Invalid or expired reset token
- `PASSWORD_TOO_WEAK` - Password doesn't meet requirements
- `PASSWORD_IN_HISTORY` - Cannot reuse recent password

---

#### `changePassword`

Change password for authenticated user.

**Arguments:**

- `oldPassword: String!` - Current password
- `newPassword: String!` - New password

**Returns:** `ChangePasswordPayload`

- `success: Boolean!`
- `message: String`

**Requires:** Authenticated user

**Errors:**

- `INVALID_CREDENTIALS` - Wrong current password
- `PASSWORD_TOO_WEAK` - New password too weak
- `PASSWORD_IN_HISTORY` - Cannot reuse recent password

**Side Effects:**

- Terminates all other active sessions
- Rotates refresh tokens

---

#### `setupTotp`

Setup TOTP (2FA) for user account.

**Returns:** `TOTPSetupPayload`

- `success: Boolean!`
- `secret: String` - TOTP secret for manual entry
- `qrCodeUrl: String` - TOTP URL for QR code generation
- `backupCodes: [String!]` - One-time backup codes

**Requires:** Authenticated user

---

#### `verifyTotp`

Verify and enable TOTP.

**Arguments:**

- `code: String!` - 6-digit TOTP code

**Returns:** `TOTPVerifyPayload`

- `success: Boolean!`
- `message: String`

**Requires:** Authenticated user with TOTP setup

**Errors:**

- `INVALID_TOTP_CODE` - Wrong code

---

#### `disableTotp`

Disable TOTP for account.

**Arguments:**

- `password: String!` - User password for confirmation

**Returns:** `TOTPDisablePayload`

- `success: Boolean!`
- `message: String`

**Requires:** Authenticated user

**Errors:**

- `INVALID_CREDENTIALS` - Wrong password

---

#### `terminateSession`

End a specific session.

**Arguments:**

- `sessionId: ID!` - Session ID to terminate

**Returns:** `SessionTerminatePayload`

- `success: Boolean!`
- `message: String`

**Requires:** Authenticated user (can only terminate own sessions)

---

#### `terminateAllSessions`

End all sessions except current.

**Returns:** `SessionTerminateAllPayload`

- `success: Boolean!`
- `message: String`
- `count: Int` - Number of sessions terminated

**Requires:** Authenticated user

---

### Queries

#### `currentUser`

Get current authenticated user.

**Returns:** `UserType`

- `id: ID!`
- `email: String!`
- `firstName: String!`
- `lastName: String!`
- `emailVerified: Boolean!`
- `totpEnabled: Boolean!`
- `organisation: OrganisationType`
- `dateJoined: DateTime!`

**Requires:** Authenticated user

---

#### `activeSessions`

List all active sessions for current user.

**Returns:** `[SessionType!]!`

- `id: ID!`
- `deviceName: String`
- `browser: String`
- `location: String`
- `ipAddress: String!`
- `lastActivity: DateTime!`
- `isCurrent: Boolean!`

**Requires:** Authenticated user

---

### Types

#### `UserType`

```graphql
type UserType {
  id: ID!
  email: String!
  firstName: String!
  lastName: String!
  emailVerified: Boolean!
  totpEnabled: Boolean!
  organisation: OrganisationType
  dateJoined: DateTime!
}
```

#### `SessionType`

```graphql
type SessionType {
  id: ID!
  deviceName: String
  browser: String
  location: String
  ipAddress: String!
  createdAt: DateTime!
  lastActivity: DateTime!
  isCurrent: Boolean!
}
```

---

## Security Considerations

### 1. Password Security

**Requirements enforced:**

- Minimum length (default 12 characters)
- Uppercase, lowercase, numbers, special characters
- Common password checking
- Password history tracking

**Configuration:**

```python
SYNTEK_AUTHENTICATION = {
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_HISTORY_COUNT': 5,
    'CHECK_COMMON_PASSWORDS': True,
}
```

### 2. Rate Limiting

**Protection against:**

- Brute force attacks
- Password spraying
- Credential stuffing

**Implementation:**

```python
SYNTEK_AUTHENTICATION = {
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 minutes
}
```

### 3. Token Security

**JWT best practices:**

- Short-lived access tokens (15 minutes)
- Longer refresh tokens with rotation
- Secure token storage
- Automatic expiration

**Configuration:**

```python
SYNTEK_JWT = {
    'ACCESS_TOKEN_LIFETIME': 900,   # 15 minutes
    'REFRESH_TOKEN_LIFETIME': 86400,  # 24 hours
    'ROTATE_REFRESH_TOKENS': True,
}
```

### 4. Session Management

**Features:**

- Concurrent session limiting
- Device and location tracking
- Automatic session termination on suspicious activity
- Session timeout on inactivity

**Configuration:**

```python
SYNTEK_SESSIONS = {
    'MAX_CONCURRENT_SESSIONS': 3,
    'SESSION_TIMEOUT': 1800,
    'TERMINATE_ON_PASSWORD_CHANGE': True,
}
```

### 5. Two-Factor Authentication

**TOTP implementation:**

- Time-based one-time passwords (RFC 6238)
- 6-digit codes
- 30-second time window
- Backup codes for recovery

**Configuration:**

```python
SYNTEK_MFA = {
    'TOTP_ISSUER': 'Your App Name',
    'BACKUP_CODE_COUNT': 10,
    'ENFORCE_2FA': False,  # Set True to require for all users
}
```

### 6. Email Verification

**Prevent account abuse:**

- Verify email ownership before activation
- Configurable verification requirement
- Token-based verification links

### 7. Error Messages

**Security through obscurity:**

- Generic error messages to prevent enumeration
- Detailed logging for security teams
- No sensitive data in client responses

**Example:**

```python
# Good: Generic message
raise AuthenticationError(ErrorCode.INVALID_CREDENTIALS)

# Bad: Information leak
raise AuthenticationError(message="User with email 'admin@example.com' not found")
```

### 8. HTTPS Only

**Always use HTTPS in production:**

```python
# settings/production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules/graphql/auth

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=syntek_graphql_auth --cov-report=html

# Run specific test file
pytest tests/test_auth_mutations.py

# Run specific test
pytest tests/test_auth_mutations.py::test_register_success
```

### Code Quality

```bash
# Type checking
mypy syntek_graphql_auth

# Linting
ruff check syntek_graphql_auth

# Format code
ruff format syntek_graphql_auth

# Run all checks
pre-commit run --all-files
```

### Project Structure

```
graphql/auth/
├── syntek_graphql_auth/
│   ├── __init__.py              # Public API exports
│   ├── schema.py                # Schema creation helper
│   ├── mutations/
│   │   ├── __init__.py
│   │   ├── auth.py              # Auth mutations (register, login, etc.)
│   │   ├── totp.py              # TOTP/2FA mutations
│   │   └── session.py           # Session management
│   ├── queries/
│   │   ├── __init__.py
│   │   └── user.py              # User queries
│   └── types/
│       ├── __init__.py
│       ├── auth.py              # Auth payload types
│       ├── user.py              # User type
│       └── totp.py              # TOTP types
├── tests/
│   ├── conftest.py              # Pytest configuration
│   ├── test_auth_mutations.py  # Auth mutation tests
│   ├── test_totp_mutations.py  # TOTP tests
│   └── test_user_queries.py    # Query tests
├── README.md                    # This file
├── LICENSE                      # MIT License
├── CHANGELOG.md                 # Version history
├── pyproject.toml               # Project metadata
└── MANIFEST.in                  # Package manifest
```

---

## Testing

### Test Coverage

The module includes comprehensive tests for:

- User registration with validation
- Login with various scenarios (success, 2FA, locked account)
- Token refresh and rotation
- Password management (reset, change, history)
- TOTP setup, verification, and disable
- Session management and termination
- Error handling and edge cases

### Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=syntek_graphql_auth --cov-report=term-missing

# Specific test file
pytest tests/test_auth_mutations.py -v

# With markers
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
```

### Example Test

```python
import pytest
from syntek_graphql_auth.mutations.auth import AuthMutations

@pytest.mark.unit
def test_register_success(db, graphql_client):
    """Test successful user registration."""
    mutation = '''
        mutation Register($email: String!, $password: String!) {
            register(
                email: $email
                password: $password
                firstName: "John"
                lastName: "Doe"
            ) {
                success
                user {
                    email
                }
            }
        }
    '''

    result = graphql_client.execute(mutation, variables={
        'email': 'test@example.com',
        'password': 'SecureP@ssw0rd123'
    })

    assert result['data']['register']['success'] is True
    assert result['data']['register']['user']['email'] == 'test@example.com'
```

---

## Migration from v1.x

If you're migrating from the monolithic `syntek-graphql-auth@1.x` package, see the [Migration Guide](../../MIGRATION_GUIDE.md) for detailed instructions.

**Key Changes:**

1. Core functionality moved to `syntek-graphql-core`
2. Audit logging moved to `syntek-graphql-audit`
3. GDPR/legal moved to `syntek-graphql-compliance`
4. Import paths updated
5. Schema composition now manual

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or contributions:

- **Issues**: [GitHub Issues](https://github.com/syntek/syntek-modules/issues)
- **Documentation**: [Syntek Docs](https://docs.syntek.dev/graphql/auth)
- **Repository**: [GitHub Repository](https://github.com/syntek/syntek-modules)

---

## Related Packages

- **syntek-graphql-core** (required): Core security, errors, permissions
- **syntek-graphql-audit**: Audit logging and compliance tracking
- **syntek-graphql-compliance**: GDPR and legal compliance
- **syntek-authentication** (required): Backend authentication logic
- **syntek-sessions** (required): Session management backend
- **syntek-jwt** (required): JWT token handling
- **syntek-mfa** (required): TOTP/2FA backend

---

**Last Updated**: 2026-02-04
**Version**: 2.0.0
**Maintainer**: Syntek Development Team
