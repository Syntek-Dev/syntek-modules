# Sprint 41 — Scheduling UI

**Sprint Goal**: Implement the calendar views, availability grid, and booking form UI for the scheduling module.

**Total Points**: 5 / 11
**MoSCoW Balance**: Should 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US072](../STORIES/US072.md) | `@syntek/ui-scheduling` — Scheduling UI | 5 | Should | US042 ✓, US044 ✓, US064 ✓ |

## Notes

- This sprint is intentionally light — US072 cannot be combined with adjacent stories without exceeding capacity.
- **Parallel opportunity**: Mobile stream (Sprints 42–45) can begin concurrently with this sprint.
- Calendar views must be fully keyboard-navigable — date navigation must work without a mouse.
- Availability slots must poll or subscribe (WebSocket) for real-time updates — booking races must be handled gracefully.
