# Sprint 70 — Web & Mobile Error UI

**Sprint Goal**: Implement the web error pages package with branded error screens for all HTTP error
types, ErrorBoundary, Next.js app-router integration, and countdown redirects; and the mobile error
screens package with touch-optimised error screens, offline detection, and ErrorBoundary for React
Native.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                 | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------------------- | ------ | ------ | ------------------------- |
| [US125](../STORIES/US125.md) | `@syntek/ui-error` — Web Error Pages & Error Boundary | 5      | Should | US042 ✓, US043 ✓, US124 ✓ |
| [US126](../STORIES/US126.md) | `@syntek/mobile-error` — Mobile Error Screens         | 3      | Should | US057 ✓, US124 ✓          |

## Notes

- US125 and US126 are fully independent — no shared components, no shared hooks. Assign one per
  developer and run in parallel.
- Both stories depend on US124 (`syntek-error`) completing in Sprint 69 — the error codes and
  correlation ID format defined in the backend must match what the UI packages display.
- **US125**: `ErrorFallback` must render without any React context — it is the last-resort fallback
  and cannot depend on providers that may themselves have errored.
- **US125**: All error pages must work server-side rendered (no client-only APIs in the default
  render path) to ensure they appear correctly even when JavaScript fails to hydrate.
- **US126**: `MobileOfflineScreen` must listen to `@react-native-community/netinfo` and auto-dismiss
  when connectivity is restored — do not require the user to tap Retry manually.
- **US126**: SVG illustrations must be bundled inline — no network fetches permitted in error
  screens, which by definition may render in degraded connectivity conditions.
- Both packages must use design tokens only — no hardcoded colours or spacing values.
