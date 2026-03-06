# Sprint 37 — Payments UI & Search UI

**Sprint Goal**: Implement the Stripe Elements payments UI package with checkout and subscription management, and the search bar, facets, and autocomplete UI package.

**Total Points**: 10 / 11
**MoSCoW Balance**: Must 60% / Should 40%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US052](../STORIES/US052.md) | `@syntek/ui-payments` — Payments UI | 5 | Must | US042 ✓, US044 ✓, US025 ✓ |
| [US053](../STORIES/US053.md) | `@syntek/ui-search` — Search UI | 5 | Should | US042 ✓, US045 ✓, US022 ✓ |

## Notes

- US052 and US053 are independent of each other and can be worked in parallel.
- US052 card input must use Stripe Elements — card numbers must never touch the application's own DOM or network.
- US053 search must debounce user input and show a loading skeleton during queries — never blank out results between keystrokes.
