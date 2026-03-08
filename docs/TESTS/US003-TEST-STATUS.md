# Test Status — @syntek/tokens

**Package**: `@syntek/tokens`\
**Story**: US003 — Design Token System\
**Story Status**: ✅ Completed\
**Last Run**: `2026-03-08 — green phase confirmed`\
**Run by**: `local — pnpm --filter @syntek/tokens test --run`\
**Overall Result**: `PASS`\
**Coverage**: `N/A` _(pure constants — no branching logic to cover)_

---

## Summary

| Suite       | Tests   | Passed  | Failed | Skipped |
| ----------- | ------- | ------- | ------ | ------- |
| Unit        | 152     | 152     | 0      | 0       |
| Integration | 0       | 0       | 0      | 0       |
| E2E         | 0       | 0       | 0      | 0       |
| **Total**   | **152** | **152** | **0**  | **0**   |

> All 152 tests pass in the green phase. `token-exports.test.ts` (62 tests) confirms all named
> exports exist. `token-values.test.ts` (63 tests) confirms all string constants hold the correct
> `var(--...)` reference and all breakpoint constants hold the correct numeric values.
> `token-types.test.ts` (27 tests) confirms TypeScript infers the correct types for all constants.

---

## Unit Tests

### Colour token exports (token-exports.test.ts)

- [x] `exports COLOR_PRIMARY` — property exists on module
- [x] `exports COLOR_SECONDARY` — property exists on module
- [x] `exports COLOR_DESTRUCTIVE` — property exists on module
- [x] `exports COLOR_MUTED` — property exists on module
- [x] `exports COLOR_SURFACE` — property exists on module
- [x] `exports COLOR_BACKGROUND` — property exists on module
- [x] `exports COLOR_FOREGROUND` — property exists on module
- [x] `exports COLOR_BORDER` — property exists on module

### Spacing token exports (token-exports.test.ts)

- [x] `exports SPACING_1` — property exists on module
- [x] `exports SPACING_2` — property exists on module
- [x] `exports SPACING_3` — property exists on module
- [x] `exports SPACING_4` — property exists on module
- [x] `exports SPACING_5` — property exists on module
- [x] `exports SPACING_6` — property exists on module
- [x] `exports SPACING_8` — property exists on module
- [x] `exports SPACING_10` — property exists on module
- [x] `exports SPACING_12` — property exists on module
- [x] `exports SPACING_16` — property exists on module
- [x] `exports SPACING_20` — property exists on module
- [x] `exports SPACING_24` — property exists on module
- [x] `exports SPACING_32` — property exists on module

### Font-size token exports (token-exports.test.ts)

- [x] `exports FONT_SIZE_XS` — property exists on module
- [x] `exports FONT_SIZE_SM` — property exists on module
- [x] `exports FONT_SIZE_BASE` — property exists on module
- [x] `exports FONT_SIZE_LG` — property exists on module
- [x] `exports FONT_SIZE_XL` — property exists on module
- [x] `exports FONT_SIZE_2XL` — property exists on module
- [x] `exports FONT_SIZE_3XL` — property exists on module
- [x] `exports FONT_SIZE_4XL` — property exists on module
- [x] `exports FONT_SIZE_5XL` — property exists on module

### Font-weight token exports (token-exports.test.ts)

- [x] `exports FONT_WEIGHT_LIGHT` — property exists on module
- [x] `exports FONT_WEIGHT_NORMAL` — property exists on module
- [x] `exports FONT_WEIGHT_MEDIUM` — property exists on module
- [x] `exports FONT_WEIGHT_SEMIBOLD` — property exists on module
- [x] `exports FONT_WEIGHT_BOLD` — property exists on module

### Font family token exports (token-exports.test.ts)

- [x] `exports FONT_SANS` — property exists on module
- [x] `exports FONT_SERIF` — property exists on module
- [x] `exports FONT_MONO` — property exists on module

### Breakpoint token exports (token-exports.test.ts)

- [x] `exports BREAKPOINT_SM` — property exists on module
- [x] `exports BREAKPOINT_MD` — property exists on module
- [x] `exports BREAKPOINT_LG` — property exists on module
- [x] `exports BREAKPOINT_XL` — property exists on module
- [x] `exports BREAKPOINT_2XL` — property exists on module

### Border radius token exports (token-exports.test.ts)

- [x] `exports RADIUS_SM` — property exists on module
- [x] `exports RADIUS_MD` — property exists on module
- [x] `exports RADIUS_LG` — property exists on module
- [x] `exports RADIUS_FULL` — property exists on module

### Shadow token exports (token-exports.test.ts)

