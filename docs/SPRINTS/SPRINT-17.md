# Sprint 17 — Dynamic Forms & CalDav

**Sprint Goal**: Implement the full schema-driven form engine with conditional logic, all field
types, pre-fill resolution, draft persistence, spam protection, and webhook dispatch — and the
CalDav client module for Radicale calendar integration.

**Total Points**: 16 / 11 **MoSCoW Balance**: Must 81% / Should 19% **Status**: Planned ⚠️ Over
Capacity

## Stories

| Story                        | Title                                     | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ----------------------------------------- | ------ | ------ | ---------------- |
| [US023](../STORIES/US023.md) | `syntek-forms-core` — Dynamic Form Engine | 13     | Must   | US010 ✓, US015 ✓ |
| [US035](../STORIES/US035.md) | `syntek-caldav` — Calendar / CalDav       | 3      | Should | US010 ✓          |

## Notes

- US023 and US035 are fully independent — assign one per developer and run in parallel.
- Sprint exceeds capacity at 16pts. US023 is a 13pt cohesive form engine (schema DSL, all field type
  validators, conditional engine, pre-fill resolver, draft persistence, spam protection). Both
  stories are independent — track them as parallel streams.
- US023 form schemas must be stored as tenant-scoped versioned JSON — no hardcoded form definitions.
  Schema changes create a new `FormVersion`; existing submissions always reference the version in
  use at submission time.
- US023 file upload fields route to `syntek-documents` (US031) — if not installed, file fields are
  disabled gracefully.
- US023 webhook dispatch routes via `syntek-webhooks` (US020) — if not installed, the post-submit
  hook is skipped silently.
- US035 must connect to the Radicale CalDav server on the Syntek infrastructure stack via
  `SYNTEK_CALDAV` settings.
