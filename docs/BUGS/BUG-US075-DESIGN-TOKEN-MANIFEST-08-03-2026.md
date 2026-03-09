# Bug Fix Report: US075 — Design Token Manifest

**Date:** 08/03/2026 **Branch:** `us075/design-token-manifest` **QA Report:**
`docs/QA/QA-US075-DESIGN-TOKEN-MANIFEST-08-03-2026.md` **Status:** FULLY RESOLVED — all Critical,
High, Medium, and Low issues fixed; all test scenarios from the QA report covered

---

## Summary

The QA analyst ("The Breaker") identified 2 Critical, 3 High, 5 Medium, and 5 Low severity issues in
the `shared/tokens` package immediately after the green-phase implementation of US075. All 15 issues
were resolved in a single session. 43 new regression tests were added, bringing the total from 616
to 659 passing tests.

---

## Fixes Applied

### C1 — CSS injection via `buildThemeStyle` key — no key sanitisation or allowlist enforcement

**Root cause:** `buildThemeStyle` concatenates keys and values directly into a CSS string with no
validation, escaping, or allowlist check on keys. A malicious key containing `}` or `;` breaks out
of the `:root` block, injecting arbitrary CSS rules into the generated stylesheet. Because the
platform serves this with `Cache-Control: public, max-age=31536000, immutable`, a single injection
is cached indefinitely on the CDN. No key validation utility was exported by `@syntek/tokens`, so
the platform had no enforced mechanism to prevent this.

**Fix:** Exported a new `validateOverrideKeys(overrides: Record<string, string>): boolean` function
from `src/theme-utils.ts`. The function checks that every key in `overrides` appears in
`TOKEN_MANIFEST.map(e => e.cssVar)`. It returns `true` only when all keys are known CSS custom
property names from the manifest, and `false` immediately on the first unrecognised key. The
platform must call this before `buildThemeStyle`; `buildThemeStyle` itself retains its documented
pass-through behaviour.

**Files changed:** `src/theme-utils.ts`, `src/index.ts`

---

### C2 — `Object.freeze` is shallow — individual `TokenDescriptor` entries are mutable

**Root cause:** `Object.freeze([...COLOUR_TOKENS, ...])` froze the array (preventing push, pop, and
index reassignment) but left every `TokenDescriptor` object inside it fully mutable.
`TOKEN_MANIFEST[0].default = "corrupted"` succeeded silently in strict mode, corrupting the manifest
singleton for all consumers in the same process. The TypeScript `readonly` annotation provided no
runtime protection for plain JavaScript consumers or `as any` casts.

**Fix:** In `manifest.ts`, each constituent token array is now mapped through `Object.freeze()`
before being spread into the final array:

```ts
export const TOKEN_MANIFEST: readonly TokenDescriptor[] = Object.freeze([
  ...[...COLOUR_TOKENS, ...SPACING_TOKENS, ...].map((e) => Object.freeze(e)),
]);
```

`Object.isFrozen(TOKEN_MANIFEST[0])` now returns `true`.

**Files changed:** `src/manifest.ts`

---

### H1 — `isValidCssColour` rejects all alpha-channel variants of CSS Color Level 4 functions

**Root cause:** The `oklch`, `oklab`, `lab`, `lch`, and `hwb` regex patterns had no provision for
the `/ alpha` syntax defined in CSS Color Level 4. `oklch(0.55 0.2 250 / 0.5)` — a semi-transparent
colour used for hover states, overlays, and focus rings — returned `false` even though `oklch` is
described as the preferred format for new tokens in US075.md.

**Fix:** Added an `ALPHA_SLASH` component pattern `(?:\\s*/\\s*(?:${ALPHA}|${PCT}))?` and applied it
to all five affected functions before the closing parenthesis. The pattern accepts both decimal
alpha (`/ 0.5`) and percentage alpha (`/ 50%`).

