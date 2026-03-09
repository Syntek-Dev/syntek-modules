/**
 * manifest.ts — Design Token Manifest (US075)
 *
 * TOKEN_MANIFEST is a static, read-only schema that describes every design token
 * in the @syntek/tokens package. The platform branding form reads this manifest
 * to determine which UI widget to render for each token.
 *
 * All entries follow the TokenDescriptor interface defined in types/token-manifest.ts.
 * Colour token defaults are resolved hex strings — never var() references.
 * The array is frozen at module level to satisfy the immutability requirements
 * of AC6 (same reference on repeated imports, Object.isFrozen returns true).
 */

import type { TokenDescriptor } from "./types/token-manifest.js";

// ---------------------------------------------------------------------------
// Colour tokens — category: "colour", type: "color"
// Defaults are resolved hex strings (AC5).
// ---------------------------------------------------------------------------

const COLOUR_TOKENS: TokenDescriptor[] = [
  {
    key: "COLOR_PRIMARY",
    cssVar: "--color-primary",
    category: "colour",
    type: "color",
    default: "#2563eb",
    label: "Primary colour",
  },
  {
    key: "COLOR_SECONDARY",
    cssVar: "--color-secondary",
    category: "colour",
    type: "color",
    default: "#9333ea",
    label: "Secondary colour",
  },
  {
    key: "COLOR_DESTRUCTIVE",
    cssVar: "--color-destructive",
    category: "colour",
    type: "color",
    default: "#dc2626",
    label: "Destructive colour",
  },
  {
    key: "COLOR_MUTED",
    cssVar: "--color-muted",
    category: "colour",
    type: "color",
    default: "#6b7280",
    label: "Muted colour",
  },
  {
    key: "COLOR_SURFACE",
    cssVar: "--color-surface",
    category: "colour",
    type: "color",
    default: "#ffffff",
    label: "Surface colour",
  },
  {
    key: "COLOR_BACKGROUND",
    cssVar: "--color-background",
    category: "colour",
    type: "color",
    default: "#f9fafb",
    label: "Background colour",
  },
  {
    key: "COLOR_FOREGROUND",
    cssVar: "--color-foreground",
    category: "colour",
    type: "color",
    default: "#111827",
    label: "Foreground colour",
  },
  {
    key: "COLOR_BORDER",
    cssVar: "--color-border",
    category: "colour",
    type: "color",
    default: "#e5e7eb",
    label: "Border colour",
  },
  {
    key: "COLOR_SUCCESS",
    cssVar: "--color-success",
    category: "colour",
    type: "color",
    default: "#16a34a",
    label: "Success colour",
  },
  {
    key: "COLOR_WARNING",
    cssVar: "--color-warning",
    category: "colour",
    type: "color",
    default: "#d97706",
    label: "Warning colour",
  },
  {
    key: "COLOR_INFO",
    cssVar: "--color-info",
    category: "colour",
    type: "color",
    default: "#0284c7",
    label: "Info colour",
  },
];

// ---------------------------------------------------------------------------
// Spacing tokens — category: "spacing", type: "px"
// Defaults are numbers representing pixel values (AC3).
// ---------------------------------------------------------------------------

