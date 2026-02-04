# GraphQL Integration Examples

This directory contains example projects demonstrating how to integrate Syntek GraphQL modules into Django projects.

## Available Examples

### 1. Minimal Auth (`minimal-auth/`)

A minimal example showing authentication-only integration.

**Features:**
- User registration and login
- JWT token management
- Password reset functionality
- TOTP 2FA support
- Session management

**Modules used:**
- `syntek-graphql-core`
- `syntek-graphql-auth`

**Use case:** Perfect for projects that only need authentication without audit logging or GDPR compliance features.

### 2. Full Features (`full-features/`)

A comprehensive example demonstrating all GraphQL modules.

**Features:**
- All authentication features (from minimal example)
- Audit logging and security monitoring
- GDPR data export and deletion
- Legal document management
- Consent tracking

**Modules used:**
- `syntek-graphql-core`
- `syntek-graphql-auth`
- `syntek-graphql-audit`
- `syntek-graphql-compliance`

**Use case:** Ideal for production applications requiring comprehensive security, compliance, and audit capabilities.

## Quick Start

### Prerequisites

- Python 3.14+
- uv package manager
- PostgreSQL 18.1+
- Redis (for rate limiting and sessions)

### Running an Example

```bash
# Navigate to the example directory
cd examples/graphql/minimal-auth

# Install dependencies
uv pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Access GraphQL playground
# http://localhost:8000/graphql/
```

## Environment Variables

All examples require these environment variables:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@example.com

# JWT
JWT_ACCESS_TOKEN_LIFETIME=900  # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days

# TOTP
TOTP_ISSUER=YourAppName
TOTP_ENCRYPTION_KEY=your-fernet-key-here

# reCAPTCHA (optional)
RECAPTCHA_SECRET_KEY=your-recaptcha-secret
```

## Testing Examples

Each example includes a test suite:

```bash
# Run tests
pytest

# With coverage
pytest --cov

# Specific test file
pytest tests/test_authentication.py
```

## Example Queries and Mutations

### Registration

```graphql
mutation Register {
  register(input: {
    email: "user@example.com"
    password: "SecurePass123!"
    firstName: "John"
    lastName: "Doe"
  }) {
    success
    message
    user {
      id
      email
      firstName
      lastName
    }
  }
}
```

### Login

```graphql
mutation Login {
  login(
    email: "user@example.com"
    password: "SecurePass123!"
  ) {
    success
    message
    token
    refreshToken
    user {
      id
      email
    }
  }
}
```

### Get Current User

```graphql
query Me {
  me {
    id
    email
    firstName
    lastName
    isVerified
    totpEnabled
  }
}
```

### Enable 2FA

```graphql
mutation EnableTotp {
  enableTotp {
    secret
    qrCodeUri
    backupCodes
  }
}
```

### Verify 2FA

```graphql
mutation VerifyTotp {
  verifyTotp(code: "123456") {
    success
    message
  }
}
```

### Request Data Export (Full example only)

```graphql
mutation RequestDataExport {
  requestDataExport {
    success
    message
    requestId
  }
}
```

### Get Audit Logs (Full example only)

```graphql
query AuditLogs {
  auditLogs(limit: 10) {
    id
    action
    timestamp
    ipAddress
    userAgent
    metadata
  }
}
```

## Project Structure

Each example follows this structure:

```
example-name/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # Example-specific documentation
├── config/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py               # URL configuration
│   └── wsgi.py               # WSGI configuration
├── schema.py                  # GraphQL schema composition
└── tests/                     # Test suite
    ├── __init__.py
    ├── conftest.py           # Pytest fixtures
    ├── test_authentication.py
    ├── test_totp.py
    └── test_sessions.py
```

## Customisation

### Adding Custom Fields to Schema

```python
# schema.py
import strawberry
from syntek_graphql_auth.queries.user import UserQueries

@strawberry.type
class Query(UserQueries):
    @strawberry.field
    def health_check(self) -> bool:
        """Custom health check endpoint."""
        return True

    @strawberry.field
    def api_version(self) -> str:
        """Return API version."""
        return "1.0.0"
```

### Adding Custom Mutations

```python
# schema.py
import strawberry
from syntek_graphql_auth.mutations.auth import AuthMutations

@strawberry.type
class Mutation(AuthMutations):
    @strawberry.mutation
    def custom_action(self, info, input: str) -> str:
        """Custom mutation."""
        return f"Processed: {input}"
```

### Custom Permissions

```python
# permissions.py
from syntek_graphql_core.permissions import BasePermission

class IsAdmin(BasePermission):
    """Permission class that only allows admin users."""

    message = "Only administrators can access this resource."

    def has_permission(self, source, info, **kwargs) -> bool:
        """Check if user is an admin."""
        user = info.context.request.user
        return user.is_authenticated and user.is_staff

# Use in schema
from permissions import IsAdmin

@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAdmin])
    def admin_only_field(self) -> str:
        return "Admin data"
```

## Best Practices

1. **Use Environment Variables:** Never hardcode sensitive information
2. **Enable Security Extensions:** Always use query depth and complexity limiting
3. **Implement Rate Limiting:** Protect your API from abuse
4. **Use HTTPS in Production:** Never use HTTP for sensitive data
5. **Validate Input:** Always validate and sanitise user input
6. **Log Security Events:** Use audit logging for security monitoring
7. **Regular Updates:** Keep dependencies up to date
8. **Test Thoroughly:** Write comprehensive tests for your GraphQL operations

## Production Deployment

### Security Checklist

- [ ] `DEBUG = False` in settings
- [ ] Strong `SECRET_KEY` (use secrets.token_urlsafe(50))
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] HTTPS enabled (`SECURE_SSL_REDIRECT = True`)
- [ ] Secure cookies (`SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`)
- [ ] HSTS enabled (`SECURE_HSTS_SECONDS = 31536000`)
- [ ] Rate limiting configured
- [ ] Query introspection disabled
- [ ] Error messages don't leak sensitive information
- [ ] Database credentials in environment variables
- [ ] Redis password protected
- [ ] JWT tokens have appropriate expiry times
- [ ] CORS configured correctly
- [ ] Content Security Policy (CSP) headers configured

### Performance Optimisation

1. **Use Connection Pooling:**
   ```python
   DATABASES = {
       'default': {
           'CONN_MAX_AGE': 600,  # 10 minutes
       }
   }
   ```

2. **Enable Query Caching:**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

3. **Use DataLoader for N+1 Prevention:**
   ```python
   from strawberry.dataloader import DataLoader

   # Implement efficient data loading
   ```

## Troubleshooting

### Common Issues

1. **Import Errors:** Ensure all Syntek modules are installed
2. **Database Errors:** Run migrations and check database connection
3. **Redis Errors:** Ensure Redis is running
4. **Authentication Errors:** Check JWT secret key and token expiry
5. **CORS Errors:** Configure CORS headers correctly

### Getting Help

- **Documentation:** https://docs.syntek.dev/graphql
- **Issues:** https://github.com/syntek/syntek-modules/issues
- **Discussions:** https://github.com/syntek/syntek-modules/discussions

## Contributing

Found a bug or want to improve an example? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Licence

All examples are released under the MIT Licence.
