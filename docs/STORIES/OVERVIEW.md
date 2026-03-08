# Syntek Modules — Stories Overview

**Last Updated**: 08/03/2026 **Version**: 0.1.0 **Maintained By**: Syntek Development Team
**Language**: British English (en_GB) **Timezone**: Europe/London

---

## Table of Contents

- [Design Token Architecture Decision](#design-token-architecture-decision)
- [TDD/BDD Workflow](#tddbdd-workflow)
- [Story Index](#story-index)
  - [Epic 1 — Foundation & Workspace](#epic-1--foundation--workspace)
  - [Epic 2 — Rust Encryption Layer](#epic-2--rust-encryption-layer)
  - [Epic 3 — Core Backend Modules](#epic-3--core-backend-modules)
  - [Epic 4 — Backend Feature Modules](#epic-4--backend-feature-modules)
  - [Epic 5 — Backend Compliance & Media](#epic-5--backend-compliance--media)
  - [Epic 6 — Web Frontend Core](#epic-6--web-frontend-core)
  - [Epic 7 — Web Frontend Features](#epic-7--web-frontend-features)
  - [Epic 8 — Mobile Packages](#epic-8--mobile-packages)
- [Points Summary](#points-summary)
- [Build Order](#build-order)

---

## Design Token Architecture Decision

Token **definitions** (defaults) live in `shared/tokens/` within `syntek-modules` as CSS custom
properties and TypeScript constants. These are the canonical defaults shipped with every module.

Token **overrides** (per-tenant customisation) live in `syntek-platform`'s database via the
`syntek-settings` module (`TenantDesignToken` model), served via GraphQL at runtime and applied at
`:root` level by the frontend.

Rules:

- `shared/tokens/tokens.css` — all CSS custom property declarations with default values
- `shared/tokens/tokens.ts` — TypeScript constants mirroring CSS custom properties
- All UI packages import tokens; **never** hardcode colour, spacing, or type values (ESLint
  enforced)
- `syntek-platform` writes overrides to `TenantDesignToken` (US016); the frontend applies them at
  `:root`

---

## TDD/BDD Workflow

Every story follows **Red → Green → Refactor** as defined in `.claude/TESTING.md`:

1. **Red** — write all failing tests (unit, integration, security negatives) before any
   implementation
2. **Green** — write the minimum code to pass all tests
3. **Refactor** — clean up without breaking any test

A story is only complete when:

- All unit tests pass
- All integration tests pass
- Security-critical negative tests pass (IDOR, injection, privilege escalation, auth bypass)
- Linting and type checking are clean (`ruff`/`mypy` for Python; `eslint`/`tsc` for TypeScript;
  `clippy`/`rustfmt` for Rust)

---

## Story Index

### Epic 1 — Foundation & Workspace

| Story             | Title                                                           | Points | Status       |
| ----------------- | --------------------------------------------------------------- | ------ | ------------ |
| [US001](US001.md) | Monorepo Workspace Configuration                                | 5      | ✅ Completed |
| [US002](US002.md) | Shared TypeScript Types Package                                 | 3      | ✅ Completed |
| [US003](US003.md) | Design Token System                                             | 5      | ✅ Completed |
| [US004](US004.md) | Shared GraphQL Operations Package                               | 3      | ✅ Completed |
| [US005](US005.md) | CI/CD Pipeline (Forgejo Actions)                                | 5      | Completed    |
| [US074](US074.md) | `syntek-manifest` — Module Manifest Spec & CLI Shared Framework | 5      | To Do        |

### Epic 2 — Rust Encryption Layer

| Story             | Title                                                   | Points | Status |
| ----------------- | ------------------------------------------------------- | ------ | ------ |
| [US006](US006.md) | `syntek-crypto` — Core Cryptographic Primitives         | 8      | To Do  |
| [US007](US007.md) | `syntek-pyo3` — PyO3 Django Bindings                    | 8      | To Do  |
| [US008](US008.md) | `syntek-graphql-crypto` — GraphQL Encryption Middleware | 8      | To Do  |

### Epic 3 — Core Backend Modules

| Story             | Title                                                   | Points | Status |
| ----------------- | ------------------------------------------------------- | ------ | ------ |
| [US009](US009.md) | `syntek-auth` — Authentication Module                   | 13     | To Do  |
| [US010](US010.md) | `syntek-tenancy` — Multi-Tenancy Module                 | 13     | To Do  |
| [US011](US011.md) | `syntek-permissions` — RBAC Module                      | 8      | To Do  |
| [US012](US012.md) | `syntek-security` — Security Middleware Module          | 5      | To Do  |
| [US013](US013.md) | `syntek-audit` — Immutable Audit Logging                | 8      | To Do  |
| [US014](US014.md) | `syntek-logging` — Structured Logging Module            | 5      | To Do  |
| [US015](US015.md) | `syntek-tasks` — Background Task Queue                  | 5      | To Do  |
| [US016](US016.md) | `syntek-settings` — Per-Tenant Settings & Design Tokens | 5      | To Do  |
| [US017](US017.md) | `syntek-flags` — Feature Flags Module                   | 5      | To Do  |
| [US018](US018.md) | `syntek-groups` — Groups & Organisational Hierarchy     | 5      | To Do  |

### Epic 4 — Backend Feature Modules

| Story             | Title                                                | Points | Status |
| ----------------- | ---------------------------------------------------- | ------ | ------ |
| [US019](US019.md) | `syntek-notifications` — Multi-Channel Notifications | 8      | To Do  |
| [US020](US020.md) | `syntek-webhooks` — Inbound & Outbound Webhooks      | 8      | To Do  |
| [US021](US021.md) | `syntek-bulk` — Bulk Import/Export                   | 8      | To Do  |
| [US022](US022.md) | `syntek-search` — Full-Text Search                   | 8      | To Do  |
| [US023](US023.md) | `syntek-forms` — Dynamic Forms                       | 8      | To Do  |
| [US024](US024.md) | `syntek-events` — Events & Ticketing                 | 8      | To Do  |
| [US025](US025.md) | `syntek-payments` — Stripe Payment Processing        | 13     | To Do  |
| [US026](US026.md) | `syntek-invoicing` — Invoicing & UK VAT              | 8      | To Do  |
| [US027](US027.md) | `syntek-donations` — Donation Management             | 8      | To Do  |
| [US028](US028.md) | `syntek-reporting` — Reporting & Exports             | 8      | To Do  |

### Epic 5 — Backend Compliance & Media

| Story             | Title                                                       | Points | Status |
| ----------------- | ----------------------------------------------------------- | ------ | ------ |
| [US029](US029.md) | `syntek-gdpr` — GDPR Compliance Module                      | 8      | To Do  |
| [US030](US030.md) | `syntek-media` — Cloudinary Media Module                    | 5      | To Do  |
| [US031](US031.md) | `syntek-documents` — MinIO Document Storage                 | 5      | To Do  |
| [US032](US032.md) | `syntek-membership` — Membership & Tiers                    | 5      | To Do  |
| [US033](US033.md) | `syntek-integrations` — Third-Party Integrations            | 5      | To Do  |
| [US034](US034.md) | `syntek-i18n` — Internationalisation                        | 3      | To Do  |
| [US035](US035.md) | `syntek-caldav` — CalDav Integration                        | 3      | To Do  |
| [US036](US036.md) | `syntek-geo` — Address & Geo Module                         | 3      | To Do  |
| [US037](US037.md) | `syntek-accounting` — Accounting & Ledger                   | 8      | To Do  |
| [US038](US038.md) | `syntek-email-marketing` — Email Marketing                  | 5      | To Do  |
| [US039](US039.md) | `syntek-api-keys` — Developer API Keys                      | 3      | To Do  |
| [US040](US040.md) | `syntek-comments` — Threaded Comments                       | 3      | To Do  |
| [US041](US041.md) | `syntek-loyalty` — Loyalty & Referrals                      | 5      | To Do  |
| [US062](US062.md) | `syntek-subscriptions` — Recurring Subscription Lifecycle   | 5      | To Do  |
| [US063](US063.md) | `syntek-analytics` — Privacy-First Analytics                | 3      | To Do  |
| [US064](US064.md) | `syntek-scheduling` — Appointment & Availability Scheduling | 8      | To Do  |
| [US065](US065.md) | `syntek-locations` — Location Model & Geospatial Queries    | 3      | To Do  |
| [US066](US066.md) | `syntek-inventory` — Inventory & Stock Management           | 5      | To Do  |
| [US067](US067.md) | `syntek-feedback` — Surveys & Feedback                      | 5      | To Do  |

### Epic 6 — Web Frontend Core

| Story             | Title                                           | Points | Status |
| ----------------- | ----------------------------------------------- | ------ | ------ |
| [US042](US042.md) | `@syntek/ui` — Design System Component Library  | 21     | To Do  |
| [US043](US043.md) | `@syntek/session` — Session Management          | 5      | To Do  |
| [US044](US044.md) | `@syntek/api-client` — Generated GraphQL Client | 5      | To Do  |
| [US045](US045.md) | `@syntek/data-hooks` — Data Fetching Hooks      | 3      | To Do  |
| [US046](US046.md) | `@syntek/forms` — Headless Form Primitives      | 5      | To Do  |
| [US047](US047.md) | `@syntek/layout` — Shell Layout Package         | 5      | To Do  |

### Epic 7 — Web Frontend Features

| Story             | Title                                                  | Points | Status |
| ----------------- | ------------------------------------------------------ | ------ | ------ |
| [US048](US048.md) | `@syntek/ui-auth` — Authentication UI                  | 8      | To Do  |
| [US049](US049.md) | `@syntek/ui-gdpr` — Cookie Consent & Privacy UI        | 5      | To Do  |
| [US050](US050.md) | `@syntek/data-table` — Sortable Paginated Table        | 5      | To Do  |
| [US051](US051.md) | `@syntek/ui-notifications` — Notification Feed UI      | 5      | To Do  |
| [US052](US052.md) | `@syntek/ui-payments` — Stripe Checkout UI             | 5      | To Do  |
| [US053](US053.md) | `@syntek/ui-search` — Search Bar & Facets UI           | 5      | To Do  |
| [US054](US054.md) | `@syntek/ui-reporting` — Charts & Report Builder UI    | 5      | To Do  |
| [US055](US055.md) | `@syntek/ui-settings` — Settings Page Scaffold         | 5      | To Do  |
| [US056](US056.md) | `@syntek/ui-onboarding` — Multi-Step Onboarding Wizard | 5      | To Do  |
| [US068](US068.md) | `@syntek/ui-donations` — Donations UI                  | 5      | To Do  |
| [US069](US069.md) | `@syntek/ui-comments` — Comments UI                    | 3      | To Do  |
| [US070](US070.md) | `@syntek/ui-feedback` — Feedback & Surveys UI          | 3      | To Do  |
| [US071](US071.md) | `@syntek/ui-maps` — Maps & Location Picker UI          | 5      | To Do  |
| [US072](US072.md) | `@syntek/ui-scheduling` — Scheduling & Calendar UI     | 5      | To Do  |

### Epic 8 — Mobile Packages

| Story             | Title                                                  | Points | Status |
| ----------------- | ------------------------------------------------------ | ------ | ------ |
| [US057](US057.md) | `@syntek/mobile-ui` — NativeWind Mobile Design System  | 13     | To Do  |
| [US058](US058.md) | `@syntek/mobile-auth` — Mobile Authentication          | 8      | To Do  |
| [US059](US059.md) | `@syntek/mobile-notifications` — Push Notifications    | 5      | To Do  |
| [US060](US060.md) | `@syntek/mobile-payments` — Apple Pay & Google Pay     | 5      | To Do  |
| [US061](US061.md) | `@syntek/mobile-sync` — Offline SQLite Sync            | 5      | To Do  |
| [US073](US073.md) | `@syntek/mobile-media` — Mobile Media Capture & Upload | 3      | To Do  |

---

## Points Summary

| Epic                                | Stories | Points  |
| ----------------------------------- | ------- | ------- |
| Epic 1 — Foundation & Workspace     | 6       | 26      |
| Epic 2 — Rust Encryption Layer      | 3       | 24      |
| Epic 3 — Core Backend Modules       | 10      | 72      |
| Epic 4 — Backend Feature Modules    | 10      | 87      |
| Epic 5 — Backend Compliance & Media | 19      | 90      |
| Epic 6 — Web Frontend Core          | 6       | 44      |
| Epic 7 — Web Frontend Features      | 14      | 64      |
| Epic 8 — Mobile Packages            | 6       | 39      |
| **Total**                           | **74**  | **446** |

---

## Build Order

```text
Phase 1 — Foundation (US001–US005, US074)
  US001 → US002 | US003 | US004 | US005 | US074

Phase 2 — Rust Layer (US006–US008, strict order)
  US006 → US007 → US008

Phase 3 — Core Backend (strict order, each depends on previous)
  US009 → US010 → US011 → US012 → US013 → US014 → US015 → US016 → US017 → US018

Phase 4 — Backend Features (parallelise after Phase 3)
  US019 | US020 | US022 | US030 | US031
  → US021 | US023 | US025
  → US024 | US026 | US027 | US028
  → US029 | US032 | US033 | US062
  → US034–US041 | US063 | US065 | US066 | US067
  → US064 (needs US033, US019, US015)

Phase 5 — Web Frontend Core (US003 + US009 required)
  US042 → US043 → US044 → US045 | US046 | US047

Phase 6 — Web Frontend Features (after Phase 5 + relevant backend)
  US048 | US049 | US050
  → US051 | US052 | US053 | US054 | US055 | US056
  → US068 | US069 | US070 | US071 | US072

Phase 7 — Mobile (after US003, US009, US057)
  US057 → US058 → US059 | US060 | US061 | US073
```