const SPACING_TOKENS: TokenDescriptor[] = [
  {
    key: "SPACING_1",
    cssVar: "--spacing-1",
    category: "spacing",
    type: "px",
    default: 4,
    label: "Spacing 1 (4px)",
  },
  {
    key: "SPACING_2",
    cssVar: "--spacing-2",
    category: "spacing",
    type: "px",
    default: 8,
    label: "Spacing 2 (8px)",
  },
  {
    key: "SPACING_3",
    cssVar: "--spacing-3",
    category: "spacing",
    type: "px",
    default: 12,
    label: "Spacing 3 (12px)",
  },
  {
    key: "SPACING_4",
    cssVar: "--spacing-4",
    category: "spacing",
    type: "px",
    default: 16,
    label: "Spacing 4 (16px)",
  },
  {
    key: "SPACING_5",
    cssVar: "--spacing-5",
    category: "spacing",
    type: "px",
    default: 20,
    label: "Spacing 5 (20px)",
  },
  {
    key: "SPACING_6",
    cssVar: "--spacing-6",
    category: "spacing",
    type: "px",
    default: 24,
    label: "Spacing 6 (24px)",
  },
  {
    key: "SPACING_8",
    cssVar: "--spacing-8",
    category: "spacing",
    type: "px",
    default: 32,
    label: "Spacing 8 (32px)",
  },
  {
    key: "SPACING_10",
    cssVar: "--spacing-10",
    category: "spacing",
    type: "px",
    default: 40,
    label: "Spacing 10 (40px)",
  },
  {
    key: "SPACING_12",
    cssVar: "--spacing-12",
    category: "spacing",
    type: "px",
    default: 48,
    label: "Spacing 12 (48px)",
  },
  {
    key: "SPACING_16",
    cssVar: "--spacing-16",
    category: "spacing",
    type: "px",
    default: 64,
    label: "Spacing 16 (64px)",
  },
  {
    key: "SPACING_20",
    cssVar: "--spacing-20",
    category: "spacing",
    type: "px",
    default: 80,
    label: "Spacing 20 (80px)",
  },
  {
    key: "SPACING_24",
    cssVar: "--spacing-24",
    category: "spacing",
    type: "px",
    default: 96,
    label: "Spacing 24 (96px)",
  },
  {
    key: "SPACING_32",
    cssVar: "--spacing-32",
    category: "spacing",
    type: "px",
    default: 128,
    label: "Spacing 32 (128px)",
  },
];

// ---------------------------------------------------------------------------
// Font-size tokens — category: "typography", type: "rem"
// ---------------------------------------------------------------------------

const FONT_SIZE_TOKENS: TokenDescriptor[] = [
  {
    key: "FONT_SIZE_XS",
    cssVar: "--font-size-xs",
    category: "typography",
    type: "rem",
    default: 0.75,
    label: "Font size XS (12px)",
  },
  {
    key: "FONT_SIZE_SM",
    cssVar: "--font-size-sm",
    category: "typography",
    type: "rem",
    default: 0.875,
    label: "Font size SM (14px)",
  },
  {
    key: "FONT_SIZE_BASE",
    cssVar: "--font-size-base",
    category: "typography",
    type: "rem",
    default: 1,
    label: "Font size Base (16px)",
  },
  {
    key: "FONT_SIZE_LG",
    cssVar: "--font-size-lg",
    category: "typography",
    type: "rem",
    default: 1.125,
    label: "Font size LG (18px)",
  },
  {
    key: "FONT_SIZE_XL",
    cssVar: "--font-size-xl",
    category: "typography",
    type: "rem",
    default: 1.25,
    label: "Font size XL (20px)",
  },
  {
    key: "FONT_SIZE_2XL",
    cssVar: "--font-size-2xl",
    category: "typography",
    type: "rem",
    default: 1.5,
    label: "Font size 2XL (24px)",
  },
  {
    key: "FONT_SIZE_3XL",
    cssVar: "--font-size-3xl",
    category: "typography",
    type: "rem",
    default: 1.875,
    label: "Font size 3XL (30px)",
  },
  {
    key: "FONT_SIZE_4XL",
    cssVar: "--font-size-4xl",
    category: "typography",
    type: "rem",
    default: 2.25,
    label: "Font size 4XL (36px)",
  },
  {
    key: "FONT_SIZE_5XL",
    cssVar: "--font-size-5xl",
    category: "typography",
    type: "rem",
    default: 3,
    label: "Font size 5XL (48px)",
  },
];

// ---------------------------------------------------------------------------
// Font-weight tokens — category: "typography", type: "font-weight"
// ---------------------------------------------------------------------------

const FONT_WEIGHT_TOKENS: TokenDescriptor[] = [
  {
    key: "FONT_WEIGHT_LIGHT",
    cssVar: "--font-weight-light",
    category: "typography",
    type: "font-weight",
    default: 300,
    label: "Font weight light",
  },
  {
    key: "FONT_WEIGHT_NORMAL",
    cssVar: "--font-weight-normal",
    category: "typography",
    type: "font-weight",
    default: 400,
    label: "Font weight normal",
  },
  {
    key: "FONT_WEIGHT_MEDIUM",
    cssVar: "--font-weight-medium",
    category: "typography",
    type: "font-weight",
    default: 500,
    label: "Font weight medium",
  },
  {
    key: "FONT_WEIGHT_SEMIBOLD",
    cssVar: "--font-weight-semibold",
    category: "typography",
    type: "font-weight",
    default: 600,
    label: "Font weight semibold",
  },
  {
    key: "FONT_WEIGHT_BOLD",
    cssVar: "--font-weight-bold",
    category: "typography",
    type: "font-weight",
    default: 700,
    label: "Font weight bold",
  },
];

