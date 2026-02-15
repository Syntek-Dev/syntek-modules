/**
 * Design tokens - Spacing scale
 *
 * 4px base scale for consistency across web and mobile.
 * Mobile devices benefit from slightly larger touch targets (minimum 44px for iOS).
 */

export const spacing = {
  0: '0px',
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  11: '44px',  // iOS minimum touch target
  12: '48px',
  16: '64px',
  20: '80px',
  24: '96px',
  32: '128px',
} as const;

export type SpacingToken = typeof spacing;
