# GraphQL Security Extensions

Advanced security extensions for Strawberry GraphQL providing operation-level protection against attacks and abuse.

## Overview

This module provides security extensions beyond basic query depth/complexity limiting:

1. **Rate Limiting** - Granular per-operation rate limits with global SMS cost protection
2. **Constant-Time Responses** - Prevent timing attacks on authentication operations
3. **CAPTCHA Validation** - Protect against automated attacks
4. **Input Sanitisation** - XSS and SQL injection prevention
5. **Session Fingerprinting** - Detect session hijacking
6. **Suspicious Activity Detection** - Pattern-based threat detection

## Extensions

### 1. OperationRateLimitExtension

Granular rate limiting per GraphQL operation with Redis-backed counters.

**Features:**
- Operation-specific rate limits (e.g., `sendPhoneVerification: 3/hour`)
- IP-based and user-based scoping
- Distributed rate limiting via Redis
- Automatic retry-after calculation

**Configuration:**

```python
# settings.py
GRAPHQL_RATE_LIMITS = {
    "sendPhoneVerification": "3/hour",
    "verifyPhone": "5/15min",
    "login": "5/15min",
    "totpVerify": "5/15min",
    "requestPasswordReset": "3/hour",
    "register": "10/hour",
}
GRAPHQL_DEFAULT_RATE_LIMIT = "100/hour"  # For unconfigured operations
```

**Usage:**

```python
from syntek_graphql_core import OperationRateLimitExtension

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[OperationRateLimitExtension],
)
```

**Rate Limit Format:**
- `3/hour` - 3 requests per hour
- `5/15min` - 5 requests per 15 minutes
- `10/day` - 10 requests per day
- `100/min` - 100 requests per minute

---

### 2. GlobalSMSRateLimitExtension

Prevent SMS cost attacks with global budget tracking.

**Features:**
- Global hourly SMS limit (shared across all instances)
- Daily budget tracking (prevent cost overruns)
- Alert system at 80% threshold
- Email notifications for approaching limits
- Integration with cost analytics

**Configuration:**

```python
# settings.py
GRAPHQL_GLOBAL_SMS_LIMIT = 1000  # Max SMS per hour
GRAPHQL_GLOBAL_SMS_BUDGET = 500  # Max daily spend (currency units)
GRAPHQL_SMS_COST_PER_MESSAGE = 0.05  # Cost per SMS
GRAPHQL_SMS_ALERT_THRESHOLD = 0.8  # Alert at 80%
GRAPHQL_SMS_ALERT_EMAIL = "security@example.com"
```

**Usage:**

```python
from syntek_graphql_core import GlobalSMSRateLimitExtension, OperationRateLimitExtension

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        OperationRateLimitExtension,  # Per-IP limits
        GlobalSMSRateLimitExtension,  # Global SMS protection
    ],
)
```

**Alert Example:**

When SMS usage reaches 80% of hourly limit or daily budget, an email alert is sent:

```
Subject: SMS Alert: SMS hourly usage at 82.5% (825/1000)

The global SMS hourly limit is approaching capacity.
Current usage: 825 messages sent out of 1000 allowed per hour.

Please investigate potential abuse.
```

---

### 3. ConstantTimeResponseExtension

Prevent timing attacks by ensuring authentication operations take fixed time.

**Features:**
- Fixed minimum response time for auth operations
- Automatic sleep to reach target duration
- Timing anomaly detection and logging
- Prevents username/email enumeration

**Configuration:**

```python
# settings.py
GRAPHQL_CONSTANT_TIME_DURATION = 0.2  # 200ms minimum
GRAPHQL_CONSTANT_TIME_ENABLED = True
GRAPHQL_CONSTANT_TIME_OPERATIONS = [
    "login", "verifyEmail", "verifyPhone", "totpVerify",
    "resetPassword", "changePassword", "register"
]
```

**Usage:**

```python
from syntek_graphql_core import ConstantTimeResponseExtension

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[ConstantTimeResponseExtension],
)
```

**How It Works:**

1. Record start time before execution
2. Execute the operation normally
3. Calculate elapsed time
4. Sleep for `target_duration - elapsed` to reach minimum time
5. Log unusually fast/slow responses

**Example:**

```
Operation: login
Actual execution: 45ms
Sleep duration: 155ms
Total response time: 200ms (constant)

Result: Prevents attackers from determining if email exists based on response time
```

---

### 4. CaptchaValidationExtension

Validate CAPTCHA tokens to prevent automated attacks.

**Features:**
- Support for reCAPTCHA v2, v3, and hCaptcha
- Score-based validation for reCAPTCHA v3
- Configurable per-operation requirements
- Automatic application after rate limit violations

**Configuration:**

