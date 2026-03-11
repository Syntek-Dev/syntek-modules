# Sprint 24 — Bulk Import & Analytics

**Sprint Goal**: Implement async bulk CSV/Excel/PDF import with column mapping, duplicate detection,
rollback support, and the privacy-first analytics module with Plausible/Fathom/GA4/Umami adapters
and consent gating.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 62% / Should 38% **Status**:
Planned

## Stories

| Story                        | Title                                        | Points | MoSCoW | Dependencies Met |
| ---------------------------- | -------------------------------------------- | ------ | ------ | ---------------- |
| [US021](../STORIES/US021.md) | `syntek-bulk-import` — Bulk Import           | 8      | Must   | US010 ✓, US015 ✓ |
| [US063](../STORIES/US063.md) | `syntek-analytics` — Privacy-First Analytics | 5      | Should | US029 ✓, US010 ✓ |

## Notes

- US021 and US063 are fully independent — assign one per developer and run in parallel.
- Sprint exceeds capacity at 13 pts. US021 is a Must Have (bulk import) and US063 is a Should Have
  (analytics) — they share no code or models.
- US021 all import operations must be async via Celery — never block the request thread for large
  datasets.
- US021 rollback requires `ENABLE_ROLLBACK = True` in `SYNTEK_BULK_IMPORT`; jobs older than
  `ROLLBACK_WINDOW_DAYS` cannot be rolled back.
- US063 analytics events must only fire after user consent is recorded via US029 (GDPR module).
- US063 supports four provider adapters: Plausible, Fathom, GA4 (server-side Measurement Protocol
  only — no client JS), and Umami. All tracking is server-side; no client analytics script is
  injected.
- Bulk export (`syntek-bulk-export`, US093) is a separate story in Sprint 58.
