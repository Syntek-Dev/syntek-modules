# Security Compliance Framework

This document defines security requirements for **all** modules (backend, API, web, mobile, shared UI, Rust) based on industry standards and regulations.

## Applicable Standards

All code in this repository must comply with:

- **OWASP** - Open Web Application Security Project Top 10 and ASVS
- **NIST** - Cybersecurity Framework and Special Publications (800-53, 800-63B)
- **NCSC** - UK National Cyber Security Centre guidelines
- **GDPR** - EU, UK, and Global data protection requirements
- **CIS Benchmarks** - Security configuration guidelines
- **SOC 2** - Trust Services Criteria (Security, Availability, Confidentiality)

---

## OWASP Compliance

### OWASP Top 10 (2021)

#### A01: Broken Access Control

**Backend/API:**

- Implement role-based access control (RBAC)
- Enforce principle of least privilege
- Validate permissions on every request
- Use Django's permission system correctly

```python
# Good - Permission checking
from django.contrib.auth.decorators import permission_required

@permission_required('profiles.view_profile')
def view_profile(request, user_id):
    # Only users with permission can access
    pass
```

**Web/Mobile:**

- Validate user permissions client-side (UI only)
- Always enforce server-side (never trust client)
- Hide/disable UI elements based on permissions

```typescript
// Good - UI-level permission check
const canEdit = user.permissions.includes('edit_profile');
return (
  <div>
    {canEdit && <EditButton />}
  </div>
);
```

#### A02: Cryptographic Failures

**Backend/Rust:**

- Use only TLS 1.2+ for data in transit
- Encrypt sensitive data at rest (see Rust encryption module)
- Never store passwords in plaintext (use Argon2)
- Use HSTS headers

```python
# settings/production.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**Rust:**

```rust
// Use established crypto libraries
use chacha20poly1305::{ChaCha20Poly1305, aead::Aead};
use argon2::{Argon2, PasswordHasher};
```

#### A03: Injection

**Backend:**

- Use parameterized queries (Django ORM does this automatically)
- Validate and sanitize all user inputs
- Never use raw SQL with user input

```python
# Bad - SQL injection risk
User.objects.raw(f"SELECT * FROM users WHERE username = '{username}'")

# Good - Parameterized query
User.objects.filter(username=username)
```

**GraphQL:**

- Use Strawberry's built-in input validation
- Implement query depth limiting
- Rate limit queries

```python
import strawberry
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    query=Query,
    extensions=[QueryDepthLimiter(max_depth=10)]
)
```

#### A04: Insecure Design

**Architecture:**

- Threat model all features before implementation
- Implement security by design, not as afterthought
- Use secure defaults
- Fail securely (deny by default)

#### A05: Security Misconfiguration

**Backend:**

```python
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = [env('DOMAIN')]
SECRET_KEY = env('SECRET_KEY')  # From environment

# Disable unnecessary services
INSTALLED_APPS = [
    # Only required apps
]
```

**Docker:**

```dockerfile
# Run as non-root user
USER appuser

# Remove unnecessary packages
RUN apt-get autoremove -y && apt-get clean
```

#### A06: Vulnerable and Outdated Components

**All Layers:**

- Run dependency audits regularly
- Keep all dependencies updated
- Use Dependabot/Renovate for automation

```bash
# Python
uv pip list --outdated
pip-audit

# Node.js
npm audit
npm outdated

# Rust
cargo audit
cargo outdated
```

#### A07: Identification and Authentication Failures

**Backend:**

- Enforce strong password requirements
- Implement MFA/TOTP
- Use secure session management
- Implement account lockout after failed attempts

```python
SYNTEK_AUTH = {
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_DIGITS': True,
    'PASSWORD_REQUIRE_SPECIAL': True,
    'MFA_REQUIRED': True,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 900,  # 15 minutes
}
```

#### A08: Software and Data Integrity Failures

**CI/CD:**

- Sign commits and releases
- Verify dependencies (use lock files)
- Implement code review requirements
- Use container image signing

```yaml
# .github/workflows/security.yml
- name: Verify signatures
  run: cosign verify $IMAGE_URI