```python
# settings.py
RECAPTCHA_SECRET_KEY = "your-recaptcha-secret-key"
RECAPTCHA_VERSION = "v3"  # or "v2"
RECAPTCHA_V3_MIN_SCORE = 0.5  # Minimum score for v3 (0.0-1.0)

# Optional: hCaptcha
HCAPTCHA_SECRET_KEY = "your-hcaptcha-secret-key"

GRAPHQL_CAPTCHA_REQUIRED = [
    "register",
    "requestPasswordReset",
    "changePassword",
]
GRAPHQL_CAPTCHA_ENABLED = True
```

**Usage:**

```python
from syntek_graphql_core import CaptchaValidationExtension

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[CaptchaValidationExtension],
)
```

**Client-Side Integration:**

```graphql
mutation RegisterUser($input: RegisterInput!) {
    register(
        email: $input.email,
        password: $input.password,
        captchaToken: $input.captchaToken  # Required
    ) {
        success
        user { id email }
    }
}
```

---

### 5. InputSanitisationExtension

Sanitise user inputs to prevent injection attacks.

**Features:**
- XSS prevention (HTML/JavaScript escaping)
- SQL injection pattern detection
- Command injection prevention
- Path traversal prevention
- Configurable sanitisation levels
- HTML-allowed fields for rich text

**Configuration:**

```python
# settings.py
GRAPHQL_SANITISE_INPUTS = True
GRAPHQL_SANITISATION_LEVEL = "moderate"  # "strict", "moderate", "lenient"
GRAPHQL_ALLOW_HTML_FIELDS = ["description", "bio", "content"]  # Rich text fields
GRAPHQL_LOG_SANITISATION = True
```

**Usage:**

```python
from syntek_graphql_core import InputSanitisationExtension

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[InputSanitisationExtension],
)
```

**Sanitisation Levels:**

| Level      | Description                                    | Use Case                     |
| ---------- | ---------------------------------------------- | ---------------------------- |
| `strict`   | Aggressive - strips most special characters    | High-security environments   |
| `moderate` | Balanced - escapes dangerous patterns          | General production use       |
| `lenient`  | Minimal - blocks only obvious attacks          | Development/trusted users    |

**Example:**

```python
# Input:
{
    "name": "<script>alert('XSS')</script>John",
    "bio": "SELECT * FROM users WHERE id = 1 OR 1=1"
}

# After moderate sanitisation:
{
    "name": "&lt;script&gt;alert('XSS')&lt;/script&gt;John",
    "bio": "* FROM users WHERE id = 1 1=1"  # SQL patterns removed
}
```

---

### 6. SessionFingerprintExtension

Detect session hijacking via device fingerprinting.

**Features:**
- User-Agent tracking
- IP address network tracking (/24 for privacy)
- Accept-Language fingerprinting
- Session consistency validation
- Logging mode or strict blocking mode

**Configuration:**

```python
# settings.py
GRAPHQL_FINGERPRINT_ENABLED = True
GRAPHQL_FINGERPRINT_STRICT = False  # Log only, don't block
GRAPHQL_FINGERPRINT_CACHE_TTL = 86400  # 24 hours
```

**Usage:**

```python
from syntek_graphql_core import SessionFingerprintExtension

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[SessionFingerprintExtension],
)
```

**How It Works:**

1. On first authenticated request, generate fingerprint from:
   - User-Agent (browser/OS)
   - Accept-Language (browser locale)
   - Accept-Encoding
   - IP network (/24 prefix for privacy)
   - Optional: Screen resolution, platform

2. Store fingerprint hash in cache (key: `session_fingerprint:{user_id}`)

3. On subsequent requests, compare current fingerprint with stored

4. If mismatch:
   - **Logging mode:** Log warning, allow request
   - **Strict mode:** Block request, require re-authentication

**Example Detection:**

```
User logs in from London (IP: 192.168.1.50, Chrome on Windows)
Fingerprint: abc123...

1 hour later: Request from Paris (IP: 10.0.0.100, Firefox on Mac)
Fingerprint: xyz789...

Result: Mismatch detected, session possibly hijacked
```

---

### 7. SuspiciousActivityExtension

Pattern-based threat detection with automatic blocking.

**Features:**
- Failed login velocity detection
- Multiple account registration detection
- Password reset abuse detection
- TOTP brute force detection
- Suspicion score tracking
- Automatic IP blocking
- Email alerts

**Configuration:**

```python
# settings.py
GRAPHQL_SUSPICIOUS_ACTIVITY_ENABLED = True
GRAPHQL_SUSPICIOUS_ACTIVITY_AUTO_BLOCK = False  # Manual review recommended
GRAPHQL_SUSPICIOUS_ACTIVITY_THRESHOLD = 75  # Suspicion score (0-100)
GRAPHQL_SUSPICIOUS_ACTIVITY_ALERT_EMAIL = "security@example.com"
```

