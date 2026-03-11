# Syntek Modules — Stories Overview

**Last Updated**: 11/03/2026 **Version**: 0.15.0 **Maintained By**: Syntek Development Team
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

Every story follows **Red → Green → Refactor** as defined in [Testing Guide](.claude/TESTING.md):

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

| Story             | Title                                                                  | Points | Status    |
| ----------------- | ---------------------------------------------------------------------- | ------ | --------- |
| [US006](US006.md) | `syntek-crypto` — Core Cryptographic Primitives                        | 8      | Completed |
| [US007](US007.md) | `syntek-pyo3` — PyO3 Django Bindings                                   | 8      | Completed |
| [US008](US008.md) | `syntek-graphql-crypto` — GraphQL Encryption Middleware                | 13     | Completed |
| [US076](US076.md) | Security Policy: MFA-Enforcing SSO, Key Rotation, Network Architecture | 10     | Completed |

### Epic 3 — Core Backend Modules

| Story             | Title                                                     | Points | Status |
| ----------------- | --------------------------------------------------------- | ------ | ------ |
| [US009](US009.md) | `syntek-auth` — Authentication Module                     | 13     | To Do  |
| [US010](US010.md) | `syntek-tenancy` — Multi-Tenancy Module                   | 13     | To Do  |
| [US011](US011.md) | `syntek-permissions` — RBAC Module                        | 8      | To Do  |
| [US012](US012.md) | `syntek-security` — Security Middleware Module            | 5      | To Do  |
| [US080](US080.md) | `syntek-security-validator` — Input Validation & XSS      | 8      | To Do  |
| [US081](US081.md) | `syntek-security-secrets` — Secrets Management            | 8      | To Do  |
| [US013](US013.md) | `syntek-audit` — Immutable Audit Logging                  | 8      | To Do  |
| [US014](US014.md) | `syntek-logging` — Structured Logging Module              | 5      | To Do  |
| [US015](US015.md) | `syntek-tasks` — Background Task Queue                    | 13     | To Do  |
| [US016](US016.md) | `syntek-settings` — Per-Tenant Settings & Design Tokens   | 8      | To Do  |
| [US017](US017.md) | `syntek-flags` — Feature Flags Module                     | 8      | To Do  |
| [US018](US018.md) | `syntek-groups` — Groups & Organisational Hierarchy       | 8      | To Do  |
| [US077](US077.md) | `syntek-cache` — Redis/Valkey Caching Module              | 5      | To Do  |
| [US086](US086.md) | `syntek-users` — User Domain Profiles                     | 13     | To Do  |
| [US118](US118.md) | `syntek-timescaledb` — TimescaleDB Hypertable Integration | 5      | To Do  |
| [US127](US127.md) | `syntek-ai` — AI Conversation Backend                     | 8      | To Do  |
| [US124](US124.md) | `syntek-error` — Error Handling & Custom Error Pages      | 5      | To Do  |

### Epic 4 — Backend Feature Modules

| Story             | Title                                                      | Points | Status |
| ----------------- | ---------------------------------------------------------- | ------ | ------ |
| [US112](US112.md) | `syntek-email-core` — Email Engine & Template Management   | 13     | To Do  |
| [US019](US019.md) | `syntek-notifications-core` — Core Notification Engine     | 8      | To Do  |
| [US087](US087.md) | `syntek-notifications-email` — Email Notification Channel  | 5      | To Do  |
| [US088](US088.md) | `syntek-notifications-sms` — SMS Notification Channel      | 5      | To Do  |
| [US089](US089.md) | `syntek-notifications-push` — Push Notification Channel    | 5      | To Do  |
| [US020](US020.md) | `syntek-webhooks` — Inbound & Outbound Webhooks            | 8      | To Do  |
| [US090](US090.md) | `syntek-bus` — Internal Domain Event Bus                   | 5      | To Do  |
| [US021](US021.md) | `syntek-bulk-import` — Bulk Import                         | 8      | To Do  |
| [US093](US093.md) | `syntek-bulk-export` — Bulk Export                         | 8      | To Do  |
| [US022](US022.md) | `syntek-search-core` — Site Search                         | 13     | To Do  |
| [US023](US023.md) | `syntek-forms-core` — Dynamic Form Engine                  | 13     | To Do  |
| [US024](US024.md) | `syntek-events` — Events & Ticketing                       | 8      | To Do  |
| [US025](US025.md) | `syntek-payments-core` — Multi-Provider Payment Core       | 13     | To Do  |
| [US095](US095.md) | `syntek-payments-stripe` — Stripe Adapter                  | 8      | To Do  |
| [US096](US096.md) | `syntek-payments-square` — Square Adapter                  | 5      | To Do  |
| [US097](US097.md) | `syntek-payments-paypal` — PayPal Adapter                  | 5      | To Do  |
| [US098](US098.md) | `syntek-payments-sumup` — SumUp Adapter                    | 5      | To Do  |
| [US099](US099.md) | `syntek-discount-codes` — Discount Codes & Vouchers        | 5      | To Do  |
| [US100](US100.md) | `syntek-payment-links` — Shareable Payment Links           | 5      | To Do  |
| [US026](US026.md) | `syntek-invoicing` — Invoicing, PDF Generation & UK VAT    | 13     | To Do  |
| [US027](US027.md) | `syntek-donations` — Multi-Provider Donation Management    | 13     | To Do  |
| [US028](US028.md) | `syntek-reporting-core` — Report Definition & Query Engine | 13     | To Do  |
| [US101](US101.md) | `syntek-reporting-export` — Report Export & Delivery       | 8      | To Do  |
| [US121](US121.md) | `syntek-messaging` — Real-Time Messaging & Live Chat       | 13     | To Do  |

