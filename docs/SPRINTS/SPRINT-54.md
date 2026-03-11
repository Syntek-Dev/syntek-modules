# Sprint 54 — Feature Flag UI

**Sprint Goal**: Implement the React feature flag package with `useFlag` and `useFlags` hooks,
`FlagGate` conditional render component, `FlagsAdmin` panel for tenant admin flag management, and
`FlagBadge` debug component — completing the cross-stack feature flag story alongside `syntek-flags`
(US017) and `@syntek/ui-settings` (US055).

**Total Points**: 5 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                        | Points | MoSCoW | Dependencies Met                   |
| ---------------------------- | -------------------------------------------- | ------ | ------ | ---------------------------------- |
| [US085](../STORIES/US085.md) | `@syntek/ui-flags` — Feature Flag UI Package | 5      | Should | US017 ✓, US042 ✓, US043 ✓, US044 ✓ |

## Notes

- This sprint is intentionally focused — US085 completes the cross-stack feature flag story.
- **US085** wires to the `flagStatus`, `featureFlags`, `updateFlag`, `resetFlag`, and
  `setUserFlagOverride` GraphQL operations provided by `syntek-flags` (US017).
- `useFlags([...names])` batches all flag evaluations into a single GraphQL query — no N+1 calls.
- `FlagGate` never throws for unknown flags — it renders null/fallback and emits a console warning
  in development, mirroring the backend `is_enabled` contract.
- `FlagsAdmin` requires `manage_flags` permission (enforced at the GraphQL resolver). The component
  surfaces `PermissionDenied` as an error state, not a crash.
- `FlagBadge` is a debug/admin-only component — it exposes the flag name visually and must not be
  used in customer-facing UIs.
- This sprint can begin as soon as Sprint 13 (US017) and Sprints 36/37 (US042, US044) are complete.
