# Syntek Modules - Modular Repository

## Project Overview

**Syntek Modules** is a modular monorepo containing reusable Django, React, React Native, and Rust modules for installation into other projects.

This is NOT a deployable application - these are **library modules** designed to be:
- Installed via uv or pip (Django apps)
- Installed via npm/pnpm (React/React Native packages)
- Included via Cargo (Rust crates)

## Tech Stack

### Backend (Django)
- Django 6.0.2 (Python 3.14), GraphQL (Strawberry 0.291.0)
- PostgreSQL 18.1, uv package manager
- Structure: Django apps packaged as pip/uv installables

### Web (Next.js)
- Next.js 16.1.16, React 19.2.1, TypeScript 5.9
- Node.js 24.13, Tailwind 4.1
- Structure: NPM packages

### Mobile (React Native)
- React Native 0.83.x, TypeScript 5.9, NativeWind 4
- Structure: NPM packages

### Shared UI
- Cross-platform components for web and mobile

### Security & Infrastructure
- Rust: Encryption/decryption via PyO3 bindings
- OpenBao: Secrets management
- GlitchTip: External logging
- Cloudinary: Media storage

## Repository Structure

```
syntek-modules/
├── backend/                    # Django modules (security bundles + features)
│   ├── security-core/          # Middleware, headers, CORS, CSRF, rate limiting
│   ├── security-auth/          # Auth, sessions, cookies, JWT, API keys
│   ├── security-input/         # Validation, SQL injection prevention
│   ├── security-network/       # IP filtering, request signing, OpenBao
│   └── [27+ feature modules]   # profiles, media, payments, etc.
│
├── web/packages/               # Next.js/React modules
│   ├── security-core/          # Client-side security
│   ├── security-auth/          # Client auth & sessions
│   └── ui-*/                   # UI components
│
├── mobile/packages/            # React Native modules
│   ├── security-core/          # Mobile security (cert pinning, secure storage)
│   ├── security-auth/          # Mobile auth & biometrics
│   └── mobile-*/               # Mobile features
│
├── shared/                     # Cross-platform components, hooks, utils
├── rust/                       # Encryption, hashing, LLM gateway, PyO3 bindings
├── graphql/                    # GraphQL encryption middleware
├── examples/                   # Example integrations
├── tests/                      # Integration tests
└── docs/                       # Architecture & security docs
```

## Module Categories

### Security Bundles (Backend)
- **security-core**: HTTP security (middleware, headers, CORS, CSRF, rate limiting, cache)
- **security-auth**: Authentication & sessions (MFA, TOTP, JWT, API keys)
- **security-input**: Input protection (validation, SQL injection prevention)
- **security-network**: Network security (IP filtering, OpenBao secrets)

### Security Bundles (Web/Mobile)
- Similar structure for client-side security

### Feature Modules (Backend)
groups, profiles, media, logging, accounting, ai_integration, email_marketing, payments, notifications, search, audit, forms_surveys, contact, bookings, comments_ratings, analytics, reporting, uploads, feature_flags, webhooks, i18n, cms_primitives

### UI Modules (Web/Mobile)
Authentication, profiles, media, notifications, search, forms, comments, analytics, bookings, payments, webhooks, feature flags

## Installation

### Django Modules
```bash
# Install security bundles (recommended)
uv pip install syntek-security-core
uv pip install syntek-security-auth

# Or individual modules
uv pip install syntek-authentication
uv pip install syntek-profiles
```

### Web/Mobile Modules
```json
{
  "dependencies": {
    "@syntek/security-core": "^1.0.0",
    "@syntek/ui-auth": "^1.0.0",
    "@syntek/mobile-auth": "^1.0.0"
  }
}
```

### Rust Modules
```toml
[dependencies]
syntek-encryption = { path = "../syntek-modules/rust/encryption" }
```

## Configuration

