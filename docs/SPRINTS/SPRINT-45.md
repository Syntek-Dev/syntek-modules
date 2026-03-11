# Sprint 45 — Comments & Feedback UI

**Sprint Goal**: Implement the full comments, reviews, and discussions UI package with hooks, thread
rendering, reaction controls, and moderation tools; and the feedback and surveys UI package with the
survey form renderer, admin builder, analytics dashboard, and NPS widget.

**Total Points**: 16 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Could 100% **Status**: Planned

## Stories

| Story                        | Title                                                      | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ---------------------------------------------------------- | ------ | ------ | ------------------------- |
| [US069](../STORIES/US069.md) | `@syntek/ui-comments` — Comments, Reviews & Discussions UI | 8      | Could  | US042 ✓, US044 ✓, US040 ✓ |
| [US070](../STORIES/US070.md) | `@syntek/ui-feedback` — Feedback & Surveys UI              | 8      | Could  | US042 ✓, US044 ✓, US067 ✓ |

## Notes

- US069 and US070 are fully independent — no shared components, no shared hooks. Assign one per
  developer and run in parallel.
- Sprint exceeds capacity at 16 pts. Both stories are Could Have — they can be deferred to a future
  sprint if team velocity requires it, without blocking any Must or Should Have stories.
- US071 (`@syntek/ui-maps` — Maps, Routing & Live Tracking UI) has been moved to Sprint 64 to allow
  US069 and US070 to be properly expanded.
- US069 optimistic UI must revert cleanly on error — never leave a ghost comment in the thread.
- US069 moderation controls are gated on the moderator permission from syntek-permissions (US011) —
  moderator role check must be performed server-side in the GraphQL resolver, not client-only.
- US070 NPS widget must not appear immediately on page load — implement the configurable
  displayDelay and store dismissal in sessionStorage so the widget does not reappear.
- US070 SurveyBuilder drag-and-drop uses @hello-pangea/dnd (same as @syntek/ui-email-builder).
