# Security Quick Reference Card

Quick reference for security requirements across all layers. See `.claude/SECURITY-COMPLIANCE.md` for full details.

## OWASP Top 10 Quick Checks

### A01: Broken Access Control

```python
# ✅ GOOD
@permission_required('app.view_resource')
def view_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id, owner=request.user)

# ❌ BAD
def view_resource(request, resource_id):
    resource = Resource.objects.get(id=resource_id)  # No permission check!
```

### A02: Cryptographic Failures

```python
# ✅ GOOD - Encrypted storage
from syntek_encryption import get_encryptor
encrypted_data = get_encryptor().encrypt_field(sensitive_data)

# ❌ BAD - Plaintext storage
user.ssn = "123-45-6789"  # Never store sensitive data unencrypted!
```

### A03: Injection

```python
# ✅ GOOD - Parameterized query
User.objects.filter(username=username)

# ❌ BAD - SQL injection risk
User.objects.raw(f"SELECT * FROM users WHERE username = '{username}'")
```

### A07: Identification and Authentication Failures

```python
# ✅ GOOD - Strong password + MFA
SYNTEK_AUTH = {
    'PASSWORD_MIN_LENGTH': 12,
    'MFA_REQUIRED': True,
    'MAX_LOGIN_ATTEMPTS': 5,
}

# ❌ BAD - Weak password policy
SYNTEK_AUTH = {
    'PASSWORD_MIN_LENGTH': 6,  # Too short!
    'MFA_REQUIRED': False,     # MFA should be required!
}
```

### A09: Security Logging and Monitoring Failures

```python
# ✅ GOOD - Log security events
logger.warning("Failed login", extra={'user': username, 'ip': ip_address})

# ❌ BAD - Log sensitive data
logger.debug(f"Password: {password}")  # NEVER LOG PASSWORDS!
```

---

## GDPR Quick Checks

### Right to Access (Article 15)

```python
# ✅ REQUIRED
@strawberry.mutation
def export_user_data(user_id: int) -> UserDataExport:
    """Export all user data in machine-readable format"""
    return get_all_user_data(user_id)
```

### Right to Erasure (Article 17)

```python
# ✅ REQUIRED
@strawberry.mutation
def delete_user_account(user_id: int) -> bool:
    """Delete user and all associated data"""
    user = User.objects.get(id=user_id)
    user.delete()  # Must cascade to all related data
    return True
```

### Data Minimization (Article 5)

```python
# ✅ GOOD - Only collect necessary data
class User(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=150)

# ❌ BAD - Collecting unnecessary data
class User(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=150)
    birth_date = models.DateField()  # Do you really need this?
    ssn = models.CharField(max_length=11)  # Definitely don't need this!
```

### Encryption (Article 32)

```rust
// ✅ GOOD - Encrypt before storage
let encrypted = encryptor.encrypt_field(pii_data.as_bytes())?;
db.store(encrypted);

// ❌ BAD - Store plaintext
db.store(pii_data);  // GDPR violation!
```

---

## NIST 800-63B Quick Checks

### Password Requirements

```python
# ✅ GOOD
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': '...MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django_pwned_passwords.validators.PwnedPasswordsValidator'},
]

# ❌ BAD
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': '...MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    # Missing breach detection!
]
```

### MFA Support

```python
# ✅ GOOD - Support TOTP/WebAuthn
SYNTEK_AUTH = {
    'MFA_REQUIRED': True,
    'MFA_METHODS': ['totp', 'webauthn'],
}

# ❌ BAD - SMS-only MFA
SYNTEK_AUTH = {
    'MFA_METHODS': ['sms'],  # SMS is not secure enough!
}
```

---

## CIS Controls Quick Checks

### Control 3: Data Protection

```python
# ✅ GOOD - Classify data
class Document(models.Model):
    classification = models.CharField(
        choices=[('public', 'Public'), ('confidential', 'Confidential')],
        default='confidential'
    )

# ❌ BAD - No classification
class Document(models.Model):
    content = models.TextField()  # What's the sensitivity level?
```

### Control 4: Secure Configuration

```python
# ✅ GOOD - Production settings
DEBUG = False
ALLOWED_HOSTS = [env('DOMAIN')]
SECRET_KEY = env('SECRET_KEY')

# ❌ BAD - Insecure settings
DEBUG = True  # NEVER in production!
ALLOWED_HOSTS = ['*']  # Too permissive!
SECRET_KEY = 'hardcoded-key-123'  # Never hardcode secrets!
```

---

## Rust Security Quick Checks

### Memory Safety

```rust
// ✅ GOOD - Safe Rust
fn process_data(data: &[u8]) -> Vec<u8> {
    data.iter().map(|&b| b ^ 0xFF).collect()
}

// ❌ BAD - Unnecessary unsafe
fn process_data(data: &[u8]) -> Vec<u8> {
    unsafe {
        // Avoid unsafe unless absolutely necessary!
    }
}
```

