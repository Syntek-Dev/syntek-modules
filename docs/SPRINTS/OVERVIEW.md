# Syntek Modules — Sprint Overview

**Last Updated**: 11/03/2026 **Total Stories**: 130 **Total Points**: 763 **Total Sprints**: 70
**Sprint Capacity**: 11 points maximum **Status**: In Progress (US008 Completed 10/03/2026 — Sprint
05 in progress, US076 pending)

---

## Capacity Warnings

Several stories or sprint groupings exceed the 11-point sprint capacity. Notes per sprint:

| Story / Sprint                      | Points | Recommendation                                                                                        |
| ----------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| Sprint 02 (US003+US005+US074+US075) | 20     | All four are fully independent — assign one per team member and run in parallel                       |
| Sprint 06 (US009)                   | 13     | Split: auth-core (JWT, login, session) / auth-extended (MFA, passkeys, OAuth)                         |
| Sprint 07 (US010)                   | 13     | Split: tenancy-core (schema isolation, middleware) / tenancy-lifecycle (provisioning, domains)        |
| Sprint 08 (US011+US077)             | 13     | Both are fully independent — US011 RBAC (Must), US077 cache (Must); parallel tracks                   |
| Sprint 11 (US015+US016)             | 21     | Both are fully independent — US015 tasks (Must), US016 settings (Must); parallel tracks               |
| Sprint 12 (US112)                   | 13     | Single cohesive story — multi-provider sending, suppression list, template versioning tightly coupled |
| Sprint 13 (US017+US018)             | 16     | Both are fully independent — US017 flags (Must), US018 groups (Must); parallel tracks                 |
| Sprint 17 (US023+US035)             | 16     | Both are fully independent — US023 forms engine (Must), US035 CalDav (Should); parallel tracks        |
| Sprint 18 (US025)                   | 13     | Split: payments-core (intents, webhooks) / payments-subscriptions (plans, billing)                    |
| Sprint 21 (US030)                   | 13     | Single cohesive story — Cloudinary client, metadata DB, presigned URLs tightly coupled                |
| Sprint 22 (US031)                   | 13     | Single cohesive story — MinIO client, versioning, permission gate, presigned URLs tightly coupled     |
| Sprint 24 (US021+US063)             | 13     | Both are fully independent — US021 bulk import (Must), US063 analytics (Should); parallel tracks      |
| Sprint 25 (US022)                   | 13     | Split by adapter: ES/OS + protocol + signals (Track A) vs. Meilisearch/SQLite + synonyms (Track B)    |
| Sprint 29 (US028)                   | 13     | Single cohesive story — aggregate pipeline, caching, scheduling, and role gate tightly coupled        |
| Sprint 31 (US038+US041)             | 10     | Both are fully independent Should Have stories — assign one per developer and run in parallel         |
| Sprint 36 (US042)                   | 21     | Split across 2+ sprints: primitives first, then overlays and complex components                       |
| Sprint 42 (US052+US053)             | 13     | Both are fully independent — assign one per developer and run in parallel                             |
| Sprint 45 (US069+US070)             | 16     | Both are fully independent — US069 comments UI (Could), US070 feedback UI (Could); parallel tracks    |
| Sprint 47 (US057)                   | 13     | Split: mobile-primitives (core inputs, typography) / mobile-complex (navigation, overlays)            |
| Sprint 49 (US059+US073)             | 13     | Both are fully independent — US059 push notifications (Must), US073 mobile media (Should); parallel   |
| Sprint 52 (US080+US081)             | 16     | Both are fully independent — US080 validator (Must), US081 secrets (Must); parallel tracks            |
| Sprint 55 (US086)                   | 13     | Single cohesive story — PROFILE_SCHEMA engine, status lifecycle, avatar, encrypted fields             |
| Sprint 56 (US020+US091)             | 16     | Both are fully independent — US020 webhooks (Should), US091 legal (Must); parallel tracks             |
| Sprint 60 (US054)                   | 13     | Single cohesive story — chart components, hooks, ReportBuilder tightly coupled                        |
| Sprint 61 (US101+US103)             | 13     | Both are fully independent — US101 reporting export (Should), US103 analytics UI (Should); parallel   |
| Sprint 62 (US113)                   | 13     | Single cohesive story — DnD blocks, Tiptap, preview iframe, and undo stack tightly coupled            |
| Sprint 64 (US071)                   | 13     | Single cohesive story — map renderer, LocationPicker, RouteMap, LiveTracker tightly coupled           |
| Sprint 66 (US121)                   | 13     | Single cohesive story — Channels consumer, message persistence, presence, and push tightly coupled    |

---

## Parallel Development Streams

This plan is sequenced for a single team. With separate frontend, backend, and mobile developers,
the following streams can run in parallel:

- **Web Frontend stream** (US042 onwards) can begin from Sprint 3 — US042 only needs US002 and US003
- **Mobile stream** (US057 onwards) can begin from Sprint 3 — US057 only needs US002 and US003
- The Rust layer (Sprints 3–5) can run in parallel with the frontend streams

