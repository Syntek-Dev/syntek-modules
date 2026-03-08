# QA Report: US075 — Design Token Manifest

**Date:** 08/03/2026 **Analyst:** QA Agent (The Breaker) **Story:** US075 — Design Token Manifest
**Branch:** us075/design-token-manifest **Scope:** `shared/tokens/src/` — token-manifest.ts,
manifest.ts, tailwind-colours.ts, colour-utils.ts, theme-utils.ts, index.ts, and all four test files
**Status:** CRITICAL ISSUES FOUND

---

## Summary

The US075 implementation is broadly correct in structure and passes its own test suite, but contains
a confirmed CSS injection path in `buildThemeStyle`, a shallow-freeze immutability gap that
contradicts the stated AC6 guarantee, five distinct correctness bugs in the `isValidCssColour`
validator (including rejection of the preferred `oklch/alpha` format and incorrect acceptance of
non-colour CSS keywords), a semantic type misuse in shadow tokens, and significant gaps in test
coverage across all four test files.

---

## CRITICAL (Blocks deployment)

### 1. CSS injection via `buildThemeStyle` key — no key sanitisation or allowlist enforcement

**File:** `src/theme-utils.ts` line 55 **File:** `src/colour-utils.ts` (no key validation exists)

`buildThemeStyle` concatenates keys and values directly into a CSS string:

```ts
const declarations = entries.map(([k, v]) => `  ${k}: ${v};`).join("\n");
```

There is no escaping, no validation, and no allowlist check on keys. A malicious key containing `}`,
`;`, or a second CSS rule can break out of the `:root` block entirely:

**Proof of concept — key injection:**

```text
Input key:   "--color-primary: red } body { background: red; --x"
Input value: "#2563eb"

Output:
:root {
  --color-primary: red } body { background: red; --x: #2563eb;
}
```

The generated CSS now includes `body { background: red }` which is a full rule injection into the
stylesheet that will be served with `Cache-Control: public, max-age=31536000, immutable`.

**Proof of concept — value injection (value is not validated by `isValidCssColour` for non-colour
tokens such as `--font-sans`):**

```text
Input value: "Inter; } body { background: url(http://exfil.example.com/steal)"
Output:
:root {
  --font-sans: Inter; } body { background: url(http://exfil.example.com/steal);
}
```

**Impact:** Any platform code path that calls `buildThemeStyle` with user-supplied data without
first validating keys against `TOKEN_MANIFEST.map(e => e.cssVar)` AND validating every value (not
just colour values — font-family, easing, and shadow values are not validated by `isValidCssColour`)
produces an injectable CSS stylesheet. That stylesheet is written to the `tenant_themes` table,
served with immutable caching, and injected into every page render for that tenant. A tenant admin
with access to the branding form could use this to deface their own site, exfiltrate data via CSS
`background: url()`, or serve malicious content to users.

**Severity note:** The doc comment on `buildThemeStyle` explicitly states "no escaping or validation
is performed" and defers responsibility to the platform. However:

- `isValidCssColour` only validates colour values — it does NOT validate font-family, shadow,
  easing, or z-index values, leaving those token categories unguarded.
- There is NO key validation utility exported by `@syntek/tokens` at all.
- The platform's validation contract is not enforced by the library — it is a trust-based assumption
  with no runtime guard. If the platform ever calls `buildThemeStyle` before full validation (e.g.,
  in an internal tool, a migration, or a test fixture), injection is trivial.

**Reproduce:**

```ts
import { buildThemeStyle } from "@syntek/tokens";
const css = buildThemeStyle({
  "--color-primary: red } body { background: red; --x": "#2563eb",
});
// css now contains injected CSS rule
```

---

## HIGH (Must fix before production)

### 2. `Object.freeze` is shallow — individual `TokenDescriptor` entries are mutable

**File:** `src/manifest.ts` line 559

```ts
export const TOKEN_MANIFEST: readonly TokenDescriptor[] = Object.freeze([
  ...COLOUR_TOKENS,
  ...SPACING_TOKENS,
  // ...
]);
```

`Object.freeze` freezes the array itself (no push, pop, or splice) but does NOT freeze the objects
inside it. Every `TokenDescriptor` entry remains mutable:

