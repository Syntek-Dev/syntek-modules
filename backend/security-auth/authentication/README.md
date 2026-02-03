# Syntek Authentication Module

Django authentication module with JWT, MFA (TOTP), and advanced security features.

## Features

- JWT authentication with refresh tokens
- TOTP-based two-factor authentication
- Password strength validation
- Common password checking
- Password history tracking
- Login attempt limiting
- Account lockout
- Encrypted credential storage (via Rust)

## Installation

```bash
uv pip install syntek-authentication

# Or from git
uv pip install "git+https://github.com/syntek/syntek-modules.git#subdirectory=backend/authentication"

# Or local development
uv pip install -e /path/to/syntek-modules/backend/authentication
```

## Django Setup

### 1. Add to INSTALLED_APPS

```python
# settings/base.py
INSTALLED_APPS = [
    # ...
    'syntek_authentication',
    # ...
]
```

### 2. Configure Settings

```python
# settings/base.py
SYNTEK_AUTH = {
    # TOTP Configuration
    'TOTP_REQUIRED': False,  # Require TOTP for all users
    'TOTP_ISSUER_NAME': 'Syntek Platform',

    # Password Requirements
    'PASSWORD_LENGTH': 12,
    'SPECIAL_CHARS_REQUIRED': True,
    'UPPERCASE_REQUIRED': True,
    'LOWERCASE_REQUIRED': True,
    'NUMBERS_REQUIRED': True,
    'COMMON_PASSWORD_CHECK': True,
    'PASSWORD_HISTORY_COUNT': 5,  # Prevent reusing last 5 passwords

    # Login Security
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 minutes in seconds
    'LOCKOUT_INCREMENT': True,  # Increase lockout time with each violation

    # JWT Configuration
    'JWT_EXPIRY': 3600,  # 1 hour
    'REFRESH_TOKEN_EXPIRY': 86400,  # 24 hours
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': env('JWT_SECRET_KEY'),

    # Session Configuration
    'SESSION_TIMEOUT': 1800,  # 30 minutes of inactivity
    'SESSION_ABSOLUTE_TIMEOUT': 43200,  # 12 hours absolute

    # Security Features
    'ALLOW_SIMULTANEOUS_SESSIONS': False,
    'LOG_LOGIN_ATTEMPTS': True,
    'NOTIFY_FAILED_LOGINS': True,
    'NOTIFY_NEW_DEVICE_LOGIN': True,
}
```

### 3. Run Migrations

```bash
python manage.py migrate syntek_authentication
```

### 4. Add to GraphQL Schema

```python
# schema.py
import strawberry
from syntek_authentication.graphql import AuthMutations, AuthQueries

@strawberry.type
class Query(AuthQueries):
    pass

@strawberry.type
class Mutation(AuthMutations):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

## Usage

### GraphQL Mutations

#### Login

```graphql
mutation Login {
  login(email: "user@example.com", password: "SecurePassword123!") {
    success
    token
    refreshToken
    user {
      id
      email
      totpEnabled
    }
    errors
  }
}
```

#### Login with TOTP

```graphql
mutation LoginWithTOTP {
  login(
    email: "user@example.com"
    password: "SecurePassword123!"
    totpCode: "123456"
  ) {
    success
    token
    refreshToken
    user {
      id
      email
    }
  }
}
```

#### Enable TOTP

```graphql
mutation EnableTOTP {
  enableTotp {
    success
    qrCode  # Data URL for QR code
    secret  # Manual entry secret
    backupCodes
  }
}
```

#### Verify TOTP Setup

```graphql
mutation VerifyTOTP {
  verifyTotp(code: "123456") {
    success
    message
  }
}
```

#### Refresh Token

```graphql
mutation RefreshToken {
  refreshToken(refreshToken: "your-refresh-token") {
    success
    token
    refreshToken
  }
}
```

#### Change Password

```graphql
mutation ChangePassword {
  changePassword(
    currentPassword: "OldPassword123!"
    newPassword: "NewSecurePassword456!"
  ) {
    success
    errors
  }
}
```

### Python API

```python
from syntek_authentication.services import AuthService

