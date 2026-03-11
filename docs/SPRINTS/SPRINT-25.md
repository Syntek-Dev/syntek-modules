# Sprint 25 — Site Search

**Sprint Goal**: Implement the site search abstraction layer with Elasticsearch, OpenSearch,
Meilisearch, and SQLite FTS backend adapters — tenant-isolated indices, async indexing on model
save, faceted queries, autocomplete, snippet extraction, synonym support, and full rebuild command.

**Total Points**: 13 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned ⚠️ Over Capacity

## Stories

| Story                        | Title                              | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ---------------------------------- | ------ | ------ | ---------------- |
| [US022](../STORIES/US022.md) | `syntek-search-core` — Site Search | 13     | Should | US010 ✓, US015 ✓ |

## Notes

- US022 exceeds sprint capacity at 13pts. The complexity comes from implementing four independent
  backend adapters (Elasticsearch, OpenSearch, Meilisearch, SQLite FTS) each with the same
  `SearchBackend` protocol. Recommended split if a single sprint is too large:
  - **Track A:** `SearchBackend` protocol + ES/OpenSearch adapters + signal hooks + Celery task
  - **Track B:** Meilisearch adapter + SQLite FTS adapter + synonym/stop-word + management command
- Search indices must be tenant-scoped — queries must never return results from another tenant's
  index.
- Index updates must be async via Celery (US015) to avoid blocking write operations on model save.
- The SQLite backend requires no external service — suitable for development environments and small
  sites. Connection configuration for all other backends comes from `SYNTEK_SEARCH` settings.
- `syntek-search-core` is a backend-only module. The React UI is in US053 (`@syntek/ui-search`,
  Sprint 42).
