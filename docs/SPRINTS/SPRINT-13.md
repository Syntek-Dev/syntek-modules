# Sprint 13 — Notifications & Geolocation

**Sprint Goal**: Implement the multi-channel notification system (in-app, push, SMS, email) with
per-user preferences, and the geolocation module with UK postcode lookup and `nearby()` spatial
queries.

**Total Points**: 11 / 11 **MoSCoW Balance**: Must 73% / Could 27% **Status**: Planned

## Stories

| Story                        | Title                                                | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ---------------------------------------------------- | ------ | ------ | ---------------- |
| [US019](../STORIES/US019.md) | `syntek-notifications` — Multi-Channel Notifications | 8      | Must   | US010 ✓, US015 ✓ |
| [US036](../STORIES/US036.md) | `syntek-geo` — Address & Geolocation                 | 3      | Could  | US010 ✓          |

## Notes

- US019 and US036 are independent of each other and can be worked in parallel.
- US019 notification dispatch must be async via Celery (US015); never block the request cycle.
- US036 geocoding API credentials must be injected via `SYNTEK_GEO` settings — never hardcoded.