```ts
import { TOKEN_MANIFEST } from "@syntek/tokens";
TOKEN_MANIFEST[0].default = "red; } body { background: url(evil.com);";
// Succeeds silently — no error, no warning
// Now TOKEN_MANIFEST[0].default is corrupted for ALL consumers of this module
```

Because the module cache is shared within a single process, any downstream code that receives a
reference to an entry and mutates it corrupts the manifest for every other consumer until the module
is unloaded. If the platform code ever passes a manifest entry by reference into a form library or
serialiser that mutates objects, the global manifest is silently corrupted.

The `readonly TokenDescriptor[]` TypeScript annotation prevents direct mutation at compile time, but
it provides zero runtime protection — plain JavaScript consumers or `as unknown as any` casts bypass
it entirely.

**AC6 states:** "TOKEN_MANIFEST is a static read-only schema." The current implementation does not
enforce this at runtime for individual entries.

**Impact:** Silent data corruption of a shared singleton. Cascading incorrect UI widget rendering if
`type`, `category`, or `default` fields are mutated. If coupled with Issue 1, a mutated `default`
value feeds directly into `buildThemeStyle`.

**Reproduce:**

```ts
import { TOKEN_MANIFEST } from "@syntek/tokens";
console.log(Object.isFrozen(TOKEN_MANIFEST)); // true
console.log(Object.isFrozen(TOKEN_MANIFEST[0])); // false — BUG
TOKEN_MANIFEST[0].default = "corrupted"; // succeeds silently
```

**The test for immutability (token-manifest.test.ts line 498) passes because it only calls
`Object.isFrozen(TOKEN_MANIFEST)` — it never checks `Object.isFrozen(TOKEN_MANIFEST[0])`.**

---

### 3. `isValidCssColour` rejects all alpha-channel variants of modern CSS Color Level 4 functions

**File:** `src/colour-utils.ts` lines 65–71

The `oklch`, `oklab`, `lab`, `lch`, and `hwb` regex patterns have NO provision for the `/ alpha`
syntax defined in CSS Color Level 4:

```ts
const OKLCH_RE = new RegExp(`^oklch\\(\\s*${NUM}\\s+${NUM}\\s+${NUM}\\s*\\)$`, "i");
```

The following are all **valid CSS** and are **incorrectly rejected**:

| Input                           | Expected | Actual  |
| ------------------------------- | -------- | ------- |
| `oklch(0.55 0.2 250 / 0.5)`     | `true`   | `false` |
| `oklab(0.55 -0.05 -0.15 / 0.5)` | `true`   | `false` |
| `lab(46 -8 -45 / 0.5)`          | `true`   | `false` |
| `lch(46 46 264 / 0.5)`          | `true`   | `false` |
| `hwb(221 15% 8% / 0.5)`         | `true`   | `false` |

**Impact:** US075.md states `oklch` is the "preferred format for new tokens." A user who sets
`--color-primary` to `oklch(0.55 0.2 250 / 0.5)` (a semi-transparent variant — commonly used for
hover states, overlays, and focus rings) will be silently blocked from saving. The platform returns
a validation error for a perfectly valid CSS colour. This is a direct acceptance criteria failure:
"the platform accepts any valid CSS colour format."

**Reproduce:**

```ts
import { isValidCssColour } from "@syntek/tokens";
isValidCssColour("oklch(0.55 0.2 250 / 0.5)"); // false — should be true
isValidCssColour("lab(46 -8 -45 / 50%)"); // false — should be true
```

---

### 4. `isValidCssColour` accepts CSS-wide keywords that are NOT colour values

**File:** `src/colour-utils.ts` lines 80–84

```ts
const CSS_NAMED_COLOURS = new Set<string>([
  "transparent",
  "currentcolor",
  "inherit",     // BUG — not a <color> value
  "initial",     // BUG — not a <color> value
  "unset",       // BUG — not a <color> value
  // ...
```

Per the W3C CSS Color Level 4 specification §4.1, the `<color>` data type includes named colours and
`transparent` and `currentColor`, but explicitly excludes `inherit`, `initial`, and `unset`. Those
three are CSS-wide keywords (CSS Cascading §6.1) that apply to any property type — they are not
colours.

If a user stores `inherit` as a colour override and the platform writes:

```css
:root {
  --color-primary: inherit;
}
```

