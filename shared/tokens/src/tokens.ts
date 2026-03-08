/**
 * tokens.ts
 *
 * Canonical design token constants for all Syntek UI packages.
 *
 * Each string constant holds a CSS custom property reference of the form
 * `var(--<property-name>)`. Components pass these directly to inline styles
 * or Tailwind arbitrary-value utilities. The actual colour/size values live
 * in `tokens.css` and can be overridden at `:root` in any consuming project
 * without touching component code.
 *
 * Breakpoint constants are numeric pixel values (no CSS var) so they can be
 * used directly in JavaScript media-query logic and NativeWind/StyleSheet
 * configuration where a raw number is required.
 */

// ---------------------------------------------------------------------------
// Colour tokens — semantic aliases
// ---------------------------------------------------------------------------

/** References `--color-primary` — default: blue-600. */
export const COLOR_PRIMARY = "var(--color-primary)";

/** References `--color-secondary` — default: purple-600. */
export const COLOR_SECONDARY = "var(--color-secondary)";

/** References `--color-destructive` — default: red-600. */
export const COLOR_DESTRUCTIVE = "var(--color-destructive)";

/** References `--color-muted` — default: gray-500. */
export const COLOR_MUTED = "var(--color-muted)";

/** References `--color-surface` — default: white. */
export const COLOR_SURFACE = "var(--color-surface)";

/** References `--color-background` — default: gray-50. */
export const COLOR_BACKGROUND = "var(--color-background)";

/** References `--color-foreground` — default: gray-900. */
export const COLOR_FOREGROUND = "var(--color-foreground)";

/** References `--color-border` — default: gray-200. */
export const COLOR_BORDER = "var(--color-border)";

// ---------------------------------------------------------------------------
// Spacing tokens — 4 px base scale
// ---------------------------------------------------------------------------

/** References `--spacing-1` — 4 px. */
export const SPACING_1 = "var(--spacing-1)";

/** References `--spacing-2` — 8 px. */
export const SPACING_2 = "var(--spacing-2)";

/** References `--spacing-3` — 12 px. */
export const SPACING_3 = "var(--spacing-3)";

/** References `--spacing-4` — 16 px. */
export const SPACING_4 = "var(--spacing-4)";

/** References `--spacing-5` — 20 px. */
export const SPACING_5 = "var(--spacing-5)";

/** References `--spacing-6` — 24 px. */
export const SPACING_6 = "var(--spacing-6)";

/** References `--spacing-8` — 32 px. */
export const SPACING_8 = "var(--spacing-8)";

/** References `--spacing-10` — 40 px. */
export const SPACING_10 = "var(--spacing-10)";

/** References `--spacing-12` — 48 px. */
export const SPACING_12 = "var(--spacing-12)";

/** References `--spacing-16` — 64 px. */
export const SPACING_16 = "var(--spacing-16)";

/** References `--spacing-20` — 80 px. */
export const SPACING_20 = "var(--spacing-20)";

/** References `--spacing-24` — 96 px. */
export const SPACING_24 = "var(--spacing-24)";

/** References `--spacing-32` — 128 px. */
export const SPACING_32 = "var(--spacing-32)";

// ---------------------------------------------------------------------------
// Typography — font-size scale
// ---------------------------------------------------------------------------

/** References `--font-size-xs` — 0.75 rem. */
export const FONT_SIZE_XS = "var(--font-size-xs)";

/** References `--font-size-sm` — 0.875 rem. */
export const FONT_SIZE_SM = "var(--font-size-sm)";

/** References `--font-size-base` — 1 rem. */
export const FONT_SIZE_BASE = "var(--font-size-base)";

/** References `--font-size-lg` — 1.125 rem. */
export const FONT_SIZE_LG = "var(--font-size-lg)";

/** References `--font-size-xl` — 1.25 rem. */
export const FONT_SIZE_XL = "var(--font-size-xl)";

/** References `--font-size-2xl` — 1.5 rem. */
export const FONT_SIZE_2XL = "var(--font-size-2xl)";

/** References `--font-size-3xl` — 1.875 rem. */
export const FONT_SIZE_3XL = "var(--font-size-3xl)";

/** References `--font-size-4xl` — 2.25 rem. */
export const FONT_SIZE_4XL = "var(--font-size-4xl)";

/** References `--font-size-5xl` — 3 rem. */
export const FONT_SIZE_5XL = "var(--font-size-5xl)";

// ---------------------------------------------------------------------------
// Typography — font-weight
// ---------------------------------------------------------------------------

/** References `--font-weight-light` — 300. */
export const FONT_WEIGHT_LIGHT = "var(--font-weight-light)";

/** References `--font-weight-normal` — 400. */
export const FONT_WEIGHT_NORMAL = "var(--font-weight-normal)";

