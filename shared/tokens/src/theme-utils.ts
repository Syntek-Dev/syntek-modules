import { TOKEN_MANIFEST } from "./manifest.js";

/**
 * theme-utils.ts — CSS theme block generator (US075)
 *
 * The only Next.js integration surface @syntek/tokens exposes.
 *
 * buildThemeStyle converts a per-tenant override map into a :root { ... } CSS
 * block. syntek-platform calls this on branding form save, minifies the result,
 * computes a sha256 hash, and writes the compiled CSS to the tenant_themes table.
 * The platform then serves it from /api/theme/{tenantId}.css?v={hash} with
 * Cache-Control: public, max-age=31536000, immutable so the CDN caches it
 * indefinitely. The hash in the URL acts as the cache-bust key.
 *
 * Responsibilities of this function:
 *   ✓ Format the CSS :root block from the override map
 *
 * NOT responsibilities of this function:
 *   ✗ Validate keys or values — use isValidCssColour before calling this
 *   ✗ Minify the output — the platform strips whitespace before writing to DB
 *   ✗ Hash the output — the platform computes sha256 for the ETag / URL version
 *   ✗ Cache, revalidate, or serve — those are syntek-platform concerns
 *   ✗ Write to the database — syntek-platform owns tenant_themes
 *
 * See SYNTEK-ARCHITECTURE.md § "Design Token Theming Architecture" for the full
 * optimised caching flow.
 */

/**
 * Convert a per-tenant token override map into a CSS `:root { ... }` block.
 *
 * @param overrides - A flat map of CSS custom property names to their override
 *   values, e.g. `{ "--color-primary": "oklch(0.55 0.2 250)" }`.
 *   Keys and values are written as-is — no escaping or validation is performed.
 * @returns A CSS string of the form:
 *   ```css
 *   :root {
 *     --color-primary: oklch(0.55 0.2 250);
 *   }
 *   ```
 *   Returns `":root {\n}"` when `overrides` is empty.
 *
 * @example
 * ```ts
 * import { buildThemeStyle } from "@syntek/tokens";
 *
 * const css = buildThemeStyle({
 *   "--color-primary": "oklch(0.55 0.2 250)",
 *   "--font-sans": "Inter, ui-sans-serif",
 * });
 * // ":root {\n  --color-primary: oklch(0.55 0.2 250);\n  --font-sans: Inter, ui-sans-serif;\n}"
 * ```
 */
export function buildThemeStyle(overrides: Record<string, string>): string {
  const entries = Object.entries(overrides);
  if (entries.length === 0) return ":root {\n}";
  const declarations = entries.map(([k, v]) => `  ${k}: ${v};`).join("\n");
  return `:root {\n${declarations}\n}`;
}

/**
 * Validate that every key in `overrides` is a recognised CSS custom property
 * from TOKEN_MANIFEST. This provides an allowlist check that callers MUST use
 * before passing overrides to `buildThemeStyle` to prevent CSS injection.
 *
 * Returns `true` only if ALL keys are valid cssVar names from the manifest.
 * Returns `true` for an empty overrides map (no keys to validate).
 *
 * @param overrides - The override map to validate.
 * @returns `true` if every key is a recognised TOKEN_MANIFEST cssVar.
 */
export function validateOverrideKeys(overrides: Record<string, string>): boolean {
  if (_allowedCssVars === undefined) {
    _allowedCssVars = new Set(TOKEN_MANIFEST.map((e) => e.cssVar));
  }
  const keys = Object.keys(overrides);
  return keys.every((key) => _allowedCssVars!.has(key));
}

let _allowedCssVars: Set<string> | undefined;