```

#### A09: Security Logging and Monitoring Failures

**Backend:**

- Log all authentication events
- Log authorization failures
- Monitor for suspicious activity
- Never log sensitive data

```python
import logging

logger = logging.getLogger(__name__)

# Good - Log security events
logger.warning(
    "Failed login attempt",
    extra={
        'user': username,
        'ip': request.META['REMOTE_ADDR'],
        'user_agent': request.META['HTTP_USER_AGENT'],
    }
)

# Bad - Don't log passwords
logger.debug(f"Password: {password}")  # NEVER DO THIS
```

#### A10: Server-Side Request Forgery (SSRF)

**Backend:**

- Validate and sanitize URLs
- Use allowlists for external requests
- Disable URL redirects where possible

```python
from urllib.parse import urlparse

ALLOWED_DOMAINS = ['api.example.com', 'cdn.example.com']

def fetch_external_resource(url):
    parsed = urlparse(url)
    if parsed.netloc not in ALLOWED_DOMAINS:
        raise ValueError("Domain not allowed")

    # Proceed with request
    response = requests.get(url, timeout=5)
    return response
```

---

## NIST Cybersecurity Framework

### Identify

- Asset inventory (dependencies, services, data)
- Risk assessment for each feature
- Document security architecture

### Protect

- Access control (authentication + authorization)
- Data security (encryption at rest and in transit)
- Protective technology (firewalls, WAF)

### Detect

- Security monitoring (GlitchTip/Sentry)
- Anomaly detection
- Audit logs

### Respond

- Incident response plan
- Security patches within 24-48 hours for critical
- Communication procedures

### Recover

- Backup and recovery procedures
- Business continuity plan
- Post-incident analysis

### NIST 800-63B (Digital Identity Guidelines)

**Password Requirements:**

- Minimum 8 characters (recommend 12+)
- Check against breached password lists
- No periodic password changes required
- Allow all printable characters
- No composition rules (except minimum length)

```python
from django.contrib.auth.password_validation import validate_password
from django_pwned_passwords.validators import PwnedPasswordsValidator

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django_pwned_passwords.validators.PwnedPasswordsValidator',
     'OPTIONS': {'error_message': 'Password has been compromised'}},
]
```

**MFA Requirements:**

- Support TOTP (Time-based One-Time Password)
- Support WebAuthn/FIDO2
- SMS/Email as backup (not primary)

---

## NCSC Guidelines

### Cyber Essentials Plus

#### Secure Configuration

```python
# settings/production.py
# 1. Disable unused features
INSTALLED_APPS = [...]  # Only required apps

# 2. Strong authentication
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True

# 3. Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

#### Malware Protection

- Scan uploaded files for malware
- Validate file types and content
- Use Content Security Policy (CSP)

```python
# Web security headers
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Minimize unsafe-inline
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

#### Patch Management

- Apply security patches within 14 days (critical: 24-48 hours)
- Automated dependency updates
- Regular vulnerability scanning

---

## GDPR Compliance

### Lawfulness, Fairness, and Transparency (Article 5)

- Clear privacy policy
- Explicit consent for data processing
- Document legal basis for processing

### Purpose Limitation (Article 5)

- Collect only necessary data
- Document purpose for each data field
- Don't repurpose data without consent

### Data Minimization (Article 5)

```python
class UserProfile(models.Model):
    # Only collect what's needed
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)  # Required
    # Don't collect unnecessary PII
    # birth_date = models.DateField()  # Only if needed
```

### Accuracy (Article 5)

- Provide mechanisms to update data
- Regular data validation
- Allow users to correct inaccuracies

### Storage Limitation (Article 5)

- Implement data retention policies
- Automatic deletion after retention period
- Document retention periods

```python
from datetime import timedelta
from django.utils import timezone

class DataRetentionMixin:
    RETENTION_PERIOD = timedelta(days=365 * 7)  # 7 years

    def delete_if_expired(self):
        if timezone.now() - self.created_at > self.RETENTION_PERIOD:
            self.delete()
