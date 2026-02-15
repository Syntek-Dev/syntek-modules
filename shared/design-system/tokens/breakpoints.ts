/**
 * Design tokens - Responsive breakpoints
 *
 * Breakpoints for responsive design across web and mobile.
 * Mobile-first approach (min-width).
 */

export const breakpoints = {
  sm: '640px',   // Small devices (landscape phones)
  md: '768px',   // Medium devices (tablets)
  lg: '1024px',  // Large devices (laptops)
  xl: '1280px',  // Extra large devices (desktops)
  '2xl': '1536px', // 2X large devices (large desktops)
} as const;

export type BreakpointToken = typeof breakpoints;
