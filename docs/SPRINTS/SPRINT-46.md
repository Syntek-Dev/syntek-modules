# Sprint 46 — Scheduling UI & Background Job Progress UI

**Sprint Goal**: Implement the calendar views, availability grid, and booking form UI for the
scheduling module, and the background job progress package for tracking long-running Celery tasks
from the frontend.

**Total Points**: 10 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                           | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------------- | ------ | ------ | ------------------------- |
| [US072](../STORIES/US072.md) | `@syntek/ui-scheduling` — Scheduling UI         | 5      | Should | US042 ✓, US044 ✓, US064 ✓ |
| [US084](../STORIES/US084.md) | `@syntek/ui-tasks` — Background Job Progress UI | 5      | Should | US042 ✓, US044 ✓, US015 ✓ |

## Notes

- US072 and US084 are independent of each other and can be worked in parallel.
- **US072**: Calendar views must be fully keyboard-navigable — date navigation must work without a
  mouse. Availability slots must poll or subscribe (WebSocket) for real-time updates — booking races
  must be handled gracefully.
- **US084**: Polls the `taskStatus(taskId)` GraphQL query from `syntek-tasks` (US015). No WebSocket
  or subscription dependency — polling only. Consumers who need real-time push can layer Django
  Channels subscriptions on top. All components are headless-friendly with design token styling and
  className override support.
- **Parallel opportunity**: Mobile stream (Sprints 42–45) can begin concurrently with this sprint.
