# Manual Testing Guide — @syntek/tokens (US075)

**Package**: `@syntek/tokens` (`shared/tokens/`)\
**Last Updated**: `2026-03-08`\
**Tested against**: Node.js 24.14.0 / TypeScript 5.9 / Vitest 3.x

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

- [ ] Node.js 24 installed
- [ ] `pnpm install` run from repo root
- [ ] Working directory: `shared/tokens/`

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
   //   label: "Primary colour"   (or similar)
   // }
   ```

#### Expected Result

- [ ] `TOKEN_MANIFEST.length` is ≥ 1 (green phase: should cover all token categories)
- [ ] Every entry has `key`, `cssVar`, `category`, `type`, `default`, `label` fields
- [ ] `COLOR_PRIMARY` entry: `type === "color"`, `default === "#2563eb"`,
      `cssVar === "--color-primary"`
- [ ] No entry `default` for a colour token contains `"var(--"` — all are hex strings
- [ ] Spacing entries have `type === "px"` and numeric `default`
- [ ] Font-family entries have `type === "font-family"`

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

- [ ] `Object.isFrozen(TOKEN_MANIFEST)` returns `true`
- [ ] Attempting to push to the array throws in strict mode (or silently fails in sloppy mode)
- [ ] The manifest length is unchanged after the attempted mutation

---

### Scenario 3 — TAILWIND_COLOURS palette lookup

**What this tests**: The palette map covers all Tailwind v4 families at scales 50–950 and
resolveTailwindColour returns correct hex values.

#### Steps

1. Import and inspect:

   ```js
   import { TAILWIND_COLOURS, resolveTailwindColour } from "./src/index.js";

   // Should have 242 entries (22 families × 11 scales)
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

3. Verify all 22 families have an entry for scale 500:

   ```js
   const families = [
     "slate",
     "gray",
     "zinc",
     "neutral",
     "stone",
     "red",
     "orange",
     "amber",
     "yellow",
     "lime",
     "green",
     "emerald",
     "teal",
     "cyan",
     "sky",
     "blue",
     "indigo",
     "violet",
     "purple",
     "fuchsia",
     "pink",
     "rose",
   ];
   const missing = families.filter((f) => !TAILWIND_COLOURS[`${f}-500`]);
   console.log("Missing families:", missing); // Expected: []
   ```

#### Expected Result

- [ ] `Object.keys(TAILWIND_COLOURS).length` is 242
- [ ] `TAILWIND_COLOURS["blue-600"]` === `"#2563eb"`
- [ ] All values are lowercase hex strings matching `/^#[0-9a-f]{6}$/`
- [ ] `resolveTailwindColour("blue-600")` returns `"#2563eb"`
- [ ] `resolveTailwindColour("not-a-colour-999")` returns `undefined`
- [ ] All 22 families are present at scale 500

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
   console.log(
     "Valid:",
     valid.map((v) => [v, isValidCssColour(v)]),
   );

   // Should all return false
   const invalid = ["blue-600", "#xyz", "not-a-colour", "", "42", "var(--color-primary)", "16px"];
   console.log(
     "Invalid:",
     invalid.map((v) => [v, isValidCssColour(v)]),
   );
   ```

#### Expected Result

- [ ] All valid colour strings return `true`
- [ ] All invalid strings return `false`
- [ ] `"blue-600"` (Tailwind name) returns `false` — must be resolved to hex first
- [ ] `"var(--color-primary)"` returns `false` — CSS variables are not direct colours
- [ ] Empty string returns `false`

---

### Scenario 5 — TypeScript types compile correctly

**What this tests**: The exported types `TokenDescriptor`, `TokenCategory`, and `TokenWidgetType`
are usable in TypeScript without error.

#### Steps

1. Create a temporary `smoke.ts` in the package root:

   ```ts
   import {
     TOKEN_MANIFEST,
     TAILWIND_COLOURS,
     resolveTailwindColour,
     isValidCssColour,
   } from "@syntek/tokens";
   import type { TokenDescriptor, TokenCategory, TokenWidgetType } from "@syntek/tokens";

   // Type-check: TOKEN_MANIFEST is readonly
   const _manifest: readonly TokenDescriptor[] = TOKEN_MANIFEST;

   // Type-check: TokenCategory and TokenWidgetType are string unions
   const _cat: TokenCategory = "colour";
   const _type: TokenWidgetType = "color";

   // Type-check: TAILWIND_COLOURS is a readonly record
   const _hex: string | undefined = TAILWIND_COLOURS["blue-600"];

   // Type-check: utilities have correct signatures
   const _resolved: string | undefined = resolveTailwindColour("blue-600");
   const _valid: boolean = isValidCssColour("#2563eb");

   console.log("Smoke test passed");
   ```

2. Run type-check:

   ```bash
   pnpm --filter @syntek/tokens type-check
   ```

#### Expected Result

- [ ] `tsc --noEmit` exits with code 0 (no type errors)
- [ ] `TOKEN_MANIFEST` is typed as `readonly TokenDescriptor[]`
- [ ] `TAILWIND_COLOURS` is typed as `Readonly<Record<string, string>>`
- [ ] `resolveTailwindColour` is typed as `(name: string) => string | undefined`
- [ ] `isValidCssColour` is typed as `(value: string) => boolean`

---

## Regression Checklist

Run before marking the US075 PR ready for review:

- [ ] All automated tests pass: `pnpm --filter @syntek/tokens test`
- [ ] Pre-existing US003 tests still pass (no regressions)
- [ ] `tsc --noEmit` exits 0 for the tokens package
- [ ] `TOKEN_MANIFEST.length` covers all token categories (colour, spacing, typography, radius,
      z-index, transition)
- [ ] All 8 semantic colour tokens are in the manifest with hex defaults
- [ ] `TAILWIND_COLOURS` has 242 entries
- [ ] `isValidCssColour` accepts all 15 valid formats in the story table
- [ ] `isValidCssColour` rejects Tailwind scale names and var() references
- [ ] ESLint passes: `pnpm --filter @syntek/tokens lint`

---

## Known Issues

_None at time of writing. Update this section if issues are discovered during testing._

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
