# Sprint 08 — Permissions, RBAC & Cache Infrastructure

**Sprint Goal**: Implement role-based access control with object-level permissions, role strategy
configuration (group / per-user / hybrid), and the shared Redis/Valkey caching infrastructure that
rate limiting, session lockout, and all subsequent modules depend on.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                            | Points | MoSCoW | Dependencies Met               |
| ---------------------------- | ------------------------------------------------ | ------ | ------ | ------------------------------ |
| [US011](../STORIES/US011.md) | `syntek-permissions` — RBAC & Object Permissions | 8      | Must   | US009 ✓, US010 ✓               |
| [US077](../STORIES/US077.md) | `syntek-cache` — Redis/Valkey Caching Module     | 5      | Must   | US001 ✓ (independent of US011) |

## Notes

- ⚠️ 13 points exceeds the 11-point sprint capacity. Both stories are fully independent — US011 and
  US077 share no files and can run in parallel. The over-capacity is acceptable given the parallel
  workload split.
- **US011** depends on US009 (auth) and US010 (tenancy) for user identity and tenant-scoped roles.
  Permission checks must always be tenant-scoped — a role in Tenant A has no authority in Tenant B.
- **US077** only depends on US001 (monorepo setup) and can start immediately. It is intentionally
  placed here so that Sprint 09 (US012 security/rate limiting) can depend on it.
- GraphQL permission directives (`@hasPermission`, `@hasRole`) implemented in US011 and used by all
  subsequent backend modules.
- `syntek-cache` configures Django's `CACHES['default']` automatically. All modules use
  `django.core.cache.cache` — no module manages its own Redis connection.
