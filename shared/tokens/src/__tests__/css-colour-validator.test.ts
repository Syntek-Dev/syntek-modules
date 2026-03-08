/**
 * Unit tests — isValidCssColour utility (US075).
 *
 * Acceptance criteria covered:
 *   AC11 — The platform accepts any valid CSS colour format before saving an
 *           override to syntek-settings.
 *   AC12 — Tailwind palette names (e.g. "blue-600") are NOT valid CSS colours
 *           and must be resolved to hex before this function is called.
 *
 * Supported formats under test:
 *   hex   — #rrggbb, #rgb, #rrggbbaa
 *   rgb() / rgba()
 *   hsl() / hsla()
 *   hwb()
 *   lab() / lch()
 *   oklab() / oklch()
 *   CSS named colours (white, transparent, cornflowerblue, …)
 *
 * Red phase: isValidCssColour always returns false, so all valid-format tests
 * fail and only the "rejects invalid" tests pass.
 */

import { describe, it, expect } from "vitest";

import { isValidCssColour } from "../colour-utils.js";

// ---------------------------------------------------------------------------
// Valid colour formats
// ---------------------------------------------------------------------------

describe("isValidCssColour — hex formats", () => {
  it("accepts 6-digit hex (#rrggbb)", () => {
    expect(isValidCssColour("#2563eb")).toBe(true);
  });

  it("accepts 3-digit hex (#rgb)", () => {
    expect(isValidCssColour("#fff")).toBe(true);
  });

  it("accepts 3-digit hex (#000)", () => {
    expect(isValidCssColour("#000")).toBe(true);
  });

  it("accepts 8-digit hex with alpha (#rrggbbaa)", () => {
    expect(isValidCssColour("#2563ebcc")).toBe(true);
  });

  it("accepts uppercase hex", () => {
    expect(isValidCssColour("#FF0000")).toBe(true);
  });

  it("accepts mixed-case hex", () => {
    expect(isValidCssColour("#Ff5733")).toBe(true);
  });
});

describe("isValidCssColour — rgb() and rgba()", () => {
  it("accepts rgb(r, g, b) with integers", () => {
    expect(isValidCssColour("rgb(37, 99, 235)")).toBe(true);
  });

  it("accepts rgb(0, 0, 0) black", () => {
    expect(isValidCssColour("rgb(0, 0, 0)")).toBe(true);
  });

  it("accepts rgb(255, 255, 255) white", () => {
    expect(isValidCssColour("rgb(255, 255, 255)")).toBe(true);
  });

  it("accepts rgba(r, g, b, a) with decimal alpha", () => {
    expect(isValidCssColour("rgba(37, 99, 235, 0.8)")).toBe(true);
  });

  it("accepts rgba with alpha = 0", () => {
    expect(isValidCssColour("rgba(0, 0, 0, 0)")).toBe(true);
  });

  it("accepts rgba with alpha = 1", () => {
    expect(isValidCssColour("rgba(255, 255, 255, 1)")).toBe(true);
  });
});

describe("isValidCssColour — hsl() and hsla()", () => {
  it("accepts hsl(h, s%, l%)", () => {
    expect(isValidCssColour("hsl(221, 83%, 53%)")).toBe(true);
  });

  it("accepts hsl(0, 0%, 100%) white", () => {
    expect(isValidCssColour("hsl(0, 0%, 100%)")).toBe(true);
  });

  it("accepts hsla(h, s%, l%, a)", () => {
    expect(isValidCssColour("hsla(221, 83%, 53%, 0.8)")).toBe(true);
  });

  it("accepts hsla with alpha = 0", () => {
    expect(isValidCssColour("hsla(0, 0%, 0%, 0)")).toBe(true);
  });
});

describe("isValidCssColour — hwb()", () => {
  it("accepts hwb(h w% b%)", () => {
    expect(isValidCssColour("hwb(221 15% 8%)")).toBe(true);
  });

  it("accepts hwb(0 0% 0%)", () => {
    expect(isValidCssColour("hwb(0 0% 0%)")).toBe(true);
  });
});

describe("isValidCssColour — lab() and lch()", () => {
  it("accepts lab(L a b)", () => {
    expect(isValidCssColour("lab(46 -8 -45)")).toBe(true);
  });

  it("accepts lab with positive and negative a/b axes", () => {
    expect(isValidCssColour("lab(50 25 -30)")).toBe(true);
  });

  it("accepts lch(L C H)", () => {
    expect(isValidCssColour("lch(46 46 264)")).toBe(true);
  });

  it("accepts lch with hue angle 0", () => {
    expect(isValidCssColour("lch(50 30 0)")).toBe(true);
  });
});

describe("isValidCssColour — oklab() and oklch()", () => {
  it("accepts oklab(L a b)", () => {
    expect(isValidCssColour("oklab(0.55 -0.05 -0.15)")).toBe(true);
  });

  it("accepts oklab with zero axes", () => {
    expect(isValidCssColour("oklab(1 0 0)")).toBe(true);
  });

  it("accepts oklch(L C H)", () => {
    expect(isValidCssColour("oklch(0.55 0.2 250)")).toBe(true);
  });

  it("accepts oklch(0 0 0) black", () => {
    expect(isValidCssColour("oklch(0 0 0)")).toBe(true);
  });

  it("accepts oklch(1 0 0) white", () => {
    expect(isValidCssColour("oklch(1 0 0)")).toBe(true);
  });
});

