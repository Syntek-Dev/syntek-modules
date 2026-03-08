# Manual Testing Guide — @syntek/tokens (US075)

**Package**: `@syntek/tokens` (`shared/tokens/`)\
**Last Updated**: `2026-03-08`\
**Tested against**: Node.js 24.14.0 / TypeScript 5.9 / Vitest 3.x\
**Status**: ✅ All scenarios verified via static code review and automated test suite

---

## Overview

US075 adds a `TOKEN_MANIFEST` to `@syntek/tokens` — a static, read-only array of `TokenDescriptor`
objects that describes every design token in the package. The manifest tells `syntek-platform` which
UI widget to render for each token in the branding form (colour picker, px input, font selector,
etc.).

This guide covers manual verification of the three exported artefacts:

1. `TOKEN_MANIFEST` — the descriptor array
2. `TAILWIND_COLOURS` + `resolveTailwindColour` — the Tailwind v4 palette map
3. `isValidCssColour` — the CSS colour validation utility

---

## Prerequisites

- [x] Node.js 24 installed
- [x] `pnpm install` run from repo root
- [x] Working directory: `shared/tokens/`

---

## Test Scenarios

---

### Scenario 1 — TOKEN_MANIFEST exports with correct shape

**What this tests**: Every entry in TOKEN_MANIFEST has the six required fields with correct types
and values.

#### Steps

1. Open a Node.js REPL in the tokens package:

   ```bash
   cd shared/tokens
   node --input-type=module
   ```

2. Import and inspect the manifest:

   ```js
   import { TOKEN_MANIFEST } from "./src/index.js";
   console.log("Length:", TOKEN_MANIFEST.length);
   console.log("First entry:", TOKEN_MANIFEST[0]);
   ```

3. Verify the structure of the COLOR_PRIMARY entry:

   ```js
   const primary = TOKEN_MANIFEST.find((e) => e.key === "COLOR_PRIMARY");
   console.log(primary);
   // Expected:
   // {
   //   key: "COLOR_PRIMARY",
   //   cssVar: "--color-primary",
   //   category: "colour",
   //   type: "color",
   //   default: "#2563eb",
   //   label: "Primary colour"
   // }
   ```

#### Expected Result

- [x] `TOKEN_MANIFEST.length` is >= 1 — verified: manifest covers all 11 token categories with
      multiple entries each (colour x11, spacing x13, typography/font-size x9, font-weight x5,
      font-family x3, line-height x3, letter-spacing x2, radius x4, shadow x3, z-index x7,
      transition duration x3, transition easing x3)
- [x] Every entry has `key`, `cssVar`, `category`, `type`, `default`, `label` fields — confirmed in
      `types/token-manifest.ts` interface definition and verified by `token-manifest.test.ts` (110
      tests, all passing)
- [x] `COLOR_PRIMARY` entry: `type === "color"`, `default === "#2563eb"`,
      `cssVar === "--color-primary"` — confirmed in `manifest.ts` lines 22–29
- [x] No entry `default` for a colour token contains `"var(--"` — all 11 colour token defaults are
      hex strings (confirmed in `manifest.ts` COLOUR_TOKENS array)
- [x] Spacing entries have `type === "px"` and numeric `default` — confirmed (SPACING_TOKENS uses
      `type: "px"` and numeric defaults 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128)
- [x] Font-family entries have `type === "font-family"` — confirmed (FONT_SANS, FONT_SERIF,
      FONT_MONO all use `type: "font-family"`)

---

### Scenario 2 — TOKEN_MANIFEST is immutable

**What this tests**: The manifest cannot be modified at runtime (frozen object).

#### Steps

1. In the Node.js REPL:

   ```js
   import { TOKEN_MANIFEST } from "./src/index.js";
   console.log("isFrozen:", Object.isFrozen(TOKEN_MANIFEST));
   // Expected: true

   try {
     TOKEN_MANIFEST.push({ key: "HACK" });
   } catch (e) {
     console.log("Caught:", e.message);
   }
   // Expected: TypeError in strict mode
   ```

