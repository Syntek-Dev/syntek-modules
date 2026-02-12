# Minimal Auth Example

A minimal Django project demonstrating authentication-only GraphQL integration with Syntek modules.

## Features

- User registration with email verification
- Login with JWT token generation
- Password reset functionality
- TOTP 2FA support
- Session management
- Security middleware (CSRF, rate limiting, security headers)

## Modules Used

- `syntek-graphql-core` - Security foundation
- `syntek-graphql-auth` - Authentication mutations and queries
- `syntek-authentication` - Backend user model and auth logic
- `syntek-sessions` - Session management
- `syntek-jwt` - JWT token handling
- `syntek-mfa` - TOTP 2FA implementation
- `syntek-security-core` - Security middleware

## Installation

### 1. Install Dependencies

```bash
uv pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost:5432/minimal_auth_example
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.example.com
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your-password
JWT_SECRET_KEY=your-jwt-secret
TOTP_ENCRYPTION_KEY=your-fernet-key
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
python manage.py runserver
```

### 6. Access GraphQL Playground

Visit: http://localhost:8000/graphql/

## Example Queries and Mutations

### Register a New User

```graphql
mutation Register {
  register(
    input: {
      email: "user@example.com"
      password: "SecurePass123!"
      firstName: "John"
      lastName: "Doe"
    }
  ) {
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
  login(email: "user@example.com", password: "SecurePass123!") {
    success
    message
    token
    refreshToken
    user {
      id
      email
      firstName
      lastName
    }
  }
}
```

### Get Current User

Add the JWT token to the HTTP headers:

```
Authorization: Bearer <your-token-here>
```

Then run:

```graphql
query Me {
  me {
    id
    email
    firstName
    lastName
    isVerified
    totpEnabled
    createdAt
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

### Verify 2FA Code

```graphql
mutation VerifyTotp {
  verifyTotp(code: "123456") {
    success
    message
  }
}
```

### Change Password

```graphql
mutation ChangePassword {
  changePassword(
    oldPassword: "SecurePass123!"
    newPassword: "NewSecurePass456!"
  ) {
    success
    message
  }
}
```

### Request Password Reset

```graphql
mutation RequestPasswordReset {
  requestPasswordReset(email: "user@example.com") {
    success
    message
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

## Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov

# Specific test
pytest tests/test_authentication.py -v
```

## Project Structure

```
minimal-auth/
├── manage.py                   # Django management
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── README.md                  # This file
├── config/                    # Django configuration
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py               # URL routes
│   └── wsgi.py               # WSGI config
├── schema.py                  # GraphQL schema
└── tests/                     # Tests
    ├── conftest.py           # Pytest fixtures
    ├── test_authentication.py
    ├── test_totp.py
    └── test_sessions.py
```

## Security Features

### Enabled by Default

1. **CSRF Protection:** GraphQL-compatible CSRF middleware
2. **Rate Limiting:** Per-IP and per-user rate limits
3. **Security Headers:** HSTS, CSP, X-Frame-Options, etc.
4. **Query Depth Limiting:** Prevents deeply nested queries (max 10 levels)
5. **Query Complexity Limiting:** Prevents expensive queries (max 1000 complexity)
6. **JWT Token Rotation:** Tokens expire after 15 minutes
7. **Strong Password Validation:** Enforces password complexity rules
8. **TOTP 2FA:** Optional two-factor authentication
9. **Session Management:** Limit concurrent sessions

### Production Recommendations

1. Set `DEBUG = False`
2. Use strong `SECRET_KEY` (50+ characters)
3. Enable HTTPS (`SECURE_SSL_REDIRECT = True`)
4. Configure `ALLOWED_HOSTS` properly
5. Use secure cookies
6. Disable introspection (`INTROSPECTION = False`)
7. Set appropriate rate limits
8. Use Redis for session storage
9. Enable audit logging (add syntek-graphql-audit)

## Customisation

### Adding Custom Fields to User Query

```python
# schema.py
import strawberry
from syntek_graphql_auth.queries.user import UserQueries

@strawberry.type
class Query(UserQueries):
    @strawberry.field
    def health_check(self) -> bool:
        """Health check endpoint."""
        return True
```

### Adding Custom Mutations

```python
# schema.py
import strawberry
from syntek_graphql_auth.mutations.auth import AuthMutations

@strawberry.type
class Mutation(AuthMutations):
    @strawberry.mutation
    def custom_action(self, info, value: str) -> str:
        """Custom mutation example."""
        return f"Received: {value}"
```

## Next Steps

1. **Add Audit Logging:** Install `syntek-graphql-audit` for security monitoring
2. **Add GDPR Compliance:** Install `syntek-graphql-compliance` for data export/deletion
3. **Deploy to Production:** Follow the production checklist in main README
4. **Customise:** Add your own business logic and mutations

## Support

- **Documentation:** https://docs.syntek.dev/graphql
- **Examples:** See `../full-features/` for comprehensive example
- **Issues:** https://github.com/syntek/syntek-modules/issues
