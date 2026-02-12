# Syntek GraphQL Audit

Comprehensive audit logging and session management queries for Syntek GraphQL. Provides GraphQL queries for accessing audit logs with filtering and pagination, active session management, and available audit action types.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Query Examples](#query-examples)
- [Organisation Boundaries](#organisation-boundaries)
- [Security Considerations](#security-considerations)
- [Development](#development)
- [Testing](#testing)
- [License](#license)

---

## Overview

**syntek-graphql-audit** provides GraphQL queries for accessing audit logs and managing user sessions with full organisation boundary enforcement and permission checking.

This package is designed to work seamlessly with:

- **syntek-graphql-core**: Provides permission classes and error handling
- **syntek-audit**: Django app for audit log models and recording
- **syntek-sessions**: Django app for session management

The audit package enables security teams and administrators to:

- View audit logs for compliance and forensics
- Monitor user activity within organisation boundaries
- Manage active user sessions
- Discover available audit action types
- Apply filters and pagination to large datasets

## Features

- **4 GraphQL Queries**: Dedicated queries for audit logs and session management
- **User Audit Logs**: View personal audit logs with filtering and pagination
- **Organisation Audit Logs**: View organisation-wide audit logs (with permission checks)
- **Session Management**: View active sessions with limits and current session identification
- **Available Actions**: Discover all audit action types available in the system
- **Flexible Filtering**: Filter by action, user ID, and date range
- **Pagination Support**: Configurable limit (max 100) and offset
- **Organisation Boundaries**: Strict enforcement of organisation isolation
- **Permission Checks**: Built-in permission validation using syntek-graphql-core
- **Type-Safe**: Full TypeScript-compatible GraphQL types with proper null handling
- **Production-Ready**: Comprehensive error handling and edge case management

## Installation

### Prerequisites

**Required Packages:**

- `syntek-graphql-core>=1.0.0` - Core GraphQL security and utilities
- `syntek-audit` - Django app with AuditLog model
- `syntek-sessions` - Django app with session management

### Using uv (Recommended)

```bash
uv pip install syntek-graphql-audit
```

This will automatically install `syntek-graphql-core>=1.0.0` and other dependencies.

### Using pip

```bash
pip install syntek-graphql-audit
```

### Poetry

```toml
[tool.poetry.dependencies]
syntek-graphql-audit = "^1.0.0"
```

### With Optional Dependencies

For development with testing tools:

```bash
uv pip install syntek-graphql-audit[dev]
```

---

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
    'syntek_graphql_audit',
    # Your apps
    'syntek_audit',
    'syntek_sessions',
]

# GraphQL configuration (from syntek-graphql-core)
GRAPHQL_MAX_QUERY_DEPTH = 10
GRAPHQL_MAX_QUERY_COMPLEXITY = 1000
GRAPHQL_ENABLE_INTROSPECTION = DEBUG
```

### 2. Add Middleware

```python
# settings.py

MIDDLEWARE = [
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

### 3. Include Audit Queries in GraphQL Schema

```python
# schema.py

import strawberry
from syntek_graphql_core import (
    QueryDepthLimitExtension,
    QueryComplexityLimitExtension,
    IntrospectionControlExtension,
)
from syntek_graphql_audit import AuditQuery

@strawberry.type
class Query:
    # Include audit queries
    audit: AuditQuery = strawberry.field(default_factory=AuditQuery)

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

Audit queries are configured through the audit models and session management service. No additional Django settings are required.

### Default Pagination

| Setting          | Default | Description                                 |
| ---------------- | ------- | ------------------------------------------- |
| Pagination Limit | 20      | Default records per page                    |
| Maximum Limit    | 100     | Hard maximum per page (enforced in queries) |

### Model Integration

Queries integrate with:

- `syntek_audit.models.AuditLog` - For audit log queries
- `syntek_sessions.services.SessionManagementService` - For session queries

---

## Usage Examples

### Basic Query: Get My Audit Logs

```graphql
query {
  audit {
    myAuditLogs {
      items {
        id
        action
        userEmail
        userAgent
        createdAt
        metadata
      }
      totalCount
      hasNextPage
      hasPreviousPage
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "audit": {
      "myAuditLogs": {
        "items": [
          {
            "id": "1",
            "action": "LOGIN",
            "userEmail": "user@example.com",
            "userAgent": "Mozilla/5.0...",
            "createdAt": "2025-02-04T10:30:00Z",
            "metadata": {
              "ip_address": "192.168.1.1",
              "mfa_used": true
            }
          }
        ],
        "totalCount": 42,
        "hasNextPage": true,
        "hasPreviousPage": false
      }
    }
  }
}
```

### Query with Filters: Specific Action Type

```graphql
query {
  audit {
    myAuditLogs(filters: { action: "LOGIN" }) {
      items {
        id
        action
        userAgent
        createdAt
      }
      totalCount
    }
  }
}
```

### Query with Date Filtering

```graphql
query {
  audit {
    myAuditLogs(
      filters: {
        dateFrom: "2025-01-01T00:00:00Z"
        dateTo: "2025-02-04T23:59:59Z"
      }
      pagination: { limit: 50, offset: 0 }
    ) {
      items {
        id
        action
        createdAt
      }
      totalCount
      hasNextPage
    }
  }
}
```

### Query with Pagination

```graphql
query {
  audit {
    myAuditLogs(pagination: { limit: 25, offset: 50 }) {
      items {
        id
        action
        createdAt
      }
      totalCount
      hasNextPage
      hasPreviousPage
    }
  }
}
```

### Organisation Audit Logs (Admin Only)

```graphql
query {
  audit {
    organisationAuditLogs(
      filters: { action: "LOGIN" }
      pagination: { limit: 50, offset: 0 }
    ) {
      items {
        id
        action
        userEmail
        organisationName
        userAgent
        createdAt
      }
      totalCount
    }
  }
}
```

**Note**: Returns empty result set if user lacks `audit.view_auditlog` permission.

### Get Active Sessions

```graphql
query {
  audit {
    mySessions {
      activeSessions {
        id
        deviceFingerprint
        userAgent
        createdAt
        lastActivityAt
        expiresAt
        isCurrent
      }
      totalSessions
      maxSessions
      canCreateNewSession
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "audit": {
      "mySessions": {
        "activeSessions": [
          {
            "id": "sess_123",
            "deviceFingerprint": "a1b2c3d4e5f6",
            "userAgent": "Mozilla/5.0 (Chrome)",
            "createdAt": "2025-02-01T09:00:00Z",
            "lastActivityAt": "2025-02-04T10:30:00Z",
            "expiresAt": "2025-02-11T09:00:00Z",
            "isCurrent": true
          },
          {
            "id": "sess_124",
            "deviceFingerprint": "f6e5d4c3b2a1",
            "userAgent": "Mozilla/5.0 (Firefox)",
            "createdAt": "2025-01-28T14:00:00Z",
            "lastActivityAt": "2025-02-03T16:45:00Z",
            "expiresAt": "2025-02-04T14:00:00Z",
            "isCurrent": false
          }
        ],
        "totalSessions": 2,
        "maxSessions": 5,
        "canCreateNewSession": true
      }
    }
  }
}
```

### Get Available Audit Actions

```graphql
query {
  audit {
    availableAuditActions
  }
}
```

**Response:**

```json
{
  "data": {
    "audit": {
      "availableAuditActions": [
        "LOGIN",
        "LOGOUT",
        "LOGIN_FAILED",
        "PASSWORD_CHANGED",
        "MFA_ENABLED",
        "MFA_DISABLED",
        "SESSION_REVOKED",
        "DATA_EXPORT",
        "ACCOUNT_DELETED",
        "PROFILE_UPDATED"
      ]
    }
  }
}
```

### Error Handling: Permission Denied

```graphql
query {
  audit {
    organisationAuditLogs {
      items {
        id
      }
    }
  }
}
```

**Response (User lacks permission):**

```json
{
  "errors": [
    {
      "message": "You do not have permission to view organisation audit logs",
      "extensions": {
        "code": "PERMISSION_DENIED"
      }
    }
  ],
  "data": {
    "audit": {
      "organisationAuditLogs": null
    }
  }
}
```

### Error Handling: Not Authenticated

```graphql
query {
  audit {
    myAuditLogs {
      items {
        id
      }
    }
  }
}
```

**Response (Without authentication):**

```json
{
  "errors": [
    {
      "message": "Authentication required",
      "extensions": {
        "code": "NOT_AUTHENTICATED"
      }
    }
  ],
  "data": {
    "audit": {
      "myAuditLogs": null
    }
  }
}
```

---

## API Reference

### Query Type: AuditQuery

#### `myAuditLogs(filters?: AuditLogFilterInput, pagination?: PaginationInput) -> AuditLogConnection`

Get audit logs for the current authenticated user.

**Description:**
Returns paginated audit logs filtered to the current user only. Users can only see their own logs. Respects organisation boundaries automatically.

**Parameters:**

- `filters` (optional): `AuditLogFilterInput` - Optional filtering options
- `pagination` (optional): `PaginationInput` - Pagination parameters (default: limit=20, offset=0)

**Returns:** `AuditLogConnection`

**Requires:** Authentication (IsAuthenticated permission)

**Example:**

```python
# In Python/Django context
from syntek_graphql_audit import AuditQuery
from strawberry.types import Info

query = AuditQuery()
logs = query.my_audit_logs(
    info=info,
    filters=AuditLogFilterInput(action="LOGIN"),
    pagination=PaginationInput(limit=50, offset=0)
)
```

---

#### `organisationAuditLogs(filters?: AuditLogFilterInput, pagination?: PaginationInput) -> AuditLogConnection`

Get audit logs for the current user's organisation.

**Description:**
Returns paginated audit logs for the entire organisation. Requires `audit.view_auditlog` permission. This query enforces strict organisation boundary checks and will not expose logs from other organisations.

**Parameters:**

- `filters` (optional): `AuditLogFilterInput` - Optional filtering options (includes user_id)
- `pagination` (optional): `PaginationInput` - Pagination parameters (default: limit=20, offset=0)

**Returns:** `AuditLogConnection`

**Requires:**

- Authentication (IsAuthenticated permission)
- Django permission `audit.view_auditlog`

**Raises:**

- `PermissionError` if user lacks permission to view organisation logs

**Example:**

```graphql
query {
  audit {
    organisationAuditLogs(
      filters: {
        userId: "123"
        action: "LOGIN_FAILED"
        dateFrom: "2025-02-01T00:00:00Z"
      }
    ) {
      items {
        id
        action
        userEmail
        createdAt
      }
      totalCount
    }
  }
}
```

---

#### `mySessions() -> SessionManagementInfo`

Get active sessions for the current user.

**Description:**
Returns information about all active sessions for the current user, including:

- List of active sessions with device details
- Total number of active sessions
- Maximum sessions allowed per user
- Whether user can create a new session

The current session is identified and marked with `isCurrent: true`.

**Parameters:** None

**Returns:** `SessionManagementInfo`

**Requires:** Authentication (IsAuthenticated permission)

**Example:**

```graphql
query {
  audit {
    mySessions {
      activeSessions {
        id
        deviceFingerprint
        isCurrent
      }
      totalSessions
      maxSessions
      canCreateNewSession
    }
  }
}
```

---

#### `availableAuditActions() -> [String!]!`

Get list of available audit log action types.

**Description:**
Returns all audit action types that can be used in the system. These match the `ActionType` choices defined in the AuditLog model. Useful for building filter dropdowns and validating action queries.

**Parameters:** None

**Returns:** `[String!]!` - List of action type strings

**Requires:** Authentication (IsAuthenticated permission)

**Example:**

```graphql
query {
  audit {
    availableAuditActions
  }
}
```

---

### Input Types

#### `AuditLogFilterInput`

Filter options for audit log queries.

| Field      | Type       | Default | Description                                           |
| ---------- | ---------- | ------- | ----------------------------------------------------- |
| `action`   | `String`   | null    | Filter by audit action type (e.g., "LOGIN", "LOGOUT") |
| `userId`   | `ID`       | null    | Filter by user ID (only in organisationAuditLogs)     |
| `dateFrom` | `DateTime` | null    | Filter logs created on or after this date (ISO 8601)  |
| `dateTo`   | `DateTime` | null    | Filter logs created on or before this date (ISO 8601) |

**Example:**

```graphql
filters: {
  action: "LOGIN"
  dateFrom: "2025-01-01T00:00:00Z"
  dateTo: "2025-02-04T23:59:59Z"
}
```

---

#### `PaginationInput`

Pagination parameters for query results.

| Field    | Type  | Default | Min | Max | Description                      |
| -------- | ----- | ------- | --- | --- | -------------------------------- |
| `limit`  | `Int` | 20      | 1   | 100 | Records per page (capped at 100) |
| `offset` | `Int` | 0       | 0   | n/a | Number of records to skip        |

**Example:**

```graphql
pagination: {
  limit: 50
  offset: 100
}
```

---

### Return Types

#### `AuditLogType`

GraphQL type representing a single audit log entry.

| Field               | Type        | Nullable | Description                                           |
| ------------------- | ----------- | -------- | ----------------------------------------------------- |
| `id`                | `ID!`       | No       | Unique audit log ID                                   |
| `action`            | `String!`   | No       | Audit action type (e.g., "LOGIN", "PASSWORD_CHANGED") |
| `userId`            | `ID`        | Yes      | User ID who performed the action                      |
| `userEmail`         | `String`    | Yes      | Email of user who performed the action                |
| `organisationId`    | `ID`        | Yes      | Organisation ID                                       |
| `organisationName`  | `String`    | Yes      | Organisation name                                     |
| `userAgent`         | `String!`   | No       | Browser/client user agent string                      |
| `deviceFingerprint` | `String!`   | No       | Device fingerprint hash                               |
| `metadata`          | `JSON!`     | No       | Additional metadata (custom JSON object)              |
| `createdAt`         | `DateTime!` | No       | When the action was performed (ISO 8601)              |

**Example Response:**

```json
{
  "id": "audit_123",
  "action": "LOGIN",
  "userId": "user_456",
  "userEmail": "user@example.com",
  "organisationId": "org_789",
  "organisationName": "Acme Corporation",
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "deviceFingerprint": "a1b2c3d4e5f6g7h8i9j0",
  "metadata": {
    "ip_address": "192.168.1.1",
    "mfa_used": true,
    "login_method": "email"
  },
  "createdAt": "2025-02-04T10:30:00Z"
}
```

---

#### `SessionTokenType`

GraphQL type representing a user session.

| Field               | Type        | Nullable | Description                           |
| ------------------- | ----------- | -------- | ------------------------------------- |
| `id`                | `ID!`       | No       | Unique session ID                     |
| `deviceFingerprint` | `String!`   | No       | Device fingerprint hash               |
| `userAgent`         | `String!`   | No       | Browser/client user agent string      |
| `createdAt`         | `DateTime!` | No       | When session was created (ISO 8601)   |
| `lastActivityAt`    | `DateTime!` | No       | Last time session was used (ISO 8601) |
| `expiresAt`         | `DateTime!` | No       | When session will expire (ISO 8601)   |
| `isCurrent`         | `Boolean!`  | No       | Whether this is the current session   |

**Example Response:**

```json
{
  "id": "sess_abc123",
  "deviceFingerprint": "f1e2d3c4b5a6",
  "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X)",
  "createdAt": "2025-01-28T14:00:00Z",
  "lastActivityAt": "2025-02-04T10:30:00Z",
  "expiresAt": "2025-02-11T14:00:00Z",
  "isCurrent": true
}
```

---

#### `AuditLogConnection`

Paginated connection for audit log results.

| Field             | Type               | Nullable | Description                                              |
| ----------------- | ------------------ | -------- | -------------------------------------------------------- |
| `items`           | `[AuditLogType!]!` | No       | List of audit logs on current page                       |
| `totalCount`      | `Int!`             | No       | Total number of logs matching filters (across all pages) |
| `hasNextPage`     | `Boolean!`         | No       | Whether there are more logs after current page           |
| `hasPreviousPage` | `Boolean!`         | No       | Whether there are logs before current page               |

**Example Response:**

```json
{
  "items": [
    /* AuditLogType objects */
  ],
  "totalCount": 127,
  "hasNextPage": true,
  "hasPreviousPage": false
}
```

---

#### `SessionManagementInfo`

Information about user's session management status.

| Field                 | Type                   | Nullable | Description                             |
| --------------------- | ---------------------- | -------- | --------------------------------------- |
| `activeSessions`      | `[SessionTokenType!]!` | No       | List of active sessions                 |
| `totalSessions`       | `Int!`                 | No       | Number of active sessions               |
| `maxSessions`         | `Int!`                 | No       | Maximum allowed sessions per user       |
| `canCreateNewSession` | `Boolean!`             | No       | Whether user can create another session |

**Example Response:**

```json
{
  "activeSessions": [
    /* SessionTokenType objects */
  ],
  "totalSessions": 2,
  "maxSessions": 5,
  "canCreateNewSession": true
}
```

---

## Query Examples

### Complete Real-World Example: Audit Log Dashboard

```graphql
query GetAuditDashboard($limit: Int, $offset: Int) {
  audit {
    # Get user's recent activity
    myAuditLogs(pagination: { limit: $limit, offset: $offset }) {
      items {
        id
        action
        userAgent
        createdAt
        metadata
      }
      totalCount
      hasNextPage
    }

    # Get active sessions for device management
    mySessions {
      activeSessions {
        id
        deviceFingerprint
        userAgent
        lastActivityAt
        isCurrent
      }
      totalSessions
      maxSessions
    }

    # Get available filters
    availableAuditActions
  }
}
```

**Variables:**

```json
{
  "limit": 20,
  "offset": 0
}
```

### Security Event Investigation Query

```graphql
query InvestigateFailedLogins {
  audit {
    organisationAuditLogs(
      filters: {
        action: "LOGIN_FAILED"
        dateFrom: "2025-02-01T00:00:00Z"
        dateTo: "2025-02-04T23:59:59Z"
      }
      pagination: { limit: 100 }
    ) {
      items {
        id
        userEmail
        userAgent
        createdAt
        metadata
      }
      totalCount
    }
  }
}
```

### Compliance Report Query

```graphql
query ComplianceReport($startDate: String, $endDate: String) {
  audit {
    organisationAuditLogs(
      filters: { dateFrom: $startDate, dateTo: $endDate }
      pagination: { limit: 100, offset: 0 }
    ) {
      items {
        id
        action
        userEmail
        organisationName
        createdAt
      }
      totalCount
    }
  }
}
```

---

## Organisation Boundaries

### Critical Security Feature: Organisation Isolation

The audit package enforces strict organisation boundaries:

#### `myAuditLogs` - User Isolation

- Always filters to current authenticated user only
- Cannot see other users' logs even with permissions
- Automatically scoped to user's organisation

#### `organisationAuditLogs` - Organisation Isolation

- Filters to `current_user.organisation` only
- Cannot access logs from other organisations regardless of permissions
- Requires explicit Django permission `audit.view_auditlog`

#### Implementation

```python
# myAuditLogs
queryset = AuditLog.objects.filter(user=user)  # Current user only

# organisationAuditLogs
# 1. Permission check
if not user.has_perm("audit.view_auditlog"):
    raise PermissionError()

# 2. Organisation boundary
queryset = AuditLog.objects.filter(organisation=user.organisation)
```

### Cross-Organisation Access Prevention

If a user is part of multiple organisations:

- Each organisation's logs are completely isolated
- Querying always returns logs from the user's **current** organisation
- No API exists to switch organisations or access other org logs

---

## Security Considerations

### 1. Authentication Required

All queries require authentication via `IsAuthenticated` permission class:

```python
@strawberry.field(permission_classes=[IsAuthenticated])
def my_audit_logs(self, info: Info) -> AuditLogConnection:
    ...
```

**Protection Against:**

- Unauthenticated users accessing audit data
- Anonymous access to compliance information

### 2. Permission Checks on Organisation Logs

Organisation-level audit logs require explicit permission:

```python
if not user.has_perm("audit.view_auditlog"):
    raise PermissionError()
```

**Create the permission in Django admin:**

- App: `audit`
- Code name: `view_auditlog`
- Assign to appropriate groups (admins, compliance officers)

### 3. Organisation Boundary Enforcement

Strict isolation prevents cross-organisation data access:

```python
# Always scoped to user's organisation
queryset = AuditLog.objects.filter(organisation=user.organisation)
```

**Protection Against:**

- Accessing other organisations' audit logs
- Cross-tenant data leakage
- Privilege escalation through organisation manipulation

### 4. Pagination Limits

Hard-capped at 100 records per page to prevent performance issues:

```python
limit = min(pagination.limit, 100)  # Hard maximum
```

**Protection Against:**

- DoS attacks via large data exports
- Performance degradation from massive queries
- Database connection exhaustion

### 5. Sensitive Data Handling

IP addresses in audit metadata are **NOT encrypted** by default. To encrypt:

```python
# In AuditLog model's metadata field or serialisation:
from syntek_security_encryption import EncryptedField

class AuditLog(models.Model):
    # metadata is encrypted if using EncryptedField
    metadata = EncryptedField()  # Custom Django field
```

**Current Exposure:**

- User agent strings are visible
- IP addresses visible in metadata (if not encrypted)
- Session tokens are **never** exposed

**Recommendation:**

- Store IP addresses in separate encrypted field
- Implement encryption at rest via Django fields
- Use database-level encryption for sensitive audit data

### 6. Session Token Hashes Not Exposed

Session token hashes are **never** exposed in queries:

```python
# Token hash field is not in SessionTokenType
# Only non-sensitive session metadata is exposed
```

**Protected Fields:**

- Session token hash (database only)
- Session secret (database only)

### 7. Rate Limiting for Audit Queries

Combine with Django rate limiting middleware:

```python
# settings.py
MIDDLEWARE = [
    'syntek_security_core.middleware.RateLimitingMiddleware',
]

# In middleware configuration
RATE_LIMITING = {
    'graphql_audit': '100/hour',  # Limit audit queries to 100/hour per user
}
```

### 8. Audit Logging for Audit Queries

Consider logging who accesses audit logs:

```python
# In query resolver
from syntek_audit.services import AuditService

AuditService.log(
    user=info.context.request.user,
    action="AUDIT_LOG_VIEWED",
    metadata={
        "filters_applied": str(filters),
        "results_count": len(logs),
    }
)
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules/graphql

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
uv pip install -e "syntek-graphql-audit[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=syntek_graphql_audit

# Run specific test file
pytest tests/test_queries.py

# Run specific test
pytest tests/test_queries.py::test_my_audit_logs
```

### Code Quality

```bash
# Type checking with mypy
mypy syntek_graphql_audit

# Linting with ruff
ruff check syntek_graphql_audit

# Format code with ruff
ruff format syntek_graphql_audit

# Check imports
ruff check --select I syntek_graphql_audit
```

### Project Structure

```
graphql/syntek-graphql-audit/
├── syntek_graphql_audit/
│   ├── __init__.py                 # Public API exports
│   ├── queries/
│   │   ├── __init__.py
│   │   └── audit.py                # AuditQuery with all 4 queries
│   └── types/
│       ├── __init__.py
│       └── audit.py                # All GraphQL types
├── tests/
│   ├── conftest.py                 # Pytest configuration
│   ├── test_queries.py             # Query tests
│   ├── test_types.py               # Type tests
│   └── test_permissions.py         # Permission tests
├── README.md                       # This file
├── LICENSE                         # MIT License
├── pyproject.toml                  # Project metadata
└── MANIFEST.in                     # Package manifest
```

---

## Testing

### Test Coverage

All modules have comprehensive test coverage including:

- Query authentication checks (IsAuthenticated)
- Permission enforcement (audit.view_auditlog)
- Organisation boundary isolation
- Pagination functionality
- Filter application and validation
- Error handling and error codes
- Type conversions (model to GraphQL)
- Edge cases (empty results, max pagination)

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=syntek_graphql_audit --cov-report=html

# Run tests matching pattern
pytest -k "test_permission" -v

# Run specific test file
pytest tests/test_queries.py -v

# Run with verbose output
pytest -vv
```

### Example Test: Authentication Required

```python
import pytest
from syntek_graphql_audit import AuditQuery

def test_my_audit_logs_requires_authentication(graphql_client):
    """Test that myAuditLogs requires authentication."""
    query = """
    query {
      audit {
        myAuditLogs {
          items { id }
        }
      }
    }
    """

    # Without authentication
    result = graphql_client.execute(query)
    assert "NOT_AUTHENTICATED" in result.errors[0].extensions["code"]
```

### Example Test: Organisation Boundary

```python
def test_organisation_audit_logs_enforces_boundaries(graphql_client, user, org):
    """Test that organisation logs are scoped to user's organisation."""
    # Create audit logs in different organisations
    create_audit_log(user=user, organisation=org, action="LOGIN")
    other_user = create_user(organisation=other_org)
    create_audit_log(user=other_user, organisation=other_org, action="LOGIN")

    # Query organisation audit logs
    result = graphql_client.execute(query, authenticated_user=user)

    # Should only return logs from user's organisation
    assert len(result.data.audit.organisationAuditLogs.items) == 1
    assert result.data.audit.organisationAuditLogs.items[0].organisation_id == org.id
```

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues, questions, or contributions:

- **Issues**: [GitHub Issues](https://github.com/syntek/syntek-modules/issues)
- **Documentation**: [Syntek Docs](https://docs.syntek.dev/graphql/audit)
- **Repository**: [GitHub Repository](https://github.com/syntek/syntek-modules)

---

## Related Packages

- **syntek-graphql-core**: Core GraphQL security, error handling, and utilities
- **syntek-graphql-auth**: Authentication and authorization queries/mutations
- **syntek-audit**: Django audit logging models and services
- **syntek-sessions**: Django session management and revocation
- **syntek-security-auth**: JWT and token management
- **syntek-security-core**: HTTP security headers and rate limiting

---

## Changelog

### Version 1.0.0 (2025-02-04)

- Initial release with 4 GraphQL queries
- Full organisation boundary enforcement
- Permission-based access control
- Pagination and filtering support
- Complete type definitions and API reference

---

**Last Updated**: 2025-02-04
**Version**: 1.0.0
**Maintainer**: Syntek Development Team
