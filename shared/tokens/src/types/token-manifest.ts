/**
 * TypeScript type definitions for the TOKEN_MANIFEST design token descriptor system.
 *
 * These types are consumed by the @syntek/tokens package to describe each design token
 * and by syntek-platform to render the correct branding form widget per token category.
 *
 * US075 — Design Token Manifest
 */

/**
 * The broad category a token belongs to.
 * Used to group tokens in the branding form UI.
 */
export type TokenCategory =
  | "colour"
  | "spacing"
  | "typography"
  | "radius"
  | "shadow"
  | "z-index"
  | "transition";

/**
 * The UI widget type that the branding form should render for this token.
 *
 * - "color"       → colour picker (accepts hex, rgb, hsl, oklch, named colours)
 * - "px"          → number input with px unit suffix
 * - "rem"         → number input with rem unit suffix
 * - "font-family" → font selector dropdown
 * - "font-weight" → numeric select (100–900)
 * - "number"      → plain number input (no unit — used for z-index)
 * - "duration"    → number input with ms unit suffix
 * - "easing"      → text input / cubic-bezier editor
 * - "shadow"      → text input for CSS box-shadow values
 */
export type TokenWidgetType =
  | "color"
  | "px"
  | "rem"
  | "font-family"
  | "font-weight"
  | "number"
  | "duration"
  | "easing"
  | "shadow";

/**
 * Describes a single design token entry in TOKEN_MANIFEST.
 *
 * TOKEN_MANIFEST is a static, read-only schema — it is never stored in or
 * mutated by the database. Overrides are written to syntek-settings keyed
 * by tenant ID.
 */
export interface TokenDescriptor {
  /** Constant name as exported from @syntek/tokens, e.g. "COLOR_PRIMARY". */
  key: string;
  /** CSS custom property name, e.g. "--color-primary". */
  cssVar: string;
  /** Broad category used for grouping in the branding form. */
  category: TokenCategory;
  /** Widget type that the platform branding form renders for this token. */
  type: TokenWidgetType;
  /**
   * Resolved default value.
   * - Colour tokens: hex string, e.g. "#2563eb". Never a var() reference.
   * - Spacing/font-size/radius: number (unit implied by `type`).
   * - Font-family/shadow/easing: string.
   * - Font-weight/z-index/duration: number.
   */
  default: string | number;
  /** Human-readable label for the branding form field. */
  label: string;
}
