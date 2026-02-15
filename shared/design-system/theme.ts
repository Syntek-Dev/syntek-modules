/**
 * Unified theme object
 *
 * Provides a single source of truth for design tokens.
 * Can be used by both web and mobile components.
 */

import { colors, typography, spacing, borders, shadows, breakpoints, zIndex } from './tokens';

export const theme = {
  colors,
  typography,
  spacing,
  borders,
  shadows,
  breakpoints,
  zIndex,
} as const;

export type Theme = typeof theme;

/**
 * Helper function to get theme values
 *
 * @param path - Dot-notation path to theme value (e.g., 'colors.primary.500')
 * @returns Theme value
 */
export function getThemeValue(path: string): string | number {
  const keys = path.split('.');
  let value: any = theme;

  for (const key of keys) {
    value = value[key];
    if (value === undefined) {
      throw new Error(`Theme value not found: ${path}`);
    }
  }

  return value;
}
