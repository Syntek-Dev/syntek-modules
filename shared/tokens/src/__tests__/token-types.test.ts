/**
 * Type-level tests — @syntek/tokens TypeScript type verification (US003).
 *
 * Acceptance criteria covered:
 *   AC4 — TypeScript constants for all tokens are available with correct types.
 *
 * Uses Vitest's expectTypeOf API so failures surface at both compile-time
 * (tsc / vitest typecheck) and runtime.
 *
 * Red phase: types are already string/number because TS infers them from the
 * stub literals, so these tests pass even in the stub.  They serve as a
 * regression guard to ensure the green-phase implementation does not widen
 * types to `unknown` or `any`.
 */

import { describe, it, expectTypeOf } from "vitest";

import {
  COLOR_PRIMARY,
  COLOR_SECONDARY,
  COLOR_DESTRUCTIVE,
  COLOR_MUTED,
  COLOR_SURFACE,
  COLOR_BACKGROUND,
  COLOR_FOREGROUND,
  COLOR_BORDER,
  SPACING_4,
  SPACING_8,
  FONT_SIZE_BASE,
  FONT_SIZE_LG,
  FONT_WEIGHT_NORMAL,
  FONT_WEIGHT_BOLD,
  FONT_SANS,
  FONT_SERIF,
  FONT_MONO,
  BREAKPOINT_SM,
  BREAKPOINT_MD,
  BREAKPOINT_LG,
  BREAKPOINT_XL,
  BREAKPOINT_2XL,
  RADIUS_MD,
  SHADOW_MD,
  Z_MODAL,
  TRANSITION_DURATION_BASE,
  TRANSITION_EASING_DEFAULT,
} from "../index.js";

// ---------------------------------------------------------------------------
// Colour tokens — must be string
// ---------------------------------------------------------------------------

describe("Colour token types", () => {
  it("COLOR_PRIMARY is string", () => {
    expectTypeOf(COLOR_PRIMARY).toBeString();
  });
  it("COLOR_SECONDARY is string", () => {
    expectTypeOf(COLOR_SECONDARY).toBeString();
  });
  it("COLOR_DESTRUCTIVE is string", () => {
    expectTypeOf(COLOR_DESTRUCTIVE).toBeString();
  });
  it("COLOR_MUTED is string", () => {
    expectTypeOf(COLOR_MUTED).toBeString();
  });
  it("COLOR_SURFACE is string", () => {
    expectTypeOf(COLOR_SURFACE).toBeString();
  });
  it("COLOR_BACKGROUND is string", () => {
    expectTypeOf(COLOR_BACKGROUND).toBeString();
  });
  it("COLOR_FOREGROUND is string", () => {
    expectTypeOf(COLOR_FOREGROUND).toBeString();
  });
  it("COLOR_BORDER is string", () => {
    expectTypeOf(COLOR_BORDER).toBeString();
  });
});

// ---------------------------------------------------------------------------
// Spacing tokens — must be string (CSS var references)
// ---------------------------------------------------------------------------

describe("Spacing token types", () => {
  it("SPACING_4 is string", () => {
    expectTypeOf(SPACING_4).toBeString();
  });
  it("SPACING_8 is string", () => {
    expectTypeOf(SPACING_8).toBeString();
  });
});

// ---------------------------------------------------------------------------
// Font-size tokens — must be string
// ---------------------------------------------------------------------------

describe("Font-size token types", () => {
  it("FONT_SIZE_BASE is string", () => {
    expectTypeOf(FONT_SIZE_BASE).toBeString();
  });
  it("FONT_SIZE_LG is string", () => {
    expectTypeOf(FONT_SIZE_LG).toBeString();
  });
});

// ---------------------------------------------------------------------------
// Font-weight tokens — must be string
// ---------------------------------------------------------------------------

describe("Font-weight token types", () => {
  it("FONT_WEIGHT_NORMAL is string", () => {
    expectTypeOf(FONT_WEIGHT_NORMAL).toBeString();
  });
  it("FONT_WEIGHT_BOLD is string", () => {
    expectTypeOf(FONT_WEIGHT_BOLD).toBeString();
  });
});

// ---------------------------------------------------------------------------
// Font family tokens — must be string (AC6)
// ---------------------------------------------------------------------------

describe("Font family token types", () => {
  it("FONT_SANS is string", () => {
    expectTypeOf(FONT_SANS).toBeString();
  });
  it("FONT_SERIF is string", () => {
    expectTypeOf(FONT_SERIF).toBeString();
  });
  it("FONT_MONO is string", () => {
    expectTypeOf(FONT_MONO).toBeString();
  });
});

// ---------------------------------------------------------------------------
// Breakpoint tokens — must be number (AC4)
// ---------------------------------------------------------------------------

describe("Breakpoint token types", () => {
  it("BREAKPOINT_SM is number", () => {
    expectTypeOf(BREAKPOINT_SM).toBeNumber();
  });
  it("BREAKPOINT_MD is number", () => {
    expectTypeOf(BREAKPOINT_MD).toBeNumber();
  });
  it("BREAKPOINT_LG is number", () => {
    expectTypeOf(BREAKPOINT_LG).toBeNumber();
  });
  it("BREAKPOINT_XL is number", () => {
    expectTypeOf(BREAKPOINT_XL).toBeNumber();
  });
  it("BREAKPOINT_2XL is number", () => {
    expectTypeOf(BREAKPOINT_2XL).toBeNumber();
  });
});

// ---------------------------------------------------------------------------
// Misc tokens — must be string
// ---------------------------------------------------------------------------

describe("Miscellaneous token types", () => {
  it("RADIUS_MD is string", () => {
    expectTypeOf(RADIUS_MD).toBeString();
  });
  it("SHADOW_MD is string", () => {
    expectTypeOf(SHADOW_MD).toBeString();
  });
  it("Z_MODAL is string", () => {
    expectTypeOf(Z_MODAL).toBeString();
  });
  it("TRANSITION_DURATION_BASE is string", () => {
    expectTypeOf(TRANSITION_DURATION_BASE).toBeString();
  });
  it("TRANSITION_EASING_DEFAULT is string", () => {
    expectTypeOf(TRANSITION_EASING_DEFAULT).toBeString();
  });
});