// ---------------------------------------------------------------------------
// Font-family tokens — category: "typography", type: "font-family" (AC4)
// ---------------------------------------------------------------------------

const FONT_FAMILY_TOKENS: TokenDescriptor[] = [
  {
    key: "FONT_SANS",
    cssVar: "--font-sans",
    category: "typography",
    type: "font-family",
    default: "Inter, ui-sans-serif, system-ui",
    label: "Sans-serif font family",
  },
  {
    key: "FONT_SERIF",
    cssVar: "--font-serif",
    category: "typography",
    type: "font-family",
    default: "Georgia, ui-serif, serif",
    label: "Serif font family",
  },
  {
    key: "FONT_MONO",
    cssVar: "--font-mono",
    category: "typography",
    type: "font-family",
    default: "JetBrains Mono, ui-monospace, monospace",
    label: "Monospace font family",
  },
];

// ---------------------------------------------------------------------------
// Line-height tokens — category: "typography", type: "number"
// ---------------------------------------------------------------------------

const LINE_HEIGHT_TOKENS: TokenDescriptor[] = [
  {
    key: "LINE_HEIGHT_TIGHT",
    cssVar: "--line-height-tight",
    category: "typography",
    type: "number",
    default: 1.25,
    label: "Line height tight",
  },
  {
    key: "LINE_HEIGHT_BASE",
    cssVar: "--line-height-base",
    category: "typography",
    type: "number",
    default: 1.5,
    label: "Line height base",
  },
  {
    key: "LINE_HEIGHT_LOOSE",
    cssVar: "--line-height-loose",
    category: "typography",
    type: "number",
    default: 1.75,
    label: "Line height loose",
  },
];

// ---------------------------------------------------------------------------
// Letter-spacing tokens — category: "typography", type: "rem"
// ---------------------------------------------------------------------------

const LETTER_SPACING_TOKENS: TokenDescriptor[] = [
  {
    key: "LETTER_SPACING_TIGHT",
    cssVar: "--letter-spacing-tight",
    category: "typography",
    type: "rem",
    default: -0.025,
    label: "Letter spacing tight",
  },
  {
    key: "LETTER_SPACING_WIDE",
    cssVar: "--letter-spacing-wide",
    category: "typography",
    type: "rem",
    default: 0.025,
    label: "Letter spacing wide",
  },
];

// ---------------------------------------------------------------------------
// Border radius tokens — category: "radius", type: "rem"
// ---------------------------------------------------------------------------

const RADIUS_TOKENS: TokenDescriptor[] = [
  {
    key: "RADIUS_SM",
    cssVar: "--radius-sm",
    category: "radius",
    type: "rem",
    default: 0.125,
    label: "Border radius SM (2px)",
  },
  {
    key: "RADIUS_MD",
    cssVar: "--radius-md",
    category: "radius",
    type: "rem",
    default: 0.375,
    label: "Border radius MD (6px)",
  },
  {
    key: "RADIUS_LG",
    cssVar: "--radius-lg",
    category: "radius",
    type: "rem",
    default: 0.5,
    label: "Border radius LG (8px)",
  },
  {
    key: "RADIUS_XL",
    cssVar: "--radius-xl",
    category: "radius",
    type: "rem",
    default: 0.75,
    label: "Border radius XL (12px)",
  },
];

// ---------------------------------------------------------------------------
// Shadow tokens — category: "shadow", type: "shadow"
// ---------------------------------------------------------------------------

const SHADOW_TOKENS: TokenDescriptor[] = [
  {
    key: "SHADOW_SM",
    cssVar: "--shadow-sm",
    category: "shadow",
    type: "shadow",
    default: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    label: "Shadow SM",
  },
  {
    key: "SHADOW_MD",
    cssVar: "--shadow-md",
    category: "shadow",
    type: "shadow",
    default: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    label: "Shadow MD",
  },
  {
    key: "SHADOW_LG",
    cssVar: "--shadow-lg",
    category: "shadow",
    type: "shadow",
    default: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    label: "Shadow LG",
  },
];

