# Sprint 55 — User Profiles

**Sprint Goal**: Implement the domain user profile module — configurable custom profile fields,
status lifecycle, Cloudinary avatar upload, soft delete, encrypted field support, and a dynamic
GraphQL type named from `PROFILE_LABEL` — completing the Core Backend foundation for all consuming
projects that need to model customers, members, patients, or any other user domain profile distinct
from authentication identity.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                          | Points | MoSCoW | Dependencies Met                                              |
| ---------------------------- | ------------------------------ | ------ | ------ | ------------------------------------------------------------- |
| [US086](../STORIES/US086.md) | `syntek-users` — User Profiles | 13     | Must   | US007 ✓, US008 ✓, US009 ✓, US010 ✓, US011 ✓, US030 (optional) |

## Notes

- ⚠️ 13 points exceeds sprint capacity. This is a single story — the over-capacity reflects its
  scope. Avatar upload, PROFILE_SCHEMA field engine, status lifecycle, soft delete, and encrypted
  fields are all in scope and cannot be split cleanly.
- **US086 chronological fit**: The dependencies (US007–US011) are complete at the end of Sprint 08.
  Sprint 55 is its planning slot; the implementation can begin in parallel with Sprint 13 onwards
  once the dependency chain is satisfied.
- **US086 scope summary**: `SYNTEK_USERS` config contract — `PROFILE_LABEL` for domain naming
  (Customer, Member, Patient → PascalCase GraphQL type); `PROFILE_SCHEMA` for custom fields stored
  in a validated JSONField (types:
  str/text/int/float/bool/date/datetime/email/phone/url/json/choice; `encrypted: True` fields use
  AES-256-GCM via syntek-pyo3 transparently); `STATUSES` list with `STATUS_TRANSITIONS` dict for
  configurable lifecycle; Cloudinary avatar upload with transform config; `SOFT_DELETE` with
  `ActiveProfileManager` / `all_objects`; `EXPOSE_SENSITIVE_TO_SELF` allows users to read their own
  sensitive fields; dynamic GraphQL type name from PROFILE_LABEL.
- **US086 vs US009 (syntek-auth)**: auth owns identity (credentials, MFA, sessions); users owns
  domain profile (custom fields, avatar, status). `UserProfile.user` is a OneToOne FK to the auth
  `User` model. The two modules are always installed together but remain independently versioned.
- **US030 (syntek-media)** is an optional soft dependency — when installed, avatar uploads are
  processed via Cloudinary with the configured transform. When absent, avatar upload mutations
  return an `AvatarUnsupportedError`.

---

## Milestone — Core Complete

After Sprint 55 the original 84 user stories are delivered. Three additional sprints (15–16 + 52–54
already planned) complete the full 87-story ecosystem:

- **Rust security layer** (Sprints 03–05): AES-256-GCM, PyO3 bindings, GraphQL middleware
- **Core backend** (Sprints 06–13 + Sprint 55): Auth, tenancy, permissions, security (+
  COEP/COOP/CORP), logging, audit, i18n, tasks (+ chunked fan-out, cron), settings (+ schema
  registry, design tokens), flags (+ deterministic rollout, kill switch), groups (+ GROUP_TYPES
  registry, GROUP_SCHEMA, invitation max_uses), users (+ PROFILE_SCHEMA, status lifecycle,
  Cloudinary avatar, encrypted fields), cache
- **Email infrastructure** (Sprints 12, 15–16): Email core engine, email/SMS/push channel adapters
- **Feature backend** (Sprints 14, 17–35): Notification core (+ channel registry, in-app WebSocket,
  DLQ), payments, webhooks, API keys, GDPR, locations, media, documents, bulk, analytics, search,
  events, invoicing, donations, reporting, membership, integrations, email marketing (+ full
  Mailchimp-equivalent analytics, automation sequences, e-commerce attribution), loyalty,
  accounting, subscriptions, comments, scheduling, inventory, feedback
- **Backend security extensions** (Sprint 52): Input validation & XSS protection, secrets management
  with OpenBao/Vault/AWS/GCP/Azure, secret rotation with DB connection recycling
- **Web frontend core** (Sprints 36–40): Design system, session, API client, data hooks, forms,
  layout
- **Web frontend features** (Sprints 41–46): Auth UI, GDPR UI, data table, payments UI, search UI,
  reporting UI, settings UI (+ useSettings hook + TenantSettingsPanel), onboarding UI, donations UI,
  comments UI, feedback UI, maps UI, scheduling UI, background job progress UI
- **Mobile** (Sprints 47–50): Mobile design system, mobile auth, mobile notifications, mobile media,
  mobile payments, offline sync
- **Cross-platform security** (Sprint 53): Next.js security headers + CSP nonce, React Native input
  sanitisation + WebView URL validation
- **Feature flag UI** (Sprint 54): useFlag hook, FlagGate, FlagsAdmin, FlagBadge