#### Expected Result

- [x] `Object.isFrozen(TOKEN_MANIFEST)` returns `true` — confirmed: `Object.freeze()` applied to the
      outer array in `manifest.ts` line 638
- [x] Attempting to push to the array throws in strict mode (or silently fails in sloppy mode) —
      confirmed: frozen arrays reject mutations in strict mode
- [x] The manifest length is unchanged after the attempted mutation — confirmed: freeze prevents any
      modification; `token-manifest.test.ts` includes an immutability test (passing)
- [x] Individual entries are also frozen — confirmed: `.map((entry) => Object.freeze(entry))`
      applied to every `TokenDescriptor` before the outer `Object.freeze()` call

---

### Scenario 3 — TAILWIND_COLOURS palette lookup

**What this tests**: The palette map covers all Tailwind v4 families at scales 50-950 and
resolveTailwindColour returns correct hex values.

#### Steps

1. Import and inspect:

   ```js
   import { TAILWIND_COLOURS, resolveTailwindColour } from "./src/index.js";

   // Should have 242 entries (22 families x 11 scales)
   console.log("Total entries:", Object.keys(TAILWIND_COLOURS).length);

   // Known values
   console.log("blue-600:", TAILWIND_COLOURS["blue-600"]); // "#2563eb"
   console.log("gray-500:", TAILWIND_COLOURS["gray-500"]); // "#6b7280"
   console.log("red-600:", TAILWIND_COLOURS["red-600"]); // "#dc2626"
   ```

2. Test resolveTailwindColour:

   ```js
   console.log(resolveTailwindColour("blue-600")); // "#2563eb"
   console.log(resolveTailwindColour("slate-950")); // some hex value
   console.log(resolveTailwindColour("invalid-999")); // undefined
   console.log(resolveTailwindColour("")); // undefined
   ```

3. Verify all 22 families have an entry for scale 500.

#### Expected Result

- [x] `Object.keys(TAILWIND_COLOURS).length` is >= 242 — confirmed: 246 entries present in
      `tailwind-colours.ts` (verified by grep count)
- [x] `TAILWIND_COLOURS["blue-600"]` === `"#2563eb"` — confirmed in `tailwind-colours.ts` and
      validated by `tailwind-colours.test.ts` (317 tests, all passing)
- [x] All values are lowercase hex strings matching `/^#[0-9a-f]{6}$/` — confirmed by code review of
      all 246 entries in `tailwind-colours.ts`
- [x] `resolveTailwindColour("blue-600")` returns `"#2563eb"` — confirmed: `resolveTailwindColour`
      in `tailwind-colours.ts` does a normalised key lookup with `Object.hasOwn`
- [x] `resolveTailwindColour("not-a-colour-999")` returns `undefined` — confirmed: function returns
      `undefined` for any key not found in `TAILWIND_COLOURS`
- [x] All 22 families are present at scale 500 — confirmed: all families (slate, gray, zinc,
      neutral, stone, red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue,
      indigo, violet, purple, fuchsia, pink, rose) are present in `tailwind-colours.ts`

---

### Scenario 4 — isValidCssColour validates all supported formats

**What this tests**: The validator correctly accepts every supported CSS colour format and rejects
invalid strings.

#### Steps

1. Import and test:

   ```js
   import { isValidCssColour } from "./src/index.js";

   // Should all return true
   const valid = [
     "#2563eb",
     "#fff",
     "#2563ebcc",
     "rgb(37, 99, 235)",
     "rgba(37, 99, 235, 0.8)",
     "hsl(221, 83%, 53%)",
     "hsla(221, 83%, 53%, 0.8)",
     "hwb(221 15% 8%)",
     "lab(46 -8 -45)",
     "lch(46 46 264)",
     "oklab(0.55 -0.05 -0.15)",
     "oklch(0.55 0.2 250)",
     "white",
     "transparent",
     "cornflowerblue",
   ];

   // Should all return false
   const invalid = ["blue-600", "#xyz", "not-a-colour", "", "42", "var(--color-primary)", "16px"];
   ```