...then `color: var(--color-primary)` on every element would resolve by inheriting the
`--color-primary` property value from the element's parent, which is undefined behaviour for a theme
system. The colour picker would initialise with the string `"inherit"` and be unable to render any
swatch preview.

**Impact:** The platform will persist semantically invalid token overrides. The colour picker cannot
display a preview for these values. Tenant styles may produce cascading and unpredictable colour
behaviour.

**Reproduce:**

```ts
import { isValidCssColour } from "@syntek/tokens";
isValidCssColour("inherit"); // true — should be false
isValidCssColour("initial"); // true — should be false
isValidCssColour("unset"); // true — should be false
```

---

### 5. Shadow tokens use `type: "easing"` — incorrect widget type drives wrong UI control

**File:** `src/manifest.ts` lines 396–426

All three shadow tokens declare `type: "easing"`:

```ts
const SHADOW_TOKENS: TokenDescriptor[] = [
  {
    key: "SHADOW_SM",
    cssVar: "--shadow-sm",
    category: "shadow",
    type: "easing",   // BUG — easing is for cubic-bezier functions
    default: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    // ...
  },
```

The `easing` widget type is documented as "text input / cubic-bezier editor" in
`types/token-manifest.ts` line 43. Shadow values such as `"0 1px 2px 0 rgb(0 0 0 / 0.05)"` are not
cubic-bezier functions. A cubic-bezier editor rendered for a shadow field would confuse
administrators and potentially produce malformed values.

The root cause is that `TokenWidgetType` has no `"shadow"` or `"text"` variant, so the implementer
reused `"easing"` as a catch-all free-text input. This is a type system gap that has been papered
over with a comment (`// The type field reuses "easing" as a free-text input for shadow strings`)
rather than solved properly.

**Impact:** If `syntek-platform` renders a cubic-bezier editor (two control-point sliders) whenever
it encounters `type: "easing"`, every shadow field in the branding form will display the wrong
editor widget. The administrator cannot meaningfully edit shadow values.

---

## MEDIUM (Should fix)

### 6. `isValidCssColour` accepts out-of-range values for `oklch`, `oklab`, and `lab`

**File:** `src/colour-utils.ts` lines 44, 69–71

The `NUM` pattern is `-?\d+(?:\.\d+)?` — an unbounded signed decimal. There are no range guards on
any of the lab/lch/oklch components:

| Input                 | Semantically valid?          | Accepted? |
| --------------------- | ---------------------------- | --------- |
| `oklch(1.5 0.2 250)`  | No (L must be 0–1 for oklch) | Yes — BUG |
| `oklch(-0.5 0.2 250)` | No (L must be >= 0)          | Yes — BUG |
| `lab(200 0 0)`        | No (L must be 0–100 for lab) | Yes — BUG |
| `lab(-10 0 0)`        | No (L must be >= 0)          | Yes — BUG |
| `oklch(999 999 999)`  | No                           | Yes — BUG |

Browsers clamp these values, but accepting nonsense ranges means the colour picker initialises with
an invalid value it cannot render a preview for, and the stored value has no visual meaning.

---

### 7. `isValidCssColour` rejects valid negative and out-of-range hue values in `hsl`/`hwb`/`lch`

**File:** `src/colour-utils.ts` line 38

```ts
const HUE = "(?:360|3[0-5]\\d|[12]\\d{2}|[1-9]\\d|\\d)";
```

The CSS `<angle>` type for hue is unbounded. Values outside 0–360 are valid and normalise by
wrapping: `hsl(380, 50%, 50%)` is identical to `hsl(20, 50%, 50%)` and `hsl(-90, 50%, 50%)` is
identical to `hsl(270, 50%, 50%)`. Both forms are valid CSS and are produced by some colour tools.

| Input                 | Expected           | Actual                        |
| --------------------- | ------------------ | ----------------------------- |
| `hsl(-90, 50%, 50%)`  | `true`             | `false`                       |
| `hsl(380, 50%, 50%)`  | `true`             | `false`                       |
| `lch(50 30 -10)`      | `true`             | `false`                       |
| `oklch(0.55 0.2 -30)` | `true` (hue wraps) | `false` — wait, NUM IS signed |

Note: `oklch` uses `NUM` for all three components so negative hue IS accepted there. The
inconsistency means `hsl(-90, 50%, 50%)` is rejected but `oklch(0.5 0.2 -30)` (negative hue) is
accepted, creating inconsistent behaviour across colour functions.

