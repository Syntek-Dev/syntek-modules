# Test Status — @syntek/tokens (US075)

**Package**: `@syntek/tokens` (`shared/tokens/`)\
**Last Run**: `2026-03-08T00:00:00Z`\
**Run by**: TDD scaffold (red phase)\
**Overall Result**: `FAIL` (red phase — all new tests expected to fail)\
**Coverage**: pending green phase

---

## Summary

| Suite       | Tests   | Passed | Failed  | Skipped |
| ----------- | ------- | ------ | ------- | ------- |
| Unit        | ~90     | 0      | ~90     | 0       |
| Integration | 0       | 0      | 0       | 0       |
| E2E         | 0       | 0      | 0       | 0       |
| **Total**   | **~90** | **0**  | **~90** | **0**   |

> Exact counts subject to change as stubs are filled in. All tests from prior US003 stories continue
> to pass — only the new US075 tests are in the red phase.

---

## Unit Tests

### TOKEN_MANIFEST structural invariants

- [ ] `is exported as an array` — TOKEN_MANIFEST is an Array instance
- [ ] `has at least one entry` — fails: stub returns `[]`
- [ ] `every entry has a non-empty string key` — vacuously passes with empty array
- [ ] `every entry cssVar starts with '--'` — vacuously passes
- [ ] `every entry category is a valid TokenCategory` — vacuously passes
- [ ] `every entry type is a valid TokenWidgetType` — vacuously passes
- [ ] `every entry default is a string or number` — vacuously passes
- [ ] `every entry label is a non-empty string` — vacuously passes
- [ ] `all keys are unique` — vacuously passes
- [ ] `all cssVar names are unique` — vacuously passes

### Colour token entries

- [ ] `there is at least one colour token` — fails: no entries
- [ ] `all colour tokens have type "color"` — vacuously passes
- [ ] `all colour token defaults are hex strings` — vacuously passes
- [ ] `has entry for COLOR_PRIMARY` — fails: not found
- [ ] `COLOR_PRIMARY has cssVar "--color-primary"` — fails
- [ ] `COLOR_PRIMARY has type "color"` — fails
- [ ] `COLOR_PRIMARY default is "#2563eb"` — fails
- [ ] _(same for COLOR_SECONDARY, COLOR_DESTRUCTIVE, COLOR_MUTED, COLOR_SURFACE, COLOR_BACKGROUND,
      COLOR_FOREGROUND, COLOR_BORDER)_

### Spacing token entries

- [ ] `there is at least one spacing token` — fails
- [ ] `all spacing tokens have type "px"` — vacuously passes
- [ ] `all spacing token defaults are numbers` — vacuously passes
- [ ] `SPACING_1 entry: cssVar "--spacing-1", default 4` — fails
- [ ] _(same for SPACING_2, SPACING_4, SPACING_8, SPACING_16)_

### Font-size token entries

- [ ] `there is at least one font-size token` — fails
- [ ] `FONT_SIZE_XS entry: cssVar "--font-size-xs", default 0.75` — fails
- [ ] _(same for FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_LG)_

### Font-weight token entries

- [ ] `there is at least one font-weight token` — fails
- [ ] `FONT_WEIGHT_LIGHT default is 300` — fails
- [ ] `FONT_WEIGHT_NORMAL default is 400` — fails
- [ ] `FONT_WEIGHT_BOLD default is 700` — fails

### Font-family token entries

- [ ] `there is at least one font-family token` — fails
- [ ] `FONT_SANS entry: cssVar "--font-sans", type "font-family"` — fails
- [ ] `FONT_SERIF and FONT_MONO entries` — fails

### Z-index token entries

- [ ] `there is at least one z-index token` — fails
- [ ] `Z_BASE default is 0` — fails
- [ ] `Z_MODAL default is 1300` — fails
- [ ] `Z_TOOLTIP default is 1500` — fails

### Transition token entries

- [ ] `there is at least one duration token` — fails
- [ ] `TRANSITION_DURATION_FAST default is 150` — fails
- [ ] `TRANSITION_DURATION_BASE default is 200` — fails
- [ ] `TRANSITION_DURATION_SLOW default is 300` — fails
- [ ] `there is at least one easing token` — fails
- [ ] `TRANSITION_EASING_DEFAULT default is cubic-bezier(0.4, 0, 0.2, 1)` — fails

### Category coverage