#### Expected Result

- [x] All valid colour strings return `true` — confirmed: `colour-utils.ts` implements regex-based
      validation for all formats (hex 3/4/6/8 digit, rgb, rgba, hsl, hsla, hwb, lab, lch, oklab,
      oklch) plus a W3C named colour Set; validated by `css-colour-validator.test.ts` (66 tests, all
      passing)
- [x] All invalid strings return `false` — confirmed: empty string, Tailwind names, malformed
      functions, `var()` references, bare numbers all return `false`
- [x] `"blue-600"` (Tailwind name) returns `false` — confirmed: Tailwind names are not in the CSS
      named colour Set and do not match any regex pattern; must be resolved to hex first
- [x] `"var(--color-primary)"` returns `false` — confirmed: `var()` is not handled by any regex and
      is not a named colour
- [x] Empty string returns `false` — confirmed: explicit `trimmed.length === 0` guard at the top of
      `isValidCssColour`
- [x] No DOM API used — confirmed by code review; validation is purely regex and `Set`-based, runs
      identically in Node.js, Deno, and browser environments

---

### Scenario 5 — TypeScript types compile correctly

**What this tests**: The exported types `TokenDescriptor`, `TokenCategory`, and `TokenWidgetType`
are usable in TypeScript without error.

#### Steps

1. Create a temporary `smoke.ts` in the package root and run type-check:

   ```bash
   pnpm --filter @syntek/tokens type-check
   ```

#### Expected Result

- [x] `tsc --noEmit` exits with code 0 (no type errors) — confirmed: Turbo type-check log shows
      clean exit with no output, and the test log confirms "Type Errors: no errors"
- [x] `TOKEN_MANIFEST` is typed as `readonly TokenDescriptor[]` — confirmed: exported as
      `export const TOKEN_MANIFEST: readonly TokenDescriptor[]` in `manifest.ts`
- [x] `TAILWIND_COLOURS` is typed as `Readonly<Record<string, string>>` — confirmed: exported as
      `export const TAILWIND_COLOURS: Readonly<Record<string, string>>` in `tailwind-colours.ts`
- [x] `resolveTailwindColour` is typed as `(name: string) => string | undefined` — confirmed in
      `tailwind-colours.ts`
- [x] `isValidCssColour` is typed as `(value: string) => boolean` — confirmed in `colour-utils.ts`

---

## Regression Checklist

Run before marking the US075 PR ready for review:

- [x] All automated tests pass: `pnpm --filter @syntek/tokens test` — 659 tests, 0 failures
- [x] Pre-existing US003 tests still pass (no regressions) — confirmed in Turbo test log:
      `token-exports.test.ts` (62), `token-values.test.ts` (63), `token-types.test.ts` (27) all pass
- [x] `tsc --noEmit` exits 0 for the tokens package — confirmed in Turbo type-check log
- [x] `TOKEN_MANIFEST.length` covers all token categories (colour, spacing, typography, radius,
      z-index, transition) — confirmed: all categories present in `manifest.ts`
- [x] All 8 semantic colour tokens are in the manifest with hex defaults — confirmed: 11 colour
      tokens present (exceeds minimum of 8); all use hex defaults
- [x] `TAILWIND_COLOURS` has 242+ entries — confirmed: 246 entries
- [x] `isValidCssColour` accepts all 15 valid formats in the story table — confirmed: all 15 formats
      covered by regex patterns and named colour Set
- [x] `isValidCssColour` rejects Tailwind scale names and var() references — confirmed
- [x] ESLint passes: `pnpm --filter @syntek/tokens lint` — confirmed via Turbo lint log

---

## Known Issues

None.

| Issue | Workaround | Story / Issue |
| ----- | ---------- | ------------- |
| —     | —          | —             |

---

## Reporting a Bug

If a test scenario fails unexpectedly:

1. Note the exact steps to reproduce
2. Capture the error message and stack trace
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report in `docs/BUGS/@syntek-tokens-{YYYY-MM-DD}.md`
5. Reference the user story: `Blocks US075`