# Authenticate user
result = AuthService.authenticate(
    email='user@example.com',
    password='SecurePassword123!',
    totp_code='123456'  # Optional if TOTP enabled
)

if result.success:
    token = result.token
    refresh_token = result.refresh_token
    user = result.user
else:
    errors = result.errors

# Enable TOTP for user
totp_result = AuthService.enable_totp(user)
qr_code = totp_result.qr_code
secret = totp_result.secret
backup_codes = totp_result.backup_codes

# Verify TOTP code
is_valid = AuthService.verify_totp(user, code='123456')

# Change password
password_result = AuthService.change_password(
    user=user,
    current_password='OldPassword123!',
    new_password='NewSecurePassword456!'
)
```

### Django Views (Optional)

```python
from syntek_authentication.views import LoginView, TOTPSetupView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/totp/setup/', TOTPSetupView.as_view(), name='totp_setup'),
]
```

## Configuration Options

### Password Requirements

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `PASSWORD_LENGTH` | int | 12 | Minimum password length |
| `SPECIAL_CHARS_REQUIRED` | bool | True | Require special characters |
| `UPPERCASE_REQUIRED` | bool | True | Require uppercase letters |
| `LOWERCASE_REQUIRED` | bool | True | Require lowercase letters |
| `NUMBERS_REQUIRED` | bool | True | Require numbers |
| `COMMON_PASSWORD_CHECK` | bool | True | Check against common passwords |
| `PASSWORD_HISTORY_COUNT` | int | 5 | Number of previous passwords to remember |

### TOTP Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `TOTP_REQUIRED` | bool | False | Require TOTP for all users |
| `TOTP_ISSUER_NAME` | str | 'Syntek' | Issuer name in TOTP apps |
| `TOTP_BACKUP_CODES_COUNT` | int | 10 | Number of backup codes |

### Login Security

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `MAX_LOGIN_ATTEMPTS` | int | 5 | Max failed attempts before lockout |
| `LOCKOUT_DURATION` | int | 300 | Lockout duration in seconds |
| `LOCKOUT_INCREMENT` | bool | True | Increase lockout with each violation |
| `LOG_LOGIN_ATTEMPTS` | bool | True | Log all login attempts |

### JWT Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `JWT_EXPIRY` | int | 3600 | Token expiry in seconds |
| `REFRESH_TOKEN_EXPIRY` | int | 86400 | Refresh token expiry |
| `JWT_ALGORITHM` | str | 'HS256' | JWT algorithm |
| `JWT_SECRET_KEY` | str | required | JWT signing key |

## Security Features

### Encrypted Storage

All sensitive authentication data is encrypted using the Rust encryption module:
- Passwords (hashed with Argon2 + encrypted)
- TOTP secrets (encrypted)
- Backup codes (encrypted)
- Session tokens (encrypted)

### Login Attempt Tracking

The module tracks all login attempts and provides:
- IP-based rate limiting
- Progressive lockout periods
- Email notifications for suspicious activity
- Audit logs for security reviews

### Password Security

- Argon2 hashing (memory-hard, resistant to GPU attacks)
- Password strength validation
- Common password checking (100k+ common passwords)
- Password history prevention
- Encrypted storage of all password data

### TOTP Security

- RFC 6238 compliant
- 30-second time windows
- QR code generation for easy setup
- Backup codes for account recovery
- Encrypted secret storage

## Testing

```bash
# Run tests
pytest backend/authentication/tests

# With coverage
pytest backend/authentication/tests --cov

# Specific test
pytest backend/authentication/tests/test_auth.py::test_login
```

## Development

```bash
# Install in development mode
uv pip install -e backend/authentication

# Run linting
ruff check backend/authentication
black --check backend/authentication

# Type checking
mypy backend/authentication
```

## License

MIT License