- [ ] `contains at least one "colour" token` — fails
- [ ] `contains at least one "spacing" token` — fails
- [ ] `contains at least one "typography" token` — fails
- [ ] `contains at least one "radius" token` — fails
- [ ] `contains at least one "z-index" token` — fails
- [ ] `contains at least one "transition" token` — fails

### TOKEN_MANIFEST immutability

- [ ] `is frozen at runtime` — fails: `[]` is not frozen in stub
- [ ] `returns the same reference on repeated imports` — passes (ESM module cache)

---

### TAILWIND_COLOURS structure

- [ ] `is exported and is an object` — passes (stub exports `{}`)
- [ ] `is non-empty` — fails: stub is empty
- [ ] `has at least 242 entries` — fails
- [ ] `all values are hex strings` — vacuously passes

### TAILWIND_COLOURS family coverage (22 families × 11 scales)

- [ ] `contains entries for "slate" family` — fails
- [ ] `contains entries for "blue" family` — fails
- [ ] _(all 22 family tests fail)_

### TAILWIND_COLOURS scale coverage

- [ ] `has "blue-600"` — fails
- [ ] _(all 242 scale tests fail)_

### TAILWIND_COLOURS known values

- [ ] `"blue-600" resolves to "#2563eb"` — fails
- [ ] `"gray-500" resolves to "#6b7280"` — fails
- [ ] _(all known value tests fail)_

### resolveTailwindColour

- [ ] `resolves "blue-600" to "#2563eb"` — fails (returns undefined)
- [ ] `resolves "gray-500" to "#6b7280"` — fails
- [ ] `returns undefined for unknown name` — passes (stub returns undefined)
- [ ] `returns undefined for empty string` — passes
- [ ] `returns undefined for bare CSS colour` — passes
- [ ] `all family-scale combos return a hex string` — fails

---

### isValidCssColour — valid formats

- [ ] `accepts #rrggbb` — fails (stub returns false)
- [ ] `accepts #rgb` — fails
- [ ] `accepts #rrggbbaa` — fails
- [ ] `accepts rgb()` — fails
- [ ] `accepts rgba()` — fails
- [ ] `accepts hsl()` — fails
- [ ] `accepts hsla()` — fails
- [ ] `accepts hwb()` — fails
- [ ] `accepts lab()` — fails
- [ ] `accepts lch()` — fails
- [ ] `accepts oklab()` — fails
- [ ] `accepts oklch()` — fails
- [ ] `accepts named colours (white, transparent, cornflowerblue …)` — fails

### isValidCssColour — invalid values

- [ ] `rejects empty string` — passes (stub returns false)
- [ ] `rejects "blue-600"` — passes
- [ ] `rejects "#xyz"` — passes
- [ ] `rejects "not-a-colour"` — passes
- [ ] `rejects "42"` — passes
- [ ] `rejects "var(--color-primary)"` — passes
- [ ] `rejects malformed rgb` — passes
- [ ] `rejects malformed hsl` — passes

---

## Integration Tests

None for this package — @syntek/tokens is a pure TypeScript constants package with no runtime
dependencies on other services.

---

## E2E Tests

> Not applicable to this package. The platform branding form integration (SSR injection, colour
> picker, reset) will be tested in `syntek-platform`'s own E2E suite.

---

## Known Failures

All failures below are **expected** in the red phase:

| Test group                     | Failure reason                    | Story |
| ------------------------------ | --------------------------------- | ----- |
| TOKEN_MANIFEST coverage        | Stub exports empty array          | US075 |
| TAILWIND_COLOURS lookups       | Stub exports empty object         | US075 |
| isValidCssColour valid formats | Stub always returns false         | US075 |
| TOKEN_MANIFEST frozen          | Empty array literal is not frozen | US075 |

---

## How to Run

```bash
# All tests for @syntek/tokens
pnpm --filter @syntek/tokens test

# Watch mode
pnpm --filter @syntek/tokens test:watch

# With coverage
pnpm --filter @syntek/tokens exec vitest run --coverage
```

---

## Notes

- All pre-existing US003 tests (`token-exports.test.ts`, `token-values.test.ts`,
  `token-types.test.ts`) must remain green throughout US075 work.
- Green phase: implement `TOKEN_MANIFEST`, `TAILWIND_COLOURS`, `resolveTailwindColour`, and
  `isValidCssColour` in the respective source files and ensure `Object.freeze` is applied to
  `TOKEN_MANIFEST` at module level.
- The `TAILWIND_COLOURS` palette data (all 22 families × 11 scales = 242 entries) should be sourced
  from the official Tailwind CSS v4 palette definitions.
