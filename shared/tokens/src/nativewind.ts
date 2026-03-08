/**
 * nativewind.ts
 *
 * NativeWind 4 compatible Tailwind CSS config preset for Syntek design tokens.
 *
 * Consuming Expo applications import `nativewindPreset` and spread it into
 * their `tailwind.config.js`. The preset maps all Syntek token CSS custom
 * property references to Tailwind utility class keys so that `bg-primary`,
 * `text-foreground`, `p-4`, `font-sans`, and `rounded-md` resolve to the
 * correct token values at runtime via the NativeWind CSS variable engine.
 *
 * Breakpoint constants (`screens`) use numeric pixel values from `tokens.ts`
 * because NativeWind expects string pixel values for responsive breakpoints,
 * not CSS variable references.
 *
 * Usage in a consuming Expo app:
 *
 *   // tailwind.config.js
 *   const { nativewindPreset } = require('@syntek/tokens/nativewind');
 *   module.exports = {
 *     content: ['./app/**\/*.{ts,tsx}', './components/**\/*.{ts,tsx}'],
 *     presets: [nativewindPreset],
 *   };
 */

import {
  BREAKPOINT_SM,
  BREAKPOINT_MD,
  BREAKPOINT_LG,
  BREAKPOINT_XL,
  BREAKPOINT_2XL,
} from "./tokens.js";

// ---------------------------------------------------------------------------
// Type definitions
// ---------------------------------------------------------------------------

/**
 * Represents a Tailwind CSS theme section as a flat record of string keys
 * to string CSS value references (typically CSS var() expressions or px strings).
 */
type ThemeRecord = Record<string, string>;

/**
 * Represents a Tailwind CSS font-size entry. Each entry is a tuple of
 * [fontSize, lineHeightConfig] as per the Tailwind v3 font-size format.
 * NativeWind 4 accepts both plain strings and the tuple form.
 */
type FontSizeEntry = string | [string, { lineHeight?: string }];

/**
 * Shape of the Tailwind CSS theme object within the NativeWind preset.
 * Only the sections relevant to token coverage are defined here.
 */
interface NativewindTheme {
  colors: ThemeRecord;
  spacing: ThemeRecord;
  fontSize: Record<string, FontSizeEntry>;
  fontFamily: ThemeRecord;
  borderRadius: ThemeRecord;
  screens: ThemeRecord;
  boxShadow: ThemeRecord;
}

/**
 * Shape of the NativeWind 4 preset exported by this module.
 *
 * The preset follows the Tailwind CSS config `presets` object format.
 * Consuming projects pass the preset to the `presets` array in their own
 * `tailwind.config.js`. Any key in `theme` can be further extended in the
 * consuming project's own `theme.extend` block.
 */
export interface NativewindPreset {
  theme: NativewindTheme;
}

// ---------------------------------------------------------------------------
// Colour tokens
// ---------------------------------------------------------------------------

/**
 * Maps Tailwind colour utility keys to CSS custom property references.
 *
 * All values use `var(--color-<name>)` so NativeWind resolves them at
 * runtime from the token CSS variables loaded into the Expo app.
 */
const colors: ThemeRecord = {
  primary: "var(--color-primary)",
  secondary: "var(--color-secondary)",
  destructive: "var(--color-destructive)",
  muted: "var(--color-muted)",
  surface: "var(--color-surface)",
  background: "var(--color-background)",
  foreground: "var(--color-foreground)",
  border: "var(--color-border)",
};

// ---------------------------------------------------------------------------
// Spacing tokens
// ---------------------------------------------------------------------------

/**
 * Maps Tailwind spacing scale keys to CSS custom property references.
 *
 * Keys match the Tailwind default numeric scale (1–32) and correspond to
 * the SPACING_N constants exported from `tokens.ts`. Unlisted steps between
 * 8 and 12 (e.g. 9, 10, 11) are omitted to match the Syntek token scale.
 */
const spacing: ThemeRecord = {
  "1": "var(--spacing-1)",
  "2": "var(--spacing-2)",
  "3": "var(--spacing-3)",
  "4": "var(--spacing-4)",
  "5": "var(--spacing-5)",
  "6": "var(--spacing-6)",
  "8": "var(--spacing-8)",
  "10": "var(--spacing-10)",
  "12": "var(--spacing-12)",
  "16": "var(--spacing-16)",
  "20": "var(--spacing-20)",
  "24": "var(--spacing-24)",
  "32": "var(--spacing-32)",
};

// ---------------------------------------------------------------------------
// Font-size tokens
// ---------------------------------------------------------------------------

