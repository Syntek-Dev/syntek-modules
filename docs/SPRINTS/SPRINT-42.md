# Sprint 42 — Payments UI & Search UI

**Sprint Goal**: Implement the Stripe Elements payments UI package with checkout and subscription
management, and the full site search UI package with hooks-first API, autocomplete, faceted
filtering, configurable result renderer, and command palette.

**Total Points**: 13 / 11 **MoSCoW Balance**: Must 38% / Should 62% **Status**: Planned ⚠️ Over
Capacity

## Stories

| Story                        | Title                               | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------- | ------ | ------ | ------------------------- |
| [US052](../STORIES/US052.md) | `@syntek/ui-payments` — Payments UI | 5      | Must   | US042 ✓, US044 ✓, US025 ✓ |
| [US053](../STORIES/US053.md) | `@syntek/ui-search` — Search UI     | 8      | Should | US042 ✓, US044 ✓, US022 ✓ |

## Notes

- US052 and US053 are fully independent of each other and can be worked in parallel — assign one per
  developer.
- US052 card input must use Stripe Elements — card numbers must never touch the application's own
  DOM or network.
- US053 search must debounce user input and show a loading skeleton during queries — never blank out
  results between keystrokes.
- US053 `useSearch` hook must be fully usable headlessly — consuming projects may bypass all
  provided components and render results in their own UI.
- Sprint exceeds capacity at 13pts due to US053 expanding to a hooks-first API with provider
  context, command palette, and configurable result renderer. Both stories are independent and
  parallelisable; no over-capacity risk if staffed as two concurrent tracks.
