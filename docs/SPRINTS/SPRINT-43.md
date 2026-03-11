# Sprint 43 — Settings UI

**Sprint Goal**: Implement the full settings UI package including `useSettings` hook,
`TenantSettingsPanel` admin component, `DesignTokensEditor`, and end-user settings pages (profile,
security, billing, notifications).

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                     | Points | MoSCoW | Dependencies Met                            |
| ---------------------------- | ----------------------------------------- | ------ | ------ | ------------------------------------------- |
| [US055](../STORIES/US055.md) | `@syntek/ui-settings` — Settings Pages UI | 8      | Should | US042 ✓, US043 ✓, US044 ✓, US048 ✓, US016 ✓ |

## Notes

- `@syntek/ui-reporting` (US054) was moved to Sprint 60 to bring this sprint within capacity.
- **US055 scope** (8 points): Full settings UI package with four entry points — `useSettings(key)`
  hook for consuming tenant settings in any component; `useTenantSettingsAdmin()` for admin
  read/write; `TenantSettingsPanel` with auto-rendered input types (toggle/number/text/code editor
  per schema type); `DesignTokensEditor` with colour pickers and live preview; and end-user settings
  pages (profile, security, notification preferences, billing).
- `TenantSettingsPanel` renders inputs automatically from the `type` field in `tenantSettings`
  response — consuming projects do not need to build custom settings forms.
- `DesignTokensEditor` renders a disabled placeholder when `DESIGN_TOKENS_ENABLED` is False on the
  backend.
- Settings pages must gate sections behind the appropriate permissions via US011 (RBAC).
- `@syntek/ui-flags` (US085, `useFlag` / `FlagGate` / `FlagsAdmin`) is the feature flags
  counterpart, scheduled in Sprint 54.
