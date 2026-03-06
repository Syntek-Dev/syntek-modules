# Sprint 19 — Bulk Import/Export & Analytics

**Sprint Goal**: Implement async bulk CSV/Excel/JSON import and export with validation error reporting, and the privacy-first analytics module with Plausible/Fathom integration and consent gating.

**Total Points**: 11 / 11
**MoSCoW Balance**: Must 73% / Should 27%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US021](../STORIES/US021.md) | `syntek-bulk` — Bulk Import / Export | 8 | Must | US010 ✓, US015 ✓ |
| [US063](../STORIES/US063.md) | `syntek-analytics` — Privacy-First Analytics | 3 | Should | US029 ✓, US010 ✓ |

## Notes

- US021 and US063 are independent of each other and can be worked in parallel.
- US021 all bulk operations must be async via Celery — never block the request thread for large datasets.
- US063 analytics events must only fire after user consent is recorded via US029 (GDPR module).