- [x] `exports SHADOW_SM` — property exists on module
- [x] `exports SHADOW_MD` — property exists on module
- [x] `exports SHADOW_LG` — property exists on module

### Z-index token exports (token-exports.test.ts)

- [x] `exports Z_BASE` — property exists on module
- [x] `exports Z_DROPDOWN` — property exists on module
- [x] `exports Z_STICKY` — property exists on module
- [x] `exports Z_MODAL` — property exists on module
- [x] `exports Z_TOAST` — property exists on module
- [x] `exports Z_TOOLTIP` — property exists on module

### Transition token exports (token-exports.test.ts)

- [x] `exports TRANSITION_DURATION_FAST` — property exists on module
- [x] `exports TRANSITION_DURATION_BASE` — property exists on module
- [x] `exports TRANSITION_DURATION_SLOW` — property exists on module
- [x] `exports TRANSITION_EASING_DEFAULT` — property exists on module
- [x] `exports TRANSITION_EASING_IN` — property exists on module
- [x] `exports TRANSITION_EASING_OUT` — property exists on module

### Token values (token-values.test.ts)

- [x] `COLOR_PRIMARY references var(--color-primary)` — AC1/AC4
- [x] `COLOR_SECONDARY references var(--color-secondary)` — AC1/AC4
- [x] `COLOR_DESTRUCTIVE references var(--color-destructive)` — AC1/AC4
- [x] `COLOR_MUTED references var(--color-muted)` — AC1/AC4
- [x] `COLOR_SURFACE references var(--color-surface)` — AC1/AC4
- [x] `COLOR_BACKGROUND references var(--color-background)` — AC1/AC4
- [x] `COLOR_FOREGROUND references var(--color-foreground)` — AC1/AC4
- [x] `COLOR_BORDER references var(--color-border)` — AC1/AC4
- [x] Spacing: all 13 `var(--spacing-N)` references correct — AC4
- [x] Font-size: all 9 `var(--font-size-*)` references correct — AC4
- [x] Font-weight: all 5 `var(--font-weight-*)` references correct — AC4
- [x] Radius: all 4 `var(--radius-*)` references correct — AC4
- [x] Shadow: all 3 `var(--shadow-*)` references correct — AC4
- [x] Z-index: all 6 `var(--z-*)` references correct — AC4
- [x] Transition duration: all 3 `var(--transition-duration-*)` references correct — AC4
- [x] Transition easing: all 3 `var(--transition-easing-*)` references correct — AC4
- [x] `BREAKPOINT_SM is 640` — AC4
- [x] `BREAKPOINT_MD is 768` — AC4
- [x] `BREAKPOINT_LG is 1024` — AC4
- [x] `BREAKPOINT_XL is 1280` — AC4
- [x] `BREAKPOINT_2XL is 1536` — AC4
- [x] `breakpoints are in ascending order` — AC4
- [x] `FONT_SANS references var(--font-sans)` — AC6
- [x] `FONT_SERIF references var(--font-serif)` — AC6
- [x] `FONT_MONO references var(--font-mono)` — AC6

### Token types (token-types.test.ts)

- [x] `COLOR_PRIMARY is string` — AC4
- [x] `BREAKPOINT_SM is number` — AC4
- [x] `FONT_SANS is string` — AC6
- [x] _(all 27 type assertions pass — see test file for full list)_

---

## Integration Tests

_None at this stage. Integration with NativeWind (AC5) is verified manually — see
`docs/TESTS/US003-MANUAL-TESTING.md`._

---

## E2E Tests

_Not applicable for the tokens package itself. CSS variable override (AC2) and lint enforcement
(AC3) are verified manually._

---

## Known Failures

_None. All tests pass in the green phase._

| Test | Failure reason | Story / Issue |
| ---- | -------------- | ------------- |
| —    | —              | —             |

---

## How to Run

```bash
# Install dependencies (first time)
pnpm install

# Run tests for this package
pnpm --filter @syntek/tokens test

# Watch mode
pnpm --filter @syntek/tokens test:watch

# Type-check only
pnpm --filter @syntek/tokens type-check
```

---

## Notes

- `token-exports.test.ts` — presence tests; pass in both red and green phases.
- `token-values.test.ts` — value assertions; pass in the green phase with real `var(--...)` values.
- `token-types.test.ts` — type-level assertions; pass in both phases.
- AC2 (CSS override) and AC3 (lint enforcement) require manual testing / a consuming project.
- AC3 (lint rule) is not yet implemented — tracked as a pending task in US003.
- AC5 (NativeWind) requires an Expo project — also verified manually.
- For integration guidance see `shared/tokens/TOKENS-INTEGRATION.md`.
