/**
 * Unit tests — @syntek/tokens value assertions (US003).
 *
 * Acceptance criteria covered:
 *   AC1 — CSS token constants reference var(--...) so that they resolve to the
 *          default CSS custom property value when used in any component.
 *   AC4 — TypeScript constants are available with correct values.
 *   AC6 — Font family tokens reference var(--font-sans/serif/mono).
 *
 * Red phase: all CSS-var assertions fail because the stub exports empty strings.
 * Breakpoint assertions fail because the stub exports 0.
 */

import { describe, it, expect } from "vitest";

import {
  COLOR_PRIMARY,
  COLOR_SECONDARY,
  COLOR_DESTRUCTIVE,
  COLOR_MUTED,
  COLOR_SURFACE,
  COLOR_BACKGROUND,
  COLOR_FOREGROUND,
  COLOR_BORDER,
  SPACING_1,
  SPACING_2,
  SPACING_3,
  SPACING_4,
  SPACING_5,
  SPACING_6,
  SPACING_8,
  SPACING_10,
  SPACING_12,
  SPACING_16,
  SPACING_20,
  SPACING_24,
  SPACING_32,
  FONT_SIZE_XS,
  FONT_SIZE_SM,
  FONT_SIZE_BASE,
  FONT_SIZE_LG,
  FONT_SIZE_XL,
  FONT_SIZE_2XL,
  FONT_SIZE_3XL,
  FONT_SIZE_4XL,
  FONT_SIZE_5XL,
  FONT_WEIGHT_LIGHT,
  FONT_WEIGHT_NORMAL,
  FONT_WEIGHT_MEDIUM,
  FONT_WEIGHT_SEMIBOLD,
  FONT_WEIGHT_BOLD,
  FONT_SANS,
  FONT_SERIF,
  FONT_MONO,
  BREAKPOINT_SM,
  BREAKPOINT_MD,
  BREAKPOINT_LG,
  BREAKPOINT_XL,
  BREAKPOINT_2XL,
  RADIUS_SM,
  RADIUS_MD,
  RADIUS_LG,
  RADIUS_FULL,
  SHADOW_SM,
  SHADOW_MD,
  SHADOW_LG,
  Z_BASE,
  Z_DROPDOWN,
  Z_STICKY,
  Z_MODAL,
  Z_TOAST,
  Z_TOOLTIP,
  TRANSITION_DURATION_FAST,
  TRANSITION_DURATION_BASE,
  TRANSITION_DURATION_SLOW,
  TRANSITION_EASING_DEFAULT,
  TRANSITION_EASING_IN,
  TRANSITION_EASING_OUT,
} from "../index.js";

/** Helper: assert a CSS token constant looks like `var(--some-name)` */
function expectCssVar(value: string, expectedVarName: string) {
  expect(value).toBe(`var(--${expectedVarName})`);
}

// ---------------------------------------------------------------------------
// Colour tokens
// ---------------------------------------------------------------------------

describe("Colour token values", () => {
  it("COLOR_PRIMARY references var(--color-primary)", () => {
    expectCssVar(COLOR_PRIMARY, "color-primary");
  });
  it("COLOR_SECONDARY references var(--color-secondary)", () => {
    expectCssVar(COLOR_SECONDARY, "color-secondary");
  });
  it("COLOR_DESTRUCTIVE references var(--color-destructive)", () => {
    expectCssVar(COLOR_DESTRUCTIVE, "color-destructive");
  });
  it("COLOR_MUTED references var(--color-muted)", () => {
    expectCssVar(COLOR_MUTED, "color-muted");
  });
  it("COLOR_SURFACE references var(--color-surface)", () => {
    expectCssVar(COLOR_SURFACE, "color-surface");
  });
  it("COLOR_BACKGROUND references var(--color-background)", () => {
    expectCssVar(COLOR_BACKGROUND, "color-background");
  });
  it("COLOR_FOREGROUND references var(--color-foreground)", () => {
    expectCssVar(COLOR_FOREGROUND, "color-foreground");
  });
  it("COLOR_BORDER references var(--color-border)", () => {
    expectCssVar(COLOR_BORDER, "color-border");
  });
});

// ---------------------------------------------------------------------------
// Spacing tokens
// ---------------------------------------------------------------------------

describe("Spacing token values", () => {
  const cases: [string, string][] = [
    [SPACING_1, "spacing-1"],
    [SPACING_2, "spacing-2"],
    [SPACING_3, "spacing-3"],
    [SPACING_4, "spacing-4"],
    [SPACING_5, "spacing-5"],
    [SPACING_6, "spacing-6"],
    [SPACING_8, "spacing-8"],
    [SPACING_10, "spacing-10"],
    [SPACING_12, "spacing-12"],
    [SPACING_16, "spacing-16"],
    [SPACING_20, "spacing-20"],
    [SPACING_24, "spacing-24"],
    [SPACING_32, "spacing-32"],
  ];

  for (const [value, varName] of cases) {
    it(`references var(--${varName})`, () => {
      expectCssVar(value, varName);
    });
  }
});

// ---------------------------------------------------------------------------
// Font-size tokens
// ---------------------------------------------------------------------------

