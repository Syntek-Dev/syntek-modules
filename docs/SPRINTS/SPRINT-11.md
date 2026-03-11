# Sprint 11 — Background Tasks & Per-Tenant Settings

**Sprint Goal**: Implement the full Celery-based background task queue with priority lanes, chunked
fan-out, cron scheduling, dead-letter queue, and GraphQL task status API — and the per-tenant typed
key-value settings store.

**Total Points**: 21 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                         | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | --------------------------------------------- | ------ | ------ | ------------------------- |
| [US015](../STORIES/US015.md) | `syntek-tasks` — Background Tasks (Celery)    | 13     | Must   | US010 ✓, US014 ✓, US077 ✓ |
| [US016](../STORIES/US016.md) | `syntek-settings` — Per-Tenant Settings Store | 8      | Must   | US010 ✓, US011 ✓, US077 ✓ |

## Notes

- ⚠️ 18 points exceeds sprint capacity. US015 and US016 are fully independent — no shared files, no
  shared database tables. The over-capacity is acceptable given the parallel workload.
- **US015 scope increase** (5 → 13 points): The expanded scope covers chunked fan-out for bulk
  operations (`dispatch_chunked`, configurable chunk sizes per task type), per-task rate limits,
  `django-celery-beat` for database-backed cron scheduling, a `TaskResult` model with incremental
  progress reporting, a `taskStatus` GraphQL query, Prometheus metrics, and the `DeadLetterQueue`
  management command with replay support.
- **US015** depends on US077 (`syntek-cache`) for the Redis/Valkey broker and result backend. It
  also depends on US014 (`syntek-logging`) for request ID propagation into task workers.
- **Celery Beat** runs as a single Beat process alongside N worker processes. `django-celery-beat`
  stores schedules in the Django database — cluster-safe, restart-safe. No separate cron system is
  required for this stack.
- **Chunking pattern**: `dispatch_chunked` splits bulk work (emails, SMS, push, in-app
  notifications) into bounded chunks dispatched to the `low` priority queue as a Celery group. Chunk
  sizes are configurable per task type in `SYNTEK_TASKS['CHUNK_SIZES']`.
- **Pickle ban**: `TASK_SERIALIZER: 'pickle'` raises `ImproperlyConfigured` at startup. JSON
  serialisation is enforced for all tasks.
- **US016 scope increase** (5 → 8 points): Full `SYNTEK_SETTINGS` config contract with a schema
  registry, typed setting definitions with custom validators, module-level `register_settings()`
  API, Redis caching, design token overrides (`TenantDesignToken` model), and a full GraphQL API
  (`tenantSettings`, `designTokens` queries; `updateSetting`, `updateDesignToken`, `resetSetting`
  mutations). `REQUIRE_ADMIN_FOR_WRITE` uses US011 RBAC; caching uses US077.
- **US016** settings values must be typed and validated at read time — no raw string-only store.
- **US016** is depended upon by many subsequent modules for per-tenant configuration overrides.
- **US084** (`@syntek/ui-tasks` — job progress UI) is the frontend companion to US015, scheduled in
  Epic 7 alongside other web frontend feature packages.
