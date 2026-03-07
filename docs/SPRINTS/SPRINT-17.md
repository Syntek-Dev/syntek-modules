# Sprint 17 — GDPR Compliance & Locations

**Sprint Goal**: Implement the GDPR/compliance module covering Subject Access Requests,
right-to-erasure, consent tracking, and retention policies; and the locations module for
multi-location management with geospatial queries.

**Total Points**: 11 / 11 **MoSCoW Balance**: Must 73% / Could 27% **Status**: Planned

## Stories

| Story                        | Title                                    | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ---------------------------------------- | ------ | ------ | ------------------------- |
| [US029](../STORIES/US029.md) | `syntek-gdpr` — GDPR & Compliance        | 8      | Must   | US009 ✓, US010 ✓, US013 ✓ |
| [US065](../STORIES/US065.md) | `syntek-locations` — Location Management | 3      | Could  | US010 ✓, US036 ✓          |

## Notes

- US029 and US065 are independent of each other and can be worked in parallel.
- US029 erasure workflows must cascade through all modules that store personal data — document the
  integration points clearly.
- US065 depends on US036 (geo) for geocoding; ensure US036 completes in Sprint 13 before starting
  US065.