```

### Security (Article 32)

- Encryption at rest and in transit
- Pseudonymization where appropriate
- Regular security testing

**Rust Encryption:**

```rust
use syntek_encryption::Encryptor;

// Encrypt PII before storage
let encrypted_email = encryptor.encrypt_field(email.as_bytes())?;
let encrypted_phone = encryptor.encrypt_field(phone.as_bytes())?;
```

### Accountability (Article 5)

- Maintain records of processing activities
- Conduct Data Protection Impact Assessments (DPIA)
- Appoint Data Protection Officer if required

### Rights of Data Subjects

#### Right of Access (Article 15)

```python
@strawberry.mutation
def export_user_data(info, user_id: int) -> UserDataExport:
    """Export all user data (GDPR Article 15)"""
    user = User.objects.get(id=user_id)

    # Decrypt and export all user data
    return UserDataExport(
        personal_info=user.get_personal_data(),
        activity_log=user.get_activity_log(),
        format='JSON'
    )
```

#### Right to Erasure (Article 17)

```python
@strawberry.mutation
def delete_user_account(info, user_id: int) -> bool:
    """Delete user account and all data (GDPR Article 17)"""
    user = User.objects.get(id=user_id)

    # Zeroize encrypted data before deletion
    user.zeroize_encrypted_fields()

    # Delete user and cascade
    user.delete()

    return True
```

#### Right to Data Portability (Article 20)

- Provide data in machine-readable format (JSON, CSV)
- Include all personal data
- Allow direct transfer to another controller

### Breach Notification (Article 33-34)

- Detect breaches within 72 hours
- Notify supervisory authority within 72 hours
- Notify affected individuals if high risk

---

## CIS Benchmarks

### CIS Controls v8

#### Control 1: Inventory and Control of Enterprise Assets

```yaml
# Document all services
services:
  - name: Django Backend
    version: 6.0.2
    exposed_ports: [8000]
  - name: PostgreSQL
    version: 18.1
    exposed_ports: [5432]
```

#### Control 2: Inventory and Control of Software Assets

- Maintain dependency manifests
- Use lock files (requirements.txt, package-lock.json, Cargo.lock)
- Regular dependency audits

#### Control 3: Data Protection

- Classify data (public, internal, confidential, restricted)
- Encrypt sensitive data at rest
- Secure data in transit (TLS 1.2+)

```python
# Data classification example
class DataClassification(models.TextChoices):
    PUBLIC = 'public', 'Public'
    INTERNAL = 'internal', 'Internal'
    CONFIDENTIAL = 'confidential', 'Confidential'
    RESTRICTED = 'restricted', 'Restricted'

class Document(models.Model):
    classification = models.CharField(
        max_length=20,
        choices=DataClassification.choices,
        default=DataClassification.INTERNAL
    )
```

#### Control 4: Secure Configuration

- Harden configurations
- Remove default credentials
- Disable unnecessary services

```bash
# PostgreSQL hardening
# postgresql.conf
ssl = on
password_encryption = scram-sha-256
log_connections = on
log_disconnections = on
```

#### Control 5: Account Management

- Implement least privilege
- Regular access reviews
- Disable unused accounts

#### Control 6: Access Control Management

- Use MFA for all privileged accounts
- Implement role-based access control
- Log all access attempts

#### Control 8: Audit Log Management

```python
# Enable comprehensive logging
LOGGING = {
    'version': 1,
    'handlers': {
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/app/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security'],
            'level': 'INFO',
        },
    },
}
```

---

## SOC 2 Compliance

### Trust Services Criteria

#### CC1: Control Environment

- Document security policies
- Security awareness training
- Code of conduct

#### CC2: Communication and Information

- Internal security communications
- External security disclosures
- Incident reporting procedures

#### CC3: Risk Assessment

- Regular risk assessments
- Threat modeling for new features
- Vulnerability management program

#### CC4: Monitoring Activities

```python
# Implement monitoring
from django.core.signals import request_finished

@receiver(request_finished)
def log_request(sender, **kwargs):
    # Log all API requests
    logger.info("Request completed", extra={
        'path': request.path,
        'method': request.method,
        'status': response.status_code,
    })