### Zeroize Sensitive Data

```rust
// ✅ GOOD - Auto-zeroize
use zeroize::Zeroize;

let mut secret = String::from("password");
// ... use secret ...
secret.zeroize();

// ❌ BAD - No zeroization
let secret = String::from("password");
// Memory still contains "password"!
```

### Cryptography

```rust
// ✅ GOOD - Established library
use chacha20poly1305::ChaCha20Poly1305;

// ❌ BAD - Custom crypto
fn my_custom_encryption(data: &[u8]) -> Vec<u8> {
    // Don't roll your own crypto!
}
```

---

## Web/Mobile Quick Checks

### Content Security Policy

```typescript
// ✅ GOOD - Strict CSP
const cspHeader = `
  default-src 'self';
  script-src 'self';
  style-src 'self';
`;

// ❌ BAD - Permissive CSP
const cspHeader = `
  default-src *;
  script-src * 'unsafe-inline' 'unsafe-eval';
`;
```

### XSS Prevention

```typescript
// ✅ GOOD - Sanitize user input
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);

// ❌ BAD - Unsafe rendering
<div dangerouslySetInnerHTML={{__html: userInput}} />
```

### Secure Storage

```typescript
// ✅ GOOD - Use secure storage
import SecureStore from "expo-secure-store";
await SecureStore.setItemAsync("token", authToken);

// ❌ BAD - Use localStorage for sensitive data
localStorage.setItem("token", authToken); // Not secure!
```

---

## Security Headers Checklist

Required for all web applications:

```python
# settings/production.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'",)
```

---

## Dependency Scanning

Run before every commit:

```bash
# Python
pip-audit
uv pip list --outdated

# Node.js
npm audit
npm outdated

# Rust
cargo audit
cargo outdated
```

---

## Security Testing Checklist

Before merging any PR:

- [ ] **Input validation** - All user inputs validated
- [ ] **Authentication** - Auth required for protected endpoints
- [ ] **Authorization** - Permission checks on all operations
- [ ] **Encryption** - Sensitive data encrypted
- [ ] **Logging** - Security events logged (no sensitive data)
- [ ] **Dependencies** - No known vulnerabilities
- [ ] **Error handling** - Errors don't leak information
- [ ] **Rate limiting** - DoS protection in place
- [ ] **CSRF/XSS** - Protections enabled
- [ ] **Security headers** - All headers configured
- [ ] **GDPR compliance** - Data subject rights supported
- [ ] **Tests** - Security tests passing

---

## Common Mistakes to Avoid

### ❌ Hardcoded Secrets

```python
# WRONG
SECRET_KEY = 'django-insecure-hardcoded-key-123'
DATABASE_PASSWORD = 'password123'

# RIGHT
SECRET_KEY = env('SECRET_KEY')
DATABASE_PASSWORD = env('DATABASE_PASSWORD')
```

### ❌ Logging Sensitive Data

```python
# WRONG
logger.debug(f"User password: {password}")
logger.info(f"Credit card: {credit_card}")

# RIGHT
logger.info(f"User {user_id} authenticated")
logger.info(f"Payment processed for order {order_id}")
```

### ❌ Weak Password Validation

```python
# WRONG
if len(password) >= 6:
    # Too short!

# RIGHT
if len(password) >= 12 and check_against_breaches(password):
    # Strong password
```

### ❌ Missing Authorization Checks

```python
# WRONG
def delete_resource(request, resource_id):
    Resource.objects.get(id=resource_id).delete()

# RIGHT
def delete_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    if not request.user.has_perm('app.delete_resource', resource):
        raise PermissionDenied
    resource.delete()
```

### ❌ Storing Plaintext Passwords

```python
# WRONG
user.password = password

# RIGHT
user.set_password(password)  # Hashes with Argon2
```

---

## Emergency Response

### If You Discover a Security Vulnerability

1. **DO NOT** create a public GitHub issue
2. **DO NOT** commit a fix to main branch
3. **DO** email <info@syntekstudio.com> immediately
4. **DO** include: description, impact, reproduction steps
5. **WAIT** for security team response before proceeding

### If You Suspect a Data Breach

1. **IMMEDIATELY** notify security team
2. **DOCUMENT** what happened, when, and what data was affected
3. **DO NOT** delete logs or evidence
4. **PREPARE** for potential breach notification (72-hour GDPR requirement)

---

## Quick Links

- Full compliance guide: `.claude/SECURITY-COMPLIANCE.md`
- Rust security: `.claude/SYNTEK-RUST-SECURITY-GUIDE.md`
- Agent guidelines: `.claude/CLAUDE.md`
- Reporting: <security@syntek.example>

---

**Remember:** Security is everyone's responsibility. When in doubt, ask!
