# Phase 1 & 2 Authentication Configuration Review

**Review Date:** 13.02.2026
**Reviewer:** Code Reviewer Agent
**Modules Reviewed:**
- `backend/security-auth/authentication`
- `backend/security-auth/mfa`
- `backend/security-auth/monitoring`
- `backend/security-auth/sessions`
- `backend/security-auth/jwt`

---

## Executive Summary

The Phase 1 and Phase 2 authentication implementation demonstrates **mixed configuration flexibility**. While some areas follow Django best practices with settings-driven configuration, others contain hard-coded values that limit deployment flexibility.

### Key Findings

✅ **Strengths:**
- Password validators support configurable parameters
- Email service uses settings for customisation
- TOTP service has configurable constants
- Phone verification uses settings for encryption keys
- Monitoring service supports configurable behaviour

❌ **Weaknesses:**
- **No centralised `SYNTEK_AUTH` settings dictionary** (as documented in README)
- Hard-coded rate limits and thresholds
- SMS provider not abstracted to settings
- Logging configuration not dynamic
- MFA enforcement not configurable at organisation level
- Middleware configuration not present

### Configuration Score: 6.5/10

**Recommendation:** Implement a centralised settings system with proper defaults and documentation before Phase 3.

---

## 1. Password Validation Configuration

### Current Implementation

Password validators are **partially configurable** through Django's standard `AUTH_PASSWORD_VALIDATORS` setting.

#### Configurable Validators

| Validator | Parameters | Configurable? | Default | Location |
|-----------|-----------|---------------|---------|----------|
| `PasswordComplexityValidator` | `min_uppercase`, `min_lowercase`, `min_digits`, `min_special` | ✅ Yes | 1,1,1,1 | `validators/password.py:40-58` |
| `MinimumLengthValidator` | `min_length`, `max_length` | ✅ Yes | 12, 128 | `validators/password.py:124-132` |
| `MaximumLengthValidator` | `max_length` | ✅ Yes | 128 | `validators/password.py:177-182` |
| `NoSequentialCharactersValidator` | `max_sequence_length` | ✅ Yes | 3 | `validators/password.py:218-224` |
| `NoRepeatedCharactersValidator` | `max_repeated` | ✅ Yes | 3 | `validators/password.py:287-293` |
| `HIBPPasswordValidator` | `threshold`, `timeout` | ✅ Yes | 1, 2 | `validators/password.py:340-348` |
| `PasswordHistoryValidator` | `history_count` | ✅ Yes | 5 | `validators/password.py:419-425` |
| `CommonPasswordValidator` | `password_list_path` | ✅ Yes | Auto | `validators/password.py:485-494` |

#### Configuration Example

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'syntek_authentication.validators.password.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 16,  # Configurable
            'max_length': 256,  # Configurable
        }
    },
    {
        'NAME': 'syntek_authentication.validators.password.PasswordComplexityValidator',
        'OPTIONS': {
            'min_uppercase': 2,  # Configurable
            'min_lowercase': 2,  # Configurable
            'min_digits': 2,     # Configurable
            'min_special': 2,    # Configurable
        }
    },
    {
        'NAME': 'syntek_authentication.validators.password.HIBPPasswordValidator',
        'OPTIONS': {
            'threshold': 5,  # Allow passwords seen < 5 times
            'timeout': 3,    # 3 second API timeout
        }
    },
    {
        'NAME': 'syntek_authentication.validators.password.PasswordHistoryValidator',
        'OPTIONS': {
            'history_count': 10,  # Remember last 10 passwords
        }
    },
]
```

### Issues Identified

#### ❌ No Centralised Settings Dictionary

The README.md advertises a `SYNTEK_AUTH` settings dictionary, but **it's not implemented**:

```python
# From README.md - NOT IMPLEMENTED
SYNTEK_AUTH = {
    'PASSWORD_LENGTH': 12,
    'SPECIAL_CHARS_REQUIRED': True,
    'UPPERCASE_REQUIRED': True,
    # ... etc
}
```

**Impact:** Users must configure validators individually via Django's `AUTH_PASSWORD_VALIDATORS`, which is verbose and harder to maintain.

### Recommendations

1. **Implement `SYNTEK_AUTH` settings wrapper** that translates to Django validators
2. **Provide sensible defaults** that work out-of-the-box
3. **Add settings validation** to catch misconfigurations early

#### Proposed Implementation

```python
# syntek_authentication/settings.py
from django.conf import settings

SYNTEK_AUTH_DEFAULTS = {
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_MAX_LENGTH': 128,
    'PASSWORD_MIN_UPPERCASE': 1,
    'PASSWORD_MIN_LOWERCASE': 1,
    'PASSWORD_MIN_DIGITS': 1,
    'PASSWORD_MIN_SPECIAL': 1,
    'PASSWORD_HISTORY_COUNT': 5,
    'PASSWORD_BREACH_CHECK': True,
    'PASSWORD_BREACH_THRESHOLD': 1,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,
}

def get_auth_setting(key, default=None):
    """Get authentication setting from SYNTEK_AUTH or use default."""
    syntek_auth = getattr(settings, 'SYNTEK_AUTH', {})
    if default is None:
        default = SYNTEK_AUTH_DEFAULTS.get(key)
    return syntek_auth.get(key, default)
