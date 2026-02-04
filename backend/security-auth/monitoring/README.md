# Syntek Monitoring - Security Monitoring Module

## Overview

Syntek Monitoring provides suspicious activity detection, security alerts, and real-time monitoring for Django applications. It detects unusual login patterns, location changes, password modifications, and security setting changes.

## Features

- **Login Location Tracking**: Detect logins from new locations
- **IP Address Monitoring**: Track and cache known IP addresses
- **Password Change Alerts**: Notify users of password changes
- **2FA Alerts**: Alert on MFA enable/disable events
- **Account Lockout Notifications**: Alert on account lockouts
- **Audit Integration**: Log all security events
- **Email Notifications**: Send security alerts to users
- **Redis Caching**: Fast IP address lookup

## Installation

```bash
uv pip install syntek-monitoring
```

## Configuration

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'syntek_authentication',  # Required dependency
    'syntek_monitoring',
]
```

Settings:

```python
SYNTEK_MONITORING = {
    'ENABLE_LOGIN_ALERTS': True,
    'ENABLE_PASSWORD_ALERTS': True,
    'ENABLE_MFA_ALERTS': True,
    'ENABLE_LOCKOUT_ALERTS': True,
    'IP_CACHE_TTL': 86400,  # 24 hours
    'EMAIL_ALERTS': True,
}

# Redis configuration for IP caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## Usage

### Monitor Login Activity

```python
from syntek_monitoring.services.suspicious_activity_service import SuspiciousActivityService

# Check for suspicious login (call after successful authentication)
SuspiciousActivityService.check_login_location(user, ip_address)
# Sends email if login from new location
```

### Alert on Password Change

```python
# After password change
SuspiciousActivityService.alert_password_change(user)
# Sends email notification
```

### Alert on MFA Changes

```python
# After MFA enabled
SuspiciousActivityService.alert_mfa_enabled(user)

# After MFA disabled
SuspiciousActivityService.alert_mfa_disabled(user)
```

### Alert on Account Lockout

```python
# After account lockout
SuspiciousActivityService.alert_account_lockout(user, reason="Too many failed attempts")
```

## API Reference

### Services

#### SuspiciousActivityService

- `check_login_location(user, ip_address)`: Check if login is from new location
- `alert_password_change(user)`: Send password change notification
- `alert_mfa_enabled(user)`: Send MFA enabled notification
- `alert_mfa_disabled(user)`: Send MFA disabled notification
- `alert_account_lockout(user, reason)`: Send account lockout notification
- `get_known_ips(user)`: Get list of user's known IP addresses
- `clear_ip_cache(user)`: Clear cached IP addresses for user

## Integration with Authentication

```python
# In your authentication flow
from syntek_monitoring.services.suspicious_activity_service import SuspiciousActivityService

def login_view(request):
    # ... authenticate user ...

    if user.is_authenticated:
        # Check for suspicious activity
        ip_address = request.META.get('REMOTE_ADDR')
        SuspiciousActivityService.check_login_location(user, ip_address)

        # Continue with normal login flow
        # ...
```

## Email Templates

The module uses the following email templates (customize in your project):

- `emails/security/login_new_location.html`: New location login alert
- `emails/security/password_changed.html`: Password change notification
- `emails/security/mfa_enabled.html`: MFA enabled notification
- `emails/security/mfa_disabled.html`: MFA disabled notification
- `emails/security/account_locked.html`: Account lockout notification

## Testing

```bash
pytest tests/
```

## Security Considerations

- IP addresses are cached in Redis for performance
- All security events are logged to audit trail
- Email notifications are sent asynchronously
- False positives minimized with IP caching
- Notifications include actionable information

## Performance

- Redis caching ensures fast IP lookups
- Asynchronous email sending prevents blocking
- IP cache TTL configurable per environment
- Minimal database queries

## License

MIT
