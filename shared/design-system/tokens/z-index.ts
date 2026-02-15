/**
 * Design tokens - Z-index stacking order
 *
 * Defines z-index constants for layered UI elements.
 * Ensures consistent stacking order across the application.
 */

export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  fixed: 1200,
  modalBackdrop: 1300,
  modal: 1400,
  popover: 1500,
  toast: 1600,
  tooltip: 1700,
} as const;

export type ZIndexToken = typeof zIndex;