### Django Settings
```python
INSTALLED_APPS = [
    'syntek_security_core',      # Auto-includes all sub-modules
    'syntek_security_auth',
    'syntek_profiles',
    # ... other modules
]

SYNTEK_SECURITY_CORE = {
    'RATE_LIMITING': {'BACKEND': 'redis', 'DEFAULT_RATE': '100/hour'},
    'CSRF': {'TOKEN_ROTATION': True},
}

SYNTEK_SECURITY_AUTH = {
    'AUTHENTICATION': {'TOTP_REQUIRED': True},
    'JWT': {'ACCESS_TOKEN_LIFETIME': 900},
}
```

## Security Compliance

**ALL code must comply with:**
- OWASP Top 10
- NIST Cybersecurity Framework
- NCSC Guidelines
- GDPR (EU/UK/Global)
- CIS Benchmarks
- SOC 2

See `.claude/SECURITY-COMPLIANCE.md` for detailed requirements.

## Development

### Using Rust CLI
```bash
# Install CLI
cd rust/project-cli && cargo install --path .

# Commands
syntek dev           # Start development
syntek test          # Run tests
syntek lint --fix    # Lint and fix
syntek format        # Format code
syntek build         # Build for production
```

### Lock Files
- Python: `uv.lock` (committed)
- Rust: `Cargo.lock` (committed)
- Node: `pnpm-lock.yaml` (gitignored for libraries)

## Key Principles

1. **Modularity** - Each module is independently installable
2. **No Coupling** - Modules don't depend on each other unless explicitly declared
3. **Version Control** - Semantic versioning for each module
4. **Documentation** - Every module MUST have comprehensive README.md
5. **Security** - All sensitive data encrypted via Rust layer
6. **Testing** - Comprehensive tests for each module

## Agent Guidelines

### When Creating/Modifying Modules

1. **Understand bundling** - Security modules are bundled but can be installed individually
2. **Keep modules independent** - Avoid cross-dependencies
3. **Write comprehensive README.md FIRST** - Include installation, configuration, usage examples, API reference
4. **Provide examples** - Show real-world usage
5. **Test thoroughly** - Unit + integration tests
6. **Version properly** - Semantic versioning
7. **Security first** - Use Rust encryption layer for sensitive data

### Security Checklist (ALL code)
- [ ] Input validation and sanitization
- [ ] Parameterized queries (no SQL injection)
- [ ] Strong authentication (MFA support)
- [ ] Authorization checks on all operations
- [ ] Encryption for sensitive data (at rest and in transit)
- [ ] Security logging (no sensitive data in logs)
- [ ] Error messages don't leak information
- [ ] Rate limiting implemented
- [ ] CSRF/XSS protection
- [ ] Security headers configured
- [ ] Dependencies scanned for vulnerabilities
- [ ] GDPR data subject rights supported

### File Locations
- Backend bundles: `backend/security-<bundle>/`
- Backend modules: `backend/<module>/`
- Web bundles: `web/packages/security-<bundle>/`
- Web UI: `web/packages/ui-<component>/`
- Mobile bundles: `mobile/packages/security-<bundle>/`
- Mobile features: `mobile/packages/mobile-<feature>/`
- Shared: `shared/{components,hooks,utils}/`
- Rust: `rust/<crate>/`
- GraphQL: `graphql/{middleware,schema}/`

## README Requirements

Every module MUST include:
1. Overview
2. Features
3. Installation
4. Configuration (all options in table format)
5. Usage Examples
6. API Reference
7. Security Considerations
8. Testing
9. Development

See `backend/security-auth/authentication/README.md` for reference.

## Related Documentation

- `.claude/SYNTEK-GUIDE.md` - Agent command reference
- `.claude/SECURITY-COMPLIANCE.md` - MANDATORY compliance requirements
- `.claude/SYNTEK-RUST-SECURITY-GUIDE.md` - Rust security guidelines
- `docs/security/` - OWASP, NIST, NCSC, GDPR, CIS documentation
- Individual module READMEs - Module-specific docs