// ---------------------------------------------------------------------------
// Z-index tokens — category: "z-index", type: "number"
// ---------------------------------------------------------------------------

const Z_INDEX_TOKENS: TokenDescriptor[] = [
  {
    key: "Z_BASE",
    cssVar: "--z-base",
    category: "z-index",
    type: "number",
    default: 0,
    label: "Z-index base",
  },
  {
    key: "Z_DROPDOWN",
    cssVar: "--z-dropdown",
    category: "z-index",
    type: "number",
    default: 1000,
    label: "Z-index dropdown",
  },
  {
    key: "Z_STICKY",
    cssVar: "--z-sticky",
    category: "z-index",
    type: "number",
    default: 1100,
    label: "Z-index sticky",
  },
  {
    key: "Z_OVERLAY",
    cssVar: "--z-overlay",
    category: "z-index",
    type: "number",
    default: 1200,
    label: "Z-index overlay",
  },
  {
    key: "Z_MODAL",
    cssVar: "--z-modal",
    category: "z-index",
    type: "number",
    default: 1300,
    label: "Z-index modal",
  },
  {
    key: "Z_POPOVER",
    cssVar: "--z-popover",
    category: "z-index",
    type: "number",
    default: 1400,
    label: "Z-index popover",
  },
  {
    key: "Z_TOOLTIP",
    cssVar: "--z-tooltip",
    category: "z-index",
    type: "number",
    default: 1500,
    label: "Z-index tooltip",
  },
];

// ---------------------------------------------------------------------------
// Transition duration tokens — category: "transition", type: "duration"
// ---------------------------------------------------------------------------

const TRANSITION_DURATION_TOKENS: TokenDescriptor[] = [
  {
    key: "TRANSITION_DURATION_FAST",
    cssVar: "--transition-duration-fast",
    category: "transition",
    type: "duration",
    default: 150,
    label: "Transition duration fast (150ms)",
  },
  {
    key: "TRANSITION_DURATION_BASE",
    cssVar: "--transition-duration-base",
    category: "transition",
    type: "duration",
    default: 200,
    label: "Transition duration base (200ms)",
  },
  {
    key: "TRANSITION_DURATION_SLOW",
    cssVar: "--transition-duration-slow",
    category: "transition",
    type: "duration",
    default: 300,
    label: "Transition duration slow (300ms)",
  },
];

// ---------------------------------------------------------------------------
// Transition easing tokens — category: "transition", type: "easing"
// ---------------------------------------------------------------------------

const TRANSITION_EASING_TOKENS: TokenDescriptor[] = [
  {
    key: "TRANSITION_EASING_DEFAULT",
    cssVar: "--transition-easing-default",
    category: "transition",
    type: "easing",
    default: "cubic-bezier(0.4, 0, 0.2, 1)",
    label: "Transition easing default",
  },
  {
    key: "TRANSITION_EASING_IN",
    cssVar: "--transition-easing-in",
    category: "transition",
    type: "easing",
    default: "cubic-bezier(0.4, 0, 1, 1)",
    label: "Transition easing in",
  },
  {
    key: "TRANSITION_EASING_OUT",
    cssVar: "--transition-easing-out",
    category: "transition",
    type: "easing",
    default: "cubic-bezier(0, 0, 0.2, 1)",
    label: "Transition easing out",
  },
];

// ---------------------------------------------------------------------------
// TOKEN_MANIFEST — exported as a frozen readonly array (AC6)
// Frozen at module level so Object.isFrozen returns true and the same
// reference is returned on every import via the module cache.
// Each individual TokenDescriptor is also frozen to prevent silent mutation
// of shared singleton entries at runtime.
// ---------------------------------------------------------------------------

export const TOKEN_MANIFEST: readonly TokenDescriptor[] = Object.freeze(
  [
    ...COLOUR_TOKENS,
    ...SPACING_TOKENS,
    ...FONT_SIZE_TOKENS,
    ...FONT_WEIGHT_TOKENS,
    ...FONT_FAMILY_TOKENS,
    ...LINE_HEIGHT_TOKENS,
    ...LETTER_SPACING_TOKENS,
    ...RADIUS_TOKENS,
    ...SHADOW_TOKENS,
    ...Z_INDEX_TOKENS,
    ...TRANSITION_DURATION_TOKENS,
    ...TRANSITION_EASING_TOKENS,
  ].map((entry) => Object.freeze(entry)),
);