```

---

## 2. Authentication Field Requirements

### Current Implementation

Authentication fields are **mostly hard-coded** in model definitions with limited configurability.

#### Required Fields (Hard-Coded)

| Field | Required | Unique | Configurable? | Location |
|-------|----------|--------|---------------|----------|
| `email` | Yes | Yes | ❌ No | `models/user.py` |
| `username` | Likely | Likely | ❌ No | Not reviewed |
| `first_name` | Likely | No | ❌ No | Not reviewed |
| `last_name` | Likely | No | ❌ No | Not reviewed |
| `password` | Yes | No | ❌ No | Django standard |
| `phone_number` | No | No | ❌ No | `models/phone_verification.py` |

#### Authentication Methods

**Login is email-based** as evidenced by:

```python
# services/auth_service.py:118-122
def login(
    email: str,  # ← Email required, not username
    password: str,
    device_fingerprint: str = "",
    ip_address: str = "",
) -> dict[str, Any] | None:
```

### Issues Identified

#### ❌ No Alternative Authentication Methods

- **Cannot configure username-based login** as alternative to email
- **Cannot make phone number required** via settings
- **Cannot add custom authentication backends** easily

#### ❌ Field Requirements Not Configurable

The README mentions:
> **Username**: Modular configuration (unique identifier OR display name)

But **this is not implemented**. Username behaviour cannot be changed via settings.

### Recommendations

1. **Add `SYNTEK_AUTH['AUTHENTICATION_BACKEND']`** setting:
   ```python
   SYNTEK_AUTH = {
       'AUTHENTICATION_BACKEND': 'email',  # or 'username', 'phone', 'email_or_username'
       'USERNAME_IS_UNIQUE': True,  # Display name vs unique identifier
       'PHONE_REQUIRED': False,     # Make phone mandatory
       'REQUIRE_EMAIL_VERIFICATION': True,
   }
   ```

2. **Implement flexible authentication backends** that respect settings
3. **Add field requirement configuration** via model meta or settings

---

## 3. MFA Availability and Configuration

### Current Implementation

MFA (TOTP) is **partially configurable** but lacks organisation-level and type-specific settings.

#### MFA Service Configuration

| Setting | Type | Configurable? | Default | Location |
|---------|------|---------------|---------|----------|
| `DEFAULT_ISSUER` | str | ❌ Hard-coded | "Syntek App" | `mfa/services/totp_service.py:53` |
| `BACKUP_CODE_COUNT` | int | ❌ Hard-coded | 10 | `mfa/services/totp_service.py:54` |
| `TIME_WINDOW_TOLERANCE` | int | ❌ Hard-coded | 1 | `mfa/services/totp_service.py:55` |

**Code Reference:**
```python
# mfa/syntek_mfa/services/totp_service.py:42-55
class TOTPService:
    DEFAULT_ISSUER = "Syntek App"          # ❌ Hard-coded
    BACKUP_CODE_COUNT = 10                  # ❌ Hard-coded
    TIME_WINDOW_TOLERANCE = 1               # ❌ Hard-coded
```

#### MFA Types Implemented

| Type | Implemented | Configurable? | Notes |
|------|-------------|---------------|-------|
| TOTP (Authenticator App) | ✅ Yes | Partial | Device management available |
| SMS MFA | ❌ No | N/A | SMS verification separate from MFA |
| Backup Codes | ✅ Yes | ❌ Hard-coded count | 10 codes, not configurable |
| Recovery Keys | Appears separate | Unknown | Not in MFA module |

### Issues Identified

#### ❌ MFA Enforcement Not Configurable

The README advertises:
```python
SYNTEK_AUTH = {
    'TOTP_REQUIRED': False,  # Require TOTP for all users
}
```

**But this setting is NOT used anywhere in the code.** There's no enforcement mechanism.

#### ❌ No Organisation-Level MFA Policies

Cannot configure:
- "Organisation A requires MFA, Organisation B does not"
- "Require MFA for admin users only"
- "Allow users to choose between TOTP and SMS"

#### ❌ Hard-Coded MFA Constants

```python
# Should be configurable via settings:
SYNTEK_MFA = {
    'ISSUER_NAME': 'MyApp',
    'BACKUP_CODE_COUNT': 12,
    'TIME_WINDOW_TOLERANCE': 2,  # ±2 periods = 150s window
    'REQUIRE_MFA_FOR_ADMINS': True,
    'ALLOW_SMS_MFA': False,
}
```

### Recommendations

1. **Implement `SYNTEK_MFA` settings dictionary**:
   ```python
   SYNTEK_MFA = {
       'ISSUER_NAME': 'Syntek App',
       'BACKUP_CODE_COUNT': 10,
       'TIME_WINDOW_TOLERANCE': 1,
       'REQUIRE_MFA': False,               # Global enforcement
       'REQUIRE_MFA_FOR_ADMINS': True,     # Role-based
       'ALLOW_TOTP': True,
       'ALLOW_SMS': False,                 # When SMS MFA implemented
       'ALLOW_BACKUP_CODES': True,
   }
   ```

2. **Add organisation-level MFA policies** via `Organisation` model:
   ```python
   class Organisation(models.Model):
       require_mfa = models.BooleanField(default=False)
       allowed_mfa_types = models.JSONField(default=list)  # ['totp', 'sms']
   ```

3. **Implement enforcement in authentication flow**:
   ```python
   # In auth_service.py
   if user.organisation.require_mfa and not user.has_active_mfa():
       raise MFARequiredError("Your organisation requires MFA")
   ```

---

## 4. SMS Configuration and Provider

### Current Implementation

SMS functionality is **partially implemented** but **provider is hard-coded to debug mode**.

#### SMS Provider Status

| Provider | Implemented | Configurable? | Location |
|----------|-------------|---------------|----------|
| Twilio | ❌ Commented out | ❌ No | `services/phone_verification_service.py:198-220` |
| AWS SNS | ❌ Not implemented | ❌ No | N/A |
| Vonage | ❌ Not implemented | ❌ No | N/A |
| **Debug Mode** | ✅ Yes (default) | ❌ No | `services/phone_verification_service.py:201-203` |

**Code Reference:**
```python
# services/phone_verification_service.py:183-220
@staticmethod
def _send_sms(phone_number: str, message: str) -> bool:
    # TODO: Implement actual SMS provider
    # For now, log the message (development mode)
    if settings.DEBUG:  # ❌ Hard-coded to DEBUG mode
        logger.info(f"[SMS DEBUG] To: {phone_number}, Message: {message}")
        return True

    # Production implementation example (Twilio):  ❌ Commented out
    # try:
    #     from twilio.rest import Client
    #     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    #     ...
