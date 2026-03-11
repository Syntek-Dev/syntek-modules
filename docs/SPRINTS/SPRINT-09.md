# Sprint 09 — Security Middleware & Structured Logging

**Sprint Goal**: Implement the HTTP security middleware layer (rate limiting per-user/per-tenant/
per-IP, burst allowance, CORS, CSP, HSTS, IP filtering) and the structured JSON logging module with
Sentry/Glitchtip integration.

**Total Points**: 10 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                   | Points | MoSCoW | Dependencies Met |
| ---------------------------- | --------------------------------------- | ------ | ------ | ---------------- |
| [US012](../STORIES/US012.md) | `syntek-security` — Security Middleware | 8      | Must   | US010 ✓, US077 ✓ |
| [US014](../STORIES/US014.md) | `syntek-logging` — Structured Logging   | 5      | Must   | US010 ✓          |

## Notes

- US012 and US014 are independent of each other and can be worked in parallel.
- **US012 now depends on US077 (`syntek-cache`)** — the rate limiter uses syntek-cache
  (Redis/Valkey) for per-user, per-tenant, and per-IP counters. US077 must be complete before US012
  begins.
- US012 rate limiting: per-IP (unauthenticated), per-user (authenticated, overrides per-IP),
  per-tenant (aggregate across all users), and burst window — all configurable via
  `SYNTEK_SECURITY`.
- US012 story points increased from 5 to 8 — the full per-user/per-tenant rate limiting
  implementation with burst allowance and rate limit headers adds significant scope over the
  original basic per-IP limiter.
- US014 must emit structured JSON logs consumable by Loki on the Syntek infrastructure stack.
- Both modules are foundational — all subsequent modules rely on security middleware and logging.
