# Security

**Last Updated**: 24/02/2026
**Version**: 1.6.0
**Maintained By**: Development Team
**Language**: British English (en_GB)
**Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [Secrets Management](#secrets-management)
- [Authentication and Authorisation](#authentication-and-authorisation)
- [Input Validation and Sanitisation](#input-validation-and-sanitisation)
- [Database Security](#database-security)
- [API Security](#api-security)
- [OWASP Top 10 Mitigations](#owasp-top-10-mitigations)
- [Stack-Specific Security](#stack-specific-security)
  - [Laravel / TALL Stack](#laravel--tall-stack)
  - [Django Stack](#django-stack)
  - [React / TypeScript Stack](#react--typescript-stack)
- [Dependency Security](#dependency-security)
- [Security Testing](#security-testing)
- [Security Checklist](#security-checklist)

---

## Overview

Security is not optional and not a phase — it is a continuous requirement embedded in every decision. All agents and developers must apply the rules in this document when writing, reviewing, or modifying any code in this project.

The guiding principle is **defence in depth**: multiple independent layers of protection, so that a single failure does not compromise the system.

---

## Secrets Management

**Never hardcode secrets.** This is an absolute rule with no exceptions.

- All secrets, API keys, tokens, and credentials must be stored in environment variables.
- Environment variable files (`.env.*`) must never be committed to version control. They are listed in `.gitignore`.
- Each environment (development, test, staging, production) uses a separate set of credentials.
- Provide `.env.*.example` files with placeholder values and documentation to show what variables are required — never the real values.
- In production, use a secrets manager (AWS Secrets Manager, HashiCorp Vault, or equivalent) rather than plaintext environment files.
- Rotate all secrets immediately if a breach is suspected.

**Repository hygiene:**
- Run `git diff --cached` before every commit and verify no secrets are staged.
- Use pre-commit hooks (`gitleaks`, `detect-secrets`, or similar) to block accidental secret commits.
- If a secret is accidentally committed, treat the secret as compromised and rotate it immediately — rewriting git history does not make the secret safe.

---

## Authentication and Authorisation

### Authentication

- Use the framework's built-in authentication system. Do not roll your own.
- Passwords must be hashed using bcrypt (work factor ≥ 12) or argon2id. Never store plaintext or reversibly encrypted passwords.
- Enforce strong password requirements: minimum 12 characters, reject common passwords.
- Implement multi-factor authentication (MFA/2FA) for admin and privileged user accounts.
- Session tokens must be regenerated on privilege change (login, role change, password reset).
- Implement account lockout or exponential back-off after repeated failed login attempts.

### Authorisation

- Implement role-based access control (RBAC) or policy-based authorisation using the framework's built-in tools.
- Apply the **principle of least privilege**: every user, role, and API key has only the permissions it needs and nothing more.
- Authorisation checks must happen on the server — never trust client-side role claims.
- Every API endpoint must explicitly declare who can access it. A missing policy is a bug, not a valid "open to all" state.
- **IDOR prevention**: always scope queries to the authenticated user's resources. Never trust user-supplied IDs alone.

```php
// WRONG — attacker can access any order by guessing the ID
$order = Order::find($request->order_id);

// CORRECT — scoped to the authenticated user
$order = Order::where('user_id', auth()->id())->findOrFail($request->order_id);
```

```python
# WRONG
order = Order.objects.get(id=order_id)

# CORRECT
order = Order.objects.get(id=order_id, user=request.user)
```

---

## Input Validation and Sanitisation

Assume all external input is hostile until proven otherwise. This includes:

- HTTP request bodies, query strings, and URL parameters
- Uploaded files
- Webhook payloads
- Third-party API responses
- Data from databases when it originated from user input

Rules:

1. **Validate before use.** Reject invalid input at the earliest possible boundary.
2. **Use framework validation.** Use Laravel's Form Requests, Django's serialisers/forms, or Zod/Yup schemas in TypeScript. Do not write custom validation from scratch.
3. **Allowlist, not blocklist.** Specify what is permitted, not what is forbidden.
4. **Sanitise output, not input.** Do not strip HTML on input; escape it on output. This preserves the original data for auditing while preventing injection on display.
5. **Validate file uploads:** check MIME type via content inspection (not file extension), enforce maximum file size, store uploads outside the webroot, and scan for malware in production.

---

## Database Security

- **Parameterised queries always.** Never concatenate user input into SQL strings. Use the ORM or prepared statements.
- **Principle of least privilege for database users.** The application database user should have only `SELECT`, `INSERT`, `UPDATE`, `DELETE` on the tables it needs — not `DROP`, `CREATE`, or `GRANT`.
- Use separate database users for the application and for migrations/admin tasks.
- Encrypt sensitive columns at rest (PII, payment data, health records) using column-level encryption.
- Never log raw SQL queries in production — they may contain sensitive parameter values.
- Run `EXPLAIN` on slow queries before adding indexes. Do not add indexes speculatively.

---

## API Security

- **Authenticate every endpoint** unless it is explicitly designed to be public (e.g., a public product catalogue).
- **Rate limit all endpoints**, especially authentication endpoints. Use exponential back-off for repeated failures.
- **Return consistent error shapes.** Do not leak internal details (stack traces, file paths, database errors) in error responses.
- Set appropriate HTTP security headers on all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | Restrictive policy | Prevents XSS |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Prevents clickjacking |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforces HTTPS |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer leakage |
| `Permissions-Policy` | Restrictive policy | Limits browser feature access |

- **CORS:** explicitly configure allowed origins. Do not use wildcard `*` for authenticated APIs.
- **CSRF protection:** enable CSRF tokens for all state-changing requests in server-rendered applications. Verify `Origin` or `Referer` headers for SPA/API deployments.
- **Webhook verification:** always verify webhook signatures before processing. Reject unsigned or incorrectly signed payloads.

---

## OWASP Top 10 Mitigations

| Vulnerability | Mitigation |
|---------------|-----------|
| **A01 Broken Access Control** | RBAC/policy enforcement on every endpoint; scope all queries to authenticated user |
| **A02 Cryptographic Failures** | bcrypt/argon2id for passwords; TLS everywhere; encrypt PII at rest |
| **A03 Injection** | Parameterised queries always; framework validation on all inputs |
| **A04 Insecure Design** | Threat model new features; apply least privilege; security review before launch |
| **A05 Security Misconfiguration** | Review default framework settings; disable debug mode in production; remove unused routes |
| **A06 Vulnerable Components** | Regular `composer audit`, `pip audit`, `npm audit`; pin all dependencies; update regularly |
| **A07 Auth and Session Failures** | Framework auth; regenerate sessions on login; enforce MFA for admin |
| **A08 Software Integrity Failures** | Pin dependency versions; verify package integrity; use signed commits |
| **A09 Logging and Monitoring Failures** | Log all auth events, admin actions, and errors; alert on anomalies |
| **A10 SSRF** | Validate and allowlist outbound URLs; block requests to private IP ranges |

---

## Stack-Specific Security

### Laravel / TALL Stack

**Enable all built-in protections — do not disable them:**

```php
// CSRF protection is enabled by default — never exclude routes without good reason
// Do not add routes to the $except array in VerifyCsrfToken unless absolutely necessary
```

**Mass assignment protection:** always use `$fillable` or `$guarded` on models. Never use `$guarded = []`.

```php
// WRONG
protected $guarded = [];

// CORRECT
protected $fillable = ['name', 'email', 'role'];
```

**Authorization policies:** every controller action that modifies data must call `$this->authorize()` or use a policy.

```php
public function update(Request $request, Order $order): JsonResponse
{
    $this->authorize('update', $order); // throws 403 if user cannot update this order
    // ...
}
```

**Query scopes for multi-tenancy / user isolation:**

```php
// Apply global scopes or always chain ->where('user_id', auth()->id())
// Use model observers or policies to prevent cross-user data access
```

**Signed URLs for file access:** never expose direct storage URLs for private files. Use Laravel's `Storage::temporaryUrl()` with short expiry times.

**Rate limiting:** apply `throttle` middleware to all authentication and sensitive endpoints.

```php
Route::middleware(['auth:sanctum', 'throttle:60,1'])->group(function () {
    // authenticated routes
});
Route::middleware('throttle:5,1')->post('/login', [AuthController::class, 'login']);
```

### Django Stack

**Security settings that must be enabled in staging and production:**

```python
# settings/production.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
```

**Never disable CSRF protection on views that handle state-changing requests.**

**DRF permissions:** always set a default permission class and override per view where needed:

```python
# settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": "1000/day"},
}
```

**Object-level permissions:** always check `self.check_object_permissions(request, obj)` in views, or use Django Guardian for object-level ACL.

**SECRET_KEY:** never hardcode. Load from environment:

```python
import os
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # raises KeyError if not set — intentional
```

### React / TypeScript Stack

**Never trust client-side data for security decisions.** All authorisation happens on the server.

**XSS prevention:**
- Never use `dangerouslySetInnerHTML` unless the input is sanitised server-side.
- If HTML sanitisation is required client-side, use `DOMPurify`.

```tsx
// WRONG
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// CORRECT — only if absolutely necessary and input is sanitised
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

**Sensitive data in state:** never store tokens, session cookies, or PII in `localStorage`. Use `httpOnly` cookies set by the server for authentication tokens.

**Environment variables:** Next.js/React env vars prefixed with `NEXT_PUBLIC_` or `VITE_` are exposed to the client bundle. Never put secrets in these variables.

```bash
# WRONG — exposed to the browser
NEXT_PUBLIC_STRIPE_SECRET_KEY=sk_live_...

# CORRECT — server-side only
STRIPE_SECRET_KEY=sk_live_...
```

**Content Security Policy:** configure CSP headers in the Next.js middleware or server configuration. Start restrictive and loosen only as needed.

---

## Dependency Security

Run security audits regularly and before every deployment:

```bash
# Laravel / PHP
composer audit

# Django / Python
pip-audit  # or: safety check

# Node.js / TypeScript
npm audit
# or: yarn audit
```

**When a vulnerability is found:**
1. Check if your usage is actually affected by the vulnerability
2. Update to the patched version immediately if affected
3. If no patched version exists, evaluate a mitigation or replacement
4. Do not leave known vulnerabilities unresolved in production

**Dependency update policy:**
- Run security audits weekly (automate with GitHub Dependabot or Renovate)
- Apply security patches within 7 days of release for critical/high severity
- Review and test all dependency updates before merging to production

---

## Security Testing

The following security scenarios must be covered by automated tests. See **[TESTING.md](TESTING.md)** for how to write these tests.

| Scenario | Test Type |
|----------|-----------|
| Unauthenticated access to protected endpoint returns 401 | Integration |
| Unauthorised user cannot access another user's resource (IDOR) | Integration |
| Privilege escalation: lower-role user cannot perform higher-role action | Integration |
| SQL injection characters in input are rejected or escaped | Unit / Integration |
| XSS: script tags in user-provided text are escaped on output | Integration / E2E |
| Mass assignment: protected fields cannot be set via API | Integration |
| CSRF token missing returns 419/403 | Feature |
| Rate limiting blocks excessive requests | Integration |

---

## Security Checklist

Before deploying or merging any change to staging or production:

- [ ] No secrets, API keys, or credentials in the diff
- [ ] All new endpoints have authentication and authorisation
- [ ] All user-controlled inputs are validated before use
- [ ] All database queries use parameterised statements or the ORM
- [ ] No `dangerouslySetInnerHTML` without sanitisation (React)
- [ ] No `$guarded = []` on Eloquent models (Laravel)
- [ ] Debug mode is disabled in staging and production
- [ ] HTTP security headers are set
- [ ] Dependencies have been audited (`composer audit` / `pip-audit` / `npm audit`)
- [ ] Uploaded files are validated, size-limited, and stored outside the webroot
- [ ] Sensitive data is encrypted at rest where required
- [ ] Rate limiting is applied to authentication endpoints
- [ ] Logging does not include passwords, tokens, or PII
