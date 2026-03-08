# Test Status — @syntek/tokens (US075)

**Package**: `@syntek/tokens` (`shared/tokens/`)\
**Last Run**: `2026-03-08T21:45:00Z`\
**Run by**: Vitest 3.2.4 (green phase — full implementation)\
**Overall Result**: `PASS` — 659 tests passed, 0 failed\
**Coverage**: 100% lines/statements across all source files

---

## Summary

| Suite       | Tests   | Passed  | Failed | Skipped |
| ----------- | ------- | ------- | ------ | ------- |
| Unit        | 659     | 659     | 0      | 0       |
| Integration | 0       | 0       | 0      | 0       |
| E2E         | 0       | 0       | 0      | 0       |
| **Total**   | **659** | **659** | **0**  | **0**   |

Test suite breakdown:

| File                           | Tests | Result  |
| ------------------------------ | ----- | ------- |
| `token-manifest.test.ts`       | 110   | ✅ PASS |
| `tailwind-colours.test.ts`     | 317   | ✅ PASS |
| `css-colour-validator.test.ts` | 66    | ✅ PASS |
| `token-exports.test.ts`        | 62    | ✅ PASS |
| `token-values.test.ts`         | 63    | ✅ PASS |
| `token-types.test.ts`          | 27    | ✅ PASS |
| `theme-utils.test.ts`          | 14    | ✅ PASS |

---

## Unit Tests

### TOKEN_MANIFEST structural invariants

- [x] `is exported as an array` — TOKEN_MANIFEST is an Array instance
- [x] `has at least one entry` — manifest contains all token categories
- [x] `every entry has a non-empty string key`
- [x] `every entry cssVar starts with '--'`
- [x] `every entry category is a valid TokenCategory`
- [x] `every entry type is a valid TokenWidgetType`
- [x] `every entry default is a string or number`
- [x] `every entry label is a non-empty string`
- [x] `all keys are unique`
- [x] `all cssVar names are unique`

### Colour token entries

- [x] `there is at least one colour token` — 11 colour tokens present
- [x] `all colour tokens have type "color"`
- [x] `all colour token defaults are hex strings`
- [x] `has entry for COLOR_PRIMARY`
- [x] `COLOR_PRIMARY has cssVar "--color-primary"`
- [x] `COLOR_PRIMARY has type "color"`
- [x] `COLOR_PRIMARY default is "#2563eb"`
- [x] _(same for COLOR_SECONDARY, COLOR_DESTRUCTIVE, COLOR_MUTED, COLOR_SURFACE, COLOR_BACKGROUND,
      COLOR_FOREGROUND, COLOR_BORDER)_

### Spacing token entries

- [x] `there is at least one spacing token` — 13 spacing tokens present
- [x] `all spacing tokens have type "px"`
- [x] `all spacing token defaults are numbers`
- [x] `SPACING_1 entry: cssVar "--spacing-1", default 4`
- [x] _(same for SPACING_2, SPACING_4, SPACING_8, SPACING_16)_

### Font-size token entries

- [x] `there is at least one font-size token` — 9 font-size tokens present
- [x] `FONT_SIZE_XS entry: cssVar "--font-size-xs", default 0.75`
- [x] _(same for FONT_SIZE_SM, FONT_SIZE_BASE, FONT_SIZE_LG)_

### Font-weight token entries

- [x] `there is at least one font-weight token` — 5 font-weight tokens present
- [x] `FONT_WEIGHT_LIGHT default is 300`
- [x] `FONT_WEIGHT_NORMAL default is 400`
- [x] `FONT_WEIGHT_BOLD default is 700`

### Font-family token entries

- [x] `there is at least one font-family token` — 3 font-family tokens present
- [x] `FONT_SANS entry: cssVar "--font-sans", type "font-family"`
- [x] `FONT_SERIF and FONT_MONO entries`

### Z-index token entries

- [x] `there is at least one z-index token` — 7 z-index tokens present
- [x] `Z_BASE default is 0`
- [x] `Z_MODAL default is 1300`
- [x] `Z_TOOLTIP default is 1500`

### Transition token entries

- [x] `there is at least one duration token` — 3 duration tokens present
- [x] `TRANSITION_DURATION_FAST default is 150`
- [x] `TRANSITION_DURATION_BASE default is 200`
- [x] `TRANSITION_DURATION_SLOW default is 300`
- [x] `there is at least one easing token` — 3 easing tokens present
- [x] `TRANSITION_EASING_DEFAULT default is cubic-bezier(0.4, 0, 0.2, 1)`

### Category coverage

- [x] `contains at least one "colour" token`
- [x] `contains at least one "spacing" token`
- [x] `contains at least one "typography" token`
- [x] `contains at least one "radius" token`
- [x] `contains at least one "z-index" token`
- [x] `contains at least one "transition" token`

### TOKEN_MANIFEST immutability

- [x] `is frozen at runtime` — `Object.freeze()` applied at module level; each entry individually
      frozen
- [x] `returns the same reference on repeated imports` — ESM module cache

---

### TAILWIND_COLOURS structure

- [x] `is exported and is an object`
- [x] `is non-empty` — 246 entries
- [x] `has at least 242 entries` — 246 entries present (exceeds minimum)
- [x] `all values are hex strings`

### TAILWIND_COLOURS family coverage (22 families × 11 scales)

- [x] `contains entries for "slate" family`
- [x] `contains entries for "blue" family`
- [x] _(all 22 family tests pass)_

### TAILWIND_COLOURS scale coverage

- [x] `has "blue-600"`
- [x] _(all 242+ scale tests pass)_

### TAILWIND_COLOURS known values

- [x] `"blue-600" resolves to "#2563eb"`
- [x] `"gray-500" resolves to "#6b7280"`
- [x] _(all known value tests pass)_

### resolveTailwindColour

- [x] `resolves "blue-600" to "#2563eb"`
- [x] `resolves "gray-500" to "#6b7280"`
- [x] `returns undefined for unknown name`
- [x] `returns undefined for empty string`
- [x] `returns undefined for bare CSS colour`
- [x] `all family-scale combos return a hex string`

---

### isValidCssColour — valid formats

- [x] `accepts #rrggbb`
- [x] `accepts #rgb`
- [x] `accepts #rrggbbaa`
- [x] `accepts rgb()`
- [x] `accepts rgba()`
- [x] `accepts hsl()`
- [x] `accepts hsla()`
- [x] `accepts hwb()`
- [x] `accepts lab()`
- [x] `accepts lch()`
- [x] `accepts oklab()`
- [x] `accepts oklch()`
- [x] `accepts named colours (white, transparent, cornflowerblue …)`

### isValidCssColour — invalid values

- [x] `rejects empty string`
- [x] `rejects "blue-600"`
- [x] `rejects "#xyz"`
- [x] `rejects "not-a-colour"`
- [x] `rejects "42"`
- [x] `rejects "var(--color-primary)"`
- [x] `rejects malformed rgb`
- [x] `rejects malformed hsl`

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

None. All tests pass in the green phase.

| Test group | Failure reason | Story |
| ---------- | -------------- | ----- |
| —          | —              | —     |

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
  `token-types.test.ts`) passed without regression — confirmed in the Turbo test log.
- `tsc --noEmit` exits 0 — no type errors across the package.
- 100% line and statement coverage confirmed in `coverage/coverage-summary.json`.
- `TOKEN_MANIFEST` is frozen at module level using `Object.freeze()` applied to both the outer array
  and each individual `TokenDescriptor` entry.
- `TAILWIND_COLOURS` has 246 entries (22 families × 11 scales = 242 required; 4 additional entries
  account for extra scale variants).