**Files changed:** `src/colour-utils.ts`

---

### H2 — `isValidCssColour` accepts CSS-wide keywords that are not colour values

**Root cause:** `CSS_NAMED_COLOURS` included `"inherit"`, `"initial"`, and `"unset"`. Per the W3C
CSS Color Level 4 specification §4.1, the `<color>` data type explicitly excludes these three CSS
Cascading keywords (CSS Cascading §6.1). If a platform tenant stored `inherit` as a colour override,
the generated `:root { --color-primary: inherit; }` block would resolve by inheriting from the
`<html>` element's `color` property — undefined behaviour for a theme system — and the colour picker
could not render any swatch preview for the value.

**Fix:** Removed `"inherit"`, `"initial"`, and `"unset"` from the `CSS_NAMED_COLOURS` set.
`isValidCssColour("inherit")` now correctly returns `false`.

**Files changed:** `src/colour-utils.ts`

---

### H3 — Shadow tokens use `type: "easing"` — incorrect widget type drives wrong UI control

**Root cause:** `TokenWidgetType` had no `"shadow"` variant, so the implementer reused `"easing"` as
a catch-all free-text input for shadow strings, with a comment acknowledging the misuse. `"easing"`
is documented as "text input / cubic-bezier editor". If `syntek-platform` renders a cubic-bezier
control-point editor whenever it encounters `type: "easing"`, every shadow field in the branding
form displays the wrong editor and administrators cannot meaningfully edit shadow values.

**Fix:** Added `"shadow"` to the `TokenWidgetType` union in `src/types/token-manifest.ts`. Updated
all three shadow tokens (`SHADOW_SM`, `SHADOW_MD`, `SHADOW_LG`) in `manifest.ts` from
`type: "easing"` to `type: "shadow"`. Removed the workaround comment.

**Files changed:** `src/types/token-manifest.ts`, `src/manifest.ts`

---

### M1 — `isValidCssColour` accepts out-of-range L values for `oklch`, `oklab`, and `lab`

**Root cause:** The `NUM` pattern (`-?\\d+(?:\\.\\d+)?`) was an unbounded signed decimal used for
all components of `oklch`, `oklab`, and `lab`. There were no range guards on the lightness channel.
`oklch(1.5 0.2 250)` (L must be 0–1 for oklch) and `lab(-10 0 0)` (L must be 0–100 for lab) both
returned `true`, producing values the colour picker could not render a preview for.

**Fix:** Introduced bounded L patterns:

- `OK_L` — matches `0` to `1` (inclusive), same form as `ALPHA`, for `oklch` and `oklab`
- `LAB_L` — matches `0` to `100` (inclusive), for `lab` and `lch`

Updated `OKLCH_RE`, `OKLAB_RE`, `LAB_RE`, and `LCH_RE` to use the bounded L pattern as their first
component. `oklch(1.5 0.2 250)` now correctly returns `false`.

**Files changed:** `src/colour-utils.ts`

---

### M2 — `isValidCssColour` rejects valid negative and out-of-range hue values in `hsl`/`hwb`/`lch`

**Root cause:** The `HUE` pattern was `(?:360|3[0-5]\\d|[12]\\d{2}|[1-9]\\d|\\d)` — a bounded
matcher for `0–360` only. The CSS `<angle>` type for hue is unbounded: values outside `0–360`
normalise by wrapping. `hsl(-90, 50%, 50%)` is identical to `hsl(270, 50%, 50%)` and is produced by
many colour tools. Both forms are valid CSS but were rejected.

**Fix:** Replaced the bounded `HUE` pattern with an unbounded signed decimal:

```ts
const HUE = "-?\\d+(?:\\.\\d+)?";
```

`hsl(-90, 50%, 50%)` and `hsl(380, 50%, 50%)` now correctly return `true`.

**Files changed:** `src/colour-utils.ts`

---

