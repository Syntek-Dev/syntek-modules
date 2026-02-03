# Syntek Modules

**Modular Repository for Django, React, React Native, and Rust Components**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-6.0.2-green.svg)](https://www.djangoproject.com/)
[![Node](https://img.shields.io/badge/node-24.13-green.svg)](https://nodejs.org/)
[![Rust](https://img.shields.io/badge/rust-1.93-orange.svg)](https://www.rust-lang.org/)

---

## Overview

**Syntek Modules** is a modular monorepo containing reusable, production-ready modules for Django backends, Next.js web frontends, React Native mobile apps, and Rust security components. This repository is designed for **library distribution**, not deployment - modules are packaged and installed into other projects.

### Key Features

- 🔒 **Security-First Architecture** - OWASP, NIST, NCSC, GDPR, CIS compliant
- 📦 **Modular Design** - Install only what you need
- 🔐 **Rust Encryption Layer** - Hardware-accelerated encryption via PyO3
- 🌐 **Cross-Platform** - Shared components for web and mobile
- 🧪 **Comprehensive Testing** - Unit, integration, and E2E tests
- 📚 **Well-Documented** - Every module has detailed README with examples

### Related Repositories

This repository pairs with:
- **syntek-dev/platform** - Main application platform
- **syntek-dev/infrastructure** - Infrastructure as Code (NixOS, Terraform, Ansible)

---

## Table of Contents

- [Syntek Modules](#syntek-modules)
  - [Overview](#overview)
    - [Key Features](#key-features)
    - [Related Repositories](#related-repositories)
  - [Table of Contents](#table-of-contents)
  - [Tech Stack](#tech-stack)
    - [Backend](#backend)
    - [Web Frontend](#web-frontend)
    - [Mobile Frontend](#mobile-frontend)
    - [Shared](#shared)
    - [Infrastructure \& Security](#infrastructure--security)
  - [Repository Structure](#repository-structure)
  - [Module Categories](#module-categories)
    - [Backend Modules](#backend-modules)
    - [Web Modules](#web-modules)
    - [Mobile Modules](#mobile-modules)
    - [Shared Modules](#shared-modules)
    - [Rust Modules](#rust-modules)
  - [Quick Start](#quick-start)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Using the CLI](#using-the-cli)
  - [Installing Modules](#installing-modules)
    - [Django Backend Modules](#django-backend-modules)
    - [Web/Mobile Modules](#webmobile-modules)
    - [Rust Modules](#rust-modules-1)
  - [Configuration](#configuration)
    - [Django Settings](#django-settings)
    - [Environment Variables](#environment-variables)
    - [Next.js Configuration](#nextjs-configuration)
  - [Development](#development)
    - [Backend Development](#backend-development)
    - [Frontend Development](#frontend-development)
    - [Rust Development](#rust-development)
  - [Security](#security)
    - [Encryption Architecture](#encryption-architecture)
    - [Compliance](#compliance)
    - [Security Checklist](#security-checklist)
  - [Testing](#testing)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [License](#license)

---

## Tech Stack

### Backend

- **Python 3.14** with **Django 6.0.2**
- **GraphQL** via Strawberry 0.291.0
- **PostgreSQL 18.1** database
- **uv** package manager (faster than pip)
- **PyO3** for Rust-Python bindings

### Web Frontend

- **Next.js 16.1.16** (App Router)
- **React 19.2.1** with **TypeScript 5.9**
- **Node.js 24.13** (npm 11.6.2)
- **Tailwind CSS 4.1** with PostCSS and Autoprefixer
- **pnpm** workspace for monorepo management

### Mobile Frontend

- **React Native 0.83.x**
- **TypeScript 5.9**
- **NativeWind 4** (Tailwind for React Native)
- **Node.js 24.13**

### Shared

- **Cross-platform UI components** for web and mobile
- **Shared hooks** and utilities
- **TypeScript** for type safety

### Infrastructure & Security

- **Rust 1.93** - Custom encryption/decryption with zero-copy operations
- **OpenBao** - Open-source secrets management (HashiCorp Vault fork)
- **GlitchTip 5.2** - External error tracking and logging
- **Cloudinary** - Media storage and transformation
- **Docker** - Containerization for development and CI/CD
- **GitHub Actions** - CI/CD pipelines

---

## Repository Structure

```
syntek-modules/
├── backend/                       # Django modules
│   ├── security-core/             # Security bundle: middleware, headers, CORS, CSRF, rate limiting
│   ├── security-auth/             # Security bundle: authentication, sessions, JWT, API keys
│   ├── security-input/            # Security bundle: validation, SQL injection prevention
│   ├── security-network/          # Security bundle: IP filtering, request signing, OpenBao
│   ├── authentication/            # User authentication (MFA, TOTP, passkeys)
│   ├── groups/                    # Role-based access control
│   ├── profiles/                  # User profile management
│   ├── media/                     # Cloudinary integration
│   ├── logging/                   # GlitchTip + file-based logging
│   ├── accounting/                # Xero, QuickBooks, Zapier integration
│   ├── ai_integration/            # AI/LLM integration (OpenAI, Anthropic)
│   ├── email_marketing/           # Mailchimp-like email campaigns
│   ├── payments/                  # Stripe, Square, PayPal, SumUp
│   ├── notifications/             # In-app notifications
│   ├── search/                    # Full-text search
│   ├── audit/                     # Audit trails and logs
│   ├── forms_surveys/             # Form builder and surveys
│   ├── bookings/                  # Booking and events
│   ├── comments_ratings/          # Comments and ratings
│   ├── analytics/                 # Analytics and feedback
│   ├── reporting/                 # Report generation
│   ├── uploads/                   # File uploads/downloads
│   ├── feature_flags/             # Feature toggles
│   ├── webhooks/                  # Webhook management
│   ├── contact/                   # Contact forms
│   ├── i18n/                      # Internationalization
│   └── cms_primitives/            # CMS building blocks
│
├── web/                           # Next.js/React modules
│   ├── packages/
│   │   ├── security-core/         # Client-side security
│   │   ├── security-auth/         # Client authentication
│   │   ├── ui-auth/               # Authentication UI
│   │   ├── ui-profiles/           # Profile management UI
│   │   ├── ui-media/              # Media UI
│   │   ├── ui-notifications/      # Notifications UI
│   │   ├── ui-search/             # Search UI
│   │   ├── ui-forms/              # Forms UI
│   │   ├── ui-comments/           # Comments UI
│   │   ├── ui-analytics/          # Analytics UI
│   │   ├── ui-bookings/           # Bookings UI
│   │   ├── ui-payments/           # Payments UI
│   │   ├── ui-webhooks/           # Webhooks UI
│   │   └── ui-feature-flags/      # Feature flags UI
│   └── README.md
│
├── mobile/                        # React Native modules
│   ├── packages/
│   │   ├── security-core/         # Mobile security (cert pinning, secure storage)
│   │   ├── security-auth/         # Mobile auth with biometrics
│   │   ├── mobile-auth/           # Auth components
│   │   ├── mobile-profiles/       # Profile components
│   │   ├── mobile-media/          # Media components
│   │   ├── mobile-notifications/  # Notifications
│   │   ├── mobile-search/         # Search
│   │   ├── mobile-forms/          # Forms
│   │   ├── mobile-comments/       # Comments
│   │   ├── mobile-analytics/      # Analytics
│   │   ├── mobile-bookings/       # Bookings
│   │   ├── mobile-payments/       # Payments
│   │   └── mobile-feature-flags/  # Feature flags
│   └── README.md
│
├── shared/                        # Cross-platform code
│   ├── components/                # Shared UI components
│   ├── hooks/                     # Shared React hooks
│   ├── utils/                     # Shared utilities
│   └── types/                     # Shared TypeScript types
│
├── rust/                          # Rust security layer
│   ├── encryption/                # Encryption/decryption crate
│   ├── security/                  # Security utilities (zeroization, hashing)
│   ├── llm-gateway/               # AI LLM gateway with rate limiting
│   ├── pyo3-bindings/             # Python bindings via PyO3
│   ├── project-cli/               # CLI tool (syntek dev/test/build)
│   └── README.md
│
├── graphql/                       # GraphQL layer
│   ├── middleware/                # Encryption/decryption middleware
│   └── schema/                    # GraphQL schema definitions
│
├── examples/                      # Example integrations
│   ├── django-example/            # Django project using modules
│   ├── nextjs-example/            # Next.js project using modules
│   └── react-native-example/     # React Native project using modules
│
├── tests/                         # Integration tests
│   ├── backend/                   # Backend integration tests
│   ├── web/                       # Web E2E tests
│   └── mobile/                    # Mobile E2E tests
│
├── docs/                          # Documentation
│   ├── architecture/              # Architecture diagrams
│   ├── security/                  # Security documentation
│   │   ├── OWASP/                 # OWASP compliance
│   │   ├── NIST/                  # NIST compliance
│   │   ├── NCSC/                  # NCSC compliance
│   │   ├── GDPR/                  # GDPR compliance
│   │   └── CIS/                   # CIS Benchmarks
│   ├── guides/                    # User guides
│   └── api/                       # API documentation
│
├── .claude/                       # Claude Code configuration
│   ├── CLAUDE.md                  # Project instructions
│   ├── SYNTEK-GUIDE.md            # Agent command reference
│   ├── SECURITY-COMPLIANCE.md     # MANDATORY security requirements
│   ├── SYNTEK-RUST-SECURITY-GUIDE.md  # Rust security guidelines
│   ├── commands/                  # Slash commands
│   ├── agents/                    # Agent definitions
│   ├── skills/                    # Stack skills
│   └── plugins/                   # Python tools
│
├── .github/                       # GitHub configuration
│   └── workflows/                 # CI/CD workflows
│
├── docker-compose.yml             # Development environment
├── pyproject.toml                 # Python dependencies
├── uv.lock                        # Python lock file
├── package.json                   # Node.js dependencies (root)
├── pnpm-workspace.yaml            # pnpm workspace configuration
├── turbo.json                     # Turbo build configuration
├── tsup.config.ts                 # TypeScript bundler config
├── CHANGELOG.md                   # Version history
├── QUICK-START.md                 # Quick start guide
└── README.md                      # This file
```

---

## Module Categories

### Backend Modules

**Security Bundles** (installable as a group or individually):

| Bundle | Description | Modules Included |
|--------|-------------|------------------|
| `security-core` | HTTP security, middleware, headers, CORS, CSRF, rate limiting, cache | Core security middleware |
| `security-auth` | Authentication, sessions, JWT, API keys, MFA, TOTP | Authentication and session management |
| `security-input` | Input validation, SQL injection prevention, sanitization | Input protection |
| `security-network` | IP filtering, request signing, OpenBao secrets integration | Network security |

**Feature Modules**:

| Module | Description |
|--------|-------------|
| `authentication` | User authentication with MFA, TOTP, WebAuthn passkeys |
| `groups` | Django groups for role-based access control |
| `profiles` | User profile management |
| `media` | Cloudinary integration for media storage |
| `logging` | GlitchTip + file-based logging |
| `accounting` | Xero, QuickBooks, Zapier integration |
| `ai_integration` | AI/LLM integration (OpenAI, Anthropic, custom gateway) |
| `email_marketing` | Email campaigns (Mailchimp-like) |
| `payments` | Stripe, Square, PayPal, SumUp integration |
| `notifications` | In-app notifications |
| `search` | Full-text search and filtering |
| `audit` | Audit trails and activity logs |
| `forms_surveys` | Form builder and survey tools |
| `bookings` | Booking and event management |
| `comments_ratings` | Comments and rating system |
| `analytics` | Analytics and feedback |
| `reporting` | Report generation and exports |
| `uploads` | File upload/download management |
| `feature_flags` | Feature toggles and A/B testing |
| `webhooks` | Webhook management |
| `contact` | Contact forms |
| `i18n` | Internationalization |
| `cms_primitives` | CMS building blocks |

### Web Modules

| Module | Description |
|--------|-------------|
| `security-core` | Client-side security (CSP, XSS protection) |
| `security-auth` | Client authentication and session management |
| `ui-auth` | Authentication UI components |
| `ui-profiles` | Profile management UI |
| `ui-media` | Media upload/display UI |
| `ui-notifications` | Notifications UI |
| `ui-search` | Search and filtering UI |
| `ui-forms` | Form builder UI |
| `ui-comments` | Comments and ratings UI |
| `ui-analytics` | Analytics dashboard UI |
| `ui-bookings` | Bookings UI |
| `ui-payments` | Payment integration UI |
| `ui-webhooks` | Webhooks management UI |
| `ui-feature-flags` | Feature flags UI |

### Mobile Modules

| Module | Description |
|--------|-------------|
| `security-core` | Mobile security (cert pinning, secure storage) |
| `security-auth` | Mobile authentication with biometrics |
| `mobile-auth` | Authentication components |
| `mobile-profiles` | Profile management |
| `mobile-media` | Media components |
| `mobile-notifications` | Push notifications |
| `mobile-search` | Search components |
| `mobile-forms` | Form components |
| `mobile-comments` | Comments and ratings |
| `mobile-analytics` | Analytics |
| `mobile-bookings` | Bookings |
| `mobile-payments` | Mobile payments |
| `mobile-feature-flags` | Feature flags |

### Shared Modules

- **components** - Cross-platform UI components
- **hooks** - Shared React hooks
- **utils** - Utility functions
- **types** - TypeScript type definitions

### Rust Modules

| Crate | Description |
|-------|-------------|
| `encryption` | High-performance encryption/decryption |
| `security` | Zeroization, secure hashing, memory protection |
| `llm-gateway` | AI LLM gateway with rate limiting |
| `pyo3-bindings` | Python bindings for Django integration |
| `project-cli` | CLI tool for development workflows |

---

## Quick Start

### Prerequisites

- **Python 3.14+** with uv installed
- **Node.js 24.13+** with pnpm installed
- **Rust 1.93+** with Cargo
- **PostgreSQL 18.1+**
- **Docker** (optional, for containerized development)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/syntek-dev/syntek-modules.git
   cd syntek-modules
   ```

2. **Set up environment:**

   ```bash
   # Copy environment template
   cp .env.dev.example .env

   # Install Python dependencies
   uv sync

   # Install Node.js dependencies
   pnpm install

   # Build Rust components
   cd rust && cargo build --release
   ```

3. **Set up database:**

   ```bash
   # Using Docker
   docker-compose up -d postgres

   # Or install PostgreSQL locally
   # Then run migrations
   uv run python manage.py migrate
   ```

### Using the CLI

The Rust CLI provides convenience commands for development:

```bash
# Install CLI
cd rust/project-cli
cargo install --path .

# Available commands
syntek dev           # Start development server
syntek test          # Run all tests
syntek lint          # Run linters
syntek lint --fix    # Lint and auto-fix
syntek format        # Format code
syntek build         # Build for production
```

See [QUICK-START.md](QUICK-START.md) for detailed setup instructions.

---

## Installing Modules

### Django Backend Modules

Install modules via uv or pip:

```bash
# Install security bundles (recommended)
uv pip install syntek-security-core
uv pip install syntek-security-auth
uv pip install syntek-security-input
uv pip install syntek-security-network

# Or install individual feature modules
uv pip install syntek-authentication
uv pip install syntek-profiles
uv pip install syntek-media
uv pip install syntek-payments
```

Add to Django settings:

```python
# settings.py
INSTALLED_APPS = [
    # Security bundles (includes all sub-modules)
    'syntek_security_core',
    'syntek_security_auth',
    'syntek_security_input',
    'syntek_security_network',

    # Feature modules
    'syntek_authentication',
    'syntek_profiles',
    'syntek_media',
    'syntek_payments',
    # ... other modules
]
```

### Web/Mobile Modules

Install via pnpm:

```json
{
  "dependencies": {
    "@syntek/security-core": "^1.0.0",
    "@syntek/security-auth": "^1.0.0",
    "@syntek/ui-auth": "^1.0.0",
    "@syntek/ui-profiles": "^1.0.0",
    "@syntek/mobile-auth": "^1.0.0"
  }
}
```

### Rust Modules

Add to `Cargo.toml`:

```toml
[dependencies]
syntek-encryption = { path = "../syntek-modules/rust/encryption" }
syntek-security = { path = "../syntek-modules/rust/security" }
```

---

## Configuration

### Django Settings

```python
# Security Core Configuration
SYNTEK_SECURITY_CORE = {
    'RATE_LIMITING': {
        'BACKEND': 'redis',
        'DEFAULT_RATE': '100/hour',
        'REDIS_URL': 'redis://localhost:6379/0',
    },
    'CSRF': {
        'TOKEN_ROTATION': True,
        'COOKIE_HTTPONLY': True,
        'COOKIE_SECURE': True,
    },
    'CORS': {
        'ALLOWED_ORIGINS': ['https://example.com'],
        'ALLOW_CREDENTIALS': True,
    },
}

# Security Auth Configuration
SYNTEK_SECURITY_AUTH = {
    'AUTHENTICATION': {
        'TOTP_REQUIRED': True,
        'PASSKEY_ENABLED': True,
        'SESSION_TIMEOUT': 3600,
    },
    'JWT': {
        'ACCESS_TOKEN_LIFETIME': 900,
        'REFRESH_TOKEN_LIFETIME': 86400,
        'ALGORITHM': 'RS256',
    },
}

# Encryption Configuration
SYNTEK_ENCRYPTION = {
    'PROVIDER': 'rust',
    'KEY_ROTATION': True,
    'BATCH_ENCRYPTION': {
        'profile': ['first_name', 'last_name', 'phone', 'email'],
    },
}
```

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/syntek_modules

# Secrets Management
OPENBAO_ADDR=https://vault.example.com
OPENBAO_TOKEN=your-token-here

# External Services
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

GLITCHTIP_DSN=https://your-dsn@glitchtip.example.com

# Payment Providers
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password

# AI Integration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Next.js Configuration

```typescript
// next.config.ts
import { NextConfig } from 'next';

const config: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME: process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME,
  },
  images: {
    domains: ['res.cloudinary.com'],
  },
};

export default config;
```

---

## Development

### Backend Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run development server
uv run python manage.py runserver

# Run migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Run tests
uv run pytest
```

### Frontend Development

```bash
# Web development
cd web
pnpm dev              # Start Next.js dev server
pnpm build            # Build for production
pnpm test             # Run tests

# Mobile development
cd mobile
pnpm android          # Run on Android
pnpm ios              # Run on iOS
pnpm test             # Run tests
```

### Rust Development

```bash
cd rust

# Build
cargo build

# Run tests
cargo test

# Run specific crate tests
cargo test -p syntek-encryption

# Benchmark
cargo bench

# Check for security vulnerabilities
cargo audit
```

---

## Security

### Encryption Architecture

All sensitive data is encrypted using the Rust encryption layer:

1. **Frontend** - Plaintext data (user input)
2. **GraphQL Middleware** - Encryption/decryption via Rust (PyO3)
3. **Database** - Encrypted data at rest

**Field-Level Encryption:**

- **Individual**: IP addresses, API keys, tokens
- **Batch**: User profile data (name, email, phone)

**Zero-Copy Operations:**

- Memory-safe encryption with zeroization
- No plaintext data persists in memory
- Secure key rotation

### Compliance

All code MUST comply with:

- ✅ **OWASP Top 10** - Web application security risks
- ✅ **NIST Cybersecurity Framework** - Security standards
- ✅ **NCSC Guidelines** - UK cybersecurity guidance
- ✅ **GDPR** (EU/UK/Global) - Data protection regulations
- ✅ **CIS Benchmarks** - Configuration hardening
- ✅ **SOC 2** - Trust service criteria

See [.claude/SECURITY-COMPLIANCE.md](.claude/SECURITY-COMPLIANCE.md) for detailed requirements.

### Security Checklist

Before merging code, verify:

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

---

## Testing

```bash
# Backend tests
uv run pytest                           # All tests
uv run pytest backend/authentication/   # Specific module
uv run pytest --cov                     # With coverage

# Frontend tests
pnpm test                               # All tests
pnpm test:watch                         # Watch mode
pnpm test:coverage                      # With coverage

# Rust tests
cargo test                              # All tests
cargo test -p syntek-encryption         # Specific crate
cargo test -- --nocapture               # Show output

# Integration tests
cd tests
pytest integration/                     # All integration tests
pytest e2e/                             # E2E tests
```

---

## Documentation

- **[.claude/CLAUDE.md](.claude/CLAUDE.md)** - Project overview and agent guidelines
- **[.claude/SYNTEK-GUIDE.md](.claude/SYNTEK-GUIDE.md)** - Agent command reference
- **[.claude/SECURITY-COMPLIANCE.md](.claude/SECURITY-COMPLIANCE.md)** - MANDATORY security requirements
- **[.claude/SYNTEK-RUST-SECURITY-GUIDE.md](.claude/SYNTEK-RUST-SECURITY-GUIDE.md)** - Rust security guidelines
- **[QUICK-START.md](QUICK-START.md)** - Quick start guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[docs/](docs/)** - Architecture, security, and API documentation
- **Individual module READMEs** - Module-specific documentation

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Read the documentation:**
   - [.claude/CLAUDE.md](.claude/CLAUDE.md) - Project structure
   - [.claude/SECURITY-COMPLIANCE.md](.claude/SECURITY-COMPLIANCE.md) - Security requirements

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Follow coding standards:**
   - Python: PEP 8, Black, isort, mypy
   - TypeScript: ESLint, Prettier
   - Rust: rustfmt, clippy

4. **Write tests:**
   - Unit tests for all new functionality
   - Integration tests for module interactions
   - Security tests for sensitive operations

5. **Update documentation:**
   - Update module README.md
   - Add examples to `examples/`
   - Update CHANGELOG.md

6. **Submit a pull request:**
   - Clear description of changes
   - Reference related issues
   - Pass all CI/CD checks

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Maintained by:** Syntek Development Team
**Language:** British English (en_GB)
**Timezone:** Europe/London
**Last Updated:** 2026-02-03