```

#### CC5: Control Activities

**Change Management:**

- All changes via pull requests
- Code review required
- Automated testing

```yaml
# .github/workflows/security.yml
on:
  pull_request:
    branches: [main]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Security Scan
        run: |
          pip-audit
          npm audit
          cargo audit
```

**Access Controls:**

```python
# Implement RBAC
class Permission(models.Model):
    name = models.CharField(max_length=100)
    resource = models.CharField(max_length=100)
    action = models.CharField(max_length=20)

def check_permission(user, resource, action):
    return Permission.objects.filter(
        user=user,
        resource=resource,
        action=action
    ).exists()
```

#### CC6: Logical and Physical Access Controls

- MFA for all production access
- VPN required for remote access
- Regular access reviews

#### CC7: System Operations

- Automated backups
- Disaster recovery testing
- Capacity monitoring

```python
# Automated backups
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'BACKUP_COUNT': 7,
        'BACKUP_SCHEDULE': 'daily',
    }
}
```

---

## Implementation Checklist

### Backend (Django)

- [ ] Input validation on all endpoints
- [ ] Parameterized queries only
- [ ] Strong password policy (NIST 800-63B)
- [ ] MFA support (TOTP + WebAuthn)
- [ ] Session management (secure cookies)
- [ ] CSRF protection enabled
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] Audit logging enabled
- [ ] Encrypted data at rest (Rust module)
- [ ] GDPR data export/delete endpoints
- [ ] Breach notification procedures

### API (GraphQL)

- [ ] Authentication required
- [ ] Authorization on all queries/mutations
- [ ] Query depth limiting
- [ ] Query complexity analysis
- [ ] Rate limiting per user/IP
- [ ] Input validation and sanitization
- [ ] Error messages don't leak info
- [ ] CORS properly configured

### Web (Next.js)

- [ ] Content Security Policy
- [ ] XSS protection
- [ ] CSRF tokens
- [ ] Secure cookie settings
- [ ] Input sanitization
- [ ] No sensitive data in localStorage
- [ ] Security headers
- [ ] Dependency scanning

### Mobile (React Native)

- [ ] Certificate pinning
- [ ] Secure storage (Keychain/KeyStore)
- [ ] No sensitive data in logs
- [ ] Code obfuscation for production
- [ ] Biometric authentication
- [ ] Root/jailbreak detection
- [ ] API key protection

### Shared UI

- [ ] XSS-safe component design
- [ ] Input validation
- [ ] No eval() or dangerouslySetInnerHTML
- [ ] Sanitize user-generated content
- [ ] Accessibility (WCAG 2.1 AA)

### Rust Security

- [ ] Memory safety (minimal unsafe)
- [ ] Zeroize for sensitive data
- [ ] Established crypto libraries
- [ ] Input validation at FFI boundaries
- [ ] Constant-time comparisons
- [ ] Overflow checks enabled
- [ ] Regular cargo audit

---

## Continuous Compliance

### Daily

- Automated security tests in CI/CD
- Dependency vulnerability scanning

### Weekly

- Review security logs
- Check for new CVEs

### Monthly

- Security patch updates
- Access reviews
- Incident response drill

### Quarterly

- Threat modeling for new features
- Security training
- Risk assessment update

### Annually

- Full security audit
- Penetration testing
- Policy review
- Compliance assessment

---

## Reporting Security Issues

Report security vulnerabilities to: <security@syntek.example> (update with real email)

**Do not:**

- Open public GitHub issues for vulnerabilities
- Disclose vulnerabilities publicly before patch

**Response timeline:**

- Initial response: 24 hours
- Assessment: 48 hours
- Critical patch: 1-7 days
- Public disclosure: After patch is released

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [NIST 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [NCSC Cyber Essentials](https://www.ncsc.gov.uk/cyberessentials)
- [GDPR Full Text](https://gdpr-info.eu/)
- [CIS Controls v8](https://www.cisecurity.org/controls/v8)
- [SOC 2 Trust Services Criteria](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html)

---

**Last Updated:** 2026-02-03
**Next Review:** 2026-05-03
