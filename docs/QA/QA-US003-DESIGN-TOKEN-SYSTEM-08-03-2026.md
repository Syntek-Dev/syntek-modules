# QA Report: US003 — Design Token System

**Date:** 08/03/2026 **Analyst:** QA Agent (The Breaker) **Story:** US003 — Design Token System
**Branch:** main (completed story) **Scope:** `shared/tokens/tokens.css`,
`shared/tokens/src/tokens.ts`, `shared/tokens/src/nativewind.ts`, `shared/tokens/src/index.ts`,
`shared/tokens/package.json`, `eslint-rules/no-hardcoded-design-values.js` **Status:** ISSUES FOUND

---

## Summary

The `@syntek/tokens` package delivers the required CSS custom properties and TypeScript constants,
and all 152 declared unit tests pass. However, the implementation has gaps traceable to the US003
acceptance criteria and task list: AC3 (lint enforcement) is acknowledged in the story as unverified
against real component files, the typography token set omits `line-height` and `letter-spacing`
constants that the story task list explicitly requires, the `no-hardcoded-design-values` ESLint rule
has a narrow font-name blocklist and does not intercept Tailwind arbitrary value syntax, the
NativeWind integration has no automated test, and `tokens.css` is entirely untested for value
correctness.

---

## CRITICAL (Blocks deployment)

None identified.

---

## HIGH (Must fix before production)