describe("isValidCssColour — CSS named colours", () => {
  const namedColours = [
    "white",
    "black",
    "red",
    "blue",
    "green",
    "transparent",
    "cornflowerblue",
    "rebeccapurple",
    "aliceblue",
    "chocolate",
    "currentColor",
  ] as const;

  for (const name of namedColours) {
    it(`accepts named colour "${name}"`, () => {
      expect(isValidCssColour(name)).toBe(true);
    });
  }
});

describe("isValidCssColour — CSS-wide keywords are NOT colours", () => {
  it('rejects "inherit" (CSS-wide keyword, not a <color> value)', () => {
    expect(isValidCssColour("inherit")).toBe(false);
  });

  it('rejects "initial" (CSS-wide keyword, not a <color> value)', () => {
    expect(isValidCssColour("initial")).toBe(false);
  });

  it('rejects "unset" (CSS-wide keyword, not a <color> value)', () => {
    expect(isValidCssColour("unset")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Invalid colour values — must be rejected
// ---------------------------------------------------------------------------

describe("isValidCssColour — invalid values are rejected", () => {
  it("rejects an empty string", () => {
    expect(isValidCssColour("")).toBe(false);
  });

  it("rejects a Tailwind scale name 'blue-600'", () => {
    // Tailwind names must be resolved to hex before validation
    expect(isValidCssColour("blue-600")).toBe(false);
  });

  it("rejects a Tailwind scale name 'emerald-400'", () => {
    expect(isValidCssColour("emerald-400")).toBe(false);
  });

  it("rejects an invalid hex '#xyz'", () => {
    expect(isValidCssColour("#xyz")).toBe(false);
  });

  it("rejects a 2-digit hex '#ff' (too short)", () => {
    expect(isValidCssColour("#ff")).toBe(false);
  });

  it("rejects an arbitrary word 'not-a-colour'", () => {
    expect(isValidCssColour("not-a-colour")).toBe(false);
  });

  it("rejects a bare number '42'", () => {
    expect(isValidCssColour("42")).toBe(false);
  });

  it("rejects a CSS pixel value '16px'", () => {
    expect(isValidCssColour("16px")).toBe(false);
  });

  it("rejects a CSS variable reference 'var(--color-primary)'", () => {
    // CSS var() references are not direct colour values
    expect(isValidCssColour("var(--color-primary)")).toBe(false);
  });

  it("rejects a plain space string '   '", () => {
    expect(isValidCssColour("   ")).toBe(false);
  });

  it("rejects a malformed rgb value 'rgb(300,0,0)' with out-of-range channel", () => {
    expect(isValidCssColour("rgb(300, 0, 0)")).toBe(false);
  });

  it("rejects a malformed hsl value 'hsl(abc, 50%, 50%)' with non-numeric hue", () => {
    expect(isValidCssColour("hsl(abc, 50%, 50%)")).toBe(false);
  });

  it("rejects a JSON object string '{\"r\":0}'", () => {
    expect(isValidCssColour('{"r":0}')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 4-digit hex (#rgba) — CSS Color Level 4
// ---------------------------------------------------------------------------

describe("isValidCssColour — 4-digit hex (#rgba)", () => {
  it('accepts "#f00f" (red, full opacity)', () => {
    expect(isValidCssColour("#f00f")).toBe(true);
  });

  it('accepts "#fff8" (white, ~53% opacity)', () => {
    expect(isValidCssColour("#fff8")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Alpha channel in modern colour functions (CSS Color Level 4)
// ---------------------------------------------------------------------------

describe("isValidCssColour — oklch/oklab/lab/lch/hwb with alpha", () => {
  it("accepts oklch with numeric alpha", () => {
    expect(isValidCssColour("oklch(0.55 0.2 250 / 0.5)")).toBe(true);
  });

  it("accepts oklch with percentage alpha", () => {
    expect(isValidCssColour("oklch(0.55 0.2 250 / 50%)")).toBe(true);
  });

  it("accepts lab with numeric alpha", () => {
    expect(isValidCssColour("lab(46 -8 -45 / 0.5)")).toBe(true);
  });

  it("accepts hwb with numeric alpha", () => {
    expect(isValidCssColour("hwb(221 15% 8% / 0.5)")).toBe(true);
  });

  it("accepts lch with numeric alpha", () => {
    expect(isValidCssColour("lch(46 46 264 / 0.5)")).toBe(true);
  });

  it("accepts oklab with numeric alpha", () => {
    expect(isValidCssColour("oklab(0.55 -0.05 -0.15 / 0.5)")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Range validation for oklch/oklab/lab L component
// ---------------------------------------------------------------------------

describe("isValidCssColour — oklch/oklab/lab L range validation", () => {
  it("rejects oklch(1.5 0.2 250) — L > 1", () => {
    expect(isValidCssColour("oklch(1.5 0.2 250)")).toBe(false);
  });

  it("rejects oklch(-0.5 0.2 250) — L < 0", () => {
    expect(isValidCssColour("oklch(-0.5 0.2 250)")).toBe(false);
  });

  it("rejects lab(200 0 0) — L > 100", () => {
    expect(isValidCssColour("lab(200 0 0)")).toBe(false);
  });

  it("rejects lab(-10 0 0) — L < 0", () => {
    expect(isValidCssColour("lab(-10 0 0)")).toBe(false);
  });
});
