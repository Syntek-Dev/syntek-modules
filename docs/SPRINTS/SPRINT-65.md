# Sprint 65 — Mobile Comments & Feedback

**Sprint Goal**: Implement the mobile comments and discussions package with touch-optimised thread
rendering, reaction controls, and moderation action sheets; and the mobile surveys and feedback
package with the touch-optimised form renderer, NPS BottomSheet widget, and conditional question
logic.

**Total Points**: 10 / 11 **MoSCoW Balance**: Could 100% **Status**: Planned

## Stories

| Story                        | Title                                                 | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------------------- | ------ | ------ | ------------------------- |
| [US119](../STORIES/US119.md) | `@syntek/mobile-comments` — Mobile Comments & Reviews | 5      | Could  | US057 ✓, US044 ✓, US040 ✓ |
| [US120](../STORIES/US120.md) | `@syntek/mobile-feedback` — Mobile Surveys & Feedback | 5      | Could  | US057 ✓, US044 ✓, US067 ✓ |

## Notes

- US119 and US120 are fully independent — no shared components, no shared hooks. Assign one per
  developer and run in parallel.
- Both are Could Have stories that mirror US069 and US070 on the React Native layer.
- US119 long-press action sheet must use `@gorhom/bottom-sheet` — already a peer dependency of
  `@syntek/mobile-ui` (US057). No additional sheet library required.
- US120 `MobileNPSWidget` stores dismissal in AsyncStorage — not sessionStorage, which is not
  available in React Native.
- US120 conditional visibility engine must share the same condition evaluation logic as US067
  server-side and US070 client-side — all three evaluate the same JSON condition schema.
- Maestro E2E coverage is required for both stories before marking complete.