### Epic 5 — Backend Compliance & Media

| Story             | Title                                                                        | Points | Status |
| ----------------- | ---------------------------------------------------------------------------- | ------ | ------ |
| [US029](US029.md) | `syntek-gdpr` — Multi-Regime Data Protection Module                          | 13     | To Do  |
| [US104](US104.md) | `syntek-consent` — Granular Consent Management                               | 8      | To Do  |
| [US030](US030.md) | `syntek-media-core` — Cloudinary Media Management                            | 13     | To Do  |
| [US106](US106.md) | `syntek-media-upload` — Chunked Upload Pipeline & Virus Scanning             | 8      | To Do  |
| [US031](US031.md) | `syntek-files` — MinIO File Storage & Document Management                    | 13     | To Do  |
| [US032](US032.md) | `syntek-membership` — Membership & Tiers                                     | 5      | To Do  |
| [US033](US033.md) | `syntek-integrations-core` — Pluggable Integration Framework                 | 8      | To Do  |
| [US108](US108.md) | `syntek-integrations-automation` — Automation Platform Bridge (n8n / Zapier) | 5      | To Do  |
| [US109](US109.md) | `syntek-integrations-accounting` — Accounting Service Connectors             | 8      | To Do  |
| [US034](US034.md) | `syntek-i18n` — Internationalisation                                         | 3      | To Do  |
| [US035](US035.md) | `syntek-caldav` — CalDav & CardDav Client                                    | 5      | To Do  |
| [US036](US036.md) | `syntek-geo` — Address & Geo Module                                          | 3      | To Do  |
| [US037](US037.md) | `syntek-accounting` — Accounting & Ledger                                    | 8      | To Do  |
| [US038](US038.md) | `syntek-email-marketing` — Email Marketing & Campaign Analytics              | 13     | To Do  |
| [US039](US039.md) | `syntek-api-keys` — Developer API Keys                                       | 3      | To Do  |
| [US040](US040.md) | `syntek-comments` — Comments, Reviews & Discussions                          | 8      | To Do  |
| [US041](US041.md) | `syntek-loyalty` — Loyalty & Referrals                                       | 5      | To Do  |
| [US062](US062.md) | `syntek-subscriptions` — Multi-Provider Subscription Lifecycle               | 8      | To Do  |
| [US063](US063.md) | `syntek-analytics` — Privacy-First Analytics                                 | 5      | To Do  |
| [US064](US064.md) | `syntek-scheduling-core` — Appointment & Booking Engine                      | 13     | To Do  |
| [US110](US110.md) | `syntek-scheduling-calendar` — Calendar Export & Sync Adapters               | 5      | To Do  |
| [US065](US065.md) | `syntek-locations-core` — Geospatial Location Platform                       | 8      | To Do  |
| [US115](US115.md) | `syntek-routing` — Multi-Stop Route Optimisation                             | 8      | To Do  |
| [US116](US116.md) | `syntek-tracking` — Live Location Tracking                                   | 13     | To Do  |
| [US066](US066.md) | `syntek-inventory` — Inventory & Stock Management                            | 8      | To Do  |
| [US067](US067.md) | `syntek-feedback` — Surveys, Feedback & Ratings                              | 8      | To Do  |
| [US091](US091.md) | `syntek-legal` — Legal Document Management                                   | 8      | To Do  |