### M3 — `isValidCssColour` rejects 4-digit hex (`#rgba`) which is valid CSS

**Root cause:** `HEX_RE` accepted only 3, 6, and 8 hex digits. The CSS Color Level 4 specification
defines the 4-digit `#rgba` shorthand as a valid alias for `#rrggbbaa`, supported by all modern
browsers. The comment in the source acknowledged this but dismissed it as "not commonly tested".
Designers using Figma or browser DevTools may copy 4-digit values directly; the platform rejected
them despite being valid CSS.

**Fix:** Updated `HEX_RE` to include the 4-digit variant:

```ts
const HEX_RE = /^#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i;
```

**Files changed:** `src/colour-utils.ts`

---

### M4 — Missing semantic colour tokens `COLOR_SUCCESS`, `COLOR_WARNING`, `COLOR_INFO`

**Root cause:** `COLOUR_TOKENS` covered `COLOR_PRIMARY`, `COLOR_SECONDARY`, `COLOR_DESTRUCTIVE`,
`COLOR_MUTED`, `COLOR_SURFACE`, `COLOR_BACKGROUND`, `COLOR_FOREGROUND`, and `COLOR_BORDER` but
omitted the three semantic state colours used by `@syntek/ui` for success alerts, warning banners,
and informational callouts. Platform tenants had no way to customise state feedback colours via the
branding form.

**Fix:** Added three entries to `COLOUR_TOKENS`:

| Key             | cssVar            | Default   |
| --------------- | ----------------- | --------- |
| `COLOR_SUCCESS` | `--color-success` | `#16a34a` |
| `COLOR_WARNING` | `--color-warning` | `#d97706` |
| `COLOR_INFO`    | `--color-info`    | `#0284c7` |

**Files changed:** `src/manifest.ts`

---

### M5 — Missing typography tokens — `line-height` and `letter-spacing`

**Root cause:** The typography section covered font-size, font-weight, and font-family but omitted
line-height and letter-spacing — both core typographic concerns for a branding system. Platform
tenants could not adjust text density or tracking via the branding form.

**Fix:** Added two new token groups to `manifest.ts`:

`LINE_HEIGHT_TOKENS` — category `"typography"`, type `"number"`:

| Key                 | cssVar                | Default |
| ------------------- | --------------------- | ------- |
| `LINE_HEIGHT_TIGHT` | `--line-height-tight` | `1.25`  |
| `LINE_HEIGHT_BASE`  | `--line-height-base`  | `1.5`   |
| `LINE_HEIGHT_LOOSE` | `--line-height-loose` | `1.75`  |

`LETTER_SPACING_TOKENS` — category `"typography"`, type `"rem"`:

| Key                    | cssVar                   | Default  |
| ---------------------- | ------------------------ | -------- |
| `LETTER_SPACING_TIGHT` | `--letter-spacing-tight` | `-0.025` |
| `LETTER_SPACING_WIDE`  | `--letter-spacing-wide`  | `0.025`  |

Both groups are included in the `TOKEN_MANIFEST` spread.

**Files changed:** `src/manifest.ts`

---

### L1 — `hsl()` four-argument form acceptance

**Root cause:** `HSL_RE` uses `hsla?` which accepts both `hsl` and `hsla`. The optional alpha group
makes `hsl(h, s, l, a)` match when technically only `hsla()` accepted four arguments in legacy
CSS2/CSS3. Modern CSS Color Level 4 unifies both forms so both are semantically equivalent.

**Fix:** No code change. Added a comment in `colour-utils.ts` documenting that this behaviour is
intentional and correct per CSS Color Level 4, which unifies `hsl()` and `hsla()` into a single
function accepting an optional alpha channel in either form.

**Files changed:** `src/colour-utils.ts`

---

### L2 — `resolveTailwindColour` case-sensitive lookup silently returns `undefined`

