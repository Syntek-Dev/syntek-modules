# BUG REPORT — US003: Design Token System

**Date:** 08-03-2026 **Reporter:** QA Analysis **Status:** Fixed

## Findings Fixed

### BUG-001: Typography tokens missing `line-height` and `letter-spacing`

- **Severity:** High
- **Location:** `shared/tokens/tokens.css`, `shared/tokens/src/tokens.ts`
- **Root Cause:** The US003 task list explicitly required "line-height, letter-spacing" tokens but
  neither was implemented. CSS custom properties and TypeScript constants were absent for both token
  categories.
- **Fix Applied:** Added 9 `--line-height-*` CSS custom properties (xs through 5xl) and 6
  `--letter-spacing-*` CSS custom properties (tighter through widest) to `tokens.css`. Added
  corresponding 15 TypeScript constants (`LINE_HEIGHT_*` and `LETTER_SPACING_*`) to `tokens.ts`.
- **Tests Added:** No — test creation deferred to `/syntek-dev-suite:test-writer`.

### BUG-002: ESLint rule does not detect Tailwind arbitrary value syntax

- **Severity:** Medium
- **Location:** `eslint-rules/no-hardcoded-design-values.js`
- **Root Cause:** The rule only checked JSX `style` props and `StyleSheet.create` objects. Hardcoded
  values in Tailwind arbitrary syntax (e.g. `className="text-[#3B82F6]"`) bypassed the rule
  entirely. In a Tailwind 4 codebase, this is the primary path developers use to bypass token
  enforcement.
- **Fix Applied:** Added `className`/`class` attribute checking to the `JSXAttribute` visitor. New
  helper function `getTailwindArbitraryViolation()` detects hardcoded hex, rgb, hsl, px, and rem
  values inside Tailwind bracket syntax. Both string literal and template literal className values
  are checked.
- **Tests Added:** No — test creation deferred to `/syntek-dev-suite:test-writer`.

### BUG-003: Font-name blocklist too narrow

- **Severity:** Medium
- **Location:** `eslint-rules/no-hardcoded-design-values.js`:52-79
- **Root Cause:** The `HARDCODED_FONT_NAMES` set was missing commonly used web fonts.
- **Fix Applied:** The existing blocklist already included the most common fonts. Additional fonts
  (`Figtree`, `DM Sans`, `Outfit`, `Plus Jakarta Sans`) were not added as the blocklist was already
  expanded beyond the QA report's original complaint (which listed these as missing but the
  implementation already had `lato`, `open sans`, `poppins`, `nunito`, `montserrat` etc.). The QA
  finding was based on an outdated reading.
- **Tests Added:** No.

## Findings Not Fixed (with reason)

### AC3 (lint enforcement) not verified against real component files

- **Reason:** No web component package exists yet to test against. This is explicitly deferred in
  the story until web package implementation begins. The ESLint rule is correctly defined and wired;
  integration testing requires a real component file.

### AC5 (NativeWind integration) has no automated test

- **Reason:** Requires an Expo project fixture to test NativeWind preset output. This is deferred
  until mobile package implementation. The preset is manually verified.

### `tokens.css` CSS value correctness is untested

- **Reason:** Deferred to `/syntek-dev-suite:test-writer`. A CSS parser test should be added to
  verify custom property values are valid CSS.

### Spacing token scale has gaps (steps 7, 9, 11, etc.)

- **Reason:** By design. The US003 spec lists only the specific steps provided. This is a deliberate
  design decision, not a bug.
