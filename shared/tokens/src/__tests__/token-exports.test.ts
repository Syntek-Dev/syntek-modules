/**
 * Unit tests — @syntek/tokens named export verification (US003).
 *
 * Verifies every expected token constant is exported from the package entry
 * point and is not undefined at runtime.
 *
 * Red phase: stub exports empty strings / zeros, so "truthy value" assertions
 * in token-values.test.ts will fail.  These presence tests ensure the module
 * shape is stable before values are filled in.
 */

import { describe, it, expect } from "vitest";

import * as tokens from "../index.js";

// ---------------------------------------------------------------------------
// Colour tokens
// ---------------------------------------------------------------------------

describe("Colour token exports", () => {
  it("exports COLOR_PRIMARY", () => {
    expect(tokens).toHaveProperty("COLOR_PRIMARY");
  });
  it("exports COLOR_SECONDARY", () => {
    expect(tokens).toHaveProperty("COLOR_SECONDARY");
  });
  it("exports COLOR_DESTRUCTIVE", () => {
    expect(tokens).toHaveProperty("COLOR_DESTRUCTIVE");
  });
  it("exports COLOR_MUTED", () => {
    expect(tokens).toHaveProperty("COLOR_MUTED");
  });
  it("exports COLOR_SURFACE", () => {
    expect(tokens).toHaveProperty("COLOR_SURFACE");
  });
  it("exports COLOR_BACKGROUND", () => {
    expect(tokens).toHaveProperty("COLOR_BACKGROUND");
  });
  it("exports COLOR_FOREGROUND", () => {
    expect(tokens).toHaveProperty("COLOR_FOREGROUND");
  });
  it("exports COLOR_BORDER", () => {
    expect(tokens).toHaveProperty("COLOR_BORDER");
  });
});

// ---------------------------------------------------------------------------
// Spacing tokens
// ---------------------------------------------------------------------------

describe("Spacing token exports", () => {
  const spacingKeys = [
    "SPACING_1",
    "SPACING_2",
    "SPACING_3",
    "SPACING_4",
    "SPACING_5",
    "SPACING_6",
    "SPACING_8",
    "SPACING_10",
    "SPACING_12",
    "SPACING_16",
    "SPACING_20",
    "SPACING_24",
    "SPACING_32",
  ] as const;

  for (const key of spacingKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});

// ---------------------------------------------------------------------------
// Typography — font-size tokens
// ---------------------------------------------------------------------------

describe("Font-size token exports", () => {
  const fontSizeKeys = [
    "FONT_SIZE_XS",
    "FONT_SIZE_SM",
    "FONT_SIZE_BASE",
    "FONT_SIZE_LG",
    "FONT_SIZE_XL",
    "FONT_SIZE_2XL",
    "FONT_SIZE_3XL",
    "FONT_SIZE_4XL",
    "FONT_SIZE_5XL",
  ] as const;

  for (const key of fontSizeKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});

// ---------------------------------------------------------------------------
// Typography — font-weight tokens
// ---------------------------------------------------------------------------

describe("Font-weight token exports", () => {
  const fontWeightKeys = [
    "FONT_WEIGHT_LIGHT",
    "FONT_WEIGHT_NORMAL",
    "FONT_WEIGHT_MEDIUM",
    "FONT_WEIGHT_SEMIBOLD",
    "FONT_WEIGHT_BOLD",
  ] as const;

  for (const key of fontWeightKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});

// ---------------------------------------------------------------------------
// Font family tokens
// ---------------------------------------------------------------------------

describe("Font family token exports", () => {
  it("exports FONT_SANS", () => {
    expect(tokens).toHaveProperty("FONT_SANS");
  });
  it("exports FONT_SERIF", () => {
    expect(tokens).toHaveProperty("FONT_SERIF");
  });
  it("exports FONT_MONO", () => {
    expect(tokens).toHaveProperty("FONT_MONO");
  });
});

// ---------------------------------------------------------------------------
// Breakpoint tokens
// ---------------------------------------------------------------------------

describe("Breakpoint token exports", () => {
  const breakpointKeys = [
    "BREAKPOINT_SM",
    "BREAKPOINT_MD",
    "BREAKPOINT_LG",
    "BREAKPOINT_XL",
    "BREAKPOINT_2XL",
  ] as const;

  for (const key of breakpointKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});

// ---------------------------------------------------------------------------
// Border radius tokens
// ---------------------------------------------------------------------------

describe("Border radius token exports", () => {
  const radiusKeys = ["RADIUS_SM", "RADIUS_MD", "RADIUS_LG", "RADIUS_FULL"] as const;

  for (const key of radiusKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});

// ---------------------------------------------------------------------------
// Shadow tokens
// ---------------------------------------------------------------------------

describe("Shadow token exports", () => {
  const shadowKeys = ["SHADOW_SM", "SHADOW_MD", "SHADOW_LG"] as const;

  for (const key of shadowKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});

// ---------------------------------------------------------------------------
// Z-index tokens
// ---------------------------------------------------------------------------

describe("Z-index token exports", () => {
  const zKeys = ["Z_BASE", "Z_DROPDOWN", "Z_STICKY", "Z_MODAL", "Z_TOAST", "Z_TOOLTIP"] as const;

  for (const key of zKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});

// ---------------------------------------------------------------------------
// Transition tokens
// ---------------------------------------------------------------------------

describe("Transition token exports", () => {
  const transitionKeys = [
    "TRANSITION_DURATION_FAST",
    "TRANSITION_DURATION_BASE",
    "TRANSITION_DURATION_SLOW",
    "TRANSITION_EASING_DEFAULT",
    "TRANSITION_EASING_IN",
    "TRANSITION_EASING_OUT",
  ] as const;

  for (const key of transitionKeys) {
    it(`exports ${key}`, () => {
      expect(tokens).toHaveProperty(key);
    });
  }
});