---

## Sprint Index

| Sprint                    | Theme                                      | Stories                    | Points | ⚠️                         |
| ------------------------- | ------------------------------------------ | -------------------------- | ------ | -------------------------- |
| [Sprint 01](SPRINT-01.md) | Repository Foundation                      | US001, US002, US004        | 11     | ✅ Completed 06/03/2026    |
| [Sprint 02](SPRINT-02.md) | Design Tokens, CI/CD & Manifest Framework  | US003, US005, US074, US075 | 20     | ✅ Completed 08/03/2026    |
| [Sprint 03](SPRINT-03.md) | Rust — Crypto Primitives                   | US006                      | 8      | Completed 09/03/2026       |
| [Sprint 04](SPRINT-04.md) | Rust — Django Bindings                     | US007                      | 8      | Completed 09/03/2026       |
| [Sprint 05](SPRINT-05.md) | Rust — GraphQL Middleware                  | US008, US076               | 23     | US008 Completed 10/03/2026 |
| [Sprint 06](SPRINT-06.md) | Authentication                             | US009                      | 13     | ⚠️ Over                    |
| [Sprint 07](SPRINT-07.md) | Multi-Tenancy                              | US010                      | 13     | ⚠️ Over                    |
| [Sprint 08](SPRINT-08.md) | Permissions, RBAC & Cache Infrastructure   | US011, US077               | 13     | ⚠️ Over                    |
| [Sprint 09](SPRINT-09.md) | Security Middleware & Structured Logging   | US012, US014               | 10     |                            |
| [Sprint 10](SPRINT-10.md) | Audit Logging & Internationalisation       | US013, US034               | 11     |                            |
| [Sprint 11](SPRINT-11.md) | Background Tasks & Per-Tenant Settings     | US015, US016               | 21     | ⚠️ Over                    |
| [Sprint 12](SPRINT-12.md) | Email Core                                 | US112                      | 13     | ⚠️ Over                    |
| [Sprint 13](SPRINT-13.md) | Feature Flags & Groups / Teams             | US017, US018               | 16     | ⚠️ Over                    |
| [Sprint 14](SPRINT-14.md) | Notification Core & Geolocation            | US019, US036               | 11     |                            |
| [Sprint 15](SPRINT-15.md) | Notification Email & SMS Channels          | US087, US088               | 10     |                            |
| [Sprint 16](SPRINT-16.md) | Notification Push Channel                  | US089                      | 5      |                            |
| [Sprint 17](SPRINT-17.md) | Dynamic Forms & CalDav                     | US023, US035               | 16     | ⚠️ Over                    |
| [Sprint 18](SPRINT-18.md) | Payments                                   | US025                      | 13     | ⚠️ Over                    |
| [Sprint 19](SPRINT-19.md) | Internal Event Bus & API Keys              | US039, US090               | 8      |                            |
| [Sprint 20](SPRINT-20.md) | GDPR Compliance & Locations                | US029, US065               | 11     |                            |
| [Sprint 21](SPRINT-21.md) | Media Core                                 | US030                      | 13     | ⚠️ Over                    |
| [Sprint 22](SPRINT-22.md) | File Storage                               | US031                      | 13     | ⚠️ Over                    |
| [Sprint 23](SPRINT-23.md) | Media Upload Pipeline                      | US106                      | 8      |                            |
| [Sprint 24](SPRINT-24.md) | Bulk Import & Analytics                    | US021, US063               | 13     | ⚠️ Over                    |
| [Sprint 25](SPRINT-25.md) | Site Search                                | US022                      | 13     | ⚠️ Over                    |
| [Sprint 26](SPRINT-26.md) | Events & Ticketing                         | US024                      | 8      |                            |
| [Sprint 27](SPRINT-27.md) | Invoicing                                  | US026                      | 8      |                            |
| [Sprint 28](SPRINT-28.md) | Donations                                  | US027                      | 8      |                            |
| [Sprint 29](SPRINT-29.md) | Reporting Core                             | US028                      | 13     | ⚠️ Over                    |
| [Sprint 30](SPRINT-30.md) | Membership & Integrations Framework        | US032, US033               | 10     |                            |
| [Sprint 31](SPRINT-31.md) | Email Marketing & Loyalty / Referrals      | US038, US041               | 10     |                            |
| [Sprint 32](SPRINT-32.md) | Accounting                                 | US037                      | 8      |                            |
| [Sprint 33](SPRINT-33.md) | Subscriptions & Comments                   | US040, US062               | 8      |                            |
| [Sprint 34](SPRINT-34.md) | Scheduling Backend                         | US064                      | 8      |                            |
| [Sprint 35](SPRINT-35.md) | Inventory & Feedback                       | US066, US067               | 10     |                            |
| [Sprint 36](SPRINT-36.md) | Web Design System                          | US042                      | 21     | ⚠️⚠️ Over                  |
| [Sprint 37](SPRINT-37.md) | Session Management & API Client            | US043, US044               | 10     |                            |
| [Sprint 38](SPRINT-38.md) | Data Hooks & Form Primitives               | US045, US046               | 8      |                            |
| [Sprint 39](SPRINT-39.md) | Layout Shell & GDPR UI                     | US047, US049               | 10     |                            |
| [Sprint 40](SPRINT-40.md) | Authentication UI                          | US048                      | 8      |                            |
| [Sprint 41](SPRINT-41.md) | Data Table & Notifications UI              | US050, US051               | 10     |                            |
| [Sprint 42](SPRINT-42.md) | Payments UI & Search UI                    | US052, US053               | 13     | ⚠️ Over                    |
| [Sprint 43](SPRINT-43.md) | Settings UI                                | US055                      | 8      |                            |
| [Sprint 44](SPRINT-44.md) | Onboarding UI & Donations UI               | US056, US068               | 10     |                            |
| [Sprint 45](SPRINT-45.md) | Comments & Feedback UI                     | US069, US070               | 16     | ⚠️ Over                    |
| [Sprint 46](SPRINT-46.md) | Scheduling UI & Background Job Progress UI | US072, US084               | 10     |                            |
| [Sprint 47](SPRINT-47.md) | Mobile Design System                       | US057                      | 13     | ⚠️ Over                    |
| [Sprint 48](SPRINT-48.md) | Mobile Authentication                      | US058                      | 8      |                            |
| [Sprint 49](SPRINT-49.md) | Mobile Notifications & Media               | US059, US073               | 13     | ⚠️ Over                    |
| [Sprint 50](SPRINT-50.md) | Mobile Payments & Offline Sync             | US060, US061               | 10     |                            |
| [Sprint 51](SPRINT-51.md) | Media UI                                   | US107                      | 8      |                            |
| [Sprint 52](SPRINT-52.md) | Security Validator & Secrets Management    | US080, US081               | 16     | ⚠️ Over                    |
| [Sprint 53](SPRINT-53.md) | Web & Mobile Security Packages             | US082, US083               | 8      |                            |
| [Sprint 54](SPRINT-54.md) | Feature Flag UI                            | US085                      | 5      |                            |
| [Sprint 55](SPRINT-55.md) | User Profiles                              | US086                      | 13     | ⚠️ Over                    |
| [Sprint 56](SPRINT-56.md) | Webhooks & Legal Document Management       | US020, US091               | 16     | ⚠️ Over                    |
| [Sprint 57](SPRINT-57.md) | Legal Documents UI                         | US092                      | 5      |                            |
| [Sprint 58](SPRINT-58.md) | Bulk Export                                | US093                      | 8      |                            |
| [Sprint 59](SPRINT-59.md) | Mobile Forms                               | US094                      | 8      |                            |
| [Sprint 60](SPRINT-60.md) | Reporting UI                               | US054                      | 13     | ⚠️ Over                    |
| [Sprint 61](SPRINT-61.md) | Reporting Export & Analytics UI            | US101, US103               | 13     | ⚠️ Over                    |
| [Sprint 62](SPRINT-62.md) | Email Builder UI                           | US113                      | 13     | ⚠️ Over                    |
| [Sprint 63](SPRINT-63.md) | Mobile Email Builder                       | US114                      | 8      |                            |
| [Sprint 64](SPRINT-64.md) | Maps UI                                    | US071                      | 13     | ⚠️ Over                    |
| [Sprint 65](SPRINT-65.md) | Mobile Comments & Feedback                 | US119, US120               | 10     |                            |
| [Sprint 66](SPRINT-66.md) | Real-Time Messaging Backend                | US121                      | 13     | ⚠️ Over                    |
| [Sprint 67](SPRINT-67.md) | Web Messaging UI                           | US122                      | 8      |                            |
| [Sprint 68](SPRINT-68.md) | Mobile Messaging UI                        | US123                      | 8      |                            |
| [Sprint 69](SPRINT-69.md) | Error Handling Backend                     | US124                      | 5      |                            |
| [Sprint 70](SPRINT-70.md) | Web & Mobile Error UI                      | US125, US126               | 8      |                            |

---

## Points by Phase

| Phase                                     | Sprints                      | Points  |
| ----------------------------------------- | ---------------------------- | ------- |
| Phase 1 — Foundation                      | 1–2                          | 31      |
| Phase 2 — Rust Layer                      | 3–5                          | 39      |
| Phase 3 — Core Backend                    | 6–14                         | 126     |
| Phase 4 — Feature Backend                 | 15–16, 17–35, 56, 58, 66, 69 | 272     |
| Phase 5 — Web Frontend                    | 36–46, 51, 60–62, 64, 67, 70 | 161     |
| Phase 6 — Mobile                          | 47–50, 59, 63, 65, 68        | 78      |
| Phase 7 — Security, Notifications & Legal | 52–57                        | 55      |
| Phase 8 — Reporting, Analytics & Media    | 23, 58, 60–61                | 42      |
| **Total**                                 | **70**                       | **804** |
