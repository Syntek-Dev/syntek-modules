/**
 * Unit tests — TAILWIND_COLOURS palette map and resolveTailwindColour utility (US075).
 *
 * Acceptance criteria covered:
 *   AC7  — TAILWIND_COLOURS is a flat readonly record mapping every Tailwind v4
 *           palette entry to its resolved hex value.
 *   AC8  — resolveTailwindColour("blue-600") returns "#2563eb".
 *   AC9  — resolveTailwindColour returns undefined for unknown palette names.
 *   AC10 — The Tailwind v4 palette covers all 22 families at scales 50–950.
 *
 * Red phase: TAILWIND_COLOURS is an empty object so lookup tests fail.
 * resolveTailwindColour returns undefined for all inputs so specific-value
 * tests fail.
 */

import { describe, it, expect } from "vitest";

import { TAILWIND_COLOURS, resolveTailwindColour } from "../tailwind-colours.js";

// ---------------------------------------------------------------------------
// The 22 Tailwind v4 palette families
// ---------------------------------------------------------------------------

const PALETTE_FAMILIES = [
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
] as const;

// Tailwind v4 scale steps (50–950)
const SCALES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950] as const;

// ---------------------------------------------------------------------------
// Structural tests
// ---------------------------------------------------------------------------

describe("TAILWIND_COLOURS structure", () => {
  it("is exported and is an object", () => {
    expect(typeof TAILWIND_COLOURS).toBe("object");
    expect(TAILWIND_COLOURS).not.toBeNull();
  });

  it("is non-empty", () => {
    expect(Object.keys(TAILWIND_COLOURS).length).toBeGreaterThan(0);
  });

  it("has at least 242 entries (22 families × 11 scales)", () => {
    // 22 families × 11 scales (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950)
    expect(Object.keys(TAILWIND_COLOURS).length).toBeGreaterThanOrEqual(242);
  });

  it("all values are lowercase hex strings starting with '#'", () => {
    for (const [key, value] of Object.entries(TAILWIND_COLOURS)) {
      expect(value, `TAILWIND_COLOURS["${key}"] = "${value}" is not a hex string`).toMatch(
        /^#[0-9a-f]{3,8}$/i,
      );
    }
  });
});

// ---------------------------------------------------------------------------
// Family coverage
// ---------------------------------------------------------------------------

describe("TAILWIND_COLOURS palette family coverage", () => {
  for (const family of PALETTE_FAMILIES) {
    it(`contains entries for the "${family}" family`, () => {
      const familyKeys = Object.keys(TAILWIND_COLOURS).filter((k) => k.startsWith(`${family}-`));
      expect(familyKeys.length).toBeGreaterThan(0);
    });
  }
});

// ---------------------------------------------------------------------------
// Scale coverage per family
// ---------------------------------------------------------------------------

describe("TAILWIND_COLOURS scale coverage", () => {
  for (const family of PALETTE_FAMILIES) {
    for (const scale of SCALES) {
      it(`has "${family}-${scale}"`, () => {
        expect(TAILWIND_COLOURS).toHaveProperty(`${family}-${scale}`);
      });
    }
  }
});

// ---------------------------------------------------------------------------
// Spot-check specific known values (from tokens.css and Tailwind v4 defaults)
// ---------------------------------------------------------------------------

describe("TAILWIND_COLOURS known values", () => {
  const knownValues: [name: string, hex: string][] = [
    // From the US075 story
    ["blue-600", "#2563eb"],
    // From tokens.css colour palette
    ["gray-50", "#f9fafb"],
    ["gray-100", "#f3f4f6"],
    ["gray-200", "#e5e7eb"],
    ["gray-300", "#d1d5db"],
    ["gray-400", "#9ca3af"],
    ["gray-500", "#6b7280"],
    ["gray-600", "#4b5563"],
    ["gray-700", "#374151"],
    ["gray-800", "#1f2937"],
    ["gray-900", "#111827"],
    ["gray-950", "#030712"],
    ["blue-50", "#eff6ff"],
    ["blue-100", "#dbeafe"],
    ["blue-500", "#3b82f6"],
    ["blue-700", "#1d4ed8"],
    ["blue-900", "#1e3a8a"],
    ["green-500", "#22c55e"],
    ["red-600", "#dc2626"],
    ["purple-600", "#9333ea"],
    ["yellow-500", "#eab308"],
    ["pink-500", "#ec4899"],
  ];

  for (const [name, hex] of knownValues) {
    it(`"${name}" resolves to "${hex}"`, () => {
      expect(TAILWIND_COLOURS[name]).toBe(hex);
    });
  }
});