### 1. Deferred acceptance criterion — AC3 (lint enforcement) is not verified against real components

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/docs/STORIES/US003.md` line 73

The story explicitly defers:

> "Green phase: lint rule verified against real component files (pending web package
> implementation)"

AC3 states: "Given a new component is added to any UI package, When I run the linter, Then any
hardcoded colour, spacing, or font-size value causes a lint failure."

The ESLint rule exists (`eslint-rules/no-hardcoded-design-values.js`) but its integration with
`eslint.config.mjs` has not been confirmed to fire against any real file in the codebase. No web
component package exists yet against which to test it. Until a component file is linted and a
hardcoded hex colour provably causes a lint failure, AC3 is unverified and the enforcement guarantee
cannot be relied upon.

**Impact:** If `eslint.config.mjs` does not correctly wire the custom rule to `packages/web/**` and
`mobile/**`, hardcoded values in components will ship to production undetected. The entire token
enforcement strategy depends on this step working end to end.

---

### 2. Typography token set omits `line-height` and `letter-spacing` — stated in story task list

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/src/tokens.ts` **File:**
`/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/tokens.css`

The US003 task list states under "Define `tokens.css`":

> "Typography scale: font-size (xs through 5xl), **line-height, letter-spacing**, font-weight
> tokens"

The implementation covers font-size, font-weight, and font-family. `tokens.css` contains no
`--line-height-*` custom properties and no `--letter-spacing-*` custom properties. `tokens.ts`
exports no corresponding TypeScript constants. The test suite (152 tests) does not include any
assertions for line-height or letter-spacing exports, confirming neither was implemented.

**Impact:** Consuming packages cannot use token-based line-height or letter-spacing values.
Developers will hardcode these values (`line-height: 1.5`, `letter-spacing: -0.02em`), bypassing the
token system and contradicting AC3's enforcement goal.

---

## MEDIUM (Should fix)

### 3. `no-hardcoded-design-values.js` ESLint rule has a narrow font-name blocklist

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/eslint-rules/no-hardcoded-design-values.js`
lines 52–60

The `HARDCODED_FONT_NAMES` set covers a fixed list of commonly misused fonts (`inter`, `roboto`,
`arial`, `helvetica`, `verdana`, `georgia`, `times new roman`, `times`). Fonts not on this list —
`Nunito`, `Poppins`, `Lato`, `Open Sans`, `Figtree`, `DM Sans`, `Outfit`, `Plus Jakarta Sans` — will
be silently accepted even though they are hardcoded font names. As the set of fonts used across
Syntek products grows, the blocklist will require manual maintenance. An allowlist approach (only
`var(--font-*)` references are accepted in string positions where a font-family is expected) would
be more robust and require no maintenance.

---

### 4. `no-hardcoded-design-values.js` does not detect hardcoded values in Tailwind arbitrary value syntax

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/eslint-rules/no-hardcoded-design-values.js`

The rule targets JSX `style` props and React Native `StyleSheet.create` objects. It does not detect
hardcoded colour values passed via Tailwind's arbitrary value syntax, for example
`className="text-[#3B82F6]"` or `className="bg-[rgb(59,130,246)]"`. In a Tailwind 4 codebase (the
stack specified in CLAUDE.md), this is the primary path by which developers will bypass the rule —
they can write arbitrary values in `className` strings without triggering any violation. AC3's
guarantee does not hold for Tailwind arbitrary values.

---

### 5. AC5 — NativeWind integration is manual-only with no automated test

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/docs/TESTS/US003-TEST-STATUS.md` line 163

The test status document notes: "AC5 (NativeWind) requires an Expo project — also verified
manually." There are no automated tests confirming that the NativeWind preset correctly maps token
values to native styles. AC5 states "Given a token value is referenced in a NativeWind class, When
the mobile component renders, Then the correct design token value is applied on both iOS and
Android." If the preset breaks following a NativeWind patch update, no automated check will catch
it.

---

### 6. `tokens.css` is not validated by any automated test — CSS value correctness is untested

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/tokens.css`

The 152 tests in `@syntek/tokens` verify that TypeScript constants hold the correct `var(--...)`
reference strings. No test parses `tokens.css` and verifies that the custom property values are
valid CSS (e.g., that `--color-primary` is a valid hex colour, that `--spacing-4` is `16px`, that
`--font-size-base` is `1rem`). If a typo is introduced into `tokens.css` (e.g.,
`--color-primary: #263eb` instead of `#2563eb`), no test will catch it. AC1 states "Given the tokens
package is installed, When I reference `var(--color-primary)` in any component, Then the value
resolves to the default token value." The default values in `tokens.css` are the mechanism for this
resolution and are entirely untested.

---

## LOW (Consider fixing)

### 7. Spacing token scale has gaps — missing steps create a hardcoding temptation

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/src/tokens.ts` lines 49–92

Spacing tokens are defined for steps 1–6, 8, 10, 12, 16, 20, 24, and 32 (mapping to 4px, 8px, 12px,
16px, 20px, 24px, 32px, 40px, 48px, 64px, 80px, 96px, and 128px). Steps 7, 9, 11, 13–15, and 17–19
are absent. The US003 spec lists only the specific steps provided, so this is by design. However, a
developer who reaches for `SPACING_7` (28px) will find no constant and is likely to hardcode `28px`
instead, contradicting AC3's enforcement goal. This gap is noted for awareness rather than as a
failing criterion.

---

## Test Scenarios Needed

- Run the `no-hardcoded-design-values` ESLint rule against a stub file containing
  `style={{ color: "#3B82F6" }}` and confirm it produces a lint error (AC3 integration test)
- Confirm the ESLint rule also fires when a hardcoded colour appears as a Tailwind arbitrary value:
  `className="text-[#3B82F6]"` — or document that this case is explicitly out of scope
- Parse `tokens.css` and verify each custom property value is a valid CSS value (e.g., `--spacing-4`
  equals `16px`, `--color-primary` equals a valid hex)
- Verify `tokens.ts` exports `LINE_HEIGHT_*` and `LETTER_SPACING_*` constants matching
  `--line-height-*` and `--letter-spacing-*` properties in `tokens.css` (currently absent)
- Confirm NativeWind preset produces a testable output against a minimal Expo fixture (AC5)

---

## Implementation Files Reviewed

| File                                                                                     | Purpose                             |
| ---------------------------------------------------------------------------------------- | ----------------------------------- |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/tokens.css`                   | CSS custom property definitions     |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/src/tokens.ts`                | TypeScript token constants          |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/src/index.ts`                 | Package entry point                 |
| `/mnt/archive/OldRepos/syntek/syntek-modules/shared/tokens/package.json`                 | Package manifest                    |
| `/mnt/archive/OldRepos/syntek/syntek-modules/eslint-rules/no-hardcoded-design-values.js` | Custom ESLint rule (AC3)            |
| `/mnt/archive/OldRepos/syntek/syntek-modules/docs/STORIES/US003.md`                      | Story, tasks, and completion status |
| `/mnt/archive/OldRepos/syntek/syntek-modules/docs/TESTS/US003-TEST-STATUS.md`            | Test status                         |

---

## Overall Risk Rating

**Medium**

The core token constants (AC1, AC2, AC4, AC6) are correctly implemented and tested. Two findings
trace directly to incomplete story tasks: `line-height` and `letter-spacing` tokens are listed in
the story task but not implemented, and AC3 (lint enforcement) is explicitly deferred with no
automated verification. The `tokens.css` CSS values being entirely untested is a secondary risk. AC5
is manually verified only. None of these will cause immediate failures in the token package itself,
but AC3 and the missing typography tokens are in-scope gaps.

---

## Handoff Signals

- Run `/syntek-dev-suite:backend` to add `--line-height-*` and `--letter-spacing-*` custom
  properties to `tokens.css` and corresponding TypeScript constants to `tokens.ts`.
- Run `/syntek-dev-suite:test-writer` to add tests that parse `tokens.css` and verify CSS property
  values, and to add an ESLint integration test that confirms AC3 fires against a stub component
  with a hardcoded hex colour.
- Run `/syntek-dev-suite:completion` to update QA status for US003 once the High items are resolved.
