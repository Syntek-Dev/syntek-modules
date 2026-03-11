# Sprint 14 — Notification Core & Geolocation

**Sprint Goal**: Implement the notification core engine — unified channel dispatch API, per-user
preferences, in-app WebSocket delivery, DLQ, and retry policy — and the geolocation module with UK
postcode lookup and `nearby()` spatial queries. Channel adapters (email, SMS, push) are separate
sub-modules delivered in Sprint 15–16.

**Total Points**: 11 / 11 **MoSCoW Balance**: Must 73% / Could 27% **Status**: Planned

## Stories

| Story                        | Title                                                  | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ------------------------------------------------------ | ------ | ------ | ---------------- |
| [US019](../STORIES/US019.md) | `syntek-notifications-core` — Core Notification Engine | 8      | Must   | US010 ✓, US015 ✓ |
| [US036](../STORIES/US036.md) | `syntek-geo` — Address & Geolocation                   | 3      | Could  | US010 ✓          |

## Notes

- US019 and US036 are independent of each other and can be worked in parallel.
- US019 notification dispatch must be async via Celery (US015); never block the request cycle.
- US019 implements the channel registry only — downstream modules (US087 email, US088 SMS, US089
  push) register their adapters via `AppConfig.ready()`. Core must remain functional with zero
  adapters installed (in-app only).
- US036 geocoding API credentials must be injected via `SYNTEK_GEO` settings — never hardcoded.
- **Channel adapters** are delivered in Sprint 15 (US087 + US088) and Sprint 16 (US089).
