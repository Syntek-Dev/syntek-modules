/**
 * Unit tests — TOKEN_MANIFEST shape and correctness (US075).
 *
 * Acceptance criteria covered:
 *   AC1 — Every token has key, cssVar, category, type, default, and label fields.
 *   AC2 — Colour tokens have type "color" → drives a colour picker widget.
 *   AC3 — Spacing tokens have type "px" → drives a number/px input widget.
 *   AC4 — Font-family tokens have type "font-family" → drives a font selector.
 *   AC5 — Colour token defaults are resolved hex strings, not var() references.
 *   AC6 — TOKEN_MANIFEST is a static read-only schema; the same reference is
 *          returned on repeated imports.
 *
 * Red phase: TOKEN_MANIFEST is an empty array, so:
 *   - "has at least one entry" fails.
 *   - "has entry for COLOR_PRIMARY" fails (not found).
 *   - per-category coverage tests fail (no entries).
 */

import { describe, it, expect } from "vitest";

import { TOKEN_MANIFEST } from "../manifest.js";
import type { TokenCategory, TokenWidgetType } from "../types/token-manifest.js";

// ---------------------------------------------------------------------------
// Allowed union values — used for structural validation
// ---------------------------------------------------------------------------

const VALID_CATEGORIES: readonly TokenCategory[] = [
  "colour",
  "spacing",
  "typography",
  "radius",
  "shadow",
  "z-index",
  "transition",
];

const VALID_WIDGET_TYPES: readonly TokenWidgetType[] = [
  "color",
  "px",
  "rem",
  "font-family",
  "font-weight",
  "number",
  "duration",
  "easing",
  "shadow",
];

// ---------------------------------------------------------------------------
// Structural invariants — applies to every entry
// ---------------------------------------------------------------------------

describe("TOKEN_MANIFEST structural invariants", () => {
  it("is exported as an array", () => {
    expect(Array.isArray(TOKEN_MANIFEST)).toBe(true);
  });

  it("has at least one entry", () => {
    expect(TOKEN_MANIFEST.length).toBeGreaterThan(0);
  });

  it("every entry has a non-empty string key", () => {
    for (const entry of TOKEN_MANIFEST) {
      expect(typeof entry.key).toBe("string");
      expect(entry.key.length).toBeGreaterThan(0);
    }
  });

  it("every entry cssVar starts with '--'", () => {
    for (const entry of TOKEN_MANIFEST) {
      expect(typeof entry.cssVar).toBe("string");
      expect(entry.cssVar.startsWith("--")).toBe(true);
    }
  });

  it("every entry category is a valid TokenCategory", () => {
    for (const entry of TOKEN_MANIFEST) {
      expect(VALID_CATEGORIES).toContain(entry.category);
    }
  });

  it("every entry type is a valid TokenWidgetType", () => {
    for (const entry of TOKEN_MANIFEST) {
      expect(VALID_WIDGET_TYPES).toContain(entry.type);
    }
  });

  it("every entry default is a string or number", () => {
    for (const entry of TOKEN_MANIFEST) {
      const t = typeof entry.default;
      expect(t === "string" || t === "number").toBe(true);
    }
  });

  it("every entry label is a non-empty string", () => {
    for (const entry of TOKEN_MANIFEST) {
      expect(typeof entry.label).toBe("string");
      expect(entry.label.length).toBeGreaterThan(0);
    }
  });

  it("all keys are unique", () => {
    const keys = TOKEN_MANIFEST.map((e) => e.key);
    const unique = new Set(keys);
    expect(unique.size).toBe(keys.length);
  });

  it("all cssVar names are unique", () => {
    const cssVars = TOKEN_MANIFEST.map((e) => e.cssVar);
    const unique = new Set(cssVars);
    expect(unique.size).toBe(cssVars.length);
  });
});

// ---------------------------------------------------------------------------
// Colour tokens — AC2 & AC5
// ---------------------------------------------------------------------------

const HEX_RE = /^#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i;

describe("Colour token entries — widget type and default values", () => {
  const colourEntries = TOKEN_MANIFEST.filter((e) => e.category === "colour");

  it("there is at least one colour token in the manifest", () => {
    expect(colourEntries.length).toBeGreaterThan(0);
  });

  it("all colour tokens have type 'color'", () => {
    for (const entry of colourEntries) {
      expect(entry.type).toBe("color");
    }
  });

  it("all colour token defaults are hex strings (not var() references)", () => {
    for (const entry of colourEntries) {
      const def = entry.default;
      expect(typeof def).toBe("string");
      expect(def as string).toMatch(HEX_RE);
    }
  });
});

// ---------------------------------------------------------------------------
// Specific colour token assertions
// ---------------------------------------------------------------------------

