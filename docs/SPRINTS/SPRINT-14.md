# Sprint 14 — Dynamic Forms & CalDav

**Sprint Goal**: Implement the schema-driven dynamic form engine with conditional logic and validation, and the CalDav client module for Radicale calendar integration.

**Total Points**: 11 / 11
**MoSCoW Balance**: Must 73% / Should 27%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US023](../STORIES/US023.md) | `syntek-forms` — Dynamic Form Engine | 8 | Must | US010 ✓, US016 ✓ |
| [US035](../STORIES/US035.md) | `syntek-caldav` — Calendar / CalDav | 3 | Should | US010 ✓ |

## Notes

- US023 and US035 are independent of each other and can be worked in parallel.
- US023 form schemas must be stored as tenant-scoped JSON — no hardcoded form definitions.
- US035 must connect to the Radicale CalDav server on the Syntek infrastructure stack via `SYNTEK_CALDAV` settings.
