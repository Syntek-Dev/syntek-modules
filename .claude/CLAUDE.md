# Project: syntek-modules

**Last Updated**: 11/03/2026 **Version**: 0.15.0 **Maintained By**: Syntek Development Team
**Language**: British English (en_GB) **Timezone**: Europe/London

---

## Table of Contents

- [Reference Guides](#reference-guides)
- [Stack Overview](#stack-overview)
- [Coding Principles](#coding-principles)
- [Skill Targets](#skill-targets)
- [Package Architecture](#package-architecture)
- [Directory Structure](#directory-structure)
- [Key Locations](#key-locations)
- [Development Commands](#development-commands)
- [Module Registry](#module-registry)
- [Configuration Pattern](#configuration-pattern)
- [Security Layer](#security-layer)
- [Versioning](#versioning)
- [Ecosystem Context](#ecosystem-context)

---

> **IMPORTANT:** Always use `syntek-dev <command>` for development tasks. See
> [Rust CLI](.claude/CLI-TOOLING.md) for the full command reference.

---

## Reference Guides

| Guide                                                        | Purpose                                                          |
| ------------------------------------------------------------ | ---------------------------------------------------------------- |
| [`.claude/CLI-TOOLING.md`](.claude/CLI-TOOLING.md)           | `syntek-dev` CLI — all commands, flags, and usage                |
| [`.claude/GIT-GUIDE.md`](.claude/GIT-GUIDE.md)               | Git workflow — lint before commit, CI before push                |
| [`.claude/VERSIONING-GUIDE.md`](.claude/VERSIONING-GUIDE.md) | Versioning rules — root files, per-module files, increment types |

---

## Stack Overview

| Component           | Technology                                         | Version             |
| ------------------- | -------------------------------------------------- | ------------------- |
| **Type**            | Multi-stack modular library (NOT a deployable app) |                     |
| **Backend**         | Django + Python                                    | 6.0.4 / 3.14.3      |
| **API Layer**       | Strawberry GraphQL                                 | 0.307.1             |
| **Database**        | PostgreSQL                                         | 18.3                |
| **Cache / Queue**   | Valkey + Celery                                    | latest stable       |
| **Web Frontend**    | Next.js + React + TypeScript                       | 16.1.6 / 19.2 / 5.9 |
| **Styling**         | Tailwind CSS                                       | 4.2                 |
| **Mobile**          | React Native (Expo) + NativeWind                   | 0.84.x / 4          |
| **Rust**            | Rust stable (encryption layer)                     | stable              |
| **Python PM**       | uv (replaces pip)                                  | latest stable       |
| **JS PM**           | pnpm workspaces + Turborepo                        | latest stable       |
| **Node.js**         | Node.js                                            | 24.14.0             |
| **npm**             | npm                                                | 11.11.0             |
| **Media**           | Cloudinary (images + video)                        | latest stable       |
| **Documents**       | MinIO (PDFs + office files only)                   | latest stable       |
| **Static Assets**   | Next.js `.next` output (caching + minification)    |                     |
| **Dev Environment** | uv venv (Python) — NO Docker for this repo         |                     |
| **Registry**        | Forgejo — git.syntek-studio.com                    |                     |
| **Install CLI**     | `syntek add <package>` (Rust CLI)                  |                     |

> All versions are the latest stable as of March 2026.

---

## Coding Principles

All code in this project follows Rob Pike's 5 Rules of Programming and Linus Torvalds' Coding Rules.

**Core rules:**

- Measure before optimising — no speed hacks without profiling
- Simple algorithms and simple data structures over fancy ones
- Data structures dominate: get the data model right and the logic becomes obvious
- Short, focused functions that do one thing
- Eliminate special cases rather than patching them with `if` statements
- Make it work first, then make it better
- Favour stability and readability over cleverness
- Maximum **750 lines** per file (grace of 50). Split into modules if exceeded.

See [Coding Principles](.claude/CODING-PRINCIPLES.md) for the full rules.

---

## Skill Targets

- **Stack Skill:** `stack-shared-lib`
- **Global Skill:** `global-workflow`

---

## Package Architecture

This repository contains four distinct package layers. Each layer has its own package manager and
publishing mechanism.

### Layer 1 — Backend (Django / Python)

- **Location:** `packages/backend/syntek-<name>/`
- **Install (consumers):** `syntek add syntek-<name>`
- **Dev tool:** `uv` (replaces pip entirely)
- **Dev environment:** `uv venv` — activate with `source .venv/bin/activate`
- **Published to:** Forgejo PyPI registry at `git.syntek-studio.com`
- **Config:** All modules configured via `SYNTEK_*` dicts in Django `settings.py`

### Layer 2 — Web Frontend (React / TypeScript)

- **Location:** `packages/web/<name>/` → publishes as `@syntek/<name>`
- **Install (consumers):** `syntek add @syntek/<name>`
- **Dev tool:** pnpm workspaces + Turborepo
- **Published to:** Forgejo npm registry at `git.syntek-studio.com`
- **Framework:** Next.js 16.1.6 / React 19.2 / TypeScript 5.9 / Tailwind 4.2

### Layer 3 — Mobile (React Native / TypeScript)

- **Location:** `mobile/<name>/` → publishes as `@syntek/mobile-<name>`
- **Install (consumers):** `syntek add @syntek/mobile-<name>`
- **Dev tool:** pnpm workspaces
- **Published to:** Forgejo npm registry
- **Framework:** React Native 0.84.x / Expo / NativeWind 4 / TypeScript 5.9

### Layer 4 — Rust (Encryption Crates)

- **Location:** `rust/<crate-name>/`
- **Dev tool:** cargo
- **Published to:** Forgejo Cargo registry
- **Purpose:** Field-level AES-256-GCM encryption, PyO3 Django bindings, GraphQL middleware
- **CRITICAL:** All sensitive fields are encrypted before any DB write. Nothing is stored as plain
  text.

### Shared

- **Location:** `shared/` — TypeScript types, GraphQL operations, design tokens
- **Used by:** All web and mobile packages via pnpm workspace protocol

---

## Directory Structure

```
syntek-modules/
├── .claude/
│   ├── CLAUDE.md                    # This file
│   ├── CODING-PRINCIPLES.md         # Rob Pike + Linus Torvalds rules
│   ├── settings.local.json          # Claude Code settings
│   ├── SYNTEK-GUIDE.md              # Plugin usage guide
│   ├── plugins/                     # Python plugin tools
│   └── commands/                    # Slash commands
│
├── packages/
│   ├── backend/                     # Django Python packages
│   │   ├── syntek-auth/
│   │   ├── syntek-permissions/
│   │   ├── syntek-tenancy/
│   │   └── ... (21 total)
│   └── web/                         # React TypeScript packages
│       ├── ui/                      # @syntek/ui
│       ├── ui-auth/                 # @syntek/ui-auth
│       ├── ui-gdpr/                 # @syntek/ui-gdpr (cookie consent)
│       └── ... (14 total)
│
├── mobile/                          # React Native packages
│   ├── mobile-auth/                 # @syntek/mobile-auth
│   └── ... (5 total)
│
├── rust/                            # Rust encryption crates
│   ├── syntek-crypto/               # AES-256-GCM, Argon2id, HMAC-SHA256
│   ├── syntek-pyo3/                 # PyO3 Django bindings
│   └── syntek-graphql-crypto/       # GraphQL middleware
│
├── shared/                          # Shared TypeScript types + GraphQL
│   ├── types/
│   └── graphql/
│
├── docs/
│   ├── METRICS/                     # Self-learning system data
│   ├── API/
│   ├── ARCHITECTURE/
│   ├── BUGS/
│   ├── GUIDES/
│   ├── PLANS/
│   ├── QA/
│   ├── STORIES/
│   └── TESTS/
│
├── pnpm-workspace.yaml              # pnpm workspace config
├── turbo.json                       # Turborepo build pipeline
├── package.json                     # Root (tooling only)
├── Cargo.toml                       # Rust workspace
├── pyproject.toml                   # uv workspace root
├── install.sh                       # First-time setup (builds syntek-dev CLI)
└── README.md
```

---

## Key Locations

| Path                          | Purpose                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------ |
| `packages/backend/`           | All Django backend modules                                                           |
| `packages/web/`               | All React web frontend packages                                                      |
| `mobile/`                     | All React Native mobile packages                                                     |
| `rust/syntek-crypto/`         | Core encryption: AES-256-GCM, Argon2id, HMAC-SHA256, zeroize                         |
| `rust/syntek-pyo3/`           | PyO3 bindings — `encrypt_field`, `decrypt_field`, `hash_password`, `verify_password` |
| `rust/syntek-graphql-crypto/` | GraphQL middleware preventing plaintext resolver output                              |
| `shared/`                     | Shared TypeScript types and GraphQL operations                                       |
| `pnpm-workspace.yaml`         | Declares all JS/TS workspace packages                                                |
| `turbo.json`                  | Turborepo pipeline for build, test, lint, type-check                                 |
| `pyproject.toml`              | uv workspace root                                                                    |
| `Cargo.toml`                  | Rust workspace root                                                                  |
| `docs/METRICS/`               | Self-learning system data                                                            |

---

## Development Commands

> **Always use `syntek-dev <command>`.** Do not invoke `pytest`, `ruff`, `cargo`, `pnpm`, or
> `basedpyright` directly when an equivalent CLI command exists. See
> [CLI Tooling](.claude/CLI-TOOLING.md) for the full reference.

### First-Time Setup

```bash
# Run once after cloning — sets up .venv, installs all deps, builds and symlinks the CLI
chmod +x install.sh && ./install.sh

# Activate the Python venv before running any command
source .venv/bin/activate
```

### Development

```bash
# Start all layers in watch mode (frontend + Storybook + Rust watcher)
syntek-dev up

# Start only the frontend
syntek-dev up --frontend

# Start only Storybook
syntek-dev up --storybook

# Start only the Rust watcher
syntek-dev up --rust
```

### Building

```bash
# Build all layers (Rust release + Python dev-install + web + mobile)
syntek-dev build

# Build all Rust crates in release mode
syntek-dev build --rust

# Build a specific Rust crate — e.g. after a version bump
syntek-dev build --rust --rust-crate syntek-pyo3

# Dev-install all Python packages into venv
syntek-dev build --python

# Build a specific Python package wheel
syntek-dev build --python --python-package syntek-auth

# Build all web packages
syntek-dev build --web

# Build mobile packages
syntek-dev build --mobile
```

### Testing

```bash
# Run all layers (Python + Rust + web + mobile)
syntek-dev test

# Python tests only
syntek-dev test --python

# Python tests for a specific backend package
syntek-dev test --python --python-package syntek-auth

# Rust tests only
syntek-dev test --rust

# Web tests for a specific package
syntek-dev test --web --web-package @syntek/ui-auth

# E2E tests (Playwright — never run by default, must be explicit)
syntek-dev test --e2e

# With coverage
syntek-dev test --python --coverage
syntek-dev test --web --coverage
```

### Linting and Type Checking

```bash
# Run all linters (ruff, basedpyright, ESLint, Prettier, clippy, markdownlint)
syntek-dev lint

# Auto-fix everything that can be fixed, then verify clean
syntek-dev lint --fix
syntek-dev lint

# Specific linters
syntek-dev lint --ruff               # Python lint (ruff)
syntek-dev lint --pyright            # Python type checking (basedpyright)
syntek-dev lint --eslint             # TypeScript/JS (ESLint)
syntek-dev lint --prettier           # TypeScript/JS/JSON/YAML/Markdown (Prettier)
syntek-dev lint --clippy             # Rust (clippy)
syntek-dev lint --markdown           # Markdown (markdownlint)

# Restrict ruff + basedpyright to a specific backend package
syntek-dev lint --ruff syntek-auth
```

### Formatting

```bash
# Format all layers
syntek-dev format

# Format only Python (ruff format)
syntek-dev format --python

# Format only TypeScript/JS/JSON/YAML/Markdown (Prettier)
syntek-dev format --ts

# Format only Rust (cargo fmt)
syntek-dev format --rust

# Check only — no writes
syntek-dev format --check
```

### Pre-Commit and Pre-Push

```bash
# Before every commit — auto-fix then verify (see .claude/GIT-GUIDE.md)
syntek-dev lint --fix
syntek-dev lint

# Before every push — full local CI (14 steps, mirrors remote CI)
syntek-dev ci
```

### Database (requires sandbox/manage.py — see docs/GUIDES/SANDBOX.md)

```bash
syntek-dev db migrate
syntek-dev db makemigrations syntek_auth
syntek-dev db rollback syntek_auth --to 0003
syntek-dev db status
syntek-dev db seed
syntek-dev db reset
syntek-dev db shell
```

---

## Module Registry

### Backend Modules (21)

| Module                 | Package                  | Key Purpose                                |
| ---------------------- | ------------------------ | ------------------------------------------ |
| Authentication         | `syntek-auth`            | MFA, passkeys, OAuth, Argon2id             |
| Permissions / RBAC     | `syntek-permissions`     | Roles, object-level permissions            |
| Multi-tenancy          | `syntek-tenancy`         | Schema isolation, domain routing           |
| Notifications          | `syntek-notifications`   | In-app, push, SMS, email                   |
| Payments               | `syntek-payments`        | Stripe, subscriptions, refunds             |
| Invoicing              | `syntek-invoicing`       | PDF invoices, VAT, UK MTD                  |
| Donations              | `syntek-donations`       | One-off, recurring, Gift Aid               |
| Events & Ticketing     | `syntek-events`          | Tickets, capacity, QR check-in             |
| Dynamic Forms          | `syntek-forms`           | Schema-driven, conditional logic           |
| Audit Logging          | `syntek-audit`           | Immutable trail, GDPR retention            |
| Structured Logging     | `syntek-logging`         | JSON logs, Sentry/Glitchtip integration    |
| Full-text Search       | `syntek-search`          | Elasticsearch/OpenSearch, facets           |
| Reporting & Exports    | `syntek-reporting`       | PDF/Excel/CSV, scheduled reports           |
| Background Tasks       | `syntek-tasks`           | Celery, priority queues, DLQ               |
| Webhooks               | `syntek-webhooks`        | Inbound/outbound, HMAC-SHA256              |
| Bulk Import/Export     | `syntek-bulk`            | CSV/Excel/JSON, async, validation          |
| Groups / Teams         | `syntek-groups`          | Nested groups, org hierarchy               |
| Feature Flags          | `syntek-flags`           | Per-tenant, percentage rollout             |
| Per-tenant Settings    | `syntek-settings`        | Typed key-value store per tenant           |
| Integrations Framework | `syntek-integrations`    | OAuth bridges, EspoCRM, CalDav             |
| Security Middleware    | `syntek-security`        | Rate limiting, CORS, CSP, HSTS             |
| Media (Cloudinary)     | `syntek-media`           | Cloudinary Python SDK, metadata in DB      |
| Documents (MinIO)      | `syntek-documents`       | MinIO SDK, PDF/doc storage, presigned URLs |
| GDPR / Compliance      | `syntek-gdpr`            | SAR, erasure, consent, retention           |
| Membership             | `syntek-membership`      | Tiers, renewals, member directory          |
| Internationalisation   | `syntek-i18n`            | Translations, locale, UK formatting        |
| Calendar / CalDav      | `syntek-caldav`          | CalDav client for Radicale on infra        |
| Address / Geo          | `syntek-geo`             | UK postcode lookup, geocoding              |
| Accounting             | `syntek-accounting`      | Double-entry, VAT, Xero/Sage/QBO           |
| Email Marketing        | `syntek-email-marketing` | Campaigns, lists, GDPR opt-out             |
| API Keys               | `syntek-api-keys`        | Developer key issuance, scopes             |
| Comments               | `syntek-comments`        | Threaded, moderation, reactions            |
| Loyalty & Referrals    | `syntek-loyalty`         | Points, tiers, referral attribution        |

### Web Packages (15)

| Package                    | Purpose                                                            |
| -------------------------- | ------------------------------------------------------------------ |
| `@syntek/ui`               | Design system — Button, Input, Modal, Header, Footer, Navbar, etc. |
| `@syntek/ui-auth`          | Login, register, MFA, OAuth, passkeys                              |
| `@syntek/ui-gdpr`          | Cookie consent popup, privacy centre, GDPR forms                   |
| `@syntek/session`          | Session context, token refresh, idle timeout                       |
| `@syntek/api-client`       | Generated typed GraphQL client                                     |
| `@syntek/data-hooks`       | usePaginatedQuery, useInfiniteScroll, useMutation                  |
| `@syntek/forms`            | Headless form primitives, Zod validation                           |
| `@syntek/layout`           | Sidebar, top nav, breadcrumbs, command palette                     |
| `@syntek/data-table`       | Sortable, filterable, paginated table                              |
| `@syntek/ui-notifications` | Notification bell, feed, WebSocket updates                         |
| `@syntek/ui-payments`      | Stripe Elements, checkout, subscriptions                           |
| `@syntek/ui-search`        | Search bar, facets, autocomplete                                   |
| `@syntek/ui-reporting`     | Charts (line, bar, pie, area), report builder                      |
| `@syntek/ui-settings`      | Account, security, billing settings pages                          |
| `@syntek/ui-onboarding`    | Multi-step wizard, progress, resumable state                       |

### Mobile Packages (5)

| Package                        | Purpose                                            |
| ------------------------------ | -------------------------------------------------- |
| `@syntek/mobile-auth`          | Biometric, social login, deep links, passkeys      |
| `@syntek/mobile-notifications` | FCM/APNs, notification centre, deep-link routing   |
| `@syntek/mobile-payments`      | Apple Pay, Google Pay, Stripe mobile               |
| `@syntek/mobile-sync`          | Offline SQLite cache, conflict resolution          |
| `@syntek/mobile-ui`            | NativeWind component library, iOS/Android adaptive |

### Rust Crates (3)

| Crate                   | Purpose                                                        |
| ----------------------- | -------------------------------------------------------------- |
| `syntek-crypto`         | AES-256-GCM encryption, Argon2id hashing, HMAC-SHA256, zeroize |
| `syntek-pyo3`           | PyO3 bindings for Django                                       |
| `syntek-graphql-crypto` | GraphQL middleware — prevents plaintext resolver output        |

---

## Configuration Pattern

All backend modules are controlled entirely through `SYNTEK_*` settings dicts. Nothing is hardcoded.
Frontends receive all configuration from Django via GraphQL.

```python
# settings.py example
SYNTEK_AUTH = {
    'MFA_REQUIRED': True,
    'PASSWORD_MIN_LENGTH': 14,
    'SESSION_TIMEOUT': 1800,
    'ARGON2ID_TIME_COST': 3,
    'ARGON2ID_MEMORY_COST': 65536,
}

SYNTEK_TENANCY = {
    'ISOLATION': 'schema',
    'DOMAIN_STRATEGY': 'subdomain',
}

SYNTEK_SECURITY = {
    'RATE_LIMIT_BACKEND': 'redis',
    'DEFAULT_RATE': '100/hour',
}

SYNTEK_MEDIA = {
    'CLOUDINARY_CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME'),
    'CLOUDINARY_API_KEY': env('CLOUDINARY_API_KEY'),
    'CLOUDINARY_API_SECRET': env('CLOUDINARY_API_SECRET'),
}

SYNTEK_DOCUMENTS = {
    'MINIO_ENDPOINT': env('MINIO_ENDPOINT'),
    'MINIO_ACCESS_KEY': env('MINIO_ACCESS_KEY'),
    'MINIO_SECRET_KEY': env('MINIO_SECRET_KEY'),
    'MINIO_BUCKET': env('MINIO_BUCKET', default='documents'),
}
```

**Rules:**

- Secrets always come from environment variables — never hardcoded
- Settings validated at Django startup via `AppConfig.ready()`
- Frontend packages have no `.env` config — all comes from GraphQL

---

## Security Layer

**Zero-plaintext guarantee:** Sensitive fields are encrypted by the Rust layer before any database
write. The frontend never handles raw cryptographic operations.

**The Rust layer is installed via `syntek add` like all other layers but is not configurable.** All
cryptographic algorithms, parameters, and key lengths are fixed by Syntek security policy. The CLI
simply pins the crate version — no prompts, no options. The configurable layers are
Django/PostgreSQL (via `SYNTEK_*` settings), GraphQL (via `@encrypted` directives and
`SYNTEK_FIELD_KEY_*` env vars), Next.js, and React Native.

| Algorithm    | Use                                 | Standard                    |
| ------------ | ----------------------------------- | --------------------------- |
| AES-256-GCM  | Field-level encryption at rest      | NIST SP 800-38D             |
| Argon2id     | Password hashing (m=64MB, t=3, p=4) | NIST SP 800-132 / OWASP     |
| HMAC-SHA-256 | Data integrity verification         | FIPS 198-1                  |
| zeroize      | Memory zeroisation after use        | OWASP Cryptographic Storage |

**PyO3 bridge functions exposed to Django:**

- `encrypt_field(plaintext, key)` → `ciphertext`
- `decrypt_field(ciphertext, key)` → `plaintext`
- `hash_password(password)` → `hash`
- `verify_password(password, hash)` → `bool`

**Compliance:** OWASP Top 10, NIST SP 800-132, NCSC guidance, GDPR Article 32, UK DPA 2018

---

## Versioning

> **IMPORTANT:** Always follow [`.claude/VERSIONING-GUIDE.md`](.claude/VERSIONING-GUIDE.md) for any
> versioning task. The guide defines the authoritative rules — do not infer versioning behaviour
> from any other source.

Two independent tracks:

- **Root workspace version** — tracks the repository as a whole (dev tooling, Rust crates, milestone
  snapshots). Files: `VERSION`, `VERSION-HISTORY.md`, `CHANGELOG.md`, `RELEASES.md`, root
  `pyproject.toml`, root `package.json`, root `Cargo.toml`.
- **Per-module version** — each published package (`packages/backend/`, `packages/web/`, `mobile/`)
  has its own semver in its own version file. Rust crates are exempt — they inherit the root
  workspace version via `version.workspace = true`.

All changelog entries (both tracks) go into the **root** `CHANGELOG.md`. There are no per-module
changelog files.

Use `/syntek-dev-suite:version` to manage all version bumps. See the Versioning Guide for the full
workflow, decision table, and per-module bump procedure.

---

## Ecosystem Context

`syntek-modules` is the foundational layer of the Syntek ecosystem. The full ecosystem:

| Repository              | Role                                                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- |
| `syntek-infrastructure` | NixOS + Rust CLI — server provisioning, Grafana, Prometheus, Loki, Glitchtip, Radicale (CalDav), Plausible |
| `syntek-modules`        | **(this repo)** — reusable packages installed into all projects                                            |
| `syntek-platform`       | Free, self-hostable CMS core (AGPL v3) — Django + GraphQL + PostgreSQL + React + React Native              |
| `syntek-ai`             | Internal knowledge layer — YAML bot definitions, markdown prompts, rule files (no executable code)         |
| `syntek-extensions`     | Paid add-ons for the platform (commercial license)                                                         |
| `syntek-saas`           | Internal Syntek-owned SaaS UI products                                                                     |
| `syntek-licensing`      | License management portal + PostgreSQL (Rust key server lives in infra)                                    |
| `syntek-docs`           | Canonical documentation for the entire ecosystem                                                           |
| `syntek-templates`      | Free starter templates (church, charity, small business, portfolio, events)                                |
| `syntek-premium`        | Paid premium starter templates (per-developer annual license)                                              |
| `syntek-store`          | Third-party developer marketplace — modules, templates, extensions, AI agents                              |
| `syntek-marketplace`    | Internal Claude Code plugins for the Syntek development team                                               |

**Install flow for consuming projects:** `syntek add <package>` → Rust CLI wraps uv/pnpm/cargo →
installs from Forgejo registry.
