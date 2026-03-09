/**
 * Unit tests — buildThemeStyle CSS generator (US075).
 *
 * buildThemeStyle is the only Next.js integration surface @syntek/tokens exposes.
 * It converts a per-tenant override map into a :root { ... } CSS block that
 * syntek-platform writes to the tenant_themes table (after minification) and
 * serves via /api/theme/{tenantId}.css.
 *
 * The function does NOT validate keys or values — that is isValidCssColour's job.
 * It does NOT minify — the platform minifies before writing to the DB.
 * It does NOT handle caching, revalidation, or <link> tags — those are platform concerns.
 *
 * Red phase: buildThemeStyle is not yet exported, so all tests fail with an import error.
 */

import { describe, it, expect } from "vitest";

import { buildThemeStyle, validateOverrideKeys } from "../theme-utils.js";

describe("buildThemeStyle", () => {
  it("returns ':root {\\n}' for an empty override map", () => {
    expect(buildThemeStyle({})).toBe(":root {\n}");
  });

  it("wraps declarations in a :root block", () => {
    const result = buildThemeStyle({ "--color-primary": "oklch(0.55 0.2 250)" });
    expect(result.startsWith(":root {")).toBe(true);
    expect(result.endsWith("}")).toBe(true);
  });

  it("formats a single override with two-space indent and semicolon", () => {
    const result = buildThemeStyle({ "--color-primary": "oklch(0.55 0.2 250)" });
    expect(result).toBe(":root {\n  --color-primary: oklch(0.55 0.2 250);\n}");
  });

  it("formats multiple overrides each on their own indented line", () => {
    const result = buildThemeStyle({
      "--color-primary": "#2563eb",
      "--color-secondary": "#9333ea",
    });
    expect(result).toBe(":root {\n  --color-primary: #2563eb;\n  --color-secondary: #9333ea;\n}");
  });

  it("passes key and value through as-is — no escaping or transformation", () => {
    const result = buildThemeStyle({ "--font-sans": "Inter, ui-sans-serif, system-ui" });
    expect(result).toContain("--font-sans: Inter, ui-sans-serif, system-ui;");
  });

  it("handles oklch values with spaces correctly", () => {
    const result = buildThemeStyle({ "--color-primary": "oklch(0.55 0.2 250)" });
    expect(result).toContain("--color-primary: oklch(0.55 0.2 250);");
  });

  it("handles all token categories in a single call", () => {
    const overrides = {
      "--color-primary": "#2563eb",
      "--spacing-4": "16px",
      "--font-sans": "Inter, sans-serif",
      "--font-weight-bold": "700",
      "--radius-md": "0.375rem",
      "--z-modal": "1300",
      "--transition-duration-base": "200ms",
      "--transition-easing-default": "cubic-bezier(0.4, 0, 0.2, 1)",
    };
    const result = buildThemeStyle(overrides);
    expect(result.startsWith(":root {")).toBe(true);
    expect(result.endsWith("}")).toBe(true);
    for (const [key, value] of Object.entries(overrides)) {
      expect(result).toContain(`  ${key}: ${value};`);
    }
  });

  it("returns a string type", () => {
    expect(typeof buildThemeStyle({})).toBe("string");
    expect(typeof buildThemeStyle({ "--color-primary": "#fff" })).toBe("string");
  });

  it("each override appears on exactly one line", () => {
    const result = buildThemeStyle({
      "--color-primary": "#2563eb",
      "--color-secondary": "#9333ea",
      "--color-muted": "#6b7280",
    });
    const lines = result.split("\n");
    // :root { + 3 declarations + closing }
    expect(lines.length).toBe(5);
    expect(lines[0]).toBe(":root {");
    expect(lines[4]).toBe("}");
  });

  it("documents that buildThemeStyle passes keys through without validation (contract)", () => {
    // buildThemeStyle has NO internal key validation — callers MUST use
    // validateOverrideKeys first. This test documents the contract.
    const result = buildThemeStyle({ "--color-primary": "red" });
    expect(result).toContain("--color-primary: red;");
  });
});

// ---------------------------------------------------------------------------
// validateOverrideKeys — allowlist enforcement
// ---------------------------------------------------------------------------

describe("validateOverrideKeys", () => {
  it("returns true for all valid cssVar keys", () => {
    expect(
      validateOverrideKeys({
        "--color-primary": "#2563eb",
        "--spacing-4": "16px",
      }),
    ).toBe(true);
  });

  it("returns false for a key not in TOKEN_MANIFEST", () => {
    expect(validateOverrideKeys({ "--not-a-real-token": "red" })).toBe(false);
  });

  it("returns false for an injection attempt key", () => {
    expect(
      validateOverrideKeys({
        "--color-primary: red } body { background: red; --x": "#2563eb",
      }),
    ).toBe(false);
  });

  it("returns true for an empty overrides map", () => {
    expect(validateOverrideKeys({})).toBe(true);
  });
});