### Epic 6 — Web Frontend Core

| Story             | Title                                                 | Points | Status |
| ----------------- | ----------------------------------------------------- | ------ | ------ |
| [US042](US042.md) | `@syntek/ui` — Design System Component Library        | 21     | To Do  |
| [US043](US043.md) | `@syntek/session` — Session Management                | 5      | To Do  |
| [US044](US044.md) | `@syntek/api-client` — GraphQL API Client             | 8      | To Do  |
| [US125](US125.md) | `@syntek/ui-error` — Web Error Pages & Error Boundary | 5      | To Do  |
| [US045](US045.md) | `@syntek/data-hooks` — Data Fetching Hooks            | 3      | To Do  |
| [US046](US046.md) | `@syntek/forms` — React Forms Package                 | 13     | To Do  |
| [US047](US047.md) | `@syntek/layout` — Shell Layout Package               | 5      | To Do  |
| [US078](US078.md) | `@syntek/ui-logging` — React Observability            | 5      | To Do  |
| [US082](US082.md) | `@syntek/ui-security` — Next.js Security Package      | 5      | To Do  |

### Epic 7 — Web Frontend Features

| Story             | Title                                                      | Points | Status |
| ----------------- | ---------------------------------------------------------- | ------ | ------ |
| [US048](US048.md) | `@syntek/ui-auth` — Authentication UI                      | 8      | To Do  |
| [US049](US049.md) | `@syntek/ui-gdpr` — Multi-Regime Compliance UI             | 13     | To Do  |
| [US092](US092.md) | `@syntek/ui-legal` — Legal Docs & Acceptance UI            | 5      | To Do  |
| [US050](US050.md) | `@syntek/data-table` — Sortable Paginated Table            | 5      | To Do  |
| [US051](US051.md) | `@syntek/ui-notifications` — Notification Feed UI          | 5      | To Do  |
| [US052](US052.md) | `@syntek/ui-payments` — Provider-Agnostic Payment UI       | 8      | To Do  |
| [US053](US053.md) | `@syntek/ui-search` — Site Search UI                       | 8      | To Do  |
| [US054](US054.md) | `@syntek/ui-reporting` — Charts & Report Builder UI        | 13     | To Do  |
| [US103](US103.md) | `@syntek/ui-analytics` — Analytics UI & Admin Dashboard    | 5      | To Do  |
| [US055](US055.md) | `@syntek/ui-settings` — Settings Pages & Tenant Admin      | 8      | To Do  |
| [US085](US085.md) | `@syntek/ui-flags` — Feature Flag UI Package               | 5      | To Do  |
| [US056](US056.md) | `@syntek/ui-onboarding` — Multi-Step Onboarding Wizard     | 5      | To Do  |
| [US084](US084.md) | `@syntek/ui-tasks` — Background Job Progress UI            | 5      | To Do  |
| [US068](US068.md) | `@syntek/ui-donations` — Donations UI Package              | 8      | To Do  |
| [US102](US102.md) | `@syntek/ui-invoicing` — Invoice Management UI             | 8      | To Do  |
| [US069](US069.md) | `@syntek/ui-comments` — Comments, Reviews & Discussions UI | 8      | To Do  |
| [US070](US070.md) | `@syntek/ui-feedback` — Feedback & Surveys UI              | 8      | To Do  |
| [US071](US071.md) | `@syntek/ui-maps` — Maps, Routing & Live Tracking UI       | 13     | To Do  |
| [US072](US072.md) | `@syntek/ui-scheduling` — Booking & Calendar UI Package    | 13     | To Do  |
| [US107](US107.md) | `@syntek/ui-media` — React Media Upload & Gallery UI       | 8      | To Do  |
| [US113](US113.md) | `@syntek/ui-email-builder` — Drag-and-Drop Email Builder   | 13     | To Do  |
| [US122](US122.md) | `@syntek/ui-messaging` — Web Messaging & Live Chat UI      | 8      | To Do  |
| [US128](US128.md) | `@syntek/ui-ai-chat` — React AI Chat UI                    | 8      | To Do  |

### Epic 8 — Mobile Packages

