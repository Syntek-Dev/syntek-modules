# Changelog

All notable changes to the Syntek Modules project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Backend Modules
- Security bundles: `security-core`, `security-auth`, `security-input`, `security-network`
  - HTTP security middleware (headers, CORS, CSRF, rate limiting, cache security)
  - Authentication and session management (MFA, JWT, API keys, cookies)
  - Input validation and SQL injection prevention
  - IP filtering, request signing, OpenBao secrets management
- Feature modules: authentication, profiles, media, logging, analytics, reporting, webhooks
- Additional modules: search, bookings, notifications, payments, forms, comments, audit
- CMS primitives with PublishableModel mixin, draft/publish, versioning
- Internationalization (i18n) with translation, currency, timezone support
- Accounting integrations (Xero, QuickBooks, Zapier)
- AI integration with Rust LLM gateway abstraction layer
- Email marketing and contact form modules
- Feature flags and uploads modules

#### Web Modules (Next.js/React)
- Security bundles: `security-core`, `security-auth`, `security-input`
  - Client-side security headers, XSS protection, CSRF handling
  - Session management, JWT, cookies, request signing
  - Form validation and rate limiting
- UI component packages for all feature modules
  - Authentication, profiles, media, notifications, search
  - Forms, comments, analytics, bookings, payments
  - Webhooks and feature flags UI

#### Mobile Modules (React Native)
- Security bundles: `security-core`, `security-auth`
  - SSL certificate pinning, secure storage, jailbreak detection
  - Biometric authentication (Face ID, Touch ID, fingerprint)
  - Session management, JWT, request signing
- Feature modules for mobile: auth, profiles, media, notifications, search, bookings, payments

#### Shared Library
- Cross-platform components (forms, security, validation, layouts, feedback, loading)
- Shared hooks (useAuth, useNotifications, useFeatureFlags)
- Utility functions (formatting, i18n, validation with Zod)

#### Rust Crates
- `encryption`: AES-256-GCM and ChaCha20-Poly1305 encryption with field-level and batch support
- `security`: Memory safety, zeroization, secure random generation
- `hashing`: Password hashing (Argon2id, bcrypt)
- `llm_gateway`: Provider-agnostic LLM abstraction (OpenAI, Anthropic, Mistral, self-hosted)
- `pyo3_bindings`: PyO3 bridge for Django integration

#### GraphQL Layer
- Encryption middleware for transparent encrypt-on-write, decrypt-on-read
- Custom directives: `@encrypted`, `@searchableEncrypted`
- Per-field encryption configuration (individual vs batched)
- Blind indexes for searchable encrypted fields

#### Infrastructure
- Docker Compose for local development (PostgreSQL, Redis, testing services)
- Python workspace configuration with uv (PEP 621)
- Node.js monorepo with pnpm workspaces and Turborepo
- Rust workspace with shared dependencies
- Environment file templates for dev, test, staging, production
- Self-learning metrics system in `docs/METRICS/`
- Comprehensive CLAUDE.md with security compliance requirements

#### Security & Compliance
- OWASP Top 10 protection across all modules
- NIST Cybersecurity Framework alignment
- NCSC best practices implementation
- GDPR/UK GDPR compliance (data subject rights, encryption, audit trails)
- CIS Benchmarks configuration
- SOC 2 trust services criteria compliance
- Security compliance documentation in `docs/security/`

#### Documentation
- Comprehensive CLAUDE.md with project architecture and all module details
- Security compliance guide with OWASP/NIST/NCSC/GDPR/CIS/SOC2 requirements
- Rust security guide for memory safety and cryptography
- Module-level README templates and examples
- Self-learning metrics system documentation

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- All sensitive data encrypted via Rust layer (AES-256-GCM)
- Memory safety with automatic zeroization of plaintext
- JWT with short-lived access tokens (15min) and refresh rotation
- Rate limiting on all endpoints (configurable per module)
- CSRF protection with double-submit cookie pattern
- SQL injection prevention with parameterized queries
- XSS protection with DOM sanitization
- SSL certificate pinning for mobile apps
- Secure session management with IP binding and user-agent validation
- OpenBao integration for secrets management and rotation
- Comprehensive security headers (HSTS, CSP, X-Frame-Options, etc.)

---

## Release Notes Template

When releasing a new version, copy this template:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features or modules

### Changed
- Changes to existing functionality

### Deprecated
- Features marked for removal

### Removed
- Features removed in this version

### Fixed
- Bug fixes

### Security
- Security patches and improvements
```

---

[Unreleased]: https://github.com/syntek/syntek-modules/compare/v0.1.0...HEAD