describe("Font-size token values", () => {
  const cases: [string, string][] = [
    [FONT_SIZE_XS, "font-size-xs"],
    [FONT_SIZE_SM, "font-size-sm"],
    [FONT_SIZE_BASE, "font-size-base"],
    [FONT_SIZE_LG, "font-size-lg"],
    [FONT_SIZE_XL, "font-size-xl"],
    [FONT_SIZE_2XL, "font-size-2xl"],
    [FONT_SIZE_3XL, "font-size-3xl"],
    [FONT_SIZE_4XL, "font-size-4xl"],
    [FONT_SIZE_5XL, "font-size-5xl"],
  ];

  for (const [value, varName] of cases) {
    it(`references var(--${varName})`, () => {
      expectCssVar(value, varName);
    });
  }
});

// ---------------------------------------------------------------------------
// Font-weight tokens
// ---------------------------------------------------------------------------

describe("Font-weight token values", () => {
  const cases: [string, string][] = [
    [FONT_WEIGHT_LIGHT, "font-weight-light"],
    [FONT_WEIGHT_NORMAL, "font-weight-normal"],
    [FONT_WEIGHT_MEDIUM, "font-weight-medium"],
    [FONT_WEIGHT_SEMIBOLD, "font-weight-semibold"],
    [FONT_WEIGHT_BOLD, "font-weight-bold"],
  ];

  for (const [value, varName] of cases) {
    it(`references var(--${varName})`, () => {
      expectCssVar(value, varName);
    });
  }
});

// ---------------------------------------------------------------------------
// Font family tokens (AC6)
// ---------------------------------------------------------------------------

describe("Font family token values", () => {
  it("FONT_SANS references var(--font-sans)", () => {
    expectCssVar(FONT_SANS, "font-sans");
  });
  it("FONT_SERIF references var(--font-serif)", () => {
    expectCssVar(FONT_SERIF, "font-serif");
  });
  it("FONT_MONO references var(--font-mono)", () => {
    expectCssVar(FONT_MONO, "font-mono");
  });
});

// ---------------------------------------------------------------------------
// Breakpoint tokens — numeric pixels (AC4)
// ---------------------------------------------------------------------------

describe("Breakpoint token values", () => {
  it("BREAKPOINT_SM is 640", () => {
    expect(BREAKPOINT_SM).toBe(640);
  });
  it("BREAKPOINT_MD is 768", () => {
    expect(BREAKPOINT_MD).toBe(768);
  });
  it("BREAKPOINT_LG is 1024", () => {
    expect(BREAKPOINT_LG).toBe(1024);
  });
  it("BREAKPOINT_XL is 1280", () => {
    expect(BREAKPOINT_XL).toBe(1280);
  });
  it("BREAKPOINT_2XL is 1536", () => {
    expect(BREAKPOINT_2XL).toBe(1536);
  });
  it("breakpoints are in ascending order", () => {
    expect(BREAKPOINT_SM).toBeLessThan(BREAKPOINT_MD);
    expect(BREAKPOINT_MD).toBeLessThan(BREAKPOINT_LG);
    expect(BREAKPOINT_LG).toBeLessThan(BREAKPOINT_XL);
    expect(BREAKPOINT_XL).toBeLessThan(BREAKPOINT_2XL);
  });
});

// ---------------------------------------------------------------------------
// Border radius tokens
// ---------------------------------------------------------------------------

describe("Border radius token values", () => {
  const cases: [string, string][] = [
    [RADIUS_SM, "radius-sm"],
    [RADIUS_MD, "radius-md"],
    [RADIUS_LG, "radius-lg"],
    [RADIUS_FULL, "radius-full"],
  ];

  for (const [value, varName] of cases) {
    it(`references var(--${varName})`, () => {
      expectCssVar(value, varName);
    });
  }
});

// ---------------------------------------------------------------------------
// Shadow tokens
// ---------------------------------------------------------------------------

describe("Shadow token values", () => {
  const cases: [string, string][] = [
    [SHADOW_SM, "shadow-sm"],
    [SHADOW_MD, "shadow-md"],
    [SHADOW_LG, "shadow-lg"],
  ];

  for (const [value, varName] of cases) {
    it(`references var(--${varName})`, () => {
      expectCssVar(value, varName);
    });
  }
});

// ---------------------------------------------------------------------------
// Z-index tokens
// ---------------------------------------------------------------------------

describe("Z-index token values", () => {
  const cases: [string, string][] = [
    [Z_BASE, "z-base"],
    [Z_DROPDOWN, "z-dropdown"],
    [Z_STICKY, "z-sticky"],
    [Z_MODAL, "z-modal"],
    [Z_TOAST, "z-toast"],
    [Z_TOOLTIP, "z-tooltip"],
  ];

  for (const [value, varName] of cases) {
    it(`references var(--${varName})`, () => {
      expectCssVar(value, varName);
    });
  }
});

// ---------------------------------------------------------------------------
// Transition tokens
// ---------------------------------------------------------------------------

describe("Transition token values", () => {
  const cases: [string, string][] = [
    [TRANSITION_DURATION_FAST, "transition-duration-fast"],
    [TRANSITION_DURATION_BASE, "transition-duration-base"],
    [TRANSITION_DURATION_SLOW, "transition-duration-slow"],
    [TRANSITION_EASING_DEFAULT, "transition-easing-default"],
    [TRANSITION_EASING_IN, "transition-easing-in"],
    [TRANSITION_EASING_OUT, "transition-easing-out"],
  ];

  for (const [value, varName] of cases) {
    it(`references var(--${varName})`, () => {
      expectCssVar(value, varName);
    });
  }
});