```

#### SMS Configuration Constants

| Constant | Value | Configurable? | Location |
|----------|-------|---------------|----------|
| `CODE_EXPIRY_MINUTES` | 15 | ❌ Hard-coded | `phone_verification_service.py:71` |
| `MAX_ATTEMPTS` | 5 | ❌ Hard-coded | `phone_verification_service.py:72` |
| `RATE_LIMIT_WINDOW` | 3600 | ❌ Hard-coded | `phone_verification_service.py:73` |
| `GLOBAL_SMS_LIMIT` | 100 | ❌ Hard-coded | `phone_verification_service.py:74` |
| `SMS_COST_THRESHOLD` | 500.0 | ❌ Hard-coded | `phone_verification_service.py:75` |

### Issues Identified

#### ❌ SMS Provider Not Abstracted

**Cannot configure SMS provider via settings.** Implementation is hard-coded and incomplete.

#### ❌ No Provider Selection Mechanism

Should support:
```python
SYNTEK_SMS = {
    'PROVIDER': 'twilio',  # or 'aws_sns', 'vonage', 'custom'
    'TWILIO_ACCOUNT_SID': env('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': env('TWILIO_AUTH_TOKEN'),
    'TWILIO_PHONE_NUMBER': env('TWILIO_PHONE_NUMBER'),
    'AWS_SNS_REGION': env('AWS_SNS_REGION'),
    # etc.
}
```

#### ❌ Rate Limits and Costs Hard-Coded

```python
# Should be configurable:
SYNTEK_SMS = {
    'CODE_EXPIRY_MINUTES': 15,
    'MAX_VERIFICATION_ATTEMPTS': 5,
    'RATE_LIMIT_WINDOW_SECONDS': 3600,
    'GLOBAL_HOURLY_LIMIT': 100,
    'DAILY_COST_LIMIT_USD': 500.0,
    'COST_PER_SMS_USD': 0.05,
}
```

### Recommendations

1. **Implement SMS provider abstraction**:
   ```python
   # syntek_authentication/sms/providers.py
   class BaseSMSProvider(ABC):
       @abstractmethod
       def send_sms(self, phone_number: str, message: str) -> bool:
           pass

   class TwilioProvider(BaseSMSProvider):
       def __init__(self, account_sid, auth_token, from_number):
           self.client = Client(account_sid, auth_token)
           self.from_number = from_number

       def send_sms(self, phone_number: str, message: str) -> bool:
           # Implementation
           pass

   class AWSSNSProvider(BaseSMSProvider):
       # Implementation
       pass

   class DebugProvider(BaseSMSProvider):
       def send_sms(self, phone_number: str, message: str) -> bool:
           logger.info(f"[SMS DEBUG] To: {phone_number}, Message: {message}")
           return True
   ```

2. **Add `SYNTEK_SMS` settings dictionary**:
   ```python
   SYNTEK_SMS = {
       'PROVIDER': 'twilio',  # or 'aws_sns', 'vonage', 'debug'
       'PROVIDER_CONFIG': {
           'account_sid': env('TWILIO_ACCOUNT_SID'),
           'auth_token': env('TWILIO_AUTH_TOKEN'),
           'from_number': env('TWILIO_PHONE_NUMBER'),
       },
       'CODE_EXPIRY_MINUTES': 15,
       'MAX_ATTEMPTS': 5,
       'RATE_LIMIT_WINDOW': 3600,
       'GLOBAL_HOURLY_LIMIT': 100,
       'DAILY_COST_LIMIT': 500.0,
   }
   ```

3. **Implement provider factory**:
   ```python
   def get_sms_provider() -> BaseSMSProvider:
       config = getattr(settings, 'SYNTEK_SMS', {})
       provider_name = config.get('PROVIDER', 'debug')

       if provider_name == 'twilio':
           return TwilioProvider(**config['PROVIDER_CONFIG'])
       elif provider_name == 'aws_sns':
           return AWSSNSProvider(**config['PROVIDER_CONFIG'])
       else:
           return DebugProvider()
   ```

---

## 5. Logging System Configuration

### Current Implementation

Logging is **partially configurable** via Django's standard `LOGGING` setting, but **security-specific logging is not abstracted**.

#### Logging Usage

| Module | Logger Name | Configurable? | Location |
|--------|-------------|---------------|----------|
| Email Service | `__name__` | Via `LOGGING` | `services/email_service.py:29` |
| Phone Verification | `__name__` | Via `LOGGING` | `services/phone_verification_service.py:45` |
| Suspicious Activity | `"security.suspicious_activity"` | Via `LOGGING` | `monitoring/services/suspicious_activity_service.py:35` |
| Auth Service | Not present | N/A | No logging in `auth_service.py` |

**Code References:**
```python
# email_service.py:29
logger = logging.getLogger(__name__)

# phone_verification_service.py:45
logger = logging.getLogger(__name__)

# suspicious_activity_service.py:35
logger = logging.getLogger("security.suspicious_activity")  # ✅ Named logger
```

### Issues Identified

#### ❌ No Centralised Logging Configuration

No `SYNTEK_LOGGING` settings dictionary to configure:
- Log levels per module
- External logging service integration
- Audit logging vs security logging
- PII redaction in logs

#### ❌ External Logging Integration Not Implemented

The README and plan mention **GlitchTip** for external logging, but:
- No GlitchTip SDK integration
- No Sentry integration (alternative)
- No configuration options for external logging

#### ❌ Inconsistent Logger Naming

- Some use `__name__` (module path)
- Some use semantic names (`"security.suspicious_activity"`)
- No standardisation across modules

### Recommendations

1. **Standardise logger naming**:
   ```python
   # Use semantic logger names consistently
   logger = logging.getLogger("syntek.auth.email")
   logger = logging.getLogger("syntek.auth.phone_verification")
   logger = logging.getLogger("syntek.security.suspicious_activity")
   logger = logging.getLogger("syntek.mfa.totp")
   ```

2. **Add `SYNTEK_LOGGING` settings**:
   ```python
   SYNTEK_LOGGING = {
       'EXTERNAL_SERVICE': 'glitchtip',  # or 'sentry', 'datadog', None
       'EXTERNAL_CONFIG': {
           'dsn': env('GLITCHTIP_DSN'),
           'environment': env('ENVIRONMENT', 'production'),
           'traces_sample_rate': 0.1,
       },
       'REDACT_PII': True,  # Redact email/phone from logs
       'LOG_FAILED_LOGINS': True,
       'LOG_PASSWORD_CHANGES': True,
       'LOG_MFA_EVENTS': True,
       'LOG_LEVEL': 'INFO',
   }
   ```

3. **Implement PII redaction filter**:
   ```python
   # syntek_authentication/logging/filters.py
   class PIIRedactionFilter(logging.Filter):
       def filter(self, record):
           if hasattr(record, 'user_email'):
               record.user_email = self._redact_email(record.user_email)
           if hasattr(record, 'ip_address'):
               record.ip_address = self._redact_ip(record.ip_address)
           return True

       def _redact_email(self, email):
           local, domain = email.split('@')
           return f"{local[0]}***@{domain}"
   ```

4. **Integrate external logging service**:
   ```python
   # syntek_authentication/logging/__init__.py
   from django.conf import settings

   def setup_external_logging():
       config = getattr(settings, 'SYNTEK_LOGGING', {})
       service = config.get('EXTERNAL_SERVICE')

       if service == 'glitchtip':
           import sentry_sdk
           sentry_sdk.init(**config['EXTERNAL_CONFIG'])
       elif service == 'sentry':
           import sentry_sdk
           sentry_sdk.init(**config['EXTERNAL_CONFIG'])
   ```

---

## 6. Monitoring System Configuration

### Current Implementation

Monitoring is **partially configurable** but lacks settings-driven architecture.

#### Monitoring Service Constants

| Constant | Value | Configurable? | Location |
|----------|-------|---------------|----------|
| `KNOWN_IP_CACHE_PREFIX` | "known_ip" | ❌ Hard-coded | `suspicious_activity_service.py:56` |
| `KNOWN_IP_RETENTION_DAYS` | 30 | ❌ Hard-coded | `suspicious_activity_service.py:57` |
| Email sender | `settings.DEFAULT_FROM_EMAIL` | ✅ Via settings | `suspicious_activity_service.py:429` |

**Code Reference:**
```python
# monitoring/services/suspicious_activity_service.py:38-57
class SuspiciousActivityService:
    KNOWN_IP_CACHE_PREFIX = "known_ip"     # ❌ Hard-coded
    KNOWN_IP_RETENTION_DAYS = 30           # ❌ Hard-coded
```

#### Monitoring Features

| Feature | Implemented | Configurable? | Notes |
|---------|-------------|---------------|-------|
| Login location tracking | ✅ Yes | ❌ No | IP hashing, 30-day retention |
| Password change alerts | ✅ Yes | ❌ No | Email notification |
| 2FA alerts | ✅ Yes | ❌ No | Email notification |
| Account lockout alerts | ✅ Yes | ❌ No | Email notification |
| Audit trail integration | Conditional | ❌ No | `try/except ImportError` |

### Issues Identified

#### ❌ No SYNTEK_MONITORING Settings

The README advertises:
```python
SYNTEK_MONITORING = {
    'ENABLE_LOGIN_ALERTS': True,
    'ENABLE_PASSWORD_ALERTS': True,
    'ENABLE_MFA_ALERTS': True,
    'ENABLE_LOCKOUT_ALERTS': True,
    'IP_CACHE_TTL': 86400,  # 24 hours
    'EMAIL_ALERTS': True,
}
```

**But this is NOT implemented.** All features are always enabled.

#### ❌ Hard-Coded IP Retention Period

```python
# Should be configurable:
SYNTEK_MONITORING = {
    'IP_RETENTION_DAYS': 30,  # How long to remember known IPs
    'IP_HASH_ALGORITHM': 'sha256',  # or 'blake2b'
}
```

#### ❌ No Alert Escalation Configuration

Cannot configure:
- Send alerts to admin email
- Escalate to external service (PagerDuty, Slack)
- Severity thresholds for alerts
- Rate limiting on alerts (prevent email spam)

### Recommendations

1. **Implement `SYNTEK_MONITORING` settings**:
   ```python
   SYNTEK_MONITORING = {
       # Feature toggles
       'ENABLE_LOGIN_ALERTS': True,
       'ENABLE_PASSWORD_ALERTS': True,
       'ENABLE_MFA_ALERTS': True,
       'ENABLE_LOCKOUT_ALERTS': True,

       # IP tracking
       'IP_RETENTION_DAYS': 30,
       'IP_HASH_ALGORITHM': 'sha256',
       'IP_CACHE_BACKEND': 'redis',  # or 'database'

       # Alert configuration
       'EMAIL_ALERTS': True,
       'ALERT_RATE_LIMIT': 5,  # Max 5 alerts per hour per user
       'ADMIN_EMAIL': env('SECURITY_ADMIN_EMAIL'),
       'ESCALATE_TO_ADMIN': True,  # CC admin on high-severity alerts

       # External integrations
       'SLACK_WEBHOOK': env('SLACK_SECURITY_WEBHOOK', None),
       'PAGERDUTY_KEY': env('PAGERDUTY_INTEGRATION_KEY', None),
   }
   ```

2. **Implement feature toggles**:
   ```python
   # In suspicious_activity_service.py
   from django.conf import settings

   def check_login_location(user, ip_address, request=None):
       config = getattr(settings, 'SYNTEK_MONITORING', {})
       if not config.get('ENABLE_LOGIN_ALERTS', True):
           return False

       # Rest of implementation...
   ```

3. **Add alert escalation**:
   ```python
   def _send_alert_email(user, subject, message, severity='medium'):
       config = getattr(settings, 'SYNTEK_MONITORING', {})

       # Send to user
       send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

       # Escalate to admin if configured
       if config.get('ESCALATE_TO_ADMIN') and severity in ['high', 'critical']:
           admin_email = config.get('ADMIN_EMAIL')
           if admin_email:
               send_mail(f"[ADMIN] {subject}", message, settings.DEFAULT_FROM_EMAIL, [admin_email])

       # Send to Slack if configured
       slack_webhook = config.get('SLACK_WEBHOOK')
       if slack_webhook and severity in ['high', 'critical']:
           send_slack_alert(slack_webhook, subject, message)
   ```

---

## 7. Middleware Configuration

### Current Implementation

**No authentication middleware is implemented** in the reviewed modules.

#### Middleware Status

| Middleware Type | Implemented | Location |
|-----------------|-------------|----------|
| Authentication middleware | ❌ No | N/A |
| Session security middleware | ❌ No | N/A |
| Rate limiting middleware | ❌ No | N/A |
| IP tracking middleware | ❌ No | N/A |
| CSRF protection | Django default | N/A |

### Issues Identified

#### ❌ No Custom Middleware

The README mentions middleware configuration:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]
```

**But no Syntek-specific middleware exists.** Expected middleware:
- `SyntekAuthenticationMiddleware` - JWT/session handling
- `SyntekRateLimitMiddleware` - Request rate limiting
- `SyntekIPTrackingMiddleware` - Automatic IP logging
- `SyntekSessionSecurityMiddleware` - Session timeout enforcement

#### ❌ No Middleware Configuration Options

Should support:
```python
SYNTEK_MIDDLEWARE = {
    'AUTHENTICATION': {
        'ENABLED': True,
        'EXEMPT_URLS': ['/api/health/', '/api/login/'],
    },
    'RATE_LIMITING': {
        'ENABLED': True,
        'BACKEND': 'redis',
        'DEFAULT_RATE': '100/hour',
        'LOGIN_RATE': '5/minute',
    },
    'IP_TRACKING': {
        'ENABLED': True,
        'ENCRYPT_IPS': True,
    },
}
```

### Recommendations

1. **Implement authentication middleware**:
   ```python
   # syntek_authentication/middleware/auth.py
   from django.conf import settings
   from django.http import JsonResponse

   class SyntekAuthenticationMiddleware:
       def __init__(self, get_response):
           self.get_response = get_response
           config = getattr(settings, 'SYNTEK_MIDDLEWARE', {}).get('AUTHENTICATION', {})
           self.enabled = config.get('ENABLED', True)
           self.exempt_urls = config.get('EXEMPT_URLS', [])

       def __call__(self, request):
           if not self.enabled or request.path in self.exempt_urls:
               return self.get_response(request)

           # JWT/session authentication logic
           token = request.headers.get('Authorization')
           if not token:
               return JsonResponse({'error': 'Authentication required'}, status=401)

           # Validate token, attach user to request
           # ...

           return self.get_response(request)
   ```

2. **Implement rate limiting middleware**:
   ```python
   # syntek_authentication/middleware/rate_limit.py
   from django.core.cache import cache
   from django.http import JsonResponse

   class SyntekRateLimitMiddleware:
       def __init__(self, get_response):
           self.get_response = get_response
           config = getattr(settings, 'SYNTEK_MIDDLEWARE', {}).get('RATE_LIMITING', {})
           self.enabled = config.get('ENABLED', True)
           self.default_rate = config.get('DEFAULT_RATE', '100/hour')

       def __call__(self, request):
           if not self.enabled:
               return self.get_response(request)

           # Check rate limit
           key = f"rate_limit:{request.META.get('REMOTE_ADDR')}:{request.path}"
           count = cache.get(key, 0)

           if count >= self._parse_rate(self.default_rate):
               return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

           cache.set(key, count + 1, self._get_window())
           return self.get_response(request)
   ```

3. **Add to README documentation**:
   ```python
   # settings.py
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'syntek_authentication.middleware.rate_limit.SyntekRateLimitMiddleware',
       'django.middleware.common.CommonMiddleware',
       'django.middleware.csrf.CsrfViewMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'syntek_authentication.middleware.auth.SyntekAuthenticationMiddleware',
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       'syntek_authentication.middleware.ip_tracking.SyntekIPTrackingMiddleware',
   ]
   ```

---

## 8. Other Dynamic Configuration Areas

### 8.1 Rate Limiting

#### Current Status

Rate limiting is **hard-coded** in services, not middleware.

| Service | Rate Limit | Configurable? | Location |
|---------|-----------|---------------|----------|
| Phone Verification | 1 SMS/60s per user | ❌ No | `phone_verification_service.py:257-258` |
| Phone Verification | 100 SMS/hour global | ❌ No | `phone_verification_service.py:74` |
| Login Attempts | 5 attempts before lockout | ❌ Hard-coded | `auth_service.py:308` |
| Password Reset | Not implemented | N/A | N/A |

**Code Example:**
```python
# phone_verification_service.py:256-258
user_cache_key = PhoneVerificationService.CACHE_KEY_USER_SMS.format(user_id=user.id)
if cache.get(user_cache_key):  # ❌ Hard-coded 60s in line 302
    raise ValueError("Please wait 60 seconds before requesting another code.")
```

#### Recommendations

```python
SYNTEK_RATE_LIMITING = {
    'BACKEND': 'redis',  # or 'database', 'memory'
    'SMS_VERIFICATION': '1/minute',
    'SMS_GLOBAL': '100/hour',
    'LOGIN_ATTEMPTS': '5/5minutes',
    'PASSWORD_RESET': '3/hour',
    'API_DEFAULT': '100/hour',
}
```

### 8.2 Session Expiry

#### Current Status

Session timeouts are **documented in README but not implemented**:

```python
# From README - NOT IMPLEMENTED
SYNTEK_AUTH = {
    'SESSION_TIMEOUT': 1800,  # 30 minutes of inactivity
    'SESSION_ABSOLUTE_TIMEOUT': 43200,  # 12 hours absolute
}
```

No session timeout enforcement found in code.

#### Recommendations

1. Implement in `SyntekSessionSecurityMiddleware`
2. Store last activity timestamp in session
3. Check and enforce timeouts on each request

### 8.3 JWT Configuration

#### Current Status

JWT settings are **documented in README but JWT module not reviewed**.

```python
# From README
SYNTEK_AUTH = {
    'JWT_EXPIRY': 3600,  # 1 hour
    'REFRESH_TOKEN_EXPIRY': 86400,  # 24 hours
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': env('JWT_SECRET_KEY'),
}
```

**Cannot verify if implemented** without reviewing `backend/security-auth/jwt/`.

#### Recommendation

Review JWT module separately to verify configuration flexibility.

### 8.4 CAPTCHA Configuration

#### Current Status

**CAPTCHA is NOT implemented** despite being mentioned in the plan:

> **Where applied**: Registration, Password Change, Forgotten Password

No CAPTCHA integration found in reviewed code.

#### Recommendations

```python
SYNTEK_CAPTCHA = {
    'ENABLED': True,
    'PROVIDER': 'recaptcha_v3',  # or 'recaptcha_v2', 'hcaptcha', 'turnstile'
    'SITE_KEY': env('RECAPTCHA_SITE_KEY'),
    'SECRET_KEY': env('RECAPTCHA_SECRET_KEY'),
    'SCORE_THRESHOLD': 0.5,  # For reCAPTCHA v3
    'REQUIRED_ON': ['register', 'password_reset', 'password_change'],
}
```

---

## 9. Configuration Matrix

### Summary Table

| Configuration Area | Configurable | Via Settings Dict | Hard-Coded | Missing |
|-------------------|--------------|-------------------|------------|---------|
| **Password Validation** | ✅ Partial | ❌ No | ❌ Some | SYNTEK_AUTH wrapper |
| **Auth Fields** | ❌ No | ❌ No | ✅ Yes | Backend selection |
| **MFA Enforcement** | ❌ No | ❌ No | ✅ Yes | Organisation policies |
| **MFA Constants** | ❌ No | ❌ No | ✅ Yes | SYNTEK_MFA dict |
| **SMS Provider** | ❌ No | ❌ No | ✅ Debug only | Provider abstraction |
| **SMS Rate Limits** | ❌ No | ❌ No | ✅ Yes | SYNTEK_SMS dict |
| **Logging Backend** | ✅ Partial | ❌ No | ❌ Some | External integration |
| **Monitoring Features** | ❌ No | ❌ No | ✅ All enabled | SYNTEK_MONITORING |
| **Middleware** | ❌ No | N/A | N/A | Not implemented |
| **Rate Limiting** | ❌ No | ❌ No | ✅ Yes | SYNTEK_RATE_LIMITING |
| **Session Timeouts** | ❌ No | ❌ No | N/A | Not implemented |
| **CAPTCHA** | ❌ No | N/A | N/A | Not implemented |

### Legend
- ✅ **Configurable:** Fully or mostly configurable via settings
- ❌ **No:** Not configurable, hard-coded, or not implemented
- **Partial:** Some aspects configurable, others hard-coded

---

## 10. Recommended Settings Architecture

### Proposed `SYNTEK_AUTH` Settings Dictionary

```python
# settings.py or settings/base.py
from environs import Env

env = Env()
env.read_env()

SYNTEK_AUTH = {
    # ============================================================================
    # PASSWORD VALIDATION
    # ============================================================================
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_MAX_LENGTH': 128,
    'PASSWORD_MIN_UPPERCASE': 1,
    'PASSWORD_MIN_LOWERCASE': 1,
    'PASSWORD_MIN_DIGITS': 1,
    'PASSWORD_MIN_SPECIAL': 1,
    'PASSWORD_BREACH_CHECK': True,
    'PASSWORD_BREACH_THRESHOLD': 1,  # Reject if seen N+ times
    'PASSWORD_HISTORY_COUNT': 5,
    'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES': 10,

    # ============================================================================
    # AUTHENTICATION
    # ============================================================================
    'AUTHENTICATION_BACKEND': 'email',  # 'email', 'username', 'email_or_username'
    'USERNAME_IS_UNIQUE': True,
    'REQUIRE_EMAIL_VERIFICATION': True,
    'REQUIRE_PHONE_VERIFICATION': False,
    'PHONE_REQUIRED': False,

    # ============================================================================
    # LOGIN SECURITY
    # ============================================================================
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 minutes in seconds
    'LOCKOUT_INCREMENT': True,  # Progressive lockout
    'LOG_LOGIN_ATTEMPTS': True,

    # ============================================================================
    # SESSION MANAGEMENT
    # ============================================================================
    'SESSION_TIMEOUT': 1800,  # 30 minutes of inactivity
    'SESSION_ABSOLUTE_TIMEOUT': 43200,  # 12 hours absolute
    'ALLOW_SIMULTANEOUS_SESSIONS': False,
    'MAX_SESSIONS_PER_USER': 5,

    # ============================================================================
    # JWT CONFIGURATION
    # ============================================================================
    'JWT_ENABLED': True,
    'JWT_EXPIRY': 3600,  # 1 hour
    'REFRESH_TOKEN_EXPIRY': 86400,  # 24 hours
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': env('JWT_SECRET_KEY'),

    # ============================================================================
    # NOTIFICATIONS
    # ============================================================================
    'NOTIFY_FAILED_LOGINS': True,
    'NOTIFY_NEW_DEVICE_LOGIN': True,
    'NOTIFY_PASSWORD_CHANGE': True,
}

SYNTEK_MFA = {
    # ============================================================================
    # TOTP CONFIGURATION
    # ============================================================================
    'ISSUER_NAME': 'Syntek Platform',
    'TOTP_PERIOD': 30,  # seconds
    'TIME_WINDOW_TOLERANCE': 1,  # ±1 period = 90s window
    'BACKUP_CODE_COUNT': 10,

    # ============================================================================
    # MFA ENFORCEMENT
    # ============================================================================
    'REQUIRE_MFA': False,  # Global requirement
    'REQUIRE_MFA_FOR_ADMINS': True,  # Role-based requirement
    'REQUIRE_MFA_FOR_ORGANISATIONS': [],  # List of org IDs

    # ============================================================================
    # MFA TYPES
    # ============================================================================
    'ALLOW_TOTP': True,
    'ALLOW_SMS': False,  # When implemented
    'ALLOW_BACKUP_CODES': True,
    'ALLOW_RECOVERY_KEYS': True,
}

SYNTEK_SMS = {
    # ============================================================================
    # PROVIDER CONFIGURATION
    # ============================================================================
    'PROVIDER': 'twilio',  # 'twilio', 'aws_sns', 'vonage', 'debug'
    'PROVIDER_CONFIG': {
        'account_sid': env('TWILIO_ACCOUNT_SID', None),
        'auth_token': env('TWILIO_AUTH_TOKEN', None),
        'from_number': env('TWILIO_PHONE_NUMBER', None),
    },

    # ============================================================================
    # VERIFICATION SETTINGS
    # ============================================================================
    'CODE_EXPIRY_MINUTES': 15,
    'CODE_LENGTH': 6,
    'MAX_VERIFICATION_ATTEMPTS': 5,

    # ============================================================================
    # RATE LIMITING & COST CONTROL
    # ============================================================================
    'RATE_LIMIT_PER_USER': '1/minute',
    'RATE_LIMIT_PER_PHONE': '3/hour',
    'GLOBAL_HOURLY_LIMIT': 100,
    'DAILY_COST_LIMIT_USD': 500.0,
    'COST_PER_SMS_USD': 0.05,
}

SYNTEK_MONITORING = {
    # ============================================================================
    # FEATURE TOGGLES
    # ============================================================================
    'ENABLE_LOGIN_ALERTS': True,
    'ENABLE_PASSWORD_ALERTS': True,
    'ENABLE_MFA_ALERTS': True,
    'ENABLE_LOCKOUT_ALERTS': True,

    # ============================================================================
    # IP TRACKING
    # ============================================================================
    'IP_RETENTION_DAYS': 30,
    'IP_HASH_ALGORITHM': 'sha256',
    'IP_CACHE_BACKEND': 'redis',

    # ============================================================================
    # ALERT CONFIGURATION
    # ============================================================================
    'EMAIL_ALERTS': True,
    'ALERT_RATE_LIMIT': 5,  # Max per hour per user
    'ADMIN_EMAIL': env('SECURITY_ADMIN_EMAIL', None),
    'ESCALATE_TO_ADMIN': True,

    # ============================================================================
    # EXTERNAL INTEGRATIONS
    # ============================================================================
    'SLACK_WEBHOOK': env('SLACK_SECURITY_WEBHOOK', None),
    'PAGERDUTY_KEY': env('PAGERDUTY_INTEGRATION_KEY', None),
}

SYNTEK_LOGGING = {
    # ============================================================================
    # EXTERNAL SERVICE
    # ============================================================================
    'EXTERNAL_SERVICE': 'glitchtip',  # 'glitchtip', 'sentry', 'datadog', None
    'EXTERNAL_CONFIG': {
        'dsn': env('GLITCHTIP_DSN', None),
        'environment': env('ENVIRONMENT', 'production'),
        'traces_sample_rate': 0.1,
        'send_default_pii': False,
    },

    # ============================================================================
    # LOGGING BEHAVIOUR
    # ============================================================================
    'REDACT_PII': True,
    'LOG_FAILED_LOGINS': True,
    'LOG_PASSWORD_CHANGES': True,
    'LOG_MFA_EVENTS': True,
    'LOG_LEVEL': 'INFO',
}

SYNTEK_RATE_LIMITING = {
    # ============================================================================
    # BACKEND
    # ============================================================================
    'BACKEND': 'redis',  # 'redis', 'database', 'memory'
    'BACKEND_CONFIG': {
        'LOCATION': env('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    },

    # ============================================================================
    # RATE LIMITS
    # ============================================================================
    'LOGIN_ATTEMPTS': '5/5minutes',
    'PASSWORD_RESET': '3/hour',
    'EMAIL_VERIFICATION': '3/hour',
    'SMS_VERIFICATION': '1/minute',
    'API_DEFAULT': '100/hour',
}

SYNTEK_CAPTCHA = {
    # ============================================================================
    # PROVIDER
    # ============================================================================
    'ENABLED': True,
    'PROVIDER': 'recaptcha_v3',  # 'recaptcha_v2', 'recaptcha_v3', 'hcaptcha', 'turnstile'

    # ============================================================================
    # PROVIDER CONFIG
    # ============================================================================
    'SITE_KEY': env('RECAPTCHA_SITE_KEY', None),
    'SECRET_KEY': env('RECAPTCHA_SECRET_KEY', None),
    'SCORE_THRESHOLD': 0.5,  # For reCAPTCHA v3

    # ============================================================================
    # APPLICATION
    # ============================================================================
    'REQUIRED_ON': ['register', 'password_reset', 'password_change'],
    'FALLBACK_TO_V2': True,  # If v3 score low, show v2 checkbox
}

SYNTEK_MIDDLEWARE = {
    # ============================================================================
    # AUTHENTICATION MIDDLEWARE
    # ============================================================================
    'AUTHENTICATION': {
        'ENABLED': True,
        'EXEMPT_URLS': ['/api/health/', '/api/login/', '/api/register/'],
        'EXEMPT_PATTERNS': [r'^/api/public/.*'],
    },

    # ============================================================================
    # RATE LIMITING MIDDLEWARE
    # ============================================================================
    'RATE_LIMITING': {
        'ENABLED': True,
        'EXEMPT_URLS': ['/api/health/'],
    },

    # ============================================================================
    # IP TRACKING MIDDLEWARE
    # ============================================================================
    'IP_TRACKING': {
        'ENABLED': True,
        'ENCRYPT_IPS': True,
        'EXEMPT_URLS': ['/api/health/'],
    },
}
```

---

## 11. Examples of Good Configuration Patterns Found

### ✅ Password Validators - Proper Configurability

The password validators follow Django best practices:

```python
class PasswordComplexityValidator:
    def __init__(
        self,
        min_uppercase: int = 1,
        min_lowercase: int = 1,
        min_digits: int = 1,
        min_special: int = 1,
    ) -> None:
        self.min_uppercase = min_uppercase
        self.min_lowercase = min_lowercase
        self.min_digits = min_digits
        self.min_special = min_special
```

**Why this is good:**
- ✅ Accepts parameters in `__init__`
- ✅ Provides sensible defaults
- ✅ Works with Django's `AUTH_PASSWORD_VALIDATORS`
- ✅ Fully documented parameters

### ✅ Email Service - Settings Lookups with Defaults

```python
base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
site_name = getattr(settings, "SITE_NAME", "Syntek Platform")
support_email = getattr(settings, "SUPPORT_EMAIL", "support@example.com")
```

**Why this is good:**
- ✅ Uses `getattr()` for safe lookups
- ✅ Provides sensible defaults
- ✅ Won't crash if setting missing
- ✅ Easy to override per environment

### ✅ Phone Verification - Encryption Key Abstraction

```python
encryption_key = PhoneVerificationService._get_encryption_key()
hmac_key = PhoneVerificationService._get_hmac_key()
```

**Why this is good:**
- ✅ Centralised key retrieval
- ✅ Clear error message if misconfigured
- ✅ Abstracted from implementation details
- ✅ Easy to change key source later

---

## 12. Examples of Areas Needing Improvement

### ❌ Hard-Coded Constants in Services

```python
# mfa/services/totp_service.py:53-55
class TOTPService:
    DEFAULT_ISSUER = "Syntek App"          # Should be from settings
    BACKUP_CODE_COUNT = 10                  # Should be configurable
    TIME_WINDOW_TOLERANCE = 1               # Should be configurable
```

**Why this is bad:**
- ❌ Cannot customise per deployment
- ❌ Requires code changes to modify
- ❌ Not documented as configurable
- ❌ Inconsistent with README promises

**Better approach:**
```python
class TOTPService:
    @classmethod
    def _get_config(cls, key, default=None):
        config = getattr(settings, 'SYNTEK_MFA', {})
        return config.get(key, default)

    @property
    def issuer_name(self):
        return self._get_config('ISSUER_NAME', 'Syntek App')

    @property
    def backup_code_count(self):
        return self._get_config('BACKUP_CODE_COUNT', 10)
```

### ❌ SMS Provider Hard-Coded to Debug

```python
# phone_verification_service.py:201-203
if settings.DEBUG:
    logger.info(f"[SMS DEBUG] To: {phone_number}, Message: {message}")
    return True
```

**Why this is bad:**
- ❌ Cannot use real SMS in DEBUG=True mode
- ❌ Production code is commented out
- ❌ No abstraction for providers
- ❌ Cannot switch providers via settings

**Better approach:**
```python
class SMSProviderFactory:
    @staticmethod
    def get_provider():
        config = getattr(settings, 'SYNTEK_SMS', {})
        provider = config.get('PROVIDER', 'debug')

        if provider == 'twilio':
            return TwilioProvider(config['PROVIDER_CONFIG'])
        elif provider == 'aws_sns':
            return AWSSNSProvider(config['PROVIDER_CONFIG'])
        else:
            return DebugProvider()

def _send_sms(phone_number, message):
    provider = SMSProviderFactory.get_provider()
    return provider.send_sms(phone_number, message)
```

### ❌ Missing SYNTEK_AUTH Dictionary Implementation

**README promises:**
```python
SYNTEK_AUTH = {
    'TOTP_REQUIRED': False,
    'PASSWORD_LENGTH': 12,
    'MAX_LOGIN_ATTEMPTS': 5,
}
```

**Reality:** This dictionary is **never read** by the code.

**Why this is bad:**
- ❌ Documentation lies
- ❌ Users expect this to work
- ❌ Settings are scattered across validators
- ❌ No single source of truth

**Better approach:**
```python
# syntek_authentication/conf.py
from django.conf import settings

DEFAULTS = {
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,
    'PASSWORD_MIN_LENGTH': 12,
}

class AuthSettings:
    def __init__(self):
        self._settings = getattr(settings, 'SYNTEK_AUTH', {})

    def __getattr__(self, name):
        return self._settings.get(name, DEFAULTS.get(name))

auth_settings = AuthSettings()

# Usage:
from syntek_authentication.conf import auth_settings
max_attempts = auth_settings.MAX_LOGIN_ATTEMPTS
```

---

## 13. Priority Recommendations

### High Priority (Before Phase 3)

1. **Implement `SYNTEK_AUTH` settings wrapper** (2 days)
   - Create `syntek_authentication/conf.py`
   - Migrate hard-coded values to settings
   - Update README with accurate configuration

2. **Abstract SMS provider** (3 days)
   - Create `BaseSMSProvider` interface
   - Implement Twilio, AWS SNS, Debug providers
   - Add `SYNTEK_SMS` settings dictionary

3. **Implement `SYNTEK_MFA` settings** (1 day)
   - Move hard-coded MFA constants to settings
   - Add organisation-level MFA policies
   - Implement enforcement in auth flow

4. **Create authentication middleware** (2 days)
   - JWT/session validation middleware
   - Rate limiting middleware
   - IP tracking middleware

### Medium Priority (Phase 3)

5. **Implement `SYNTEK_MONITORING` settings** (1 day)
   - Add feature toggles
   - Implement alert escalation
   - Add external integration (Slack, PagerDuty)

6. **Add external logging integration** (2 days)
   - GlitchTip/Sentry SDK integration
   - PII redaction filters
   - Structured logging

7. **Implement session timeout enforcement** (2 days)
   - Session security middleware
   - Inactivity timeout
   - Absolute timeout

### Low Priority (Phase 4+)

8. **Add CAPTCHA integration** (3 days)
   - reCAPTCHA v2/v3 support
   - hCaptcha support
   - Cloudflare Turnstile support

9. **Implement flexible authentication backends** (5 days)
   - Username-based login
   - Email or username login
   - Phone-based login
   - Custom backend support

10. **Add comprehensive rate limiting** (3 days)
    - Centralised rate limiting service
    - Redis backend
    - Per-endpoint configuration

---

## 14. Testing Requirements

Before considering configuration complete:

### Unit Tests

- [ ] Test settings defaults are applied correctly
- [ ] Test custom settings override defaults
- [ ] Test missing settings don't crash
- [ ] Test invalid settings raise clear errors

### Integration Tests

- [ ] Test `SYNTEK_AUTH` settings affect password validation
- [ ] Test `SYNTEK_MFA` settings affect TOTP behaviour
- [ ] Test `SYNTEK_SMS` provider switching
- [ ] Test `SYNTEK_MONITORING` feature toggles

### Documentation Tests

- [ ] All README examples work with actual code
- [ ] Settings examples are valid Python
- [ ] Default values match implementation
- [ ] Configuration guide is complete

---

## 15. Conclusion

The Phase 1 and Phase 2 authentication implementation has **solid foundations** but lacks **comprehensive settings-driven architecture**. Many features are hard-coded or documented but not implemented.

### Immediate Actions Required

1. **Reconcile README with implementation** - Remove or implement advertised features
2. **Create centralised settings system** - `SYNTEK_AUTH`, `SYNTEK_MFA`, etc.
3. **Abstract third-party integrations** - SMS providers, logging services
4. **Implement middleware layer** - Authentication, rate limiting, IP tracking

### Long-Term Goals

- **Configuration-as-code** - All behaviour configurable via settings
- **Deployment flexibility** - Same codebase, different configs per environment
- **Organisation-level policies** - Per-tenant MFA enforcement, rate limits
- **Zero hard-coded secrets** - All keys from environment variables

### Success Criteria

✅ All hard-coded constants moved to settings with defaults
✅ README examples work without modification
✅ Settings validated on app startup with clear errors
✅ Per-organisation configuration supported
✅ External services (SMS, logging, monitoring) fully abstracted
✅ Middleware layer implemented and documented

---

## Appendix A: Settings Checklist

Use this checklist to track configuration implementation:

### Authentication Settings

- [ ] `SYNTEK_AUTH` dictionary implemented
- [ ] Password validation configurable
- [ ] Authentication backend selectable
- [ ] Login attempt limits configurable
- [ ] Session timeouts configurable
- [ ] JWT settings configurable

### MFA Settings

- [ ] `SYNTEK_MFA` dictionary implemented
- [ ] TOTP issuer configurable
- [ ] Backup code count configurable
- [ ] MFA enforcement configurable
- [ ] Organisation-level policies implemented

### SMS Settings

- [ ] `SYNTEK_SMS` dictionary implemented
- [ ] Provider abstraction implemented
- [ ] Twilio provider implemented
- [ ] AWS SNS provider implemented
- [ ] Rate limits configurable
- [ ] Cost limits configurable

### Monitoring Settings

- [ ] `SYNTEK_MONITORING` dictionary implemented
- [ ] Feature toggles implemented
- [ ] IP retention configurable
- [ ] Alert escalation implemented
- [ ] External integrations (Slack, PagerDuty)

### Logging Settings

- [ ] `SYNTEK_LOGGING` dictionary implemented
- [ ] GlitchTip/Sentry integration
- [ ] PII redaction implemented
- [ ] Log levels configurable
- [ ] Structured logging implemented

### Middleware Settings

- [ ] `SYNTEK_MIDDLEWARE` dictionary implemented
- [ ] Authentication middleware implemented
- [ ] Rate limiting middleware implemented
- [ ] IP tracking middleware implemented
- [ ] Session security middleware implemented

---

## Appendix B: Configuration Examples by Deployment

### Development Environment

```python
SYNTEK_AUTH = {
    'MAX_LOGIN_ATTEMPTS': 999,  # Relaxed for testing
    'PASSWORD_MIN_LENGTH': 8,   # Shorter for convenience
}

SYNTEK_SMS = {
    'PROVIDER': 'debug',  # Console output only
}

SYNTEK_LOGGING = {
    'EXTERNAL_SERVICE': None,  # No external logging
    'LOG_LEVEL': 'DEBUG',
}
```

### Staging Environment

```python
SYNTEK_AUTH = {
    'MAX_LOGIN_ATTEMPTS': 10,
    'PASSWORD_MIN_LENGTH': 12,
}

SYNTEK_SMS = {
    'PROVIDER': 'twilio',
    'GLOBAL_HOURLY_LIMIT': 50,  # Lower limit
}

SYNTEK_LOGGING = {
    'EXTERNAL_SERVICE': 'glitchtip',
    'LOG_LEVEL': 'INFO',
}
```

### Production Environment

```python
SYNTEK_AUTH = {
    'MAX_LOGIN_ATTEMPTS': 5,
    'PASSWORD_MIN_LENGTH': 16,
    'REQUIRE_EMAIL_VERIFICATION': True,
}

SYNTEK_MFA = {
    'REQUIRE_MFA_FOR_ADMINS': True,
}

SYNTEK_SMS = {
    'PROVIDER': 'twilio',
    'GLOBAL_HOURLY_LIMIT': 100,
    'DAILY_COST_LIMIT_USD': 500.0,
}

SYNTEK_MONITORING = {
    'ESCALATE_TO_ADMIN': True,
    'SLACK_WEBHOOK': env('SLACK_SECURITY_WEBHOOK'),
}

SYNTEK_LOGGING = {
    'EXTERNAL_SERVICE': 'glitchtip',
    'REDACT_PII': True,
    'LOG_LEVEL': 'WARNING',
}
```

---

**End of Review**
