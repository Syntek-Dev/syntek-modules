# Sprint 33 — Data Hooks & Form Primitives

**Sprint Goal**: Implement the React data fetching hooks library (paginated queries, infinite scroll, mutations) and the headless form primitives package with Zod validation.

**Total Points**: 8 / 11
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US045](../STORIES/US045.md) | `@syntek/data-hooks` — Data Fetching Hooks | 3 | Must | US044 ✓ |
| [US046](../STORIES/US046.md) | `@syntek/forms` — Headless Form Primitives | 5 | Must | US042 ✓ |

## Notes

- US045 and US046 are independent of each other and can be worked in parallel.
- US045 hooks must handle loading, error, and empty states — consumers must never need to write their own fetch state logic.
- US046 form primitives are headless — they provide logic and accessibility, not styles. Styling is applied by consuming the `@syntek/ui` components.