| Story             | Title                                                      | Points | Status |
| ----------------- | ---------------------------------------------------------- | ------ | ------ |
| [US057](US057.md) | `@syntek/mobile-ui` — NativeWind Mobile Design System      | 13     | To Do  |
| [US058](US058.md) | `@syntek/mobile-auth` — Mobile Authentication              | 8      | To Do  |
| [US105](US105.md) | `@syntek/mobile-gdpr` — Mobile Compliance UI               | 5      | To Do  |
| [US059](US059.md) | `@syntek/mobile-notifications` — Push Notifications        | 5      | To Do  |
| [US060](US060.md) | `@syntek/mobile-payments` — Multi-Provider Mobile Payments | 8      | To Do  |
| [US061](US061.md) | `@syntek/mobile-sync` — Offline SQLite Sync                | 5      | To Do  |
| [US073](US073.md) | `@syntek/mobile-media` — Mobile Media Capture & Upload     | 8      | To Do  |
| [US114](US114.md) | `@syntek/mobile-email-builder` — Mobile Email Builder      | 8      | To Do  |
| [US119](US119.md) | `@syntek/mobile-comments` — Mobile Comments & Reviews      | 5      | To Do  |
| [US120](US120.md) | `@syntek/mobile-feedback` — Mobile Surveys & Feedback      | 5      | To Do  |
| [US123](US123.md) | `@syntek/mobile-messaging` — Mobile Messaging & Live Chat  | 8      | To Do  |
| [US126](US126.md) | `@syntek/mobile-error` — Mobile Error Screens              | 3      | To Do  |
| [US079](US079.md) | `@syntek/mobile-logging` — Mobile Observability            | 5      | To Do  |
| [US083](US083.md) | `@syntek/mobile-security` — React Native Security          | 3      | To Do  |
| [US094](US094.md) | `@syntek/mobile-forms` — React Native Forms Package        | 8      | To Do  |
| [US111](US111.md) | `@syntek/mobile-scheduling` — Mobile Booking UI Package    | 8      | To Do  |
| [US117](US117.md) | `@syntek/mobile-maps` — Mobile Maps, Routing & Tracking    | 8      | To Do  |
| [US129](US129.md) | `@syntek/mobile-ai-chat` — React Native AI Chat UI         | 5      | To Do  |

---

## Points Summary

| Epic                                | Stories | Points   |
| ----------------------------------- | ------- | -------- |
| Epic 1 — Foundation & Workspace     | 6       | 26       |
| Epic 2 — Rust Encryption Layer      | 4       | 39       |
| Epic 3 — Core Backend Modules       | 17      | 141      |
| Epic 4 — Backend Feature Modules    | 24      | 207      |
| Epic 5 — Backend Compliance & Media | 28      | 226      |
| Epic 6 — Web Frontend Core          | 10      | 70       |
| Epic 7 — Web Frontend Features      | 24      | 198      |
| Epic 8 — Mobile Packages            | 18      | 123      |
| **Total**                           | **130** | **1015** |

---

## Build Order