describe("Specific colour token entries", () => {
  const find = (key: string) => TOKEN_MANIFEST.find((e) => e.key === key);

  const semanticColours: [key: string, cssVar: string, hex: string, label: string][] = [
    ["COLOR_PRIMARY", "--color-primary", "#2563eb", "Primary colour"],
    ["COLOR_SECONDARY", "--color-secondary", "#9333ea", "Secondary colour"],
    ["COLOR_DESTRUCTIVE", "--color-destructive", "#dc2626", "Destructive colour"],
    ["COLOR_MUTED", "--color-muted", "#6b7280", "Muted colour"],
    ["COLOR_SURFACE", "--color-surface", "#ffffff", "Surface colour"],
    ["COLOR_BACKGROUND", "--color-background", "#f9fafb", "Background colour"],
    ["COLOR_FOREGROUND", "--color-foreground", "#111827", "Foreground colour"],
    ["COLOR_BORDER", "--color-border", "#e5e7eb", "Border colour"],
  ];

  for (const [key, cssVar, hex] of semanticColours) {
    it(`has an entry for ${key}`, () => {
      const entry = find(key);
      expect(entry).toBeDefined();
    });

    it(`${key} has cssVar "${cssVar}"`, () => {
      const entry = find(key);
      expect(entry?.cssVar).toBe(cssVar);
    });

    it(`${key} has category "colour"`, () => {
      const entry = find(key);
      expect(entry?.category).toBe("colour");
    });

    it(`${key} has type "color"`, () => {
      const entry = find(key);
      expect(entry?.type).toBe("color");
    });

    it(`${key} default is hex "${hex}"`, () => {
      const entry = find(key);
      expect(entry?.default).toBe(hex);
    });
  }
});

// ---------------------------------------------------------------------------
// Spacing tokens — AC3
// ---------------------------------------------------------------------------

describe("Spacing token entries", () => {
  const spacingEntries = TOKEN_MANIFEST.filter((e) => e.category === "spacing");

  it("there is at least one spacing token in the manifest", () => {
    expect(spacingEntries.length).toBeGreaterThan(0);
  });

  it("all spacing tokens have type 'px'", () => {
    for (const entry of spacingEntries) {
      expect(entry.type).toBe("px");
    }
  });

  it("all spacing token defaults are numbers", () => {
    for (const entry of spacingEntries) {
      expect(typeof entry.default).toBe("number");
    }
  });

  it("all spacing token cssVar names start with '--spacing-'", () => {
    for (const entry of spacingEntries) {
      expect(entry.cssVar.startsWith("--spacing-")).toBe(true);
    }
  });

  const spacingCases: [key: string, cssVar: string, defaultPx: number][] = [
    ["SPACING_1", "--spacing-1", 4],
    ["SPACING_2", "--spacing-2", 8],
    ["SPACING_4", "--spacing-4", 16],
    ["SPACING_8", "--spacing-8", 32],
    ["SPACING_16", "--spacing-16", 64],
  ];

  for (const [key, cssVar, px] of spacingCases) {
    it(`has entry ${key} with cssVar "${cssVar}" and default ${px}`, () => {
      const entry = TOKEN_MANIFEST.find((e) => e.key === key);
      expect(entry).toBeDefined();
      expect(entry?.cssVar).toBe(cssVar);
      expect(entry?.default).toBe(px);
    });
  }
});

// ---------------------------------------------------------------------------
// Typography — font-size tokens
// ---------------------------------------------------------------------------

describe("Font-size token entries", () => {
  const fontSizeEntries = TOKEN_MANIFEST.filter(
    (e) => e.category === "typography" && e.type === "rem",
  );

  it("there is at least one font-size token in the manifest", () => {
    expect(fontSizeEntries.length).toBeGreaterThan(0);
  });

  it("all font-size tokens have type 'rem'", () => {
    for (const entry of fontSizeEntries) {
      expect(entry.type).toBe("rem");
    }
  });

  it("all font-size token defaults are numbers", () => {
    for (const entry of fontSizeEntries) {
      expect(typeof entry.default).toBe("number");
    }
  });

  const fontSizeCases: [key: string, cssVar: string, defaultRem: number][] = [
    ["FONT_SIZE_XS", "--font-size-xs", 0.75],
    ["FONT_SIZE_SM", "--font-size-sm", 0.875],
    ["FONT_SIZE_BASE", "--font-size-base", 1],
    ["FONT_SIZE_LG", "--font-size-lg", 1.125],
  ];

  for (const [key, cssVar, rem] of fontSizeCases) {
    it(`has entry ${key} with cssVar "${cssVar}" and default ${rem}`, () => {
      const entry = TOKEN_MANIFEST.find((e) => e.key === key);
      expect(entry).toBeDefined();
      expect(entry?.cssVar).toBe(cssVar);
      expect(entry?.default).toBe(rem);
    });
  }
});

