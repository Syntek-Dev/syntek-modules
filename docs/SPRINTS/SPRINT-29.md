# Sprint 29 — Reporting Core

**Sprint Goal**: Implement the report definition and query engine — configurable aggregate pipeline,
role-gated access, Redis caching, Celery Beat scheduling, and versioned report definitions with full
GraphQL API.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                         | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | --------------------------------------------- | ------ | ------ | ------------------------- |
| [US028](../STORIES/US028.md) | `syntek-reporting-core` — Report Query Engine | 13     | Should | US010 ✓, US011 ✓, US015 ✓ |

## Notes

- US028 is a single cohesive story — the aggregate pipeline, caching, scheduling, and role gate are
  tightly coupled and cannot be split without creating circular dependencies.
- Report generation must be async via Celery (US015) — large reports must not block the request
  cycle.
- Report access must be permission-checked via US011 (RBAC) — tenant-scoped.
- `ReportVersion` records are immutable once created. All `ReportRun` records reference the version
  in use at generation time, so historical runs remain reproducible.
- Export logic (PDF/Excel/CSV) is intentionally excluded from this sprint and is handled by
  `syntek-reporting-export` (US101) in Sprint 61.
- Scheduled reports emit a `report_run_complete` signal — downstream consumers (US101, US019) hook
  into this signal without this module needing to know about them.
