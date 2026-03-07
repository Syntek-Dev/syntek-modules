# Syntek Modules

**A library of independently installable, production-grade packages for Django, React, React Native,
and Rust — providing the reusable building blocks that power every Syntek project.**

> Versioned and hosted on the Syntek Hetzner Forgejo instance at
> [git.syntek-studio.com](https://git.syntek-studio.com).

---

## Contributing — Quick Start

> **New to this repo?** Run the bootstrap script and the CLI will guide the rest. See
> [`docs/GUIDES/GETTING-STARTED.md`](docs/GUIDES/GETTING-STARTED.md) for the full walkthrough.

```bash
# 1. Clone
git clone git@git.syntek-studio.com:syntek/syntek-modules.git
cd syntek-modules

# 2. Bootstrap — creates .venv, installs tooling, builds syntek-dev, symlinks to PATH
chmod +x install.sh && ./install.sh

# 3. Activate Python venv
source .venv/bin/activate

# 4. Start development services
syntek-dev up

# 5. Run the full test suite
syntek-dev test

# 6. Run all linters
syntek-dev lint
```

**Key CLI commands:**

| Command                                        | What it does                                                       |
| ---------------------------------------------- | ------------------------------------------------------------------ |
| `syntek-dev up`                                | Start all dev services (frontend watch, Storybook, Rust watcher)   |
| `syntek-dev test`                              | Run all test layers (pytest, cargo test, Vitest, Jest, Playwright) |
| `syntek-dev test --python-package syntek-auth` | Test one backend module                                            |
| `syntek-dev test -m unit`                      | Run only unit tests (pytest marker)                                |
| `syntek-dev lint`                              | Run all linters (ruff, basedpyright, ESLint, clippy, markdownlint) |
| `syntek-dev lint --fix`                        | Auto-fix ruff and ESLint issues                                    |
| `syntek-dev format`                            | Format all code (ruff, prettier, cargo fmt)                        |
| `syntek-dev check`                             | Fast quality check — lint + type-check, no tests                   |
| `syntek-dev db migrate`                        | Run Django migrations via sandbox                                  |
| `syntek-dev db seed`                           | Seed the dev database with factory_boy data                        |
| `syntek-dev db seed-test`                      | Seed with test-specific scenario data                              |
| `syntek-dev open api`                          | Open GraphQL playground in browser                                 |
| `syntek-dev open storybook`                    | Open Storybook component explorer                                  |

---

## Table of Contents

- [Overview](#overview)
- [Ecosystem Architecture](#ecosystem-architecture)
  - [Repository Breakdown](#repository-breakdown)
  - [How They Work Together](#how-they-work-together)
  - [Data Flow](#data-flow)
- [Module Catalogue](#module-catalogue)
  - [Backend — Django + Python](#backend--django--python)
  - [Frontend Web — Next.js + React + TypeScript](#frontend-web--nextjs--react--typescript)
  - [Frontend Mobile — React Native + TypeScript + NativeWind](#frontend-mobile--react-native--typescript--nativewind)
  - [Rust — Field-Level Encryption](#rust--field-level-encryption)
- [Rust Encryption Architecture](#rust-encryption-architecture)
  - [Zero-Plaintext Guarantee](#zero-plaintext-guarantee)
  - [Cryptographic Algorithms](#cryptographic-algorithms)
  - [PyO3 Bridge — Django Integration](#pyo3-bridge--django-integration)
  - [GraphQL Middleware Layer](#graphql-middleware-layer)
  - [Security Standards Alignment](#security-standards-alignment)
- [Technology Stack](#technology-stack)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
  - [For Module Contributors](#for-module-contributors)
  - [For Consuming Projects](#for-consuming-projects)
  - [Versioning and Releases](#versioning-and-releases)
  - [Quality Assurance](#quality-assurance)
- [Getting Started](#getting-started)
  - [Backend Developers](#backend-developers)
  - [Frontend Web Developers](#frontend-web-developers)
  - [Mobile Developers](#mobile-developers)
  - [Rust and Cryptography](#rust-and-cryptography)
- [Security Compliance](#security-compliance)
- [Contact](#contact)

---

## Overview

`syntek-modules` is a library of independently installable packages. It is **not a deployable
application** — it is a collection of discrete, versioned modules that developers install into any
Syntek project as needed.

Each module is designed to work in isolation, be configured entirely through a single settings file
in the consuming project, and integrate seamlessly with every other module in the catalogue. There
are no hardcoded values anywhere in this repository. All frontend configuration is fetched from
Django via GraphQL at runtime.

Packages are distributed through the self-hosted Forgejo instance on the Syntek Hetzner server and
installed via:

- `syntek add syntek-<name>` — Django / Python backend modules
- `syntek add @syntek/<name>` — React / TypeScript web frontend packages
- `syntek add @syntek/mobile-<name>` — React Native / TypeScript mobile packages
- Cargo manifest — Rust encryption crates

**Key Capabilities:**

- **39 Backend Modules** — Authentication, RBAC, multi-tenancy, notifications, payments, invoicing,
  donations, events, forms, audit logging, structured logging, full-text search, reporting,
  background tasks, webhooks, bulk import/export, groups, feature flags, settings store, third-party
  integrations, security middleware, media (Cloudinary), documents (MinIO), GDPR compliance,
  membership, subscriptions, internationalisation, CalDav, address and geo, accounting, email
  marketing, developer API keys, comments, loyalty and referrals, analytics, scheduling, locations,
  inventory, and surveys
- **20 Frontend Web Packages** — Auth UI, session management, typed GraphQL client, data-fetching
  hooks, form primitives, design system, layout shell, data table, notifications, payments, search,
  reporting, settings scaffold, onboarding wizard, GDPR/cookie consent, donations, comments,
  feedback, maps, and scheduling
- **6 Mobile Packages** — Biometric auth, push notifications, payments, offline sync, media capture,
  and NativeWind design system
- **3 Rust Crates** — Field-level AES-256-GCM encryption, PyO3 Django bindings, and GraphQL
  middleware
- **Zero-Plaintext Architecture** — All sensitive data is encrypted at the application layer by the
  Rust layer before any database write; the frontend never touches raw cryptographic operations
- **Settings-Driven Configuration** — Every module is controlled through `SYNTEK_*` settings
  dictionaries; nothing is hardcoded
- **Semantic Versioning** — Each module is versioned independently; changelogs are maintained per
  module
- **Security-First Design** — Aligned with OWASP Top 10, NIST SP 800-132, NCSC guidance, and GDPR
  Article 32

---

## Ecosystem Architecture

`syntek-modules` is the foundational layer of a multi-repository ecosystem. Understanding the role
of each repository is essential to understanding where modules fit in the overall picture.

### Repository Breakdown

#### 1. syntek-infrastructure

_NixOS configuration and Rust CLI tooling for server design and provisioning_

- **Purpose**: Infrastructure as Code for server provisioning, hardening, and management
- **Technology**: NixOS configuration, Rust CLI tools
- **Features**:
  - Automated, reproducible server deployment and configuration via NixOS
  - Complete observability stack: Grafana dashboards, Loki log aggregation, Prometheus metrics,
    Glitchtip error tracking
  - Security hardening, firewall rules, and compliance baselines (CIS Benchmarks)
  - Infrastructure scaling and automated alerting rules
  - Rust CLI tooling for deployment orchestration and server lifecycle management
- **Target Users**: DevOps engineers, system administrators

#### 2. syntek-modules _(this repository)_

_Reusable modular library of Django, React, React Native, and Rust packages_

- **Purpose**: The shared building-block library installed into all Syntek projects
- **Technology**: Django 6.0.4, Python 3.14.3, Next.js 16.1.6, React 19.2, TypeScript 5.9, React
  Native 0.84.x (Expo), NativeWind 4, Rust stable
- **Features**:
  - 39 independently installable Django backend modules
  - 20 React / TypeScript web frontend packages
  - 6 React Native mobile packages
  - 3 Rust crates providing the cryptographic security foundation
  - Zero-plaintext data guarantee across all modules
  - Settings-driven configuration with no hardcoded values
- **Target Users**: Backend developers, frontend developers, mobile developers, security engineers

#### 3. syntek-ai

_Internal knowledge layer — YAML bot definitions, markdown prompts, and rule files_

- **Purpose**: Syntek-owned AI knowledge layer. Pure declarative files — no executable code. YAML
  bot definitions, markdown system prompts, YAML rule/guardrail definitions, and tool configuration
  files encoding Syntek's domain expertise (ministry, charity, SME operations).
- **Technology**: YAML, Markdown. No code. Loaded by `syntek-platform`'s Django AI module at
  runtime.
- **Features**:
  - Pre-built bot products: Youth Ministry Bot, Church Admin Bot, Charity Fundraising Bot
  - Same YAML/markdown format used by the AI Agent & Plugin Builder extension for community-built
    agents
  - Powers both `ai.syntekstudio.com` and the in-platform AI assistant
- **Access**: Internal to Syntek Studio only. Not directly accessible by external developers.

#### 4. syntek-platform

_The core CMS platform — Django / GraphQL / PostgreSQL backend, React / TypeScript / Tailwind web
frontend, React Native / TypeScript / NativeWind mobile frontend_

- **Purpose**: Production-ready CMS and application platform used as the foundation for all client
  projects
- **Technology**: Django 6.0.4, Strawberry GraphQL 0.307.1, PostgreSQL 18.3, React 19.2, TypeScript
  5.9, Tailwind CSS 4.2, React Native 0.84.x (Expo), NativeWind 4
- **Features**:
  - Drag-and-drop page builder with real-time collaborative editing — available on both web and
    mobile (React Native)
  - Online development environment: Monaco Editor and TTY terminal access
  - Multi-tenancy with schema-level isolation
  - GraphQL API layer consumed by both web and mobile frontends
  - Content versioning workflow: `feature` → `testing` → `dev` → `staging` → `production`
  - Cloudinary for all media (images, video) — metadata stored in PostgreSQL, assets served via
    Cloudinary CDN
  - MinIO for document storage only (PDFs, spreadsheets, office files) — presigned URLs; not used
    for images or static assets
  - Next.js `.next` output handles all static file caching, bundling, and asset minification
  - Consumes modules from `syntek-modules` for all business logic
- **Target Users**: Full-stack developers, frontend developers, mobile developers, content editors,
  project managers

#### 5. syntek-templates

_Free curated starter templates for `syntek-platform` developers_

- **Purpose**: Ready-to-use starting points — pages, content structure, and styling — that
  developers clone and customise. Zero custom CSS required; all styling via token overrides.
- **Technology**: Django fixtures, Next.js page components, module manifest file
- **Features**:
  - Church and ministry websites, charity/non-profit sites, small business landing pages,
    portfolios, event microsites
  - Each template declares required modules and minimum platform version
  - Zero custom CSS — token overrides only
- **Access**: Free. No license required. Available to all `syntek-platform` users.

#### 6. syntek-premium

_Paid premium starter templates_

- **Purpose**: More polished designs, more page types, and more advanced content structures than the
  free tier. Same technical structure as `syntek-templates`.
- **Features**:
  - Higher design quality; more page types per template (blog, events, shop stubs, membership area)
  - May include pre-configured extension stubs ready to activate with a valid extension license
  - Ongoing Syntek support and updates
- **Access**: Per-developer annual license (unlimited client installations). Syntek clients included
  automatically.

#### 7–12. Additional Ecosystem Repositories

| Repository           | Purpose                                                                                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `syntek-extensions`  | Individually purchasable paid add-ons for `syntek-platform` (e-commerce, membership, events, email marketing, AI Agent Builder, etc.)                         |
| `syntek-saas`        | Internal Syntek-owned SaaS products (email UI kit, app UI kit, web UI kit) built on `syntek-modules`                                                          |
| `syntek-licensing`   | Developer license portal (Django + Next.js) + PostgreSQL. Rust key server lives in `syntek-infrastructure`.                                                   |
| `syntek-docs`        | Canonical documentation for the entire ecosystem — platform setup, module API reference, extension development guide                                          |
| `syntek-store`       | Third-party developer marketplace. Developers publish modules, templates, extensions, and AI agents; receive 100% of sale price minus Square processing fees. |
| `syntek-marketplace` | Internal Claude Code plugins for the Syntek development team (`syntek-dev-suite`, `syntek-infra-plugin`)                                                      |

### How They Work Together

1. `syntek-infrastructure` provisions and hardens the servers that host everything
2. `syntek-modules` is the foundation — every Syntek-built product is constructed from modules
3. `syntek-platform` is the free, self-hostable CMS core built on top of modules
4. `syntek-extensions` adds paid functionality to the platform via its hook system
5. `syntek-templates` and `syntek-premium` provide free and paid starting-point scaffolds
6. `syntek-ai` provides the AI knowledge layer (YAML/markdown configs) loaded by the platform at
   runtime
7. `syntek-licensing` gates paid features; the Rust key server in `syntek-infrastructure` handles
   cryptographic validation
8. `syntek-store` allows third-party developers to publish and sell their own modules, templates,
   extensions, and AI agents
9. `syntek-docs` is the single source of truth for all ecosystem documentation
10. `syntek-marketplace` provides the internal Claude Code plugins used by the Syntek development
    team

### Data Flow

```text
syntek-modules (foundation — Apache 2.0)
        │ consumed by all products below
        ├──► syntek-platform (CMS core — AGPL v3)
        │         │ hook system
        │         ├──► syntek-extensions (paid add-ons)
        │         ├──► syntek-templates  (free starters)
        │         └──► syntek-premium    (paid starters)
        ├──► syntek-saas     (internal SaaS products)
        └──► syntek-licensing (license portal UI)

syntek-ai (YAML/MD knowledge files)
        └──► loaded by syntek-platform Django AI module at runtime

syntek-licensing ◄──► syntek-infrastructure (Rust key server)
        └──► validates entitlements for extensions, modules, templates

syntek-store
        └──► third-party modules / templates / extensions / AI agents
             license keys issued via syntek-licensing on purchase

syntek-infrastructure
        └──► hosts all of the above for Syntek-managed clients
             (self-hosting: developers run on their own servers, no dependency on Syntek infra)
```

---

## Module Catalogue

### Backend — Django + Python

All backend modules are installed via `syntek add syntek-<name>` (Rust CLI) and configured through
`SYNTEK_*` settings dictionaries in the consuming project's `settings.py`. Nothing is hardcoded; all
configuration is exposed to frontends through the GraphQL API.

---

#### Authentication (`syntek-auth`)

```bash
syntek add syntek-auth
```

Multi-factor authentication, passkeys, social OAuth, and account security for Django applications.

- **MFA**: Time-based one-time passwords (TOTP), SMS-based OTP, email OTP, and hardware key support
- **Passkeys**: WebAuthn / FIDO2 passkey registration and authentication
- **Social OAuth**: Pre-built adapters for Google, Microsoft, Apple, and extensible provider
  interface
- **Session Management**: Sliding window sessions, session revocation, concurrent session limits
- **JWT**: Short-lived access tokens and rotating refresh tokens; RS256 signing
- **Password Security**: Argon2id hashing (via Rust layer) with OWASP-recommended parameters;
  minimum entropy checks; breach detection via HaveIBeenPwned API
- **Account Lockout**: Configurable lockout thresholds, progressive back-off, admin override
- **Brute-Force Protection**: Redis-backed rate limiting per IP and per account

---

#### Permissions / RBAC (`syntek-permissions`)

```bash
syntek add syntek-permissions
```

Role-based access control with object-level granularity and scope-based API access.

- **Roles**: Hierarchical role definitions with inheritance; built-in `superuser`, `admin`,
  `member`, `viewer` roles plus custom role creation
- **Object-Level Permissions**: Per-object grants checked at the ORM layer; compatible with Django's
  permission system
- **Permission Groups**: Named bundles of permissions assigned to roles or individual users
- **Scope-Based API Access**: OAuth2-style scopes on JWT tokens; scope enforcement in GraphQL
  resolvers
- **Tenant Isolation**: Permissions are always scoped to a tenant; cross-tenant permission grants
  are prohibited by design

---

#### Multi-Tenancy (`syntek-tenancy`)

```bash
syntek add syntek-tenancy
```

Complete multi-tenant isolation with schema-per-tenant or row-based strategies.

- **Isolation Strategies**: Schema-per-tenant (PostgreSQL schemas) or row-based isolation with
  `tenant_id` foreign keys; configurable per deployment
- **Tenant Provisioning**: Async tenant creation with schema migration, default data seeding, and
  admin user bootstrap
- **Domain Routing**: Middleware that resolves the active tenant from the request's `Host` header
- **Subdomain Mapping**: Automatic `<slug>.yourdomain.com` routing; custom domain support with SSL
  verification
- **Tenant Lifecycle**: Suspend, deactivate, archive, and delete workflows with data retention
  policies
- **Cross-Tenant Queries**: Opt-in superuser-only cross-tenant query interface for platform
  administrators

---

#### Notifications (`syntek-notifications`)

```bash
syntek add syntek-notifications
```

Unified notification dispatch across in-app, push, SMS, and email channels.

- **In-App Notifications**: Real-time delivery via WebSocket; notification feed with read/unread
  state
- **Push Notifications**: Firebase Cloud Messaging (FCM) for Android; Apple Push Notification
  Service (APNs) for iOS; device token management
- **SMS**: Twilio and AWS SNS adapters; number validation; opt-out management
- **Email**: SMTP and AWS SES adapters; HTML + plain-text templates; unsubscribe handling
- **Notification Preferences**: Per-user, per-channel, per-notification-type preferences stored and
  honoured
- **Delivery Tracking**: Delivery status, open tracking (email), failure recording
- **Retry Logic**: Exponential back-off with configurable max attempts; dead-letter queue for
  permanently failed deliveries

---

#### Payments (`syntek-payments`)

```bash
syntek add syntek-payments
```

Stripe-native payment processing with full subscription lifecycle management.

- **Payment Intents**: Server-side payment intent creation and confirmation; 3DS2 support
- **Subscriptions**: Plan creation, subscription management, trial periods, upgrades, downgrades,
  cancellations
- **Metered Billing**: Usage record reporting, metered plan support, billing period summaries
- **Payment Methods**: Card, BACS Direct Debit, SEPA; saved payment method management per customer
- **Refunds**: Full and partial refunds with reason codes; automatic reversal on disputed charges
- **Dispute Handling**: Webhook-driven dispute detection, evidence submission helpers, dispute
  lifecycle tracking
- **Webhook Security**: HMAC-SHA256 signature verification on all incoming Stripe webhook events

---

#### Invoicing (`syntek-invoicing`)

```bash
syntek add syntek-invoicing
```

Professional invoice generation with UK VAT compliance and HMRC MTD compatibility.

- **Invoice Generation**: PDF invoices rendered via WeasyPrint; fully templatable layout
- **Line Items**: Arbitrary line items with quantity, unit price, VAT rate, and discount support
- **VAT / Tax Calculation**: UK VAT rates (standard 20%, reduced 5%, zero); automatic VAT number
  validation via HMRC API
- **Invoice Numbering**: Configurable sequential numbering with prefix/suffix patterns; gap-free
  sequence enforcement
- **Payment Status**: Draft, sent, partial, paid, overdue, and void states with transition guards
- **Credit Notes**: Full and partial credit notes linked to original invoices; automatic balance
  adjustment
- **UK MTD-Compatible**: Data structures and submission helpers aligned with HMRC Making Tax Digital
  requirements

---

#### Donations (`syntek-donations`)

```bash
syntek add syntek-donations
```

Donation management for charities, churches, and non-profit organisations.

- **One-Off Donations**: Single payment donations with Stripe Payment Intents
- **Recurring Donations**: Weekly, monthly, and annual recurring donations via Stripe Subscriptions
- **Gift Aid**: UK Gift Aid declaration capture, eligibility checks, and HMRC-compatible claim data
  export
- **Donor Management**: Donor profiles, giving history, cumulative totals, communication preferences
- **Campaign Tracking**: Named fundraising campaigns with target amounts, progress tracking, and end
  dates
- **Anonymous Donations**: Full support for anonymous giving with no personally identifiable data
  stored

---

#### Events and Ticketing (`syntek-events`)

```bash
syntek add syntek-events
```

End-to-end event management from creation through check-in.

- **Event Creation**: Single and recurring events; draft, published, cancelled states; rich
  description with media attachments
- **Ticket Types**: Unlimited ticket tiers per event (e.g., General Admission, VIP, Staff);
  individual pricing, capacity, and sale windows per tier
- **Capacity Management**: Real-time sold/remaining counts; over-booking prevention via
  database-level locking
- **Waitlists**: Automatic waitlist enrolment when capacity is reached; notification-driven release
  when places become available
- **QR Code Check-In**: Unique QR code per ticket; scan-based check-in with duplicate prevention and
  offline-capable validation
- **Seat Maps**: Configurable seating plans with zone and row definitions; seat-level reservation
- **Refund Policies**: Per-event configurable refund windows; automatic and manual refund processing
  via Stripe

---

#### Dynamic Forms (`syntek-forms`)

```bash
syntek add syntek-forms
```

Schema-driven form definitions with conditional logic and webhook integration.

- **Schema-Driven Definitions**: Forms defined as JSON schemas stored in the database; fully dynamic
  with no code changes required to add or modify forms
- **Field Types**: Text, textarea, number, email, phone, date, date-range, file upload, single/multi
  select, checkbox, radio, rich text, signature, and geolocation
- **Conditional Logic**: Show/hide and required/optional conditions based on the values of other
  fields; nested condition groups
- **Multi-Step Forms**: Wizard-style multi-step forms with per-step validation; resumable progress
  saved to session
- **Submissions Storage**: All submissions stored with schema version snapshot; queryable via admin
  and GraphQL
- **Webhooks on Submit**: Configurable outbound webhooks triggered on form submission; signed
  payloads; retry on failure

---

#### Audit Logging (`syntek-audit`)

```bash
syntek add syntek-audit
```

Immutable, tamper-evident audit trail for all significant actions in the system.

- **Actor / Resource / Action Model**: Every log entry records who did what to which resource, when,
  and from where (IP, user agent)
- **Immutability**: Audit records are append-only at the database level; no update or delete
  permissions granted to the application user
- **Tamper Detection**: Each log entry includes an HMAC of its content; batch integrity checks
  verify the chain has not been modified
- **GDPR-Compliant Retention**: Configurable retention windows per action category; automated
  anonymisation of PII after the retention period expires
- **Queryable Log Store**: Filterable by actor, resource type, resource ID, action type, date range,
  and IP; paginated GraphQL query interface
- **Structured Export**: Audit logs exportable as JSON, CSV, or PDF reports for compliance
  submissions

---

#### Structured Logging (`syntek-logging`)

```bash
syntek add syntek-logging
```

Production-grade structured logging with Sentry integration and request tracing.

- **JSON-Structured Logs**: All log output formatted as machine-parseable JSON; compatible with Loki
  ingestion in `syntek-infrastructure`
- **Request ID Propagation**: Unique request ID generated per HTTP request and threaded through all
  log statements, Celery tasks, and outbound HTTP calls
- **Sentry Integration**: Automatic error capture and performance tracing via the Sentry SDK;
  release tracking; environment tagging
- **File-Based Dev Logging**: Human-readable coloured console output in development; JSON output in
  staging and production
- **Log Levels per Environment**: Configurable per-environment log levels; `DEBUG` suppressed in
  production by default
- **Sensitive Field Redaction**: Automatic redaction of fields matching configurable patterns
  (passwords, tokens, card numbers) before log emission

---

#### Full-Text Search (`syntek-search`)

```bash
syntek add syntek-search
```

Elasticsearch / OpenSearch integration with per-model indexing and multi-tenant isolation.

- **Search Backend**: Elasticsearch 8.x and OpenSearch 2.x both supported; configurable per
  deployment
- **Per-Model Indexing**: Decorator-based index definitions on Django models; incremental and
  full-index rebuild commands
- **Faceted Search**: Aggregation-based facets (category, price range, date, custom fields);
  real-time facet counts
- **Autocomplete**: Prefix and edge-ngram analysers for instant-search suggestions; typo-tolerance
  via fuzzy matching
- **Relevance Tuning**: Per-field boost weights; recency decay functions; pinned results for
  admin-curated ordering
- **Multi-Tenant Index Isolation**: Separate indices per tenant; cross-index queries prohibited at
  the query-builder level

---

#### Reporting and Exports (`syntek-reporting`)

```bash
syntek add syntek-reporting
```

Role-gated report definitions with scheduled delivery and multi-format export.

- **Report Definitions**: Admin-configurable report schemas specifying data source, filters,
  columns, aggregations, and access roles
- **Scheduled Reports**: Cron-based report scheduling via Celery Beat; delivery to email, S3, or
  in-app notification
- **PDF Export**: Reports rendered to PDF via WeasyPrint; branded templates with logo, headers, and
  page numbers
- **Excel Export**: `.xlsx` export via openpyxl; formatted tables with column headers, data types,
  and freeze panes
- **CSV Export**: Standards-compliant CSV with configurable delimiters and encoding
- **Chart Data Queries**: Optimised aggregate pipeline queries for time-series, distribution, and
  comparison charts; results cacheable in Redis
- **Aggregate Pipelines**: Complex multi-step aggregation definitions using Django ORM annotations;
  reusable across reports and API endpoints

---

#### Background Tasks / Queue (`syntek-tasks`)

```bash
syntek add syntek-tasks
```

Celery-based task queue with priority lanes, monitoring, and dead-letter handling.

- **Celery + Redis**: Redis broker and result backend; broker transport options configurable for
  high-availability setups
- **Task Scheduling**: Celery Beat integration; cron and interval-based periodic tasks defined in
  settings
- **Priority Queues**: Four priority lanes (`critical`, `high`, `default`, `low`); separate Celery
  worker pools per lane
- **Retry Policies**: Per-task configurable max retries, retry delays, and back-off multipliers;
  `autoretry_for` exception lists
- **Dead-Letter Queues**: Failed tasks that exhaust retries are routed to a dead-letter queue with
  full context preservation for manual replay
- **Task Monitoring**: Flower dashboard integration; task success/failure rates; queue depth metrics
  exported to Prometheus

---

#### Webhooks (`syntek-webhooks`)

```bash
syntek add syntek-webhooks
```

Inbound ingestion and outbound dispatch with cryptographic verification and retry logic.

- **Inbound Webhook Ingestion**: Configurable endpoint per integration; raw payload stored before
  processing; idempotency key deduplication
- **Inbound Routing**: Rule-based routing of inbound events to handler functions based on event type
  headers or payload fields
- **Outbound Event Dispatch**: Domain event bus triggers outbound webhooks on configurable
  model/action combinations
- **Signature Verification**: HMAC-SHA256 request signing on all outbound payloads; inbound
  signature verification for Stripe, GitHub, and custom HMAC schemes
- **Retry with Exponential Back-off**: Failed outbound deliveries retried up to 10 times with
  exponential back-off and jitter; configurable per endpoint
- **Delivery Logs**: Full request/response log per delivery attempt; accessible via admin and
  GraphQL for debugging

---

#### Bulk Import / Export (`syntek-bulk`)

```bash
syntek add syntek-bulk
```

Async bulk data operations with validation, progress tracking, and error reporting.

- **CSV / Excel / JSON Import**: File upload with format auto-detection; configurable field mapping
  between file columns and model fields
- **Validation**: Row-level and cross-row validation rules; per-row error accumulation with line
  number references; partial import support
- **Progress Tracking**: Import job progress stored in Redis; real-time progress via WebSocket or
  polling endpoint
- **Error Reporting**: Downloadable error report in the original file format with error annotations
  per failing row
- **Async Processing**: Large imports processed via Celery task; chunked processing to avoid memory
  pressure
- **Field Mapping**: Admin-configurable column-to-field mapping saved per import type; header
  auto-detection; transformation functions

---

#### Groups / Teams / Hierarchy (`syntek-groups`)

```bash
syntek add syntek-groups
```

Flexible organisational structure with nested groups, team membership, and invitation flows.

- **Nested Groups**: Arbitrary depth group hierarchies; parent/child relationships with configurable
  maximum depth
- **Team Membership**: Role-scoped membership (owner, admin, member, viewer); membership history
  tracking
- **Group Permissions**: Permission bundles assigned at the group level and inherited by all members
- **Organisational Hierarchy**: Department / team / sub-team structure; org chart data available via
  GraphQL
- **Invitation Flows**: Email-based invitation with expiry and revocation; accept/decline tracking;
  re-invitation after expiry

---

#### Feature Flags (`syntek-flags`)

```bash
syntek add syntek-flags
```

Runtime feature toggles with granular targeting and an admin control interface.

- **Per-Tenant Flags**: Flags evaluated in the context of the active tenant; different values per
  tenant with no code changes
- **Per-User Flags**: User-level overrides for targeted rollouts, beta programmes, and A/B tests
- **Percentage Rollout**: Deterministic hash-based percentage rollout; consistent flag value per
  user across requests
- **Environment-Scoped Flags**: Independent flag values per environment (development, staging,
  production)
- **Flag Evaluation API**: Single endpoint returning all active flag values for the current user and
  tenant; cacheable response
- **Admin UI Controls**: Flags manageable from the Django admin without deployment; change history
  recorded in audit log

---

#### Per-Tenant Settings Store (`syntek-settings`)

```bash
syntek add syntek-settings
```

Typed key-value settings with per-tenant overrides and schema versioning.

- **Key-Value Store**: Arbitrary typed settings stored per tenant; values encrypted at rest via the
  Rust layer
- **Typed Settings Schema**: Settings declared with Python type annotations; type coercion and
  validation on write
- **Defaults with Override Support**: Global defaults defined in code; tenant-level overrides stored
  in the database; fallback chain: tenant → environment → default
- **Settings Versioning**: Each settings write creates a versioned snapshot; rollback to any
  previous value supported

---

#### Third-Party Integrations Framework (`syntek-integrations`)

```bash
syntek add syntek-integrations
```

OAuth-based third-party connections with encrypted credential storage and health monitoring.

- **OAuth-Based Connections**: Standard OAuth2 authorisation code flow for connecting third-party
  services; token storage and automatic refresh
- **Credential Storage**: All OAuth tokens and API keys encrypted at rest via the Rust
  `syntek-crypto` layer; never stored as plain text
- **Integration Health Checks**: Scheduled background tasks verify each active integration's
  connectivity; failed checks trigger in-app notifications
- **Plug-In Adapter Pattern**: New integrations implemented as adapter classes conforming to a
  standard interface; no changes required to the core module
- **Supported Integrations**: Pre-built adapters for Slack, Microsoft Teams, Google Workspace,
  Mailchimp, HubSpot, Xero, and QuickBooks

---

#### Rate Limiting / Security Middleware (`syntek-security`)

```bash
syntek add syntek-security
```

Comprehensive HTTP security middleware stack covering rate limiting, IP management, and OWASP
Top 10.

- **Redis-Backed Rate Limiting**: Sliding window rate limiting per IP, per user, and per API key;
  configurable limits per endpoint pattern
- **IP Allowlist / Blocklist**: Dynamic allow and block lists stored in Redis; admin-manageable
  without deployment
- **Bot Detection**: User-agent analysis, request pattern analysis, and honeypot endpoint
  integration
- **CORS**: Configurable per-origin CORS policy; preflight caching; credential request handling
- **Content Security Policy (CSP)**: Nonce-based CSP header generation; report-only mode for policy
  development
- **HTTP Strict Transport Security (HSTS)**: HSTS header injection with configurable `max-age` and
  `includeSubDomains`
- **OWASP Top 10 Middleware Stack**: SQL injection header detection, clickjacking protection
  (`X-Frame-Options`), MIME sniffing prevention (`X-Content-Type-Options`), referrer policy,
  permissions policy

---

#### Media — Cloudinary (`syntek-media`)

```bash
syntek add syntek-media
```

Cloudinary-backed media management for images and video, with metadata stored in PostgreSQL.

- **Upload**: Direct upload to Cloudinary with per-tenant folder structure; chunked upload for large
  files
- **Image Transformations**: Crop, resize, format conversion, quality adjustment, and CDN delivery
  URL generation on demand
- **Video Support**: Video upload with transcoding status polling; thumbnail generation
- **MIME Allowlist**: Images and video only — PDFs and office documents are handled by
  `syntek-documents`
- **Metadata Model**: Original filename, dimensions, filesize, MIME type, Cloudinary public ID, and
  CDN URL stored in PostgreSQL
- **Virus Scanning**: Configurable scanner adapter hook on upload
- **GDPR Erasure Hook**: Deletes Cloudinary assets and anonymises PostgreSQL metadata on erasure
  request

---

#### Documents — MinIO (`syntek-documents`)

```bash
syntek add syntek-documents
```

MinIO-backed document storage for PDFs and office files, with presigned URL access control.

- **Upload**: Tenant-isolated bucket paths in MinIO; configurable bucket name and endpoint via
  settings
- **MIME Allowlist**: PDFs, spreadsheets, and Word documents only — images and video are handled by
  `syntek-media`
- **Presigned URLs**: Time-limited presigned download URLs generated on demand; direct download
  without proxying through Django
- **Document Model**: Filename, filesize, MIME type, MinIO object key, uploader, and upload
  timestamp stored in PostgreSQL
- **File Versioning**: New uploads create a version record; previous versions retained with rollback
  support
- **Virus Scanning**: Configurable scanner adapter hook on upload
- **GDPR Erasure Hook**: Hard-deletes MinIO object and anonymises PostgreSQL metadata on erasure
  request

---

#### GDPR / Compliance (`syntek-gdpr`)

```bash
syntek add syntek-gdpr
```

Full GDPR and UK Data Protection Act 2018 compliance toolkit.

- **Subject Access Requests (SAR)**: Collect and export all personal data held for a user as JSON or
  PDF
- **Right to Erasure**: Anonymise or delete personal data across all registered modules via a single
  erasure request; modules register their erasure handlers with `syntek-gdpr`
- **Consent Management**: Granular consent records per purpose category (analytics, marketing,
  functional); full consent history log
- **Data Retention Policies**: Configurable retention periods per data category; automated
  enforcement via Celery Beat
- **Processing Register**: Data processing activity register with controller and processor records;
  exportable for regulatory submissions
- **Strawberry Queries**: `consentHistory`, `subjectAccessRequest(userId)`, `processingRegister`
- **Strawberry Mutations**: `recordConsent`, `withdrawConsent`, `submitSAR`, `submitErasureRequest`

---

#### Membership (`syntek-membership`)

```bash
syntek add syntek-membership
```

Membership tier management with renewals, lapsed member handling, and a configurable member
directory.

- **Membership Tiers**: Configurable tier definitions with name, price, and associated permission
  bundles
- **Membership Lifecycle**: Active, pending renewal, lapsed, and cancelled states with automated
  transitions at renewal date
- **Renewal Reminders**: Configurable notification dispatch at configurable days before expiry via
  `syntek-notifications`
- **Member Directory**: Opt-in directory listing with configurable visible fields and per-member
  privacy controls
- **Bulk Import**: Import member lists from CSV with tier assignment
- **Payments Integration**: Online membership payment via `syntek-payments`; Stripe Subscriptions
  for recurring billing

---

#### Subscriptions (`syntek-subscriptions`)

```bash
syntek add syntek-subscriptions
```

Recurring subscription lifecycle management extending `syntek-payments`.

- **Subscription Model**: Plan, status, current period start/end, trial end, and
  cancel-at-period-end flag
- **Billing Cycles**: Monthly, quarterly, and annual billing; pro-rata upgrades and downgrades
- **Usage-Based Billing**: Metered usage records reported to Stripe; billing period summaries
- **Grace Period Handling**: Failed payment retry schedule; subscription suspension after exhausted
  retries; reinstatement on successful payment
- **Webhook-Driven State Sync**: Stripe events update subscription status in real time; no polling
  required

---

#### Internationalisation (`syntek-i18n`)

```bash
syntek add syntek-i18n
```

Locale detection, translation management, and UK-centric date, number, and currency formatting.

- **Locale Detection**: Inferred from the `Accept-Language` header, user preference, or tenant
  default; falls back gracefully
- **Translation Strings**: Django translation framework integration with `.po` / `.mo` file support
  and a management command for extraction
- **Date Formatting**: UK-default `DD/MM/YYYY`; configurable per locale
- **Number Formatting**: Locale-aware thousand separators and decimal points
- **Currency Formatting**: GBP default; multi-currency display with locale-appropriate symbols and
  formatting
- **GraphQL Locale Context**: Active locale resolved per request and available in all Strawberry
  resolvers

---

#### CalDav Sync (`syntek-caldav`)

```bash
syntek add syntek-caldav
```

CalDav client for syncing events and appointments with the Radicale server in
`syntek-infrastructure`.

- **CalDav Client**: `caldav` Python library integration; configurable server URL and credentials
  via `SYNTEK_CALDAV` settings
- **Event Sync**: Push `syntek-events` records to CalDav calendars; pull external CalDav events into
  the local database
- **Per-User Calendars**: Each user gets a personal CalDav calendar endpoint; events always scoped
  to tenant
- **iCal Export**: Generate `.ics` files for any event, date range, or calendar view on demand

---

#### Address and Geo (`syntek-geo`)

```bash
syntek add syntek-geo
```

UK postcode lookup and address geocoding with Redis caching.

- **UK Postcode Lookup**: postcodes.io or OS Places API; returns street, town, county, and
  coordinates per postcode
- **Address Geocoding**: Convert an address string to latitude/longitude via Google Maps or OS
  Places API
- **Response Caching**: All lookups cached in Redis with configurable TTL to avoid redundant
  external API calls
- **Error Handling**: `InvalidPostcodeError` for malformed postcodes; graceful degradation when the
  external API is unavailable
- **Strawberry Queries**: `lookupPostcode(postcode)`, `geocodeAddress(address)`

---

#### Accounting and Ledger (`syntek-accounting`)

```bash
syntek add syntek-accounting
```

Double-entry accounting ledger with UK VAT calculation and Xero / Sage / QuickBooks Online sync.

- **Double-Entry Validation**: Every journal entry must balance (debits == credits);
  `UnbalancedEntryError` raised on rejection
- **Chart of Accounts**: Assets, liabilities, equity, income, and expenses; configurable account
  codes per tenant
- **VAT Calculation**: UK VAT period summaries with output tax, input tax, and net VAT payable
- **Xero Sync**: Post transactions to Xero via `syntek-integrations`; sync status recorded per
  transaction
- **Sage and QuickBooks Online**: Adapter-based sync for both platforms using the same
  `syntek-integrations` credential store
- **Strawberry Queries**: `accounts`, `journalEntries`, `vatReturn(period)`
- **Strawberry Mutations**: `postJournalEntry`, `syncToXero`, `syncToSage`, `syncToQBO`

---

#### Email Marketing (`syntek-email-marketing`)

```bash
syntek add syntek-email-marketing
```

Mailing list management, campaign dispatch, open/click tracking, and GDPR opt-out enforcement.

- **Mailing Lists**: Create and manage subscriber lists with double opt-in confirmation support
- **Campaign Dispatch**: HTML campaign sending via the configured email backend; unsubscribe list
  enforced at dispatch — no exceptions
- **Unsubscribe Handling**: One-click unsubscribe link generation and handler; permanently excluded
  contacts cannot be re-added without a new explicit opt-in
- **Open Tracking**: Pixel embedded in campaign emails; `EmailOpen` record created with timestamp on
  pixel load
- **Click Tracking**: Redirect-based click tracking; `EmailClick` record created per link click
- **GDPR Erasure Hook**: Anonymises email address and open/click records on erasure request from
  `syntek-gdpr`

---

#### Developer API Keys (`syntek-api-keys`)

```bash
syntek add syntek-api-keys
```

Scoped API key issuance for machine-to-machine access to the GraphQL API.

- **Key Generation**: Cryptographically random keys shown to the developer once only; stored as
  HMAC-SHA256 hash — never plain text
- **Scope-Based Access Control**: Keys issued with explicit scopes (e.g. `orders:read`);
  unauthorised scope returns 403 at the resolver level
- **Revocation**: Immediate revocation via `revoked_at` timestamp; cached in Redis for
  sub-millisecond rejection; revoked key returns 401
- **Audit Integration**: API key ID (not plaintext key) recorded as the actor in `syntek-audit` on
  every authenticated request
- **Strawberry Queries**: `apiKeys` — metadata only; key values are never returned after creation
- **Strawberry Mutations**: `createApiKey`, `revokeApiKey`

---

#### Comments and Discussions (`syntek-comments`)

```bash
syntek add syntek-comments
```

Threaded comments attachable to any Django model, with moderation and reactions.

- **Generic FK**: Comments linked to any model via `content_type` / `object_id`; no schema changes
  required per target model
- **Threaded Replies**: Parent FK on `Comment`; configurable maximum nesting depth
- **Moderation**: Hold-for-review state triggered by configurable content patterns; `approveComment`
  mutation for moderators
- **Reactions**: Emoji/type reactions per comment; unique-per-user constraint; aggregate counts
  maintained
- **Strawberry Queries**: `comments(contentType, objectId)`, `commentThread(id)`
- **Strawberry Mutations**: `addComment`, `editComment`, `deleteComment`, `addReaction`,
  `removeReaction`, `approveComment`

---

#### Loyalty and Referrals (`syntek-loyalty`)

```bash
syntek add syntek-loyalty
```

Points engine, tier progression, and referral attribution for customer loyalty programmes.

- **Points Engine**: Configurable earn rules per action type; credits, debits, and running balance
  tracked per user via `LoyaltyTransaction`
- **Tier Progression**: Automatic tier evaluation on balance change; promotion and demotion
  notifications dispatched via `syntek-notifications`
- **Referral Links**: Unique referral link generation per user; conversion attribution on qualifying
  actions; configurable reward on conversion
- **Redemption**: Points debit with negative-balance guard; redemption records linked to the
  originating `LoyaltyTransaction`
- **Strawberry Queries**: `loyaltyAccount`, `loyaltyTransactions`, `referralStats`
- **Strawberry Mutations**: `redeemPoints`, `generateReferralLink`

---

#### Analytics (`syntek-analytics`)

```bash
syntek add syntek-analytics
```

Privacy-first analytics integration with Plausible and Fathom.

- **Plausible Integration**: Page view and custom event tracking via the Plausible Events API
- **Fathom Integration**: Alternative privacy-first backend; switchable via `SYNTEK_ANALYTICS`
  settings
- **Django Middleware**: Automatic server-side page view tracking for non-Next.js views
- **Custom Event API**: `track_event(name, properties)` callable from any view or Celery task
- **Consent-Gated**: Analytics scripts injected only after the user grants analytics consent via
  `syntek-gdpr`; no tracking without explicit consent
- **Admin Dashboard**: Aggregate page view and event data queryable via Strawberry GraphQL

---

#### Scheduling (`syntek-scheduling`)

```bash
syntek add syntek-scheduling
```

Appointment and availability scheduling with calendar integration.

- **Availability Slots**: Define available time windows per resource (person, room, or service);
  slot granularity configurable
- **Booking Model**: Appointment records linked to slots, attendees, and resources; `pending`,
  `confirmed`, and `cancelled` states
- **Recurring Events**: Weekly, monthly, and custom recurrence rules; individual occurrence
  exceptions
- **Timezone Handling**: All times stored as UTC; displayed in the user's configured timezone
- **Google Calendar Sync**: Push confirmed bookings to Google Calendar via `syntek-integrations`
- **iCal Export**: Generate `.ics` files for confirmed appointments on demand
- **Strawberry Queries**: `availableSlots(resourceId, dateRange)`, `appointments`
- **Strawberry Mutations**: `bookAppointment`, `cancelAppointment`, `confirmAppointment`

---

#### Locations (`syntek-locations`)

```bash
syntek add syntek-locations
```

Location model with geospatial query support for proximity-based features.

- **Location Model**: Address, coordinates (latitude/longitude), and optional label and category
  fields
- **Geospatial Queries**: `nearby(lat, lng, radiusKm)` using PostgreSQL `earthdistance` extension;
  results ordered by distance
- **Geocoding Integration**: Auto-geocode address fields via `syntek-geo` on save; reverse geocoding
  of coordinates to address string
- **Generic FK Attachments**: Attach locations to any model without schema changes
- **Strawberry Queries**: `locations`, `nearbyLocations(lat, lng, radius)`, `locationDetail(id)`

---

#### Inventory (`syntek-inventory`)

```bash
syntek add syntek-inventory
```

Stock level tracking with multi-location support and low-stock alerting.

- **Inventory Items**: SKU, name, description, unit cost, and current stock level per item
- **Stock Movements**: `StockMovement` records for every in/out/adjustment with reason code and
  reference document
- **Multi-Location Stock**: Track stock levels independently per warehouse, shop, or storage
  location
- **Low-Stock Alerts**: Configurable threshold per item; notification dispatched via
  `syntek-notifications` when stock falls below threshold
- **Barcode/QR Code**: EAN-13 and QR code generation per item; scan-based lookup
- **Reservations**: Reserve stock on order creation; release on cancellation; prevents overselling
- **Strawberry Queries**: `inventory`, `stockMovements(itemId)`, `lowStockItems`
- **Strawberry Mutations**: `adjustStock`, `transferStock`, `receiveStock`

---

#### Feedback and Surveys (`syntek-feedback`)

```bash
syntek add syntek-feedback
```

Survey builder and response collection with conditional question logic and analytics.

- **Survey Model**: Multi-question surveys with configurable question types: rating scale, free
  text, single choice, multi-choice, and NPS
- **Conditional Questions**: Show/hide questions based on previous answers using the same logic
  engine as `syntek-forms`
- **Response Collection**: Anonymous and attributed response storage; duplicate submission
  prevention per user or fingerprint
- **NPS Scoring**: Automatic Net Promoter Score calculation per survey period;
  promoter/passive/detractor breakdown
- **Response Analytics**: Aggregate counts and percentages per question; full response export to CSV
- **Strawberry Queries**: `surveys`, `surveyResponses(surveyId)`, `surveyAnalytics(surveyId)`
- **Strawberry Mutations**: `createSurvey`, `submitSurveyResponse`

---

### Frontend Web — Next.js + React + TypeScript

All web packages are installed via `syntek add @syntek/<name>` (Rust CLI). Every package is fully
typed with TypeScript. No package makes direct database calls or contains hardcoded API URLs — all
data access goes through the typed GraphQL client.

---

#### Auth UI (`@syntek/ui-auth`)

```bash
syntek add @syntek/ui-auth
```

Complete authentication UI component library for web applications.

- Login form with email/password and social OAuth buttons
- Registration flow with email verification step
- MFA setup wizard: TOTP QR code display, backup codes, and challenge screen
- Password reset flow: request, email link, and new password screens
- Account lockout screen with unlock request
- Passkey enrolment: WebAuthn credential creation flow with browser support detection
- All components are headless-first with Tailwind-based default styles; fully overridable

---

#### Session Management (`@syntek/session`)

```bash
syntek add @syntek/session
```

Client-side session lifecycle management with multi-tab coordination.

- React context provider wrapping the application; session state available via `useSession()` hook
- Silent token refresh: access token refreshed before expiry using the refresh token; no visible
  interruption
- Idle timeout: configurable inactivity detection with warning modal before automatic logout
- Multi-tab synchronisation: logout and session refresh events broadcast across tabs via
  `BroadcastChannel`
- Logout on expiry: automatic redirect to login when the session cannot be refreshed

---

#### API Client (`@syntek/api-client`)

```bash
syntek add @syntek/api-client
```

Type-safe GraphQL client generated from the backend schema.

- Generated typed operations via `graphql-codegen`; all queries, mutations, and subscriptions are
  fully typed end-to-end
- Automatic JWT injection into `Authorization` header on every request
- Request signing for sensitive operations
- Error normalisation: GraphQL errors, network errors, and validation errors mapped to a consistent
  `ApiError` type
- Configurable base URL via environment variable; no hardcoded endpoints

---

#### Data Fetching Hooks (`@syntek/data-hooks`)

```bash
syntek add @syntek/data-hooks
```

Ergonomic React hooks built on top of the typed API client.

- `usePaginatedQuery`: cursor and offset pagination with loading and error states
- `useInfiniteScroll`: infinite scroll with intersection observer-based page loading
- `useMutation`: mutation wrapper with optimistic update support and automatic rollback on error
- Cache invalidation helpers: typed query key factories and invalidation utilities compatible with
  React Query

---

#### Form Primitives and Validation (`@syntek/forms`)

```bash
syntek add @syntek/forms
```

Headless form primitives with Zod schema validation and dynamic field rendering.

- Headless form components: controlled inputs, field wrappers, error display, and submit handling
  with no default styling assumptions
- Zod-based schema validation: schema defined once in TypeScript; validated on change, blur, and
  submit
- Field error display: per-field and form-level error messages with accessible ARIA associations
- Dynamic field rendering: renders form fields from a JSON schema (as generated by `syntek-forms`
  backend module); field types, labels, validation rules, and conditional visibility all driven by
  schema

---

#### Design System / UI Components (`@syntek/ui`)

```bash
syntek add @syntek/ui
```

Accessible Tailwind 4.2 component library (WCAG 2.1 AA). Every component is headless-first with
Tailwind-based default styles that are fully overridable per project.

- **Primitives**: Button, Input, Textarea, Select, Checkbox, Radio, Switch, Slider, DatePicker
- **Feedback**: Toast, Alert, Badge, Progress, Skeleton, Spinner
- **Overlay**: Modal, Drawer, Popover, Tooltip, ContextMenu, DropdownMenu
- **Navigation**: Tabs, Accordion, Breadcrumb, Pagination, Stepper
- **Data Display**: Avatar, Card, Table, List, Stat, Divider
- **Layout**: Header, Footer, Navbar (top-level site chrome — logo, links, CTA, mobile hamburger
  menu), Hero, Section, Container
- All components pass axe-core automated accessibility checks; keyboard navigation and screen reader
  support throughout
- Design tokens exposed as CSS custom properties; per-tenant branding applied by overriding token
  values at the root level

---

#### Layout Shell (`@syntek/layout`)

```bash
syntek add @syntek/layout
```

Application shell components for dashboard and admin-style layouts.

- Sidebar navigation with collapsible sections, badge counts, and active-item highlighting
- Top navigation bar with user menu, notifications bell, and global actions
- Breadcrumb navigation with auto-generation from route hierarchy
- Command palette: `Cmd+K` / `Ctrl+K` triggered; fuzzy-search navigation across routes, actions, and
  records
- Responsive shell: mobile drawer sidebar; desktop persistent sidebar; breakpoint-aware layout
  switching
- Per-tenant branding tokens: logo, primary colour, sidebar colour scheme applied at the shell level

---

#### Data Table (`@syntek/data-table`)

```bash
syntek add @syntek/data-table
```

Feature-complete data table for displaying and manipulating large datasets.

- Column sorting (client and server-side) and multi-column sort support
- Column-level and global text filtering; filter state serialised to URL query parameters
- Pagination: page-size selector; page navigation; total record count display
- Column visibility toggle: user-configurable column show/hide saved to `localStorage`
- Row selection: single and multi-row selection with `Shift+click` range selection
- Bulk actions: configurable action menu applied to selected rows; confirmation modal for
  destructive actions
- CSV export: exports current view (filtered, sorted) to CSV

---

#### Notifications UI (`@syntek/ui-notifications`)

```bash
syntek add @syntek/ui-notifications
```

In-application notification centre with real-time delivery.

- Notification bell icon with unread count badge in the layout shell
- Notification feed: chronological list with title, body, timestamp, and action link
- Read / unread state management: mark individual or all notifications as read
- Real-time updates: new notifications delivered via WebSocket subscription without page refresh
- Notification categories: configurable visual differentiation by notification type (info, success,
  warning, alert)

---

#### Payments and Checkout UI (`@syntek/ui-payments`)

```bash
syntek add @syntek/ui-payments
```

Complete payment flow UI built on Stripe Elements.

- Stripe Elements integration: `CardElement`, `PaymentElement`, and `AddressElement` wrapped in
  React components
- Checkout flow: multi-step checkout with order summary, payment method input, and confirmation
  screen
- Subscription management: current plan display, upgrade/downgrade flow, cancellation with
  confirmation
- Invoice list: paginated invoice history with PDF download links
- Payment method management: saved card display, add new card, set default, and remove flows

---

#### Search UI (`@syntek/ui-search`)

```bash
syntek add @syntek/ui-search
```

Global search interface with faceted filtering and keyboard navigation.

- Global search bar: opens inline or in a modal; submits to the search results page
- Faceted filters: rendered from the facet aggregations returned by `syntek-search`; multi-select;
  active filter chips
- Autocomplete: debounced suggestion dropdown powered by the search module's autocomplete endpoint
- Highlighted results: search term highlighting in result titles and excerpts
- Keyboard navigation: full arrow-key and `Enter`/`Escape` navigation within the search modal

---

#### Reporting and Charts (`@syntek/ui-reporting`)

```bash
syntek add @syntek/ui-reporting
```

Chart components and a report builder UI for data visualisation.

- Chart types: Line, Bar (grouped and stacked), Pie, Donut, Area, Scatter, and Heatmap — built on
  Recharts
- Date range picker: preset ranges (today, 7 days, 30 days, custom) with calendar UI
- Report builder UI: drag-and-drop column selector, filter builder, and grouping controls — renders
  report definitions stored in `syntek-reporting`
- Export buttons: triggers PDF, Excel, and CSV export from the backend; download via signed URL

---

#### Settings Page Scaffold (`@syntek/ui-settings`)

```bash
syntek add @syntek/ui-settings
```

Pre-built settings page sections with consistent layout.

- Account settings: display name, email change with re-verification, profile photo upload
- Security settings: password change, MFA management, active sessions list with revocation
- Notification preferences: per-channel, per-type toggle matrix
- Billing: current plan, payment method management, invoice history, upgrade/downgrade
- Team management: member list, invite new members, role assignment, remove members
- Consistent two-column layout (navigation sidebar + content area) with mobile-responsive stacking

---

#### Onboarding Wizard / Stepper (`@syntek/ui-onboarding`)

```bash
syntek add @syntek/ui-onboarding
```

Multi-step onboarding wizard with resumable state.

- Multi-step wizard container with animated step transitions
- Progress indicator: numbered steps, step labels, and completion percentage
- Per-step validation: next button disabled until the current step is valid; validation errors
  displayed inline
- Resumable state: wizard progress persisted to the backend; users can leave and resume from the
  last completed step
- Per-tenant onboarding flows: wizard steps and content configured by tenant settings via GraphQL;
  no hardcoded step sequences

---

#### GDPR & Cookie Consent (`@syntek/ui-gdpr`)

```bash
syntek add @syntek/ui-gdpr
```

Reusable, fully customisable GDPR compliance UI components.

- **Cookie Consent Banner**: Configurable pop-up displayed on first visit; accepts, rejects, or
  granularly manages cookie categories (strictly necessary, analytics, marketing, preferences);
  position and content configurable via props
- **Privacy Preference Centre**: Full-screen modal allowing users to review and update their consent
  choices per category at any time; accessible via a persistent "Cookie Settings" link
- **Consent State Management**: Consent decisions stored in a typed context provider; downstream
  components (e.g. analytics scripts) conditionally rendered based on consent state
- **Plausible Integration Hook**: `usePlausible()` hook that only activates the Plausible analytics
  script once analytics consent is granted; no script injected without explicit consent
- **Data Request Forms**: Subject Access Request (SAR) and Right to Erasure request form components
  that submit to the `syntek-gdpr` backend module
- **Design Tokens**: Banner, modal, and button styles driven entirely by CSS custom property tokens;
  drop in any project's design system colours without overriding component internals
- Fully accessible: focus-trapped modal, keyboard-navigable toggle switches, `aria-live`
  announcements for consent state changes

---

#### Donations UI (`@syntek/ui-donations`)

```bash
syntek add @syntek/ui-donations
```

Donation form and giving history UI components for charities and non-profit organisations.

- Donation amount selector: preset amounts with custom entry; one-off and recurring toggle
- Gift Aid declaration form: eligibility question, confirmation checkbox, and validation
- Campaign progress bar: target amount, raised amount, and percentage filled display
- Giving history: paginated list of past donations with amounts, dates, and Gift Aid status
  indicators
- Donation confirmation: receipt display with charity branding and Gift Aid claim reference

---

#### Comments UI (`@syntek/ui-comments`)

```bash
syntek add @syntek/ui-comments
```

Threaded comment UI connecting to `syntek-comments` via GraphQL.

- `CommentThread` component: renders nested comment tree with configurable maximum display depth
- `CommentForm` with inline validation, character count, and submission loading state
- Reaction picker with aggregate counts and the current user's own reaction highlighted
- Moderation indicators: held-for-review badge visible to users with the moderator role
- Progressive disclosure: load more replies without a full page refresh

---

#### Feedback and Surveys UI (`@syntek/ui-feedback`)

```bash
syntek add @syntek/ui-feedback
```

Survey renderer and response UI connecting to `syntek-feedback` via GraphQL.

- `SurveyForm` renderer: maps survey schema to appropriate field components automatically
- Rating scale, NPS widget, and multi-choice question components
- Conditional question visibility resolved client-side from the survey schema
- Multi-page survey progress indicator
- Response confirmation screen with configurable thank-you message

---

#### Maps and Locations UI (`@syntek/ui-maps`)

```bash
syntek add @syntek/ui-maps
```

Map components and location picker integrating Mapbox or Google Maps.

- `Map` component: Mapbox GL JS or Google Maps wrapper; provider configured via `SYNTEK_MAPS`
  settings
- `LocationMarker`: pin component with configurable icon and popup content
- `LocationPicker` form field: address search-and-select input with live map preview
- Proximity list: sorted list of locations by distance from a reference point
- Cluster rendering: automatic marker clustering for dense datasets

---

#### Scheduling UI (`@syntek/ui-scheduling`)

```bash
syntek add @syntek/ui-scheduling
```

Calendar and appointment booking UI connecting to `syntek-scheduling` via GraphQL.

- Calendar view: month, week, and day views built on `react-big-calendar`
- Availability grid: visual slot picker showing available and booked slots per resource
- `BookingForm` with resource selector, date/time picker, and attendee input
- Appointment status indicators: pending, confirmed, and cancelled with colour-coded differentiation
- Cancellation flow with confirmation modal and reason capture

---

### Frontend Mobile — React Native + TypeScript + NativeWind

All mobile packages are installed via `syntek add @syntek/mobile-<name>` (Rust CLI). All packages
target both iOS and Android via Expo's managed workflow unless stated otherwise.

---

#### Auth UI (`@syntek/mobile-auth`)

```bash
syntek add @syntek/mobile-auth
```

Native mobile authentication screens and flows.

- Biometric authentication: Face ID (iOS) and Touch ID / Fingerprint (iOS + Android) via
  `expo-local-authentication`; graceful fallback to PIN/password
- Social login: Google and Apple Sign-In via Expo Auth Session; deep link callback handling
- OTP screens: SMS and email OTP input with auto-fill from the system clipboard
- Passkey support: device-bound passkey creation and assertion via the platform authenticator
- Deep link handling: handles authentication magic links and OAuth redirect URIs from email and push
  taps

---

#### Push Notifications (`@syntek/mobile-notifications`)

```bash
syntek add @syntek/mobile-notifications
```

End-to-end push notification integration for iOS and Android.

- FCM and APNs integration via `expo-notifications`; single API for both platforms
- Notification permissions flow: system permission request with pre-prompt explanation screen;
  graceful handling of denial
- In-app notification centre: mirrored from `@syntek/ui-notifications` adapted for native UI
  patterns
- Deep-link routing: notification tap navigates to the relevant screen using the notification's
  payload data; works in foreground, background, and killed states

---

#### Payments (`@syntek/mobile-payments`)

```bash
syntek add @syntek/mobile-payments
```

Native mobile payment flows for iOS and Android.

- Apple Pay: `PKPaymentRequest` integration via `@stripe/stripe-react-native`; wallet availability
  detection
- Google Pay: Google Pay API integration via Stripe; availability detection per device
- Stripe Mobile SDK: full Stripe React Native SDK integration; `PaymentSheet` and custom card form
  options
- Subscription management screens: current plan, upgrade/downgrade, cancellation
- Payment history: transaction list with status indicators and receipt links

---

#### Offline Sync (`@syntek/mobile-sync`)

```bash
syntek add @syntek/mobile-sync
```

Local data persistence and conflict-free synchronisation.

- Local SQLite cache: structured local storage via `expo-sqlite`; mirrors critical remote data for
  offline access
- Conflict resolution strategy: configurable last-write-wins or server-authoritative resolution per
  entity type
- Sync status indicator: visual indicator of pending, syncing, and synced states
- Background sync on reconnect: `NetInfo` connectivity monitoring triggers automatic sync when the
  device regains network access

---

#### Mobile UI / Design System (`@syntek/mobile-ui`)

```bash
syntek add @syntek/mobile-ui
```

NativeWind-based component library for React Native.

- NativeWind component library: Tailwind-class-driven styling matching the web design system tokens
  for visual consistency
- Platform-adaptive: components render with platform-appropriate styling (iOS vs Android) for feel
  while maintaining visual consistency
- Motion primitives: shared element transitions, list animations, and micro-interactions via
  `react-native-reanimated`
- Accessible components: all components include appropriate `accessibilityRole`,
  `accessibilityLabel`, and `accessibilityHint` props; VoiceOver and TalkBack tested

---

#### Media (`@syntek/mobile-media`)

```bash
syntek add @syntek/mobile-media
```

Camera, photo library, and video capture for React Native, uploading to `syntek-media` via GraphQL.

- Camera capture: photo and video via `expo-camera`; permission request flow with pre-prompt
  explanation screen
- Photo library picker: single and multi-select via `expo-image-picker`; original and compressed
  quality options
- Upload progress: chunked upload with real-time progress bar; cancellable in-flight uploads
- Image preview: thumbnail display with crop and rotate controls before upload
- MIME type enforcement: validates file type client-side before upload to match the `syntek-media`
  allowlist

---

### Rust — Field-Level Encryption

The Rust layer is the security foundation for all data at rest. Three crates provide the
cryptographic primitives consumed by Django and GraphQL.

```toml
[dependencies]
syntek-crypto = { git = "https://git.syntek-studio.com/syntek/syntek-modules" }
syntek-pyo3   = { git = "https://git.syntek-studio.com/syntek/syntek-modules" }
```

See the [Rust Encryption Architecture](#rust-encryption-architecture) section for full technical
detail.

---

## Rust Encryption Architecture

### Zero-Plaintext Guarantee

**Nothing sensitive is ever stored as plain text in any database.** This is not a policy — it is
enforced architecturally.

The Rust encryption layer sits between Django and the database. All sensitive fields are encrypted
at the application layer by `syntek-crypto` before any ORM write, and decrypted only after a valid
decryption key is presented and the integrity check passes. The frontend never touches raw
cryptographic operations. GraphQL resolvers never return raw encrypted ciphertext — the
`syntek-graphql-crypto` middleware layer intercepts resolver output and performs decryption before
the response is serialised.

This means that even if the PostgreSQL database were fully compromised, no sensitive data would be
readable without the application-layer encryption keys.

### Cryptographic Algorithms

#### AES-256-GCM — Symmetric Encryption (`syntek-crypto`)

All sensitive fields are encrypted using **AES-256-GCM** (Authenticated Encryption with Associated
Data).

- **Algorithm**: AES-256-GCM via the `aes-gcm` crate
- **Key Length**: 256 bits (32 bytes)
- **Nonce**: 96-bit (12-byte) random nonce generated per encryption operation via `rand_core::OsRng`
  (OS-level CSPRNG)
- **Authentication Tag**: 128-bit GCM authentication tag appended to every ciphertext; decryption
  fails immediately if the tag does not verify, preventing any use of tampered data
- **Associated Data**: Model name and field name are bound as associated data (AAD), preventing
  cross-field or cross-model ciphertext substitution attacks
- **Storage Format**: `base64(nonce || ciphertext || tag)` stored as a text field in PostgreSQL

#### Argon2id — Key Derivation and Password Hashing

Password hashing and encryption key derivation use **Argon2id** via the `argon2` crate.

- **Algorithm**: Argon2id (hybrid variant: side-channel resistant and GPU-resistant)
- **Parameters (OWASP-recommended)**:
  - Memory cost: `m = 65536` (64 MB)
  - Time cost: `t = 3` (3 iterations)
  - Parallelism: `p = 4`
- **Salt**: 128-bit random salt per operation via `OsRng`
- **Output Length**: 256 bits (32 bytes) for key derivation; 512 bits (64 bytes) for password hashes
- **NIST Alignment**: Parameters meet NIST SP 800-132 requirements for memory-hard password hashing

#### HMAC-SHA-256 — Data Integrity

All encryption key derivations and audit log entry chains are verified using **HMAC-SHA-256** via
the `hmac` and `sha2` crates.

- Provides cryptographic assurance that stored values have not been modified outside of the
  application
- Used in audit log tamper detection to chain log entries into a verifiable sequence
- Used in webhook signature generation and verification

#### Memory Safety — `zeroize`

All sensitive values (plaintext, keys, passwords) are **zeroised from memory** immediately after use
via the `zeroize` crate.

- Encryption keys are held in a `Zeroizing<Vec<u8>>` wrapper; memory is overwritten with zeros on
  drop
- Plaintext field values are zeroised after encryption is complete
- Password bytes are zeroised after Argon2id hashing
- Keys are **never written to disk, never logged, and never included in error messages**

### PyO3 Bridge — Django Integration

The `syntek-pyo3` crate exposes the Rust cryptographic operations to Django via **PyO3** bindings,
compiled as a native Python extension module.

```python
from syntek_pyo3 import encrypt_field, decrypt_field, hash_password, verify_password

# Called transparently by the Django model layer
ciphertext = encrypt_field(plaintext, field_key, model_name, field_name)
plaintext   = decrypt_field(ciphertext, field_key, model_name, field_name)

# Called by syntek-auth for password operations
hashed   = hash_password(raw_password)
is_valid = verify_password(raw_password, hashed)
```

The four exposed functions are:

| Function                                       | Description                                                                       |
| ---------------------------------------------- | --------------------------------------------------------------------------------- |
| `encrypt_field(plaintext, key, model, field)`  | Encrypts a field value with AES-256-GCM; returns base64-encoded ciphertext        |
| `decrypt_field(ciphertext, key, model, field)` | Decrypts and verifies a ciphertext; raises `DecryptionError` on integrity failure |
| `hash_password(password)`                      | Hashes a password with Argon2id; returns a PHC string                             |
| `verify_password(password, hash)`              | Verifies a password against an Argon2id PHC string; returns bool                  |

Django model fields that store sensitive data use a custom `EncryptedField` descriptor that calls
`encrypt_field` in `pre_save` and `decrypt_field` in `from_db_value` transparently. Application code
reads and writes plain Python strings; the encryption round-trip is invisible.

### GraphQL Middleware Layer

The `syntek-graphql-crypto` crate provides a **Strawberry GraphQL middleware** that intercepts
resolver execution and ensures no encrypted field values are ever returned as raw ciphertext.

- Resolver output is inspected against the field's type annotation
- Fields annotated with `@encrypted` in the schema definition are decrypted before serialisation
- If decryption fails (key missing, integrity check failed), the field is replaced with `null` and
  an error is added to the response `errors` array — the request is never aborted entirely
- The middleware is configured once at application startup; individual resolvers do not need to
  handle decryption explicitly

### Security Standards Alignment

| Standard                                    | Alignment                                                                              |
| ------------------------------------------- | -------------------------------------------------------------------------------------- |
| **OWASP Top 10**                            | Addresses A02 (Cryptographic Failures), A03 (Injection), A07 (Authentication Failures) |
| **OWASP Cryptographic Storage Cheat Sheet** | AES-256-GCM with random nonce per operation; no ECB mode; authenticated encryption     |
| **NIST SP 800-132**                         | Argon2id with memory ≥ 64 MB and ≥ 3 iterations for password-based key derivation      |
| **NCSC Guidance**                           | Encryption at rest; key management separation; no hardcoded secrets                    |
| **GDPR Article 32**                         | Appropriate technical measures; encryption of personal data at rest                    |

---

## Technology Stack

> All versions listed are the **latest stable releases** as of March 2026. This repository targets
> the current stable release of every language and framework and is updated when new stable versions
> are available.

### Backend

| Component       | Technology                 | Version                       |
| --------------- | -------------------------- | ----------------------------- |
| Framework       | Django                     | 6.0.4                         |
| Language        | Python                     | 3.14.3                        |
| API Layer       | Strawberry GraphQL         | 0.307.1 (September 2025 spec) |
| Database        | PostgreSQL                 | 18.3                          |
| Cache / Broker  | Redis                      | latest stable                 |
| Task Queue      | Celery                     | latest stable                 |
| Package Manager | uv                         | latest stable                 |
| Search          | Elasticsearch / OpenSearch | 8.x / 2.x                     |

### Frontend Web

| Component        | Technology                  | Version       |
| ---------------- | --------------------------- | ------------- |
| Framework        | Next.js                     | 16.1.6        |
| UI Library       | React                       | 19.2          |
| Language         | TypeScript                  | 5.9           |
| Styling          | Tailwind CSS                | 4.2           |
| Runtime          | Node.js                     | 24.14.0       |
| Package Manager  | npm                         | 11.11.0       |
| Monorepo Manager | pnpm                        | latest stable |
| GraphQL Client   | graphql-codegen (generated) | latest stable |
| Form Validation  | Zod                         | latest stable |
| Data Fetching    | React Query                 | latest stable |

### Frontend Mobile

| Component          | Technology                           | Version       |
| ------------------ | ------------------------------------ | ------------- |
| Framework          | React Native (Expo managed workflow) | 0.84.x        |
| Language           | TypeScript                           | 5.9           |
| Styling            | NativeWind                           | 4             |
| Animations         | react-native-reanimated              | latest stable |
| Local Storage      | expo-sqlite                          | latest stable |
| Push Notifications | expo-notifications                   | latest stable |
| Package Manager    | pnpm                                 | latest stable |

### Rust

| Component          | Technology               |
| ------------------ | ------------------------ |
| Language           | Rust (stable channel)    |
| Encryption         | `aes-gcm` crate          |
| Password Hashing   | `argon2` crate           |
| HMAC               | `hmac` + `sha2` crates   |
| Memory Zeroisation | `zeroize` crate          |
| Randomness         | `rand_core` with `OsRng` |
| Python Bindings    | `pyo3` crate             |

### Infrastructure and Distribution

| Component                      | Technology                                                     |
| ------------------------------ | -------------------------------------------------------------- |
| Package Registry               | Forgejo (self-hosted, Syntek Hetzner server)                   |
| Versioning                     | Semantic versioning per module                                 |
| Changelogs                     | Per-module `CHANGELOG.md`                                      |
| CI/CD                          | Forgejo Actions                                                |
| Code Quality                   | Ruff, mypy (Python); ESLint, tsc (TypeScript); clippy (Rust)   |
| Media (images, video)          | Cloudinary — metadata in PostgreSQL, assets via Cloudinary CDN |
| Documents (PDFs, office files) | MinIO — presigned URLs; not used for images or static assets   |
| Static files / asset pipeline  | Next.js `.next` output — caching, bundling, and minification   |

---

## Configuration

Every module in this repository is controlled entirely through `SYNTEK_*` settings dictionaries in
the consuming project's `settings.py`. Nothing is hardcoded in any module. Frontends fetch all
runtime configuration from Django via GraphQL — there are no configuration values embedded in
frontend bundles.

### Example Django Settings

```python
# syntek-auth
SYNTEK_AUTH = {
    'MFA_REQUIRED': True,
    'PASSWORD_MIN_LENGTH': 14,
    'SESSION_TIMEOUT': 1800,              # seconds
    'ARGON2ID_TIME_COST': 3,
    'ARGON2ID_MEMORY_COST': 65536,        # kilobytes (64 MB)
    'ARGON2ID_PARALLELISM': 4,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 900,              # seconds
}

# syntek-tenancy
SYNTEK_TENANCY = {
    'ISOLATION': 'schema',               # 'schema' or 'row'
    'DOMAIN_STRATEGY': 'subdomain',      # 'subdomain' or 'custom'
    'SUBDOMAIN_BASE': 'yourdomain.com',
}

# syntek-security
SYNTEK_SECURITY = {
    'RATE_LIMIT_BACKEND': 'redis',
    'DEFAULT_RATE': '100/hour',
    'IP_BLOCKLIST': [],
    'HSTS_MAX_AGE': 31536000,
    'CSP_REPORT_ONLY': False,
}

# syntek-notifications
SYNTEK_NOTIFICATIONS = {
    'EMAIL_BACKEND': 'ses',              # 'smtp' or 'ses'
    'SMS_BACKEND': 'twilio',             # 'twilio' or 'sns'
    'PUSH_FCM_SERVER_KEY': env('FCM_SERVER_KEY'),
    'PUSH_APNS_CERT': env('APNS_CERT_PATH'),
    'RETRY_MAX_ATTEMPTS': 5,
}

# syntek-payments
SYNTEK_PAYMENTS = {
    'STRIPE_SECRET_KEY': env('STRIPE_SECRET_KEY'),
    'STRIPE_WEBHOOK_SECRET': env('STRIPE_WEBHOOK_SECRET'),
    'CURRENCY': 'gbp',
    'PAYMENT_METHODS': ['card', 'bacs_debit'],
}

# syntek-search
SYNTEK_SEARCH = {
    'BACKEND': 'elasticsearch',          # 'elasticsearch' or 'opensearch'
    'URL': env('ELASTICSEARCH_URL'),
    'INDEX_PREFIX': 'myproject',
    'AUTOCOMPLETE_ENABLED': True,
}

# syntek-tasks
SYNTEK_TASKS = {
    'BROKER_URL': env('REDIS_URL'),
    'PRIORITY_QUEUES': ['critical', 'high', 'default', 'low'],
    'DEFAULT_RETRY_DELAY': 60,           # seconds
    'MAX_RETRIES': 10,
}
```

### Configuration Principles

- Every setting has a documented default; no `KeyError` if a setting is omitted
- Secrets (API keys, tokens, certificates) must be provided via environment variables and referenced
  with `env()`; the module validates at startup that required secrets are present
- Settings are validated at Django startup using `AppConfig.ready()`; misconfiguration raises a
  descriptive `ImproperlyConfigured` exception before any request is served
- Frontend modules receive their configuration exclusively via GraphQL queries to the backend; there
  are no `.env` variables for feature behaviour in frontend packages

---

## Development Workflow

### For Module Contributors

Contributors working on the modules themselves should follow this workflow.

#### Repository Setup

```bash
git clone https://git.syntek-studio.com/syntek/syntek-modules.git
cd syntek-modules
```

#### Backend Module Development

```bash
# Create and activate a virtual environment
uv venv && source .venv/bin/activate

# Install the module under development in editable mode with dev dependencies
uv pip install -e "packages/backend/syntek-auth[dev]"

# Run the module's test suite
pytest packages/backend/syntek-auth/tests/ -v

# Run linting and type checking
ruff check packages/backend/syntek-auth/
mypy packages/backend/syntek-auth/
```

#### Frontend Package Development

```bash
# Install all workspace dependencies
pnpm install

# Run tests for a specific package
pnpm --filter @syntek/ui-auth test

# Build a package
pnpm --filter @syntek/ui-auth build

# Run the development storybook for component development
pnpm --filter @syntek/ui storybook
```

#### Rust Crate Development

```bash
# Run tests
cargo test -p syntek-crypto

# Run clippy linter
cargo clippy -p syntek-crypto -- -D warnings

# Build the PyO3 extension for local testing
cd crates/syntek-pyo3 && maturin develop
```

#### Branching Strategy

Branches follow the same pattern as the wider Syntek ecosystem:

```text
feature/<module-name>/<description>  →  dev  →  staging  →  main
```

- Feature branches are created from `dev`
- Pull requests target `dev`; automated tests must pass before merge
- `dev` → `staging` merge triggers integration tests
- `staging` → `main` merge triggers a release; version tags are applied per affected module

### For Consuming Projects

Projects consuming `syntek-modules` packages follow a different workflow — they install packages as
dependencies and configure them through settings.

#### Adding a New Module to an Existing Project

```bash
# 1. Install the package
syntek add syntek-auth

# 2. Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    ...
    'syntek_auth',
]

# 3. Add the configuration block to settings.py
SYNTEK_AUTH = {
    'MFA_REQUIRED': True,
    'PASSWORD_MIN_LENGTH': 14,
    'SESSION_TIMEOUT': 1800,
}

# 4. Run migrations
python manage.py migrate

# 5. Include the module's URL patterns
# urls.py
urlpatterns += path('auth/', include('syntek_auth.urls'))
```

#### Updating a Module

```bash
# Pin to a specific version in pyproject.toml / package.json
uv pip install "syntek-auth==2.3.1"

# Or update to latest compatible version
uv pip install --upgrade syntek-auth

# Always review the module's CHANGELOG.md before upgrading
# Located at: packages/backend/syntek-auth/CHANGELOG.md
```

### Versioning and Releases

All modules are versioned independently using **semantic versioning** (`MAJOR.MINOR.PATCH`).

- `MAJOR`: Breaking changes to the public API or settings schema
- `MINOR`: New features, new settings keys (all backwards-compatible)
- `PATCH`: Bug fixes, security patches, dependency updates

Version tags follow the pattern `<module-name>/v<version>`, e.g., `syntek-auth/v2.3.1`.

Every release is accompanied by an entry in the module's `CHANGELOG.md` documenting:

- What changed and why
- Any migration steps required
- Security advisories (if applicable)

Releases are managed through Forgejo on the Syntek Hetzner server. Release artefacts are published
to the Forgejo package registry.

### Quality Assurance

Every pull request to any module must pass the following checks before merge:

- **Unit Tests**: `pytest` (Python) / `jest` (TypeScript) / `cargo test` (Rust); minimum 80% line
  coverage enforced
- **Integration Tests**: Each module includes integration tests against a real PostgreSQL and Redis
  instance (provisioned in CI via Docker)
- **Type Checking**: `mypy --strict` (Python); `tsc --noEmit` (TypeScript); `clippy -D warnings`
  (Rust)
- **Linting**: `ruff check` (Python); `eslint` (TypeScript); `cargo fmt --check` (Rust)
- **Security Scanning**: `pip-audit` for Python dependency vulnerabilities; `npm audit` for
  JavaScript; `cargo audit` for Rust
- **Dependency Licence Check**: All new dependencies vetted for GPL / copyleft licence compatibility

---

## Getting Started

### Backend Developers

Install individual modules as needed and configure them through Django settings.

```bash
# Install one or more modules
syntek add syntek-auth syntek-permissions syntek-payments

# Add to INSTALLED_APPS
# settings.py
INSTALLED_APPS = [
    ...
    'syntek_auth',
    'syntek_permissions',
    'syntek_payments',
]

# Add configuration blocks
SYNTEK_AUTH = {
    'MFA_REQUIRED': True,
    'PASSWORD_MIN_LENGTH': 14,
    'SESSION_TIMEOUT': 1800,
}

SYNTEK_PAYMENTS = {
    'STRIPE_SECRET_KEY': env('STRIPE_SECRET_KEY'),
    'STRIPE_WEBHOOK_SECRET': env('STRIPE_WEBHOOK_SECRET'),
    'CURRENCY': 'gbp',
}

# Run migrations
python manage.py migrate

# Include URL patterns
# urls.py
from django.urls import include, path

urlpatterns = [
    path('auth/', include('syntek_auth.urls')),
    path('payments/', include('syntek_payments.urls')),
]
```

All available modules, their settings schemas, and migration notes are documented in the per-module
`CHANGELOG.md` files within each package directory.

### Frontend Web Developers

```bash
# Install the core packages
syntek add @syntek/ui @syntek/api-client @syntek/data-hooks

# Install feature-specific packages as needed
syntek add @syntek/ui-auth @syntek/session
syntek add @syntek/ui-payments @syntek/ui-notifications
syntek add @syntek/data-table @syntek/ui-search
syntek add @syntek/layout @syntek/forms

# Configure the API client (typically in lib/api.ts)
import { createClient } from '@syntek/api-client'

export const api = createClient({
    endpoint: process.env.NEXT_PUBLIC_GRAPHQL_URL,
})

# Wrap the application with required providers (typically in app/layout.tsx)
import { SessionProvider } from '@syntek/session'
import { ApiClientProvider } from '@syntek/api-client'

export default function RootLayout({ children }) {
    return (
        <ApiClientProvider client={api}>
            <SessionProvider>
                {children}
            </SessionProvider>
        </ApiClientProvider>
    )
}
```

### Mobile Developers

```bash
# Install the core mobile packages
syntek add @syntek/mobile-auth @syntek/mobile-ui

# Install feature-specific packages as needed
syntek add @syntek/mobile-notifications @syntek/mobile-payments
syntek add @syntek/mobile-sync

# iOS — ensure native dependencies are linked
cd ios && pod install

# Configure notifications (requires expo-notifications setup)
# See packages/mobile/syntek-mobile-notifications/README.md
# for platform-specific APNs and FCM configuration steps
```

### Rust and Cryptography

Add the required crates to your project's `Cargo.toml`:

```toml
[dependencies]
syntek-crypto = { git = "https://git.syntek-studio.com/syntek/syntek-modules", tag = "syntek-crypto/v1.2.0" }
syntek-pyo3   = { git = "https://git.syntek-studio.com/syntek/syntek-modules", tag = "syntek-pyo3/v1.2.0" }
```

For the PyO3 bindings (required for Django integration):

```bash
# Install maturin for building the Python extension
pip install maturin

# Build and install the extension into the active virtual environment
cd crates/syntek-pyo3 && maturin develop --release

# Verify the extension is importable
python -c "from syntek_pyo3 import encrypt_field; print('OK')"
```

---

## Security Compliance

All modules in this repository are designed, implemented, and tested against the following security
standards and frameworks.

| Standard                                    | Scope                                                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **OWASP Top 10 (2021)**                     | All modules; particularly A02 Cryptographic Failures, A03 Injection, A05 Security Misconfiguration, A07 Authentication Failures |
| **OWASP Cryptographic Storage Cheat Sheet** | Rust encryption layer; AES-256-GCM with random nonce; no deprecated algorithms                                                  |
| **OWASP Authentication Cheat Sheet**        | `syntek-auth`; Argon2id hashing, account lockout, brute-force protection                                                        |
| **NIST SP 800-132**                         | Password-based key derivation using Argon2id with NIST-compliant parameters                                                     |
| **NIST SP 800-38D**                         | AES-GCM authenticated encryption implementation                                                                                 |
| **NCSC Guidance**                           | Encryption at rest, key management, secure defaults                                                                             |
| **GDPR Article 32**                         | Encryption of personal data at rest; pseudonymisation support; data minimisation in audit logs                                  |
| **UK Data Protection Act 2018**             | Aligned with GDPR obligations under UK DPA                                                                                      |
| **CIS Benchmarks**                          | Security middleware defaults (`syntek-security`) aligned with CIS hardening recommendations                                     |

### Security Reporting

Security vulnerabilities in any module must be reported responsibly to
**<security@syntek-studio.com>**. Do not open public issues for security vulnerabilities.

The security team will acknowledge reports within 48 hours and aim to release a patched version
within 14 days for critical issues.

---

## Contact

### Forgejo — Source and Packages

All code, issues, pull requests, and package releases are hosted on the Syntek self-hosted Forgejo
instance.

**Forgejo Server**: [https://git.syntek-studio.com](https://git.syntek-studio.com)

### Email Contacts

| Purpose                                   | Address                      |
| ----------------------------------------- | ---------------------------- |
| Security vulnerability reports            | <security@syntek-studio.com> |
| Technical support and integration queries | <support@syntek-studio.com>  |

### Status

**Status Page**: [https://status.syntek-studio.com](https://status.syntek-studio.com)

---

**Maintained by:** Syntek Development Team **Language:** British English (en-GB) **Versioning:**
Semantic versioning per module — Forgejo, Syntek Hetzner Server **Last Updated:** 06.03.2026
