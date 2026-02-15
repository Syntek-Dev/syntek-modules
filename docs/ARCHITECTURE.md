# Authentication System Architecture

Complete architecture documentation for the Syntek authentication system.

## Overview

Multi-layer authentication system with Django backend, GraphQL API, and cross-platform frontends (Next.js + React Native).

## Architecture Diagram

\`\`\`
┌─────────────────────────────────────────────────────────┐
│ Clients │
├─────────────────┬───────────────────┬───────────────────┤
│ Web (Next.js) │ Mobile (RN iOS) │ Mobile (RN Android)│
│ Tailwind v4 │ NativeWind 4 │ NativeWind 4 │
└────────┬────────┴─────────┬─────────┴─────────┬─────────┘
│ │ │
└──────────────────┼───────────────────┘
│
┌─────────▼─────────┐
│ GraphQL API │
│ (Strawberry) │
└─────────┬─────────┘
│
┌─────────▼─────────┐
│ Django Backend │
│ (Python 3.14) │
└─────────┬─────────┘
│
┌──────────────────┼──────────────────┐
│ │ │
┌────▼────┐ ┌─────▼──────┐ ┌─────▼─────┐
│PostgreSQL│ │Rust Security│ │ Redis │
│ 18.1 │ │ (PyO3) │ │ Cache │
└──────────┘ └────────────┘ └───────────┘
\`\`\`

## Components

### Layer 1: Django Backend (Source of Truth)

- **Purpose**: Business logic, data models, configuration
- **Technologies**: Django 6.0.2, Python 3.14
- **Responsibilities**:
  - Configuration (SYNTEK_AUTH settings)
  - Password hashing (Argon2id via Rust)
  - Email encryption (AES-256-GCM via Rust)
  - Session management
  - MFA (TOTP, WebAuthn, Backup codes)
  - Social OAuth integration
  - GDPR compliance

### Layer 2: Rust Security Layer

- **Purpose**: High-performance cryptography
- **Technologies**: Rust, PyO3
- **Responsibilities**:
  - Argon2id hashing (m=19456, t=2, p=1)
  - AES-256-GCM encryption/decryption
  - HMAC generation
  - Constant-time operations
  - TOTP generation
  - WebAuthn credential management

### Layer 3: GraphQL API

- **Purpose**: Type-safe API for frontends
- **Technologies**: Strawberry 0.291.0
- **Responsibilities**:
  - Schema definition
  - Authentication mutations
  - Configuration queries
  - Rate limiting
  - Error handling

### Layer 4: Shared Frontend (70-80% code reuse)

- **Location**: \`shared/\` directory
- **Technologies**: TypeScript 5.9, React 19.2.1
- **Shared Code**:
  - GraphQL operations (100%)
  - TypeScript types (100%)
  - Business logic hooks (90%)
  - UI components (70-80%)
  - Utilities (100%)

### Layer 5: Web Frontend (Next.js)

- **Technologies**: Next.js 16.1.16, Tailwind v4
- **Platform-Specific**:
  - Server-side rendering
  - httpOnly cookies
  - Web adapters (localStorage, WebAuthn)

### Layer 6: Mobile Frontend (React Native)

- **Technologies**: React Native 0.83.x, NativeWind 4
- **Platform-Specific**:
  - Biometric authentication
  - SecureStore
  - Deep linking
  - Push notifications

## Data Flow

### Registration Flow

1. User fills form (Web/Mobile)
2. Frontend validates (shared hook)
3. GraphQL mutation \`register\`
4. Django validates business rules
5. Rust hashes password (Argon2id)
6. Rust encrypts email (AES-256-GCM)
7. Store in PostgreSQL
8. Send verification email
9. Return JWT tokens

### Login Flow

1. User enters credentials
2. GraphQL mutation \`login\`
3. Rust decrypts email for lookup
4. Argon2id verify password
5. Check MFA requirement
6. Generate session + JWT
7. Store session in Redis
8. Return tokens

### MFA Flow

1. User requests MFA setup
2. Django generates TOTP secret
3. Return QR code + secret
4. User scans with authenticator
5. User enters TOTP code
6. Verify code
7. Store encrypted secret
8. Generate recovery keys
9. Mark MFA as enabled

## Security Features

### Implemented

- ✅ Argon2id password hashing (OWASP 2025)
- ✅ Email encryption at rest (AES-256-GCM)
- ✅ Phone number encryption
- ✅ Geolocation privacy (city-level only)
- ✅ MFA (TOTP, WebAuthn, Backup codes)
- ✅ Passkeys (FIDO2)
- ✅ Social OAuth (7 providers)
- ✅ Session fingerprinting
- ✅ Auto-logout
- ✅ Recovery keys
- ✅ Zero-downtime key rotation
- ✅ Rate limiting (per-endpoint)
- ✅ Constant-time operations
- ✅ CSRF protection
- ✅ XSS protection
- ✅ SQL injection prevention

## Database Schema

### Core Tables

- \`users\` - User accounts
- \`user_profiles\` - Extended profile data
- \`user_emails\` - Encrypted emails (1:1)
- \`user_phones\` - Encrypted phones (1:1)
- \`sessions\` - Active sessions
- \`mfa_devices\` - TOTP/WebAuthn devices
- \`recovery_keys\` - Account recovery
- \`social_accounts\` - OAuth connections
- \`audit_logs\` - Security events

### Indexes

- Composite index: (email_hmac, is_verified)
- Composite index: (phone_hmac, is_verified)
- Index: (session_token_hash)
- Index: (created_at) for cleanup

## Configuration Management

All configuration in Django settings (source of truth):

\`\`\`python
SYNTEK_AUTH = {
'PASSWORD_LENGTH': 12,
'UPPERCASE_REQUIRED': True,
'SESSION_TIMEOUT': 1800,
'IDLE_TIMEOUT': 900,
'MFA_REQUIRED': False, # ... 50+ configurable options
}
\`\`\`

Frontend fetches via GraphQL:

\`\`\`typescript
const { config } = useAuthConfig();
// config.passwordLength matches backend
\`\`\`

## Deployment

### Development

- Django runserver
- Next.js dev server
- PostgreSQL local
- Redis local

### Production

- Django + Gunicorn + Nginx
- Next.js static export or SSR
- PostgreSQL RDS
- Redis Valkey cluster
- Cloudflare CDN

## Monitoring

- **Application**: GlitchTip (Sentry protocol)
- **Performance**: Grafana + Prometheus
- **Logs**: Centralized logging
- **Alerts**: PagerDuty/Slack

## References

- [PLAN-AUTHENTICATION-SYSTEM.md](./PLANS/PLAN-AUTHENTICATION-SYSTEM.md)
- [CLAUDE.md](../.claude/CLAUDE.md)
- [API Documentation](./API.md)