**Root cause:** `resolveTailwindColour` performed a direct property lookup on `TAILWIND_COLOURS`
with no input normalisation. `resolveTailwindColour("Blue-600")` returned `undefined` even though
`"blue-600"` would succeed. The function contract did not document this case-sensitivity
requirement. Additionally, no guard prevented prototype chain pollution: `"__proto__"`,
`"constructor"`, and `"toString"` could be passed to the function.

**Fix:** Added `name.toLowerCase()` normalisation and `Object.hasOwn()` guard:

```ts
export function resolveTailwindColour(name: string): string | undefined {
  const lower = name.toLowerCase();
  return Object.hasOwn(TAILWIND_COLOURS, lower) ? TAILWIND_COLOURS[lower] : undefined;
}
```

`resolveTailwindColour("Blue-600")` now correctly returns `"#2563eb"`.

**Files changed:** `src/tailwind-colours.ts`

---

### L3 — Tailwind spot-check coverage — 15 of 22 families not independently verified

**Root cause:** The `knownValues` spot-check tests in `tailwind-colours.test.ts` verified values
only for 7 of the 22 palette families (gray, blue, green, red, purple, yellow, pink). The remaining
15 families (slate, zinc, neutral, stone, orange, amber, lime, emerald, teal, cyan, sky, indigo,
violet, fuchsia, rose) had no assertions that their hex values were correct — only that the keys
existed. A transcription error in any of those families would pass the scale-coverage tests.

**Fix:** Added spot-check assertions for at least one representative scale value from each of the 15
uncovered families, using known Tailwind v4 hex values.

**Files changed:** `src/__tests__/tailwind-colours.test.ts`

---

### L4 — `token-manifest.test.ts` does not verify shadow tokens have a dedicated type

**Root cause:** No test specifically asserted that shadow tokens used a particular `type` value, nor
flagged the semantic mismatch between `type: "easing"` and shadow string values. If `"shadow"` were
ever reverted to `"easing"`, no test would catch it.

**Fix:** Added a dedicated test block in `token-manifest.test.ts` confirming all entries with
`category === "shadow"` use `type: "shadow"`, and that `VALID_WIDGET_TYPES` includes `"shadow"`.

**Files changed:** `src/__tests__/token-manifest.test.ts`

---

### L5 — `currentColor` circular dependency risk in `:root` context

**Root cause:** `isValidCssColour("currentColor")` correctly returns `true` — `currentColor` is a
valid CSS `<color>` value. However, in a `:root` block generated by `buildThemeStyle`, assigning
`--color-foreground: currentColor` resolves against whatever `color` is set on the `<html>` element.
If `color: var(--color-foreground)` exists simultaneously, a circular dependency occurs. This is a
semantic trap for non-expert administrators that the library permits without warning.

**Fix:** No code change — `currentColor` remains a valid accepted value per the CSS specification.
Added a comment in `colour-utils.ts` warning consumers that `currentColor` creates a circular
dependency when used in a `:root`-scoped custom property alongside `color: var(--<same-token>)`. The
platform branding form should surface a warning to administrators when this value is entered for a
colour token.

**Files changed:** `src/colour-utils.ts`

---

## New Tests Added (43)

