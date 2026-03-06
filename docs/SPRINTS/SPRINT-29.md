# Sprint 29 — Scheduling Backend

**Sprint Goal**: Implement the appointment scheduling backend with availability management, atomic double-booking prevention, and calendar integration via the CalDav module.

**Total Points**: 8 / 11
**MoSCoW Balance**: Should 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US064](../STORIES/US064.md) | `syntek-scheduling` — Appointment Scheduling | 8 | Should | US010 ✓, US015 ✓, US019 ✓, US033 ✓ |

## Notes

- Booking slot reservation must use SELECT FOR UPDATE to prevent double-booking under concurrent requests.
- Appointment confirmations and reminders must dispatch via US019 (notifications).
- Calendar sync must use US035 (CalDav) for Radicale integration.
- Scheduling rules (buffer times, advance booking limits) must be configurable via `SYNTEK_SCHEDULING` settings.
