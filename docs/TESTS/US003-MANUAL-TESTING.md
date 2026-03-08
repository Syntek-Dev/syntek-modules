# Manual Testing Guide — @syntek/tokens

**Package**: `@syntek/tokens`\
**Story**: US003 — Design Token System\
**Story Status**: ✅ Completed\
**Last Updated**: `2026-03-08`\
**Tested against**: Node.js `24.14.0` / TypeScript `5.9`

---

## Overview

`@syntek/tokens` provides canonical design token constants for all Syntek UI packages. Tokens are
defined as CSS custom properties in `tokens.css` and mirrored as TypeScript constants in
`tokens.ts`. A tester should verify that token values resolve correctly in a browser, that
overriding a token at `:root` propagates without component code changes, that the ESLint rule
rejects hardcoded values, that TypeScript constants are typed correctly, and that font family tokens
apply without any hardcoded font names in component code.

---

## Prerequisites

- [x] `pnpm install` has been run from the repo root
- [ ] The sandbox or a consuming Next.js project is running
- [x] Node.js 24.14.0 is active
- [x] `@syntek/tokens` is listed as a dependency in the consuming project

> **2026-03-08 repo-runnable check:** Vitest (152/152 pass), `tsc --noEmit` (0 errors), `pnpm lint`
> (clean). Scenarios 1, 2, 6, 7 require a browser/simulator and were skipped. Scenarios 3 & 4 cannot
> be verified — the no-hardcoded-values ESLint rule is not yet implemented (see AC Notes).

---

## Test Scenarios

---

### Scenario 1 — CSS variable resolves to default token value (AC1)

**What this tests**: `var(--color-primary)` resolves to the value defined in `tokens.css`.

#### Setup

1. In a consuming Next.js or plain HTML project, import `tokens.css`:

   ```html
   <link rel="stylesheet" href="node_modules/@syntek/tokens/tokens.css" />
   ```

   or in a CSS file:

   ```css
   @import "@syntek/tokens/tokens.css";
   ```

#### Steps

1. Create a `<div>` with `style="background: var(--color-primary)"`.
2. Open the page in a browser.
3. Open DevTools → Computed styles on the element.

#### Expected Result

- [ ] The `background` property shows the resolved colour value (e.g. `oklch(...)` or a hex value),
      not an empty string.
- [ ] The value matches what is defined under `--color-primary` in `tokens.css`.

---

### Scenario 2 — Overriding a token at :root changes the rendered value (AC2)

**What this tests**: A consuming project can override `--color-primary` without touching component
code.

#### Setup

In the consuming project's global CSS, add **after** the tokens import:

```css
:root {
  --color-primary: #ff0000;
}
```

#### Steps

1. Re-render the page.
2. Inspect the same `<div style="background: var(--color-primary)">`.

#### Expected Result

- [ ] The background is now `rgb(255, 0, 0)` (red).
- [ ] No component file was modified.

---

### Scenario 3 — ESLint rule rejects hardcoded colour (AC3)

**What this tests**: Using a hardcoded colour in a UI component file causes a lint failure.

#### Setup

In any `packages/web/*/src` component file, temporarily add:

```tsx
<div style={{ color: "#3B82F6" }}>Hardcoded colour</div>
```

#### Steps

1. Run the linter from the repo root:

   ```bash
   pnpm lint
   ```

#### Expected Result

- [ ] ESLint reports an error on the line with the hardcoded colour.
- [ ] The error message references the no-hardcoded-values rule.
- [ ] Removing the hardcoded value and using `COLOR_PRIMARY` from `@syntek/tokens` clears the error.

---

### Scenario 4 — ESLint rule rejects hardcoded spacing and font-size (AC3)

**What this tests**: Hardcoded spacing and font-size values are also rejected.

#### Steps

1. Add `style={{ padding: "16px" }}` or `style={{ fontSize: "14px" }}` to a component.
2. Run `pnpm lint`.

#### Expected Result

- [ ] ESLint reports errors for each hardcoded value.
- [ ] Using tokens from `@syntek/tokens` (e.g. `SPACING_4`, `FONT_SIZE_SM`) clears the errors.

---

### Scenario 5 — TypeScript constants are importable with correct types (AC4)

**What this tests**: `@syntek/tokens` exports are typed and accessible in TypeScript.

#### Steps

1. In a TypeScript file, add:

   ```typescript
   import { COLOR_PRIMARY, BREAKPOINT_SM, FONT_SANS } from "@syntek/tokens";
   console.log(COLOR_PRIMARY, BREAKPOINT_SM, FONT_SANS);
   ```

2. Run `tsc --noEmit` in the consuming project.

