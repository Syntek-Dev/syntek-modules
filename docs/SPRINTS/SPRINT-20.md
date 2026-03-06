# Sprint 20 — Full-Text Search

**Sprint Goal**: Implement Elasticsearch/OpenSearch full-text search with facets, fuzzy matching, index management, and per-tenant index isolation.

**Total Points**: 8 / 11
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US022](../STORIES/US022.md) | `syntek-search` — Full-Text Search | 8 | Must | US010 ✓, US011 ✓ |

## Notes

- Search indices must be tenant-scoped — queries must never return results from another tenant's index.
- Index updates must be async via Celery (US015) to avoid blocking write operations.
- Connection configuration for Elasticsearch/OpenSearch must come from `SYNTEK_SEARCH` settings.