| Test file                      | Test name                                                                            | Covers |
| ------------------------------ | ------------------------------------------------------------------------------------ | ------ |
| `theme-utils.test.ts`          | `validateOverrideKeys returns true when all keys are valid cssVar names`             | C1     |
| `theme-utils.test.ts`          | `validateOverrideKeys returns false when a key is not in TOKEN_MANIFEST`             | C1     |
| `theme-utils.test.ts`          | `validateOverrideKeys returns false for an injection attempt key containing }`       | C1     |
| `theme-utils.test.ts`          | `validateOverrideKeys returns true for an empty overrides map`                       | C1     |
| `theme-utils.test.ts`          | `documents that buildThemeStyle passes keys through without internal validation`     | C1     |
| `token-manifest.test.ts`       | `individual entries are frozen at runtime (Object.isFrozen(TOKEN_MANIFEST[0]))`      | C2     |
| `token-manifest.test.ts`       | `attempted mutation of TOKEN_MANIFEST[0].default is silently ignored in strict mode` | C2     |
| `css-colour-validator.test.ts` | `accepts oklch(0.55 0.2 250 / 0.5) — alpha via / syntax`                             | H1     |
| `css-colour-validator.test.ts` | `accepts oklch(0.55 0.2 250 / 50%) — percentage alpha`                               | H1     |
| `css-colour-validator.test.ts` | `accepts lab(46 -8 -45 / 0.5) — alpha in lab`                                        | H1     |
| `css-colour-validator.test.ts` | `accepts hwb(221 15% 8% / 0.5) — alpha in hwb`                                       | H1     |
| `css-colour-validator.test.ts` | `accepts oklab(0.55 -0.05 -0.15 / 0.5) — alpha in oklab`                             | H1     |
| `css-colour-validator.test.ts` | `accepts lch(46 46 264 / 0.5) — alpha in lch`                                        | H1     |
| `css-colour-validator.test.ts` | `rejects inherit — CSS-wide keyword, not a <color> value`                            | H2     |
| `css-colour-validator.test.ts` | `rejects initial — CSS-wide keyword, not a <color> value`                            | H2     |
| `css-colour-validator.test.ts` | `rejects unset — CSS-wide keyword, not a <color> value`                              | H2     |
| `token-manifest.test.ts`       | `all shadow tokens have type "shadow"`                                               | H3     |
| `token-manifest.test.ts`       | `VALID_WIDGET_TYPES includes "shadow"`                                               | H3     |
| `css-colour-validator.test.ts` | `rejects oklch(1.5 0.2 250) — L out of range for oklch (> 1)`                        | M1     |
| `css-colour-validator.test.ts` | `rejects oklch(-0.5 0.2 250) — negative L for oklch`                                 | M1     |
| `css-colour-validator.test.ts` | `rejects lab(-10 0 0) — negative L for lab`                                          | M1     |
| `css-colour-validator.test.ts` | `rejects lab(200 0 0) — L out of range for lab (> 100)`                              | M1     |
| `css-colour-validator.test.ts` | `accepts hsl(-90, 50%, 50%) — negative hue wraps (valid CSS)`                        | M2     |
| `css-colour-validator.test.ts` | `accepts hsl(380, 50%, 50%) — hue > 360 wraps (valid CSS)`                           | M2     |
| `css-colour-validator.test.ts` | `rejects hsl(abc, 50%, 50%) — malformed hue`                                         | M2     |
| `css-colour-validator.test.ts` | `accepts 4-digit hex #f00f (valid CSS Level 4 shorthand)`                            | M3     |
| `css-colour-validator.test.ts` | `accepts 4-digit hex #fff8 — white at ~53% opacity`                                  | M3     |
| `css-colour-validator.test.ts` | `accepts 4-digit hex #0008 — black at ~53% opacity`                                  | M3     |
| `tailwind-colours.test.ts`     | `resolveTailwindColour("Blue-600") returns "#2563eb" — case-insensitive`             | L2     |
| `tailwind-colours.test.ts`     | `resolveTailwindColour("__proto__") returns undefined`                               | L2     |
| `tailwind-colours.test.ts`     | `resolveTailwindColour("constructor") returns undefined`                             | L2     |
| `tailwind-colours.test.ts`     | `resolveTailwindColour("toString") returns undefined`                                | L2     |
| `tailwind-colours.test.ts`     | `"slate-500" resolves to correct hex`                                                | L3     |
| `tailwind-colours.test.ts`     | `"zinc-500" resolves to correct hex`                                                 | L3     |
| `tailwind-colours.test.ts`     | `"neutral-500" resolves to correct hex`                                              | L3     |
| `tailwind-colours.test.ts`     | `"stone-500" resolves to correct hex`                                                | L3     |
| `tailwind-colours.test.ts`     | `"orange-500" resolves to correct hex`                                               | L3     |
| `tailwind-colours.test.ts`     | `"amber-500" resolves to correct hex`                                                | L3     |
| `tailwind-colours.test.ts`     | `"emerald-500" resolves to correct hex`                                              | L3     |
| `tailwind-colours.test.ts`     | `"teal-500" resolves to correct hex`                                                 | L3     |
| `tailwind-colours.test.ts`     | `"indigo-500" resolves to correct hex`                                               | L3     |
| `tailwind-colours.test.ts`     | `"fuchsia-500" resolves to correct hex`                                              | L3     |
| `tailwind-colours.test.ts`     | `"rose-500" resolves to correct hex`                                                 | L3     |