// ---------------------------------------------------------------------------
// resolveTailwindColour utility
// ---------------------------------------------------------------------------

describe("resolveTailwindColour", () => {
  it('resolves "blue-600" to "#2563eb"', () => {
    expect(resolveTailwindColour("blue-600")).toBe("#2563eb");
  });

  it('resolves "gray-500" to "#6b7280"', () => {
    expect(resolveTailwindColour("gray-500")).toBe("#6b7280");
  });

  it('resolves "red-600" to "#dc2626"', () => {
    expect(resolveTailwindColour("red-600")).toBe("#dc2626");
  });

  it('resolves "purple-600" to "#9333ea"', () => {
    expect(resolveTailwindColour("purple-600")).toBe("#9333ea");
  });

  it("returns undefined for an unknown name", () => {
    expect(resolveTailwindColour("not-a-colour-999")).toBeUndefined();
  });

  it("returns undefined for an empty string", () => {
    expect(resolveTailwindColour("")).toBeUndefined();
  });

  it("returns undefined for a bare CSS colour (not a Tailwind name)", () => {
    // "#2563eb" is not a Tailwind palette name — should not be in the record
    expect(resolveTailwindColour("#2563eb")).toBeUndefined();
  });

  it("returns a hex string (starts with '#') for every valid family-scale name", () => {
    for (const family of PALETTE_FAMILIES) {
      for (const scale of [50, 100, 500, 900, 950] as const) {
        const result = resolveTailwindColour(`${family}-${scale}`);
        expect(
          result,
          `resolveTailwindColour("${family}-${scale}") should not be undefined`,
        ).toBeDefined();
        expect(result).toMatch(/^#[0-9a-f]{3,8}$/i);
      }
    }
  });

  it('resolves "Blue-600" case-insensitively after toLowerCase normalisation', () => {
    expect(resolveTailwindColour("Blue-600")).toBe("#2563eb");
  });

  it('returns undefined for "__proto__" (prototype attack string)', () => {
    expect(resolveTailwindColour("__proto__")).toBeUndefined();
  });

  it('returns undefined for "constructor" (prototype attack string)', () => {
    expect(resolveTailwindColour("constructor")).toBeUndefined();
  });

  it('returns undefined for "toString" (prototype attack string)', () => {
    expect(resolveTailwindColour("toString")).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// Spot-check values for all 22 palette families (Issue 13)
// ---------------------------------------------------------------------------

describe("TAILWIND_COLOURS spot-check — all 22 families", () => {
  const spotChecks: [name: string, hex: string][] = [
    // 15 families not previously spot-checked
    ["slate-500", "#64748b"],
    ["zinc-500", "#71717a"],
    ["neutral-500", "#737373"],
    ["stone-500", "#78716c"],
    ["orange-500", "#f97316"],
    ["amber-500", "#f59e0b"],
    ["lime-500", "#84cc16"],
    ["emerald-500", "#10b981"],
    ["teal-500", "#14b8a6"],
    ["cyan-500", "#06b6d4"],
    ["sky-500", "#0ea5e9"],
    ["indigo-500", "#6366f1"],
    ["violet-500", "#8b5cf6"],
    ["fuchsia-500", "#d946ef"],
    ["rose-500", "#f43f5e"],
  ];

  for (const [name, hex] of spotChecks) {
    it(`"${name}" resolves to "${hex}"`, () => {
      expect(TAILWIND_COLOURS[name]).toBe(hex);
    });
  }
});