// ---------------------------------------------------------------------------
// Typography — font-weight tokens
// ---------------------------------------------------------------------------

describe("Font-weight token entries", () => {
  const fontWeightEntries = TOKEN_MANIFEST.filter(
    (e) => e.category === "typography" && e.type === "font-weight",
  );

  it("there is at least one font-weight token in the manifest", () => {
    expect(fontWeightEntries.length).toBeGreaterThan(0);
  });

  it("all font-weight token defaults are numeric weight values", () => {
    for (const entry of fontWeightEntries) {
      expect(typeof entry.default).toBe("number");
      expect([100, 200, 300, 400, 500, 600, 700, 800, 900]).toContain(entry.default);
    }
  });

  const weightCases: [key: string, cssVar: string, weight: number][] = [
    ["FONT_WEIGHT_LIGHT", "--font-weight-light", 300],
    ["FONT_WEIGHT_NORMAL", "--font-weight-normal", 400],
    ["FONT_WEIGHT_BOLD", "--font-weight-bold", 700],
  ];

  for (const [key, cssVar, weight] of weightCases) {
    it(`has entry ${key} with cssVar "${cssVar}" and default ${weight}`, () => {
      const entry = TOKEN_MANIFEST.find((e) => e.key === key);
      expect(entry).toBeDefined();
      expect(entry?.cssVar).toBe(cssVar);
      expect(entry?.default).toBe(weight);
    });
  }
});

// ---------------------------------------------------------------------------
// Typography — font-family tokens — AC4
// ---------------------------------------------------------------------------

describe("Font-family token entries — AC4", () => {
  const fontFamilyEntries = TOKEN_MANIFEST.filter(
    (e) => e.category === "typography" && e.type === "font-family",
  );

  it("there is at least one font-family token in the manifest", () => {
    expect(fontFamilyEntries.length).toBeGreaterThan(0);
  });

  it("all font-family tokens have type 'font-family'", () => {
    for (const entry of fontFamilyEntries) {
      expect(entry.type).toBe("font-family");
    }
  });

  it("all font-family token defaults are non-empty strings", () => {
    for (const entry of fontFamilyEntries) {
      expect(typeof entry.default).toBe("string");
      expect((entry.default as string).length).toBeGreaterThan(0);
    }
  });

  const familyCases: [key: string, cssVar: string][] = [
    ["FONT_SANS", "--font-sans"],
    ["FONT_SERIF", "--font-serif"],
    ["FONT_MONO", "--font-mono"],
  ];

  for (const [key, cssVar] of familyCases) {
    it(`has entry ${key} with cssVar "${cssVar}"`, () => {
      const entry = TOKEN_MANIFEST.find((e) => e.key === key);
      expect(entry).toBeDefined();
      expect(entry?.cssVar).toBe(cssVar);
      expect(entry?.type).toBe("font-family");
    });
  }
});

// ---------------------------------------------------------------------------
// Z-index tokens
// ---------------------------------------------------------------------------

describe("Z-index token entries", () => {
  const zIndexEntries = TOKEN_MANIFEST.filter((e) => e.category === "z-index");

  it("there is at least one z-index token in the manifest", () => {
    expect(zIndexEntries.length).toBeGreaterThan(0);
  });

  it("all z-index tokens have type 'number'", () => {
    for (const entry of zIndexEntries) {
      expect(entry.type).toBe("number");
    }
  });

  it("all z-index token defaults are non-negative integers", () => {
    for (const entry of zIndexEntries) {
      expect(typeof entry.default).toBe("number");
      expect(Number.isInteger(entry.default)).toBe(true);
      expect(entry.default as number).toBeGreaterThanOrEqual(0);
    }
  });

  const zCases: [key: string, cssVar: string, value: number][] = [
    ["Z_BASE", "--z-base", 0],
    ["Z_DROPDOWN", "--z-dropdown", 1000],
    ["Z_MODAL", "--z-modal", 1300],
    ["Z_TOOLTIP", "--z-tooltip", 1500],
  ];

  for (const [key, cssVar, value] of zCases) {
    it(`has entry ${key} with cssVar "${cssVar}" and default ${value}`, () => {
      const entry = TOKEN_MANIFEST.find((e) => e.key === key);
      expect(entry).toBeDefined();
      expect(entry?.cssVar).toBe(cssVar);
      expect(entry?.default).toBe(value);
    });
  }
});

// ---------------------------------------------------------------------------
// Transition tokens
// ---------------------------------------------------------------------------