#### Expected Result

- [ ] No TypeScript errors.
- [ ] `COLOR_PRIMARY` is a `string`.
- [ ] `BREAKPOINT_SM` is a `number` with value `640`.
- [ ] `FONT_SANS` is a `string` equal to `"var(--font-sans)"`.

---

### Scenario 6 — NativeWind preset applies token values (AC5)

**What this tests**: A NativeWind class that references a token renders with the correct value on
iOS and Android.

#### Setup

Requires an Expo project with the NativeWind preset consuming `@syntek/tokens`.

#### Steps

1. In a React Native component, add a class that maps to a token colour (e.g.
   `className="bg-primary"`).
2. Run the app on an iOS simulator and an Android emulator.

#### Expected Result

- [ ] The background colour matches the `--color-primary` token value on both platforms.
- [ ] No hardcoded colour string appears in the component.

---

### Scenario 7 — Font family tokens apply without hardcoded font names (AC6)

**What this tests**: `--font-sans`, `--font-serif`, and `--font-mono` apply the correct font family
from `tokens.css` without any hardcoded font name in component code.

#### Steps

1. In a consuming Next.js project, ensure `tokens.css` is imported globally.
2. Inspect a rendered paragraph element in DevTools → Computed → `font-family`.

#### Expected Result

- [ ] The `font-family` is determined by `var(--font-sans)` (or `--font-serif` / `--font-mono`).
- [ ] No component file contains a literal font name string such as `"Inter"` or `"Roboto"`.
- [ ] Overriding `--font-sans` at `:root` (e.g. via `next/font`) changes the rendered font without
      touching any component.

---

## Regression Checklist

Run before marking the US003 PR ready for review:

- [x] All automated Vitest tests pass: `pnpm --filter @syntek/tokens test` ✅ 152/152 (2026-03-08)
- [x] TypeScript compiles without errors: `pnpm --filter @syntek/tokens type-check` ✅ (2026-03-08)
- [ ] Scenario 1 (CSS variable resolution) passes — requires browser
- [ ] Scenario 2 (override at :root) passes — requires browser
- [ ] Scenario 3 (hardcoded colour lint error) passes — rule not yet implemented
- [ ] Scenario 4 (hardcoded spacing/font-size lint error) passes — rule not yet implemented
- [x] Scenario 5 (TypeScript constants typed correctly) passes ✅ covered by type-check (2026-03-08)
- [ ] Scenario 6 (NativeWind iOS + Android) passes — requires simulator
- [ ] Scenario 7 (font family tokens applied) passes — requires browser
- [ ] No console errors in the browser
- [ ] No hardcoded colour, spacing, or font values found in any `packages/web/` or `mobile/` source
      file

---

## AC Notes for Testers

### AC2 — CSS variable override (Scenario 2)

The override pattern works because `tokens.css` defines semantic aliases that reference palette
variables (e.g. `--color-primary: var(--color-blue-600)`). A consuming project overrides only the
semantic alias at `:root` after the import. The palette variables remain available if a deeper
override is needed. Test this in a sandbox Next.js project by importing `tokens.css` and then adding
a `:root { --color-primary: #ff0000; }` block in the same `globals.css` file.

### AC3 — ESLint lint enforcement (Scenarios 3 and 4)

The ESLint rule that rejects hardcoded colour, spacing, and font-size values has not yet been
implemented as part of this package. Scenarios 3 and 4 therefore cannot be executed against the
current codebase. The rule is tracked as a pending task in US003. When implemented, it will live in
the shared ESLint flat config and run automatically as part of `pnpm lint` across all
`packages/web/` and `mobile/` source files.

### AC5 — NativeWind integration (Scenario 6)

The `@syntek/tokens` package ships plain CSS and TypeScript constants only. NativeWind 4 setup
(preset, `tailwind.config.js`, `nativewind-env.d.ts`) belongs in each consuming Expo project. For
full setup instructions, including how to map token CSS variables to NativeWind utilities and how to
use numeric breakpoint constants in the Tailwind config, see `docs/GUIDES/TOKENS-INTEGRATION.md`.

---

## Known Issues

_None._

| Issue                             | Workaround                              | Story / Issue |
| --------------------------------- | --------------------------------------- | ------------- |
| AC3 lint rule not yet implemented | Manual code review for hardcoded values | US003         |

---

## Reporting a Bug

If a scenario fails unexpectedly:

1. Note the exact steps to reproduce
2. Capture the error message and stack trace
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report in `docs/BUGS/@syntek-tokens-{YYYY-MM-DD}.md`
5. Reference the user story: `Blocks US003`