/**
 * Maps Tailwind text-size utility keys to CSS custom property references.
 *
 * Each entry uses the Tailwind tuple form so a default line-height can be
 * paired with the font-size token. NativeWind 4 supports this form.
 * Line-height values reference the corresponding CSS custom properties.
 */
const fontSize: Record<string, FontSizeEntry> = {
  xs: ["var(--font-size-xs)", { lineHeight: "var(--line-height-xs)" }],
  sm: ["var(--font-size-sm)", { lineHeight: "var(--line-height-sm)" }],
  base: ["var(--font-size-base)", { lineHeight: "var(--line-height-base)" }],
  lg: ["var(--font-size-lg)", { lineHeight: "var(--line-height-lg)" }],
  xl: ["var(--font-size-xl)", { lineHeight: "var(--line-height-xl)" }],
  "2xl": ["var(--font-size-2xl)", { lineHeight: "var(--line-height-2xl)" }],
  "3xl": ["var(--font-size-3xl)", { lineHeight: "var(--line-height-3xl)" }],
  "4xl": ["var(--font-size-4xl)", { lineHeight: "var(--line-height-4xl)" }],
  "5xl": ["var(--font-size-5xl)", { lineHeight: "var(--line-height-5xl)" }],
};

// ---------------------------------------------------------------------------
// Font-family tokens
// ---------------------------------------------------------------------------

/**
 * Maps Tailwind font-family utility keys to CSS custom property references.
 *
 * Consuming Expo projects override these at `:root` (or via NativeWind
 * CSS injection) to apply a specific typeface without touching component code.
 */
const fontFamily: ThemeRecord = {
  sans: "var(--font-sans)",
  serif: "var(--font-serif)",
  mono: "var(--font-mono)",
};

// ---------------------------------------------------------------------------
// Border radius tokens
// ---------------------------------------------------------------------------

/**
 * Maps Tailwind rounded utility keys to CSS custom property references.
 *
 * Covers the four radius steps defined in `tokens.css`.
 */
const borderRadius: ThemeRecord = {
  sm: "var(--radius-sm)",
  md: "var(--radius-md)",
  lg: "var(--radius-lg)",
  full: "var(--radius-full)",
};

// ---------------------------------------------------------------------------
// Responsive breakpoints
// ---------------------------------------------------------------------------

/**
 * Maps Tailwind screen utility keys to pixel string values.
 *
 * Breakpoints use the numeric constants from `tokens.ts` converted to `px`
 * strings because NativeWind expects string pixel values for `screens`, not
 * CSS variable references. This matches the standard Tailwind default scale.
 */
const screens: ThemeRecord = {
  sm: `${BREAKPOINT_SM}px`,
  md: `${BREAKPOINT_MD}px`,
  lg: `${BREAKPOINT_LG}px`,
  xl: `${BREAKPOINT_XL}px`,
  "2xl": `${BREAKPOINT_2XL}px`,
};

// ---------------------------------------------------------------------------
// Shadow tokens
// ---------------------------------------------------------------------------

/**
 * Maps Tailwind shadow utility keys to CSS custom property references.
 *
 * NativeWind 4 supports CSS box-shadow syntax on Android and iOS via its
 * shadow normalisation layer. The actual shadow values are defined in
 * `tokens.css` and can be overridden per project.
 */
const boxShadow: ThemeRecord = {
  sm: "var(--shadow-sm)",
  md: "var(--shadow-md)",
  lg: "var(--shadow-lg)",
};

// ---------------------------------------------------------------------------
// Preset export
// ---------------------------------------------------------------------------

/**
 * NativeWind 4 Tailwind CSS preset for Syntek design tokens.
 *
 * Spread into the `presets` array of a consuming Expo project's
 * `tailwind.config.js` to enable all Syntek token utility classes.
 *
 * The preset defines the full theme rather than only `theme.extend`, so
 * consuming projects can override individual keys via their own `theme.extend`
 * block without duplicating all token mappings.
 *
 * @example
 * ```js
 * // tailwind.config.js
 * const { nativewindPreset } = require('@syntek/tokens/nativewind');
 * module.exports = {
 *   content: ['./app/**\/*.{ts,tsx}', './components/**\/*.{ts,tsx}'],
 *   presets: [nativewindPreset],
 * };
 * ```
 */
export const nativewindPreset: NativewindPreset = {
  theme: {
    colors,
    spacing,
    fontSize,
    fontFamily,
    borderRadius,
    screens,
    boxShadow,
  },
};
