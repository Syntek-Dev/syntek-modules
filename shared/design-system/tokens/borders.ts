/**
 * Design tokens - Borders
 *
 * Border radius and widths for consistent UI elements.
 */

export const borders = {
  // Border radius
  borderRadius: {
    none: '0px',
    sm: '4px',
    DEFAULT: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
    full: '9999px',
  },

  // Border widths
  borderWidth: {
    0: '0px',
    DEFAULT: '1px',
    2: '2px',
    4: '4px',
    8: '8px',
  },
} as const;

export type BorderToken = typeof borders;
