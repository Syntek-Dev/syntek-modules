# Sprint 21 — Events & Ticketing

**Sprint Goal**: Implement the events and ticketing module with capacity management, QR code
check-in, ticket transfer, and waitlist support.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ------------------------------------ | ------ | ------ | ------------------------- |
| [US024](../STORIES/US024.md) | `syntek-events` — Events & Ticketing | 8      | Must   | US009 ✓, US010 ✓, US019 ✓ |

## Notes

- Ticket capacity must use database-level locking to prevent overselling under concurrent requests.
- QR check-in codes must be HMAC-signed (using the Rust layer) to prevent forgery.
- Event notifications (reminders, confirmations, cancellations) must dispatch via US019
  (notifications).
