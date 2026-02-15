/**
 * Design tokens - Colour palette
 *
 * Shared between Tailwind v4 (web) and NativeWind 4 (mobile).
 * Uses semantic colour names for theming support.
 * All colour contrast ratios meet WCAG 2.1 AA standards (4.5:1 for text).
 */

export const colors = {
  // Brand colours
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6', // Primary brand colour
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },

  // Semantic colours (system feedback)
  success: {
    light: '#d1fae5',
    DEFAULT: '#10b981',
    dark: '#065f46',
  },
  warning: {
    light: '#fef3c7',
    DEFAULT: '#f59e0b',
    dark: '#92400e',
  },
  error: {
    light: '#fee2e2',
    DEFAULT: '#ef4444',
    dark: '#991b1b',
  },
  info: {
    light: '#dbeafe',
    DEFAULT: '#3b82f6',
    dark: '#1e3a8a',
  },

  // Neutral colours (UI backgrounds, text)
  neutral: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#e5e5e5',
    300: '#d4d4d4',
    400: '#a3a3a3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
  },

  // Authentication-specific colours
  auth: {
    password: {
      weak: '#ef4444',     // Red - weak password
      fair: '#f59e0b',     // Orange - fair password
      good: '#10b981',     // Green - good password
      strong: '#059669',   // Dark green - strong password
    },
    mfa: {
      enabled: '#10b981',   // Green - MFA enabled
      disabled: '#ef4444',  // Red - MFA disabled
      pending: '#f59e0b',   // Orange - MFA setup pending
    },
    session: {
      active: '#10b981',      // Green - active session
      suspicious: '#f59e0b',  // Orange - suspicious activity
      expired: '#6b7280',     // Grey - expired session
    },
    verification: {
      verified: '#10b981',     // Green - verified
      unverified: '#f59e0b',   // Orange - pending verification
      failed: '#ef4444',       // Red - verification failed
    },
  },

  // Social provider colours (brand-specific)
  social: {
    google: '#4285f4',
    github: '#24292e',
    microsoft: '#00a4ef',
    apple: '#000000',
  },
} as const;

export type ColorToken = typeof colors;