**Usage:**

```python
from syntek_graphql_core import SuspiciousActivityExtension

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[SuspiciousActivityExtension],
)
```

**Detection Rules:**

| Pattern                  | Threshold                     | Score | Action                         |
| ------------------------ | ----------------------------- | ----- | ------------------------------ |
| Failed login velocity    | >5 failures in 5 minutes      | 10    | Log + increment score          |
| Multiple registrations   | >3 registrations in 1 hour    | 25    | Log + increment score          |
| Password reset abuse     | >10 resets in 1 hour          | 20    | Log + increment score          |
| TOTP brute force         | >10 failed TOTP in 10 minutes | 15    | Log + increment score          |
| Geographic anomaly       | Login from different country  | 30    | Log + increment score          |
| High suspicion score     | Score >= threshold (75)       | -     | Alert + optional auto-block    |

**Suspicion Score:**

- Scores accumulate over 24 hours
- Each suspicious activity adds points
- When score >= threshold, alerts are sent
- Optional auto-blocking for high scores

**Example:**

```
IP: 192.168.1.100

10:00 - Failed login attempt (score: 10)
10:05 - Failed login attempt (score: 20)
10:10 - Failed login attempt (score: 30)
10:15 - Failed login attempt (score: 40)
10:20 - Failed login attempt (score: 50)
10:25 - Failed login attempt (score: 60)
10:30 - Failed login attempt (score: 70)
10:35 - Password reset request (score: 90)

Result: Score exceeds threshold (75)
Action: Email alert sent, optional auto-block for 24 hours
```

---

## Complete Integration Example

```python
# schema.py
import strawberry
from syntek_graphql_core import (
    # Query structure protection
    QueryDepthLimitExtension,
    QueryComplexityLimitExtension,
    IntrospectionControlExtension,
    # Operation-level protection
    OperationRateLimitExtension,
    GlobalSMSRateLimitExtension,
    ConstantTimeResponseExtension,
    CaptchaValidationExtension,
    InputSanitisationExtension,
    SessionFingerprintExtension,
    SuspiciousActivityExtension,
)

@strawberry.type
class Query:
    # ... queries

@strawberry.type
class Mutation:
    # ... mutations

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        # Query structure protection
        QueryDepthLimitExtension,
        QueryComplexityLimitExtension,
        IntrospectionControlExtension,
        # Input sanitisation (first to clean inputs)
        InputSanitisationExtension,
        # Rate limiting
        OperationRateLimitExtension,
        GlobalSMSRateLimitExtension,
        # CAPTCHA validation
        CaptchaValidationExtension,
        # Timing attack prevention
        ConstantTimeResponseExtension,
        # Session security
        SessionFingerprintExtension,
        # Threat detection
        SuspiciousActivityExtension,
    ],
)
```

---

## Configuration Summary

### Minimal Configuration (Recommended Defaults)

```python
# settings.py

# Cache backend (Redis required for rate limiting)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}

# reCAPTCHA (generate keys from https://www.google.com/recaptcha/admin)
RECAPTCHA_SECRET_KEY = "your-secret-key"
RECAPTCHA_VERSION = "v3"

# SMS cost protection
GRAPHQL_GLOBAL_SMS_LIMIT = 1000
GRAPHQL_GLOBAL_SMS_BUDGET = 500
GRAPHQL_SMS_ALERT_EMAIL = "security@example.com"

# Security alerts
GRAPHQL_SUSPICIOUS_ACTIVITY_ALERT_EMAIL = "security@example.com"
DEFAULT_FROM_EMAIL = "noreply@example.com"
```

### Full Configuration (All Options)

