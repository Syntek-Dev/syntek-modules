# Syntek Modules — Sprint Overview

**Last Updated**: 06/03/2026
**Total Stories**: 74
**Total Points**: 446
**Total Sprints**: 45
**Sprint Capacity**: 11 points maximum
**Status**: Planned

---

## Capacity Warnings

Six stories or sprint groupings exceed the 11-point sprint capacity. Notes per sprint:

| Story / Sprint | Points | Recommendation |
|---|---|---|
| Sprint 02 (US003+US005+US074) | 15 | All three are fully independent — assign one per team member and run in parallel |
| US009 `syntek-auth` | 13 | Split: auth-core (JWT, login, session) / auth-extended (MFA, passkeys, OAuth) |
| US010 `syntek-tenancy` | 13 | Split: tenancy-core (schema isolation, middleware) / tenancy-lifecycle (provisioning, domains) |
| US025 `syntek-payments` | 13 | Split: payments-core (intents, webhooks) / payments-subscriptions (plans, billing) |
| US042 `@syntek/ui` | 21 | Split across 2+ sprints: primitives first, then overlays and complex components |
| US057 `@syntek/mobile-ui` | 13 | Split: mobile-primitives (core inputs, typography) / mobile-complex (navigation, overlays) |

---

## Parallel Development Streams

This plan is sequenced for a single team. With separate frontend, backend, and mobile developers, the following streams can run in parallel:

- **Web Frontend stream** (US042 onwards) can begin from Sprint 3 — US042 only needs US002 and US003
- **Mobile stream** (US057 onwards) can begin from Sprint 3 — US057 only needs US002 and US003
- The Rust layer (Sprints 3–5) can run in parallel with the frontend streams

---

## Sprint Index

| Sprint | Theme | Stories | Points | ⚠️ |
|---|---|---|---|---|
| [Sprint 01](SPRINT-01.md) | Repository Foundation | US001, US002, US004 | 11 | |
| [Sprint 02](SPRINT-02.md) | Design Tokens, CI/CD & Manifest Framework | US003, US005, US074 | 15 | ⚠️ Over (parallel) |
| [Sprint 03](SPRINT-03.md) | Rust — Crypto Primitives | US006 | 8 | |
| [Sprint 04](SPRINT-04.md) | Rust — Django Bindings | US007 | 8 | |
| [Sprint 05](SPRINT-05.md) | Rust — GraphQL Middleware | US008 | 8 | |
| [Sprint 06](SPRINT-06.md) | Authentication | US009 | 13 | ⚠️ Over |
| [Sprint 07](SPRINT-07.md) | Multi-Tenancy | US010 | 13 | ⚠️ Over |
| [Sprint 08](SPRINT-08.md) | Permissions & RBAC | US011 | 8 | |
| [Sprint 09](SPRINT-09.md) | Security & Logging | US012, US014 | 10 | |
| [Sprint 10](SPRINT-10.md) | Audit & Internationalisation | US013, US034 | 11 | |
| [Sprint 11](SPRINT-11.md) | Task Queue & Settings | US015, US016 | 10 | |
| [Sprint 12](SPRINT-12.md) | Feature Flags & Groups | US017, US018 | 10 | |
| [Sprint 13](SPRINT-13.md) | Notifications & Geocoding | US019, US036 | 11 | |
| [Sprint 14](SPRINT-14.md) | Dynamic Forms & CalDav | US023, US035 | 11 | |
| [Sprint 15](SPRINT-15.md) | Payment Processing | US025 | 13 | ⚠️ Over |
| [Sprint 16](SPRINT-16.md) | Webhooks & API Keys | US020, US039 | 11 | |
| [Sprint 17](SPRINT-17.md) | GDPR Compliance & Locations | US029, US065 | 11 | |
| [Sprint 18](SPRINT-18.md) | Media & Document Storage | US030, US031 | 10 | |
| [Sprint 19](SPRINT-19.md) | Bulk Operations & Analytics | US021, US063 | 11 | |
| [Sprint 20](SPRINT-20.md) | Full-Text Search | US022 | 8 | |
| [Sprint 21](SPRINT-21.md) | Events & Ticketing | US024 | 8 | |
| [Sprint 22](SPRINT-22.md) | Invoicing & UK VAT | US026 | 8 | |
| [Sprint 23](SPRINT-23.md) | Donations & Gift Aid | US027 | 8 | |
| [Sprint 24](SPRINT-24.md) | Reporting & Exports | US028 | 8 | |
| [Sprint 25](SPRINT-25.md) | Membership & Integrations | US032, US033 | 10 | |
| [Sprint 26](SPRINT-26.md) | Email Marketing & Loyalty | US038, US041 | 10 | |
| [Sprint 27](SPRINT-27.md) | Accounting & Ledger | US037 | 8 | |
| [Sprint 28](SPRINT-28.md) | Subscriptions & Comments | US062, US040 | 8 | |
| [Sprint 29](SPRINT-29.md) | Scheduling Backend | US064 | 8 | |
| [Sprint 30](SPRINT-30.md) | Inventory & Feedback | US066, US067 | 10 | |
| [Sprint 31](SPRINT-31.md) | Web Design System | US042 | 21 | ⚠️⚠️ Over |
| [Sprint 32](SPRINT-32.md) | Session & API Client | US043, US044 | 10 | |
| [Sprint 33](SPRINT-33.md) | Data Hooks & Form Primitives | US045, US046 | 8 | |
| [Sprint 34](SPRINT-34.md) | Layout Shell & GDPR UI | US047, US049 | 10 | |
| [Sprint 35](SPRINT-35.md) | Authentication UI | US048 | 8 | |
| [Sprint 36](SPRINT-36.md) | Data Table & Notifications UI | US050, US051 | 10 | |
| [Sprint 37](SPRINT-37.md) | Payments & Search UI | US052, US053 | 10 | |
| [Sprint 38](SPRINT-38.md) | Reporting & Settings UI | US054, US055 | 10 | |
| [Sprint 39](SPRINT-39.md) | Onboarding & Donations UI | US056, US068 | 10 | |
| [Sprint 40](SPRINT-40.md) | Comments, Feedback & Maps UI | US069, US070, US071 | 11 | |
| [Sprint 41](SPRINT-41.md) | Scheduling UI | US072 | 5 | |
| [Sprint 42](SPRINT-42.md) | Mobile Design System | US057 | 13 | ⚠️ Over |
| [Sprint 43](SPRINT-43.md) | Mobile Authentication | US058 | 8 | |
| [Sprint 44](SPRINT-44.md) | Mobile Notifications & Media | US059, US073 | 8 | |
| [Sprint 45](SPRINT-45.md) | Mobile Payments & Offline Sync | US060, US061 | 10 | |

---

## Points by Phase

| Phase | Sprints | Points |
|---|---|---|
| Phase 1 — Foundation | 1–2 | 26 |
| Phase 2 — Rust Layer | 3–5 | 24 |
| Phase 3 — Core Backend | 6–12 | 93 |
| Phase 4 — Feature Backend | 13–30 | 170 |
| Phase 5 — Web Frontend | 31–41 | 94 |
| Phase 6 — Mobile | 42–45 | 39 |
| **Total** | **45** | **446** |