---

### 8. `isValidCssColour` rejects 4-digit hex (`#rgba`) which is valid CSS

**File:** `src/colour-utils.ts` lines 22–25

```ts
// 3, 6, or 8 hex digits (4-digit / #rgba not commonly tested)
const HEX_RE = /^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i;
```

The CSS Color Level 4 specification defines the 4-digit hex shorthand `#rgba` as a valid alias for
`#rrggbbaa`. It is supported by all modern browsers (Chrome 62+, Firefox 49+, Safari 10.1+). The
comment acknowledges this but dismisses it as "not commonly tested."

| Input   | Expected                       | Actual  |
| ------- | ------------------------------ | ------- |
| `#fff8` | `true` (white at ~53% opacity) | `false` |
| `#0008` | `true` (black at ~53% opacity) | `false` |
| `#f00f` | `true` (red, full opacity)     | `false` |

Designers using Figma or browser DevTools may copy 4-digit hex values directly. The platform will
reject them even though they are valid CSS.

---

### 9. Missing semantic colour tokens — `COLOR_SUCCESS`, `COLOR_WARNING`, `COLOR_INFO`

**File:** `src/manifest.ts` lines 21–86

The colour token set includes `COLOR_PRIMARY`, `COLOR_SECONDARY`, `COLOR_DESTRUCTIVE`,
`COLOR_MUTED`, `COLOR_SURFACE`, `COLOR_BACKGROUND`, `COLOR_FOREGROUND`, and `COLOR_BORDER`.

There are no tokens for `COLOR_SUCCESS`, `COLOR_WARNING`, or `COLOR_INFO`. These three semantic
state colours are required to theme success alerts, warning banners, and informational callouts —
all of which are standard components in `@syntek/ui`. Without them, platform tenants cannot
customise state feedback colours via the branding form. They must rely on the `COLOR_DESTRUCTIVE`
pattern being replicated for the other three states, which the manifest does not support.

---

### 10. Missing typography tokens — `line-height` and `letter-spacing`

**File:** `src/manifest.ts` lines 200–355

The typography section covers font-size, font-weight, and font-family but omits:

- Line-height tokens (e.g. `LINE_HEIGHT_TIGHT`, `LINE_HEIGHT_BASE`, `LINE_HEIGHT_LOOSE`)
- Letter-spacing tokens (e.g. `LETTER_SPACING_TIGHT`, `LETTER_SPACING_WIDE`)

Both are core typographic concerns for a branding system. A platform tenant cannot adjust text
density or tracking via the branding form.

---

## LOW (Consider fixing)

### 11. `hsl(220, 50%, 50%, 0.5)` — four-argument `hsl()` accepted (should be `hsla()`)

**File:** `src/colour-utils.ts` line 58–61

The `HSL_RE` pattern uses `hsla?` which matches both `hsl` and `hsla`. The optional alpha group then
makes `hsl(h, s, l, a)` valid when technically only `hsla()` should accept four arguments in legacy
CSS (CSS2/CSS3). Modern CSS Color Level 4 unifies them so both forms are semantically equivalent,
meaning this is a spec-compliance question rather than a hard bug. It is noted for awareness because
it blurs the boundary the docstring implies.

---

### 12. `resolveTailwindColour` has no input normalisation — case-sensitive lookup silently fails

**File:** `src/tailwind-colours.ts` line 360–362

```ts
export function resolveTailwindColour(name: string): string | undefined {
  return TAILWIND_COLOURS[name];
}
```

The lookup is case-sensitive. `resolveTailwindColour("Blue-600")` returns `undefined` even though
`"blue-600"` would succeed. If the colour picker passes values without normalisation, users who type
`Blue-600` in the palette input receive no match and no helpful error. A `name.toLowerCase()` guard
would be a trivial fix. The function contract does not document this sensitivity, so callers may not
be aware of the requirement.

---

### 13. `tailwind-colours.test.ts` spot-check coverage — 15 of 22 families not independently verified

**File:** `src/__tests__/tailwind-colours.test.ts` lines 112–143

