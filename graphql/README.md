# Syntek GraphQL Modules

Modular GraphQL components for Django applications using Strawberry GraphQL.

## Overview

The Syntek GraphQL modules provide a complete, security-first GraphQL layer for Django applications. The modules are designed to be independently installable, allowing you to include only the functionality you need.

## Module Structure

```
graphql/
├── syntek-graphql-core/          # Security foundation
├── syntek-graphql-auth/          # Authentication & sessions
├── syntek-graphql-audit/         # Audit logging
└── syntek-graphql-compliance/    # GDPR & legal documents
```

### Module Dependencies

```
┌─────────────────────────┐
│   syntek-graphql-core   │ ← Base module (no dependencies)
└─────────────────────────┘
            ▲
            │ depends on
    ┌───────┼───────┬────────────┐
    │               │            │
┌───────┐    ┌──────────┐  ┌─────────────┐
│ Auth  │    │  Audit   │  │ Compliance  │
│ v2.0  │    │  v1.0    │  │   v1.0      │
└───────┘    └──────────┘  └─────────────┘
```

## Modules

### 1. syntek-graphql-core (v1.0.0)

**Security foundation for all GraphQL modules.**

**Features:**

- Standardized error codes and exceptions
- Permission classes (IsAuthenticated, HasPermission, IsOrganisationOwner)
- Security extensions (query depth/complexity limiting, introspection control)
- JWT authentication middleware
- Request context utilities
- Type guards for authentication

**Installation:**

```bash
uv pip install syntek-graphql-core
```

**Documentation:** [syntek-graphql-core/README.md](./syntek-graphql-core/README.md)

---

### 2. syntek-graphql-auth (v2.0.0)

**User authentication, sessions, JWT, and TOTP/2FA.**

**Features:**

- User registration with email verification
- Login/logout with JWT (RS256)
- Password reset and change
- TOTP 2FA with backup codes
- Session management (max 5 concurrent)
- Token rotation
- CAPTCHA protection

**Installation:**

```bash
uv pip install syntek-graphql-core syntek-graphql-auth
```

**Documentation:** [syntek-graphql-auth/README.md](./syntek-graphql-auth/README.md)

---

### 3. syntek-graphql-audit (v1.0.0)

**Audit log queries with organisation boundaries.**

**Features:**

- User-specific audit logs
- Organisation-wide logs (with permission checks)
- Session management information
- Filtering by action, user, date range
- Pagination support
- Organisation boundary enforcement

**Installation:**

```bash
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-audit
```

**Documentation:** [syntek-graphql-audit/README.md](./syntek-graphql-audit/README.md)

---

### 4. syntek-graphql-compliance (v1.0.0)

**GDPR operations and legal document management.**

**Features:**

- **GDPR Article 15:** Data export
- **GDPR Article 17:** Account deletion
- **GDPR Article 18:** Processing restrictions
- Consent management
- Legal document versioning (Terms, Privacy Policy, Cookie Policy, DPA)
- Acceptance tracking

**Installation:**

```bash
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-compliance
```

**Documentation:** [syntek-graphql-compliance/README.md](./syntek-graphql-compliance/README.md)

---

## Quick Start

### Installation Scenarios

#### Minimal (Auth only)

```bash
uv pip install syntek-graphql-core syntek-graphql-auth
```

#### With Audit Logging

```bash
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-audit
```

#### GDPR Compliant

```bash
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-compliance
```

#### Full Installation

```bash
uv pip install syntek-graphql-core \
               syntek-graphql-auth \
               syntek-graphql-audit \
               syntek-graphql-compliance
```

### Basic Usage

```python
import strawberry
from syntek_graphql_core.security import (
    QueryDepthLimitExtension,
    QueryComplexityLimitExtension,
    IntrospectionControlExtension,
)
from syntek_graphql_auth.mutations.auth import AuthMutations
from syntek_graphql_auth.queries.user import UserQueries

@strawberry.type
class Query(UserQueries):
    pass

@strawberry.type
class Mutation(AuthMutations):
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

See [examples/](./examples/) for more detailed usage patterns.

## Migration Guide

If you're upgrading from the monolithic `syntek-graphql-auth` package, see [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for detailed migration instructions.

## Architecture Benefits

### 1. Separation of Concerns

- Each module has a single, well-defined responsibility
- Easier to understand and maintain
- Reduced cognitive load

### 2. Selective Installation

- Install only what you need
- Smaller bundle size
- Faster installation

### 3. Independent Versioning

- Semantic versioning per module
- Breaking changes isolated
- Faster release cycles

### 4. Better Testing

- Test modules independently
- Mock dependencies cleanly
- Faster test runs

### 5. Security

- Reduced attack surface
- Easier security audits
- Isolated vulnerabilities

### 6. Compliance

- Optional GDPR module
- Clear data handling
- Easier compliance audits

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules/graphql

# Install all modules in development mode
uv pip install -e syntek-graphql-core[dev]
uv pip install -e syntek-graphql-auth[dev]
uv pip install -e syntek-graphql-audit[dev]
uv pip install -e syntek-graphql-compliance[dev]

# Run tests
pytest

# Run type checking
mypy syntek_graphql_core syntek_graphql_auth syntek_graphql_audit syntek_graphql_compliance

# Run linting
ruff check .
```

### Running Tests

```bash
# Test all modules
pytest

# Test specific module
pytest syntek-graphql-core/
pytest syntek-graphql-auth/
pytest syntek-graphql-audit/
pytest syntek-graphql-compliance/

# With coverage
pytest --cov=syntek_graphql_core --cov=syntek_graphql_auth --cov=syntek_graphql_audit --cov=syntek_graphql_compliance --cov-report=html
```

## Security Compliance

All modules comply with:

- ✅ OWASP Top 10
- ✅ NIST Cybersecurity Framework
- ✅ NCSC Guidelines
- ✅ GDPR (EU/UK/Global)
- ✅ CIS Benchmarks
- ✅ SOC 2

See individual module documentation for specific security features.

## Support

- **Documentation:** Individual module READMEs
- **Issues:** [GitHub Issues](https://github.com/syntek/syntek-modules/issues)
- **Discussions:** [GitHub Discussions](https://github.com/syntek/syntek-modules/discussions)

## License

MIT License - see individual module LICENSE files for details.

## Related Packages

### Backend Modules

- `syntek-security-core` - HTTP security middleware
- `syntek-security-auth` - Backend authentication services
- `syntek-audit` - Audit log models
- `syntek-sessions` - Session management
- `syntek-compliance` - GDPR compliance models

### Frontend Modules

- `@syntek/security-core` - Client-side security
- `@syntek/ui-auth` - React authentication components
- `@syntek/mobile-auth` - React Native authentication

## Changelog

See individual module CHANGELOG.md files:

- [syntek-graphql-core/CHANGELOG.md](./syntek-graphql-core/CHANGELOG.md)
- [syntek-graphql-auth/CHANGELOG.md](./syntek-graphql-auth/CHANGELOG.md)
- [syntek-graphql-audit/CHANGELOG.md](./syntek-graphql-audit/CHANGELOG.md)
- [syntek-graphql-compliance/CHANGELOG.md](./syntek-graphql-compliance/CHANGELOG.md)
