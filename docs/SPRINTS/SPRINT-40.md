# Sprint 40 — Comments, Feedback & Maps UI

**Sprint Goal**: Implement the comment thread UI with reactions and moderation, the survey renderer and NPS widget UI, and the map wrapper with LocationPicker component.

**Total Points**: 11 / 11
**MoSCoW Balance**: Could 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US069](../STORIES/US069.md) | `@syntek/ui-comments` — Comments UI | 3 | Could | US042 ✓, US044 ✓, US040 ✓ |
| [US070](../STORIES/US070.md) | `@syntek/ui-feedback` — Feedback & Survey UI | 3 | Could | US042 ✓, US044 ✓, US067 ✓ |
| [US071](../STORIES/US071.md) | `@syntek/ui-maps` — Maps UI | 5 | Could | US042 ✓, US044 ✓, US065 ✓, US036 ✓ |

## Notes

- All three stories are independent of each other and can be worked in parallel.
- US069 optimistic UI must revert cleanly on error — never leave a ghost comment in the UI.
- US070 NPS widget must not show immediately on page load — implement a configurable delay.
- US071 map API keys (Mapbox/Google) must come from server-side GraphQL config — never exposed in client bundles.
