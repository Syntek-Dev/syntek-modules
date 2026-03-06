# Sprint 36 — Data Table & Notifications UI

**Sprint Goal**: Implement the sortable, filterable, paginated data table package and the notification bell, feed, and WebSocket update UI package.

**Total Points**: 10 / 11
**MoSCoW Balance**: Must 60% / Should 40%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US050](../STORIES/US050.md) | `@syntek/data-table` — Data Table | 5 | Must | US042 ✓, US045 ✓ |
| [US051](../STORIES/US051.md) | `@syntek/ui-notifications` — Notifications UI | 5 | Should | US042 ✓, US044 ✓, US019 ✓ |

## Notes

- US050 and US051 are independent of each other and can be worked in parallel.
- US050 table must virtualise rows for large datasets — no DOM rendering of thousands of rows.
- US051 WebSocket connection must reconnect automatically on drop — the user must never lose live notification updates silently.