```text
Phase 1 — Foundation (US001–US005, US074)
  US001 → US002 | US003 | US004 | US005 | US074

Phase 2 — Rust Layer (US006–US008, strict order)
  US006 → US007 → US008

Phase 3 — Core Backend
  US009 → US010 → US011 → US012 → US013 → US014 → US015 → US016 → US017 → US018
  US077 (syntek-cache) — depends on US001 only; runs in parallel with US011; must complete before US012
  US080 (syntek-security-validator) — depends on US012 ✓, US014 ✓; runs after Sprint 09
  US081 (syntek-security-secrets) — depends on US001 ✓, US014 ✓; independent of US080; runs after Sprint 09
  US086 (syntek-users) — depends on US007 ✓, US008 ✓, US009 ✓, US010 ✓, US011 ✓, US030 (optional);
          can run in parallel with Sprint 12 onwards; planned in Sprint 49
  US118 (syntek-timescaledb) — depends on US014 ✓; independent of other core modules; install before any module that sets USE_TIMESCALEDB = True
  US124 (syntek-error) — depends on US010 ✓, US014 ✓; can run any time after Sprint 10; planned in Sprint 69

Phase 4 — Backend Features (parallelise after Phase 3)
  US104 (syntek-consent) — depends on US009 ✓, US010 ✓, US013 ✓, US090 ✓; must complete before US029
  → US019 | US020 | US022 | US030 (media-core, Cloudinary) | US031 (files, MinIO)
  → US112 (syntek-email-core, depends on US015 ✓, US010 ✓) — must complete before US087 and US038
  → US106 (media-upload, depends on US030 ✓, US031 ✓, US015 ✓)
  → US021 | US023 | US025 (syntek-payments-core)
  → US095 | US096 | US097 | US098 (payment adapters, all depend on US025)
  → US099 | US100 (discount codes and payment links, both depend on US025)
  → US087 (depends on US019 ✓, US112 ✓) | US088 | US089 (notification channel adapters, each depends on US019)
  → US024 | US026 (invoicing, depends on US025 ✓, US100 ✓, US019 ✓) | US027 (donations, depends on US025 ✓, US019 ✓) | US028 (reporting-core)
  → US101 (reporting-export, depends on US028 ✓, US093 ✓, US087 optional)
  → US029 (multi-regime GDPR, depends on US104 ✓, US013 ✓, US015 ✓) | US032 | US033 (integrations-core) | US108 (automation bridge) | US109 (accounting connectors) | US062 (multi-provider subscriptions, depends on US025)
  → US034–US041 | US063 | US065 (syntek-locations-core) | US066 (inventory) | US067
  → US121 (syntek-messaging, depends on US009 ✓, US010 ✓, US015 ✓, US019 ✓, US029 ✓) — Django Channels required
    US065 (syntek-locations-core) — geospatial data platform
    US115 (syntek-routing) — depends on US065 ✓, US116 ✓, US090 ✓, US015 ✓
    US116 (syntek-tracking) — depends on US065 ✓, US019 ✓, US090 ✓, US015 ✓; run in parallel with US115
    US038 depends on US087 (email channel) + US112 (email-core) + US029 (GDPR)
    US093 (bulk-export) depends on US015 ✓, US010 ✓; email delivery requires US087 (optional)
  → US064 (scheduling-core) — depends on US010 ✓, US015 ✓, US019 ✓, US090 ✓; US110 depends on US064 ✓
  US033 (integrations-core) — depends on US007 ✓, US010 ✓, US013 ✓, US090 ✓; can run independently in Phase 4
  US108 (automation bridge) — depends on US033 ✓, US090 ✓, US015 ✓; can run in parallel with US109
  US109 (accounting connectors) — depends on US033 ✓, US026 ✓, US025 ✓, US090 ✓, US015 ✓; can run in parallel with US108

Phase 5 — Web Frontend Core (US003 + US009 required)
  US042 → US043 → US044 → US045 | US046 | US047 | US078 | US082 (ui-security, after US044)

Phase 6 — Web Frontend Features (after Phase 5 + relevant backend)
  US048 | US050
  → US049 (ui-gdpr, depends on US029 ✓, US104 ✓) | US051 | US052 (ui-payments, depends on US025 ✓, US095–US098, US099) | US053 | US054 | US055 | US056
  → US068 | US102 (ui-invoicing, depends on US026 ✓, US052 ✓) | US069 | US070 | US071 (ui-maps, depends on US065 ✓, US115 ✓, US116 ✓) | US072 (ui-scheduling, depends on US064 ✓, US110 ✓) | US084 (ui-tasks, after US015 ✓) | US107 (ui-media, depends on US030 ✓, US106 ✓, US031 ✓)
  → US103 (ui-analytics, depends on US054 ✓, US063 ✓)
  → US113 (ui-email-builder, depends on US044 ✓, US112 ✓)
  → US122 (ui-messaging, depends on US044 ✓, US121 ✓)
  → US125 (ui-error, depends on US042 ✓, US043 ✓, US124 ✓) — planned in Sprint 70
  → US085 (ui-flags, after US017 ✓)

Phase 7 — Mobile (after US003, US009, US057)
  US057 → US058 → US105 (mobile-gdpr, depends on US029 ✓, US104 ✓) | US059 | US060 (mobile-payments, depends on US025 ✓, US095–US098, US099) | US061 | US073 | US079 | US083 (mobile-security, after US057)
  US114 (mobile-email-builder, depends on US057 ✓, US112 ✓) — can run in parallel after Sprint 63
  US119 (mobile-comments, depends on US057 ✓, US040 ✓) | US120 (mobile-feedback, depends on US057 ✓, US067 ✓) — parallel; planned in Sprint 65
  US123 (mobile-messaging, depends on US057 ✓, US121 ✓) — can run in parallel with Sprint 68
  US126 (mobile-error, depends on US057 ✓, US124 ✓) — planned in Sprint 70; parallel with US125
  US094 (mobile-forms) depends on US057 ✓, US044 ✓, US046 ✓, US023 ✓; can run after Sprint 45
  US111 (mobile-scheduling) — depends on US064 ✓, US110 ✓, US057 ✓
  US117 (mobile-maps) — depends on US065 ✓, US115 ✓, US116 ✓, US057 ✓
```