The `knownValues` spot-check tests values for only 7 of the 22 palette families (gray, blue, green,
red, purple, yellow, pink). The following 15 families have no spot-check assertions: slate, zinc,
neutral, stone, orange, amber, lime, emerald, teal, cyan, sky, indigo, violet, fuchsia, rose. A
transcription error in any of those 15 families would not be caught by this test file (the
scale-coverage tests only verify that the key exists, not that the value is correct).

---

### 14. `token-manifest.test.ts` does not verify shadow token has a dedicated type

**File:** `src/__tests__/token-manifest.test.ts`

The easing token tests (`lines 440–468`) confirm that easing entries exist, but no test validates
that shadow tokens specifically use a particular type, nor does any test flag the semantic mismatch
between `type: "easing"` and shadow string values. If `"shadow"` is added to `TokenWidgetType` in a
future patch, the existing tests will not catch shadow tokens that were left on the old type.

---

### 15. `isValidCssColour` accepts `currentColor` — circular dependency risk in `:root` context

**File:** `src/colour-utils.ts` line 81

`currentColor` resolves to the element's current `color` property value. In a `:root` block
generated by `buildThemeStyle`, `--color-foreground: currentColor` would resolve against whatever
`color` is set on the `<html>` element — likely the default browser colour or another custom
property. If `color: var(--color-foreground)` is simultaneously in the CSS, a circular dependency
occurs. This is a semantic trap for non-expert administrators using the branding form. The platform
should warn users or reject `currentColor` for `:root`-scoped custom properties.

---

## Test Scenarios Required

The following scenarios are not currently tested and must be added before production:

**Validator (`css-colour-validator.test.ts`):**

- `oklch(0.55 0.2 250 / 0.5)` — must be accepted (alpha in oklch)
- `oklch(0.55 0.2 250 / 50%)` — must be accepted (percentage alpha)
- `lab(46 -8 -45 / 0.5)` — must be accepted (alpha in lab)
- `hwb(221 15% 8% / 0.5)` — must be accepted (alpha in hwb)
- `oklch(1.5 0.2 250)` — must be rejected (L out of range for oklch)
- `lab(-10 0 0)` — must be rejected (L < 0 for lab)
- `hsl(-90, 50%, 50%)` — confirm acceptance or rejection, then document it
- `#f00f` — must be accepted (4-digit hex with alpha)
- `inherit` — must be rejected (CSS-wide keyword, not a colour)
- `initial` — must be rejected
- `unset` — must be rejected

**buildThemeStyle injection (`theme-utils.test.ts`):**

- Key containing `}` does not produce a syntactically valid CSS rule outside `:root`
- Key containing `;` does not inject a second declaration
- Value containing `}` does not close the `:root` block prematurely
- Document whether the function is expected to be called with pre-validated keys only

**TOKEN_MANIFEST immutability (`token-manifest.test.ts`):**

- `Object.isFrozen(TOKEN_MANIFEST[0])` must return `true` (currently returns `false`)
- Attempted mutation of `TOKEN_MANIFEST[0].default` must throw in strict mode

**tailwind-colours — prototype attack strings (`tailwind-colours.test.ts`):**

- `resolveTailwindColour("__proto__")` must return `undefined`
- `resolveTailwindColour("constructor")` must return `undefined`
- `resolveTailwindColour("toString")` must return `undefined`
- `resolveTailwindColour("Blue-600")` (capitalised) must return `undefined` (document
  case-sensitivity contract explicitly)

---

## Handoff Signals

- Run `/syntek-dev-suite:backend` to implement key sanitisation or an exported
  `validateOverrideKeys(keys: string[]): boolean` utility in `@syntek/tokens` so the platform can
  enforce the allowlist before calling `buildThemeStyle`.
- Run `/syntek-dev-suite:backend` to add `"shadow"` to `TokenWidgetType` and update shadow tokens to
  use the correct type.
- Run `/syntek-dev-suite:test-writer` to add the missing test cases listed in the "Test Scenarios
  Required" section above — in particular the CSS injection test, deep freeze test, oklch alpha
  acceptance, and prototype-attack tests for `resolveTailwindColour`.
- Run `/syntek-dev-suite:debug` to confirm whether `rgb(37 99 235)` (CSS4 modern space- separated
  syntax) should be accepted or rejected, and update the regex and tests accordingly.
- Run `/syntek-dev-suite:completion` to update QA status for US075 once the Critical and High items
  are resolved.