/** References `--font-weight-medium` — 500. */
export const FONT_WEIGHT_MEDIUM = "var(--font-weight-medium)";

/** References `--font-weight-semibold` — 600. */
export const FONT_WEIGHT_SEMIBOLD = "var(--font-weight-semibold)";

/** References `--font-weight-bold` — 700. */
export const FONT_WEIGHT_BOLD = "var(--font-weight-bold)";

// ---------------------------------------------------------------------------
// Font families
// ---------------------------------------------------------------------------

/**
 * References `--font-sans`.
 *
 * Defaults to the system sans-serif stack defined in `tokens.css`. Consuming
 * Next.js projects override this at `:root` via `next/font` variable injection
 * without modifying any component.
 */
export const FONT_SANS = "var(--font-sans)";

/**
 * References `--font-serif`.
 *
 * Defaults to the system serif stack. Override at `:root` as needed.
 */
export const FONT_SERIF = "var(--font-serif)";

/**
 * References `--font-mono`.
 *
 * Defaults to the system monospace stack. Override at `:root` as needed.
 */
export const FONT_MONO = "var(--font-mono)";

// ---------------------------------------------------------------------------
// Breakpoints — numeric pixel values (for use in JS/TS and NativeWind config)
// ---------------------------------------------------------------------------

/** Small breakpoint — 640 px. Matches the Tailwind `sm` default. */
export const BREAKPOINT_SM = 640;

/** Medium breakpoint — 768 px. Matches the Tailwind `md` default. */
export const BREAKPOINT_MD = 768;

/** Large breakpoint — 1024 px. Matches the Tailwind `lg` default. */
export const BREAKPOINT_LG = 1024;

/** Extra-large breakpoint — 1280 px. Matches the Tailwind `xl` default. */
export const BREAKPOINT_XL = 1280;

/** 2× extra-large breakpoint — 1536 px. Matches the Tailwind `2xl` default. */
export const BREAKPOINT_2XL = 1536;

// ---------------------------------------------------------------------------
// Border radius
// ---------------------------------------------------------------------------

/** References `--radius-sm` — 0.25 rem. */
export const RADIUS_SM = "var(--radius-sm)";

/** References `--radius-md` — 0.375 rem. */
export const RADIUS_MD = "var(--radius-md)";

/** References `--radius-lg` — 0.5 rem. */
export const RADIUS_LG = "var(--radius-lg)";

/** References `--radius-full` — 9999 px (pill shape). */
export const RADIUS_FULL = "var(--radius-full)";

// ---------------------------------------------------------------------------
// Shadows
// ---------------------------------------------------------------------------

/** References `--shadow-sm` — subtle elevation. */
export const SHADOW_SM = "var(--shadow-sm)";

/** References `--shadow-md` — medium elevation. */
export const SHADOW_MD = "var(--shadow-md)";

/** References `--shadow-lg` — strong elevation. */
export const SHADOW_LG = "var(--shadow-lg)";

// ---------------------------------------------------------------------------
// Z-index
// ---------------------------------------------------------------------------

/** References `--z-base` — 0, base stacking context. */
export const Z_BASE = "var(--z-base)";

/** References `--z-dropdown` — 1000, dropdown menus. */
export const Z_DROPDOWN = "var(--z-dropdown)";

/** References `--z-sticky` — 1100, sticky headers. */
export const Z_STICKY = "var(--z-sticky)";

/** References `--z-modal` — 1300, modal overlays. */
export const Z_MODAL = "var(--z-modal)";

/** References `--z-toast` — 1400, toast notifications. */
export const Z_TOAST = "var(--z-toast)";

/** References `--z-tooltip` — 1500, tooltips. */
export const Z_TOOLTIP = "var(--z-tooltip)";

// ---------------------------------------------------------------------------
// Transition
// ---------------------------------------------------------------------------

/** References `--transition-duration-fast` — 150 ms. */
export const TRANSITION_DURATION_FAST = "var(--transition-duration-fast)";

/** References `--transition-duration-base` — 200 ms. */
export const TRANSITION_DURATION_BASE = "var(--transition-duration-base)";

/** References `--transition-duration-slow` — 300 ms. */
export const TRANSITION_DURATION_SLOW = "var(--transition-duration-slow)";

/** References `--transition-easing-default` — ease-in-out (material standard). */
export const TRANSITION_EASING_DEFAULT = "var(--transition-easing-default)";

/** References `--transition-easing-in` — accelerate (enter). */
export const TRANSITION_EASING_IN = "var(--transition-easing-in)";

/** References `--transition-easing-out` — decelerate (exit). */
export const TRANSITION_EASING_OUT = "var(--transition-easing-out)";