```python
# Rate limiting
GRAPHQL_RATE_LIMITS = {
    "sendPhoneVerification": "3/hour",
    "verifyPhone": "5/15min",
    "login": "5/15min",
}
GRAPHQL_DEFAULT_RATE_LIMIT = "100/hour"

# Global SMS protection
GRAPHQL_GLOBAL_SMS_LIMIT = 1000
GRAPHQL_GLOBAL_SMS_BUDGET = 500
GRAPHQL_SMS_COST_PER_MESSAGE = 0.05
GRAPHQL_SMS_ALERT_THRESHOLD = 0.8
GRAPHQL_SMS_ALERT_EMAIL = "security@example.com"

# Constant-time responses
GRAPHQL_CONSTANT_TIME_DURATION = 0.2
GRAPHQL_CONSTANT_TIME_ENABLED = True

# CAPTCHA
RECAPTCHA_SECRET_KEY = "your-key"
RECAPTCHA_VERSION = "v3"
RECAPTCHA_V3_MIN_SCORE = 0.5
GRAPHQL_CAPTCHA_ENABLED = True

# Input sanitisation
GRAPHQL_SANITISE_INPUTS = True
GRAPHQL_SANITISATION_LEVEL = "moderate"
GRAPHQL_ALLOW_HTML_FIELDS = ["description", "bio"]
GRAPHQL_LOG_SANITISATION = True

# Session fingerprinting
GRAPHQL_FINGERPRINT_ENABLED = True
GRAPHQL_FINGERPRINT_STRICT = False
GRAPHQL_FINGERPRINT_CACHE_TTL = 86400

# Suspicious activity detection
GRAPHQL_SUSPICIOUS_ACTIVITY_ENABLED = True
GRAPHQL_SUSPICIOUS_ACTIVITY_AUTO_BLOCK = False
GRAPHQL_SUSPICIOUS_ACTIVITY_THRESHOLD = 75
GRAPHQL_SUSPICIOUS_ACTIVITY_ALERT_EMAIL = "security@example.com"
```

---

## Performance Considerations

### Redis Cache

All extensions use Redis for distributed state:
- Rate limit counters
- SMS cost tracking
- Session fingerprints
- Suspicion scores

**Ensure Redis is configured and available:**

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
```

### Extension Order

Extensions execute in the order they are added:

```python
extensions=[
    InputSanitisationExtension,      # First: Clean inputs
    OperationRateLimitExtension,     # Second: Check rate limits
    CaptchaValidationExtension,      # Third: Validate CAPTCHA
    ConstantTimeResponseExtension,   # Fourth: Add timing protection
    SessionFingerprintExtension,     # Fifth: Validate session
    SuspiciousActivityExtension,     # Last: Detect patterns
]
```

### Cache TTLs

| Cache Key                                 | TTL      | Purpose                  |
| ----------------------------------------- | -------- | ------------------------ |
| `graphql_rate_limit:{op}:{client}`        | Variable | Rate limit counters      |
| `global_sms_hourly_count`                 | 1 hour   | Global SMS counter       |
| `global_sms_daily_cost`                   | 1 day    | Global SMS budget        |
| `session_fingerprint:{user_id}`           | 24 hours | Session fingerprints     |
| `suspicious:ip_score:{ip}`                | 24 hours | Suspicion scores         |
| `suspicious:{pattern}:{ip}`               | Variable | Pattern-specific counters|

---

## Security Best Practices

1. **Enable All Extensions in Production**: Comprehensive protection requires all layers
2. **Use Strict Mode Cautiously**: SessionFingerprintExtension strict mode may block legitimate users (VPNs, mobile networks)
3. **Monitor Alerts**: Review SMS and suspicious activity alerts regularly
4. **Tune Rate Limits**: Adjust based on legitimate usage patterns
5. **Regular Testing**: Test CAPTCHA integration, rate limits, and suspicious activity detection
6. **Cache Persistence**: Use persistent Redis (not in-memory) for production
7. **Logging**: Enable comprehensive logging for security analysis

---

## Troubleshooting

### Rate Limiting Not Working

**Symptoms:** Rate limits not enforced
**Causes:**
- Redis not configured or unavailable
- Cache backend not set to Redis
- Extension not added to schema

**Solution:**
```python
# Check Redis connection
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
'value'
```

### CAPTCHA Always Fails

**Symptoms:** All CAPTCHA validations fail
**Causes:**
- Invalid secret key
- Network firewall blocking Google/hCaptcha
- Incorrect reCAPTCHA version

**Solution:**
- Verify `RECAPTCHA_SECRET_KEY` in settings
- Test API access: `curl https://www.google.com/recaptcha/api/siteverify`
- Check reCAPTCHA admin console for errors

### Constant-Time Extension Slowing API

**Symptoms:** All auth operations take 200ms minimum
**Causes:** Working as intended

**Solution:**
- Reduce `GRAPHQL_CONSTANT_TIME_DURATION` to 0.1 (100ms)
- Disable in development: `GRAPHQL_CONSTANT_TIME_ENABLED = DEBUG`

### False Positive Session Hijacking

**Symptoms:** Legitimate users blocked due to fingerprint mismatch
**Causes:**
- VPN changes
- Mobile network switching
- Browser updates

**Solution:**
- Use logging mode instead of strict: `GRAPHQL_FINGERPRINT_STRICT = False`
- Increase IP network prefix tolerance
- Provide manual session refresh mechanism

---

## License

MIT License - See LICENSE file for details.

---

**Last Updated:** 2025-02-13
**Version:** 1.0.0
**Maintainer:** Syntek Development Team