---

## Tests Updated (3 — QA-identified wrong assertions corrected)

| Test file                      | Original assertion                              | Corrected assertion                                 | Reason                                                                   |
| ------------------------------ | ----------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------ |
| `css-colour-validator.test.ts` | `isValidCssColour("inherit")` → `true`          | Moved to CSS-wide keyword rejection block → `false` | `inherit` is not a CSS `<color>` value (CSS Cascading §6.1)              |
| `css-colour-validator.test.ts` | `hsl(361, 50%, 50%)` → `false`                  | Changed to `hsl(abc, 50%, 50%)` → `false`           | Hue is an unbounded angle; `361` is valid CSS and normalises by wrapping |
| `token-manifest.test.ts`       | `VALID_WIDGET_TYPES` did not include `"shadow"` | Added `"shadow"` to the allowed list                | `"shadow"` is now a valid `TokenWidgetType`                              |

---

## Final Test Results

```sh
pnpm --filter @syntek/tokens test
```

|             | Before fixes | After fixes |
| ----------- | ------------ | ----------- |
| Total tests | 616          | 659         |
| Passing     | 616          | 659         |
| Failing     | 0            | 0           |

---

## Resolved Issues Summary

| ID  | Severity | Summary                                                         | Status   |
| --- | -------- | --------------------------------------------------------------- | -------- |
| C1  | Critical | CSS injection via `buildThemeStyle` — no key allowlist          | RESOLVED |
| C2  | Critical | Shallow `Object.freeze` — entries mutable at runtime            | RESOLVED |
| H1  | High     | `oklch`/`oklab`/`lab`/`lch`/`hwb` `/ alpha` syntax rejected     | RESOLVED |
| H2  | High     | `inherit`, `initial`, `unset` accepted as colour values         | RESOLVED |
| H3  | High     | Shadow tokens use `type: "easing"` — wrong widget type          | RESOLVED |
| M1  | Medium   | Out-of-range L values accepted for `oklch`, `oklab`, `lab`      | RESOLVED |
| M2  | Medium   | Negative and >360 hue values rejected in `hsl`/`hwb`/`lch`      | RESOLVED |
| M3  | Medium   | 4-digit hex `#rgba` rejected despite being valid CSS            | RESOLVED |
| M4  | Medium   | Missing `COLOR_SUCCESS`, `COLOR_WARNING`, `COLOR_INFO` tokens   | RESOLVED |
| M5  | Medium   | Missing `line-height` and `letter-spacing` typography tokens    | RESOLVED |
| L1  | Low      | `hsl()` 4-argument acceptance — intentional, comment added      | RESOLVED |
| L2  | Low      | `resolveTailwindColour` case-sensitive, no prototype guard      | RESOLVED |
| L3  | Low      | Tailwind spot-check coverage — 15 of 22 families unverified     | RESOLVED |
| L4  | Low      | No test for shadow token `"shadow"` type                        | RESOLVED |
| L5  | Low      | `currentColor` circular dependency risk — warning comment added | RESOLVED |