describe("Transition duration token entries", () => {
  const durationEntries = TOKEN_MANIFEST.filter(
    (e) => e.category === "transition" && e.type === "duration",
  );

  it("there is at least one transition duration token in the manifest", () => {
    expect(durationEntries.length).toBeGreaterThan(0);
  });

  it("all duration tokens have type 'duration'", () => {
    for (const entry of durationEntries) {
      expect(entry.type).toBe("duration");
    }
  });

  it("all duration token defaults are positive numbers (ms)", () => {
    for (const entry of durationEntries) {
      expect(typeof entry.default).toBe("number");
      expect(entry.default as number).toBeGreaterThan(0);
    }
  });

  const durationCases: [key: string, cssVar: string, ms: number][] = [
    ["TRANSITION_DURATION_FAST", "--transition-duration-fast", 150],
    ["TRANSITION_DURATION_BASE", "--transition-duration-base", 200],
    ["TRANSITION_DURATION_SLOW", "--transition-duration-slow", 300],
  ];

  for (const [key, cssVar, ms] of durationCases) {
    it(`has entry ${key} with cssVar "${cssVar}" and default ${ms}`, () => {
      const entry = TOKEN_MANIFEST.find((e) => e.key === key);
      expect(entry).toBeDefined();
      expect(entry?.cssVar).toBe(cssVar);
      expect(entry?.default).toBe(ms);
    });
  }
});

describe("Transition easing token entries", () => {
  const easingEntries = TOKEN_MANIFEST.filter(
    (e) => e.category === "transition" && e.type === "easing",
  );

  it("there is at least one transition easing token in the manifest", () => {
    expect(easingEntries.length).toBeGreaterThan(0);
  });

  it("all easing tokens have type 'easing'", () => {
    for (const entry of easingEntries) {
      expect(entry.type).toBe("easing");
    }
  });

  it("all easing token defaults are non-empty strings", () => {
    for (const entry of easingEntries) {
      expect(typeof entry.default).toBe("string");
      expect((entry.default as string).length).toBeGreaterThan(0);
    }
  });

  it("has entry TRANSITION_EASING_DEFAULT with cubic-bezier default", () => {
    const entry = TOKEN_MANIFEST.find((e) => e.key === "TRANSITION_EASING_DEFAULT");
    expect(entry).toBeDefined();
    expect(entry?.cssVar).toBe("--transition-easing-default");
    expect(entry?.default).toBe("cubic-bezier(0.4, 0, 0.2, 1)");
  });
});

// ---------------------------------------------------------------------------
// Category coverage — at least one entry per required category
// ---------------------------------------------------------------------------

describe("Manifest category coverage", () => {
  const categories = TOKEN_MANIFEST.map((e) => e.category);

  const required: TokenCategory[] = [
    "colour",
    "spacing",
    "typography",
    "radius",
    "z-index",
    "transition",
  ];

  for (const cat of required) {
    it(`contains at least one "${cat}" token`, () => {
      expect(categories).toContain(cat);
    });
  }
});

// ---------------------------------------------------------------------------
// TOKEN_MANIFEST immutability — read-only schema
// ---------------------------------------------------------------------------

describe("TOKEN_MANIFEST immutability", () => {
  it("is frozen at runtime (Object.isFrozen)", () => {
    expect(Object.isFrozen(TOKEN_MANIFEST)).toBe(true);
  });

  it("individual entries are frozen at runtime (Object.isFrozen)", () => {
    expect(Object.isFrozen(TOKEN_MANIFEST[0])).toBe(true);
  });

  it("attempted mutation of TOKEN_MANIFEST[0].default throws in strict mode or is silently ignored", () => {
    const original = TOKEN_MANIFEST[0].default;
    try {
      (TOKEN_MANIFEST[0] as any).default = "corrupted";
    } catch {
      /* expected in strict mode */
    }
    expect(TOKEN_MANIFEST[0].default).toBe(original);
  });

  it("returns the same reference on repeated imports", async () => {
    const { TOKEN_MANIFEST: reimport } = await import("../manifest.js");
    expect(reimport).toBe(TOKEN_MANIFEST);
  });
});

// ---------------------------------------------------------------------------
// Shadow tokens — must use type "shadow" (not "easing")
// ---------------------------------------------------------------------------

describe("Shadow token entries", () => {
  const shadowEntries = TOKEN_MANIFEST.filter((e) => e.category === "shadow");

  it("there is at least one shadow token in the manifest", () => {
    expect(shadowEntries.length).toBeGreaterThan(0);
  });

  it('all shadow tokens have type "shadow" (not "easing")', () => {
    for (const entry of shadowEntries) {
      expect(entry.type).toBe("shadow");
    }
  });

  it("all shadow token defaults are non-empty strings", () => {
    for (const entry of shadowEntries) {
      expect(typeof entry.default).toBe("string");
      expect((entry.default as string).length).toBeGreaterThan(0);
    }
  });
});
