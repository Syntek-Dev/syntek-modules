/**
 * NativeWind 4 Configuration (Mobile)
 *
 * Shared configuration for React Native applications.
 * Uses design tokens for consistency with web (Tailwind v4).
 */

import { colors, spacing, borders, shadows, breakpoints, typography } from './tokens';

const config = {
  content: [
    './src/**/*.{ts,tsx}',
    '../mobile/packages/*/src/**/*.{ts,tsx}',
    '../shared/auth/components/**/*.{ts,tsx}',
    '../shared/design-system/components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: colors.primary,
        success: colors.success,
        warning: colors.warning,
        error: colors.error,
        info: colors.info,
        neutral: colors.neutral,
        auth: colors.auth,
        social: colors.social,
      },
      spacing: {
        ...spacing,
        // Mobile-specific: iOS minimum touch target
        'touch-min': '44px',
      },
      borderRadius: borders.borderRadius,
      borderWidth: borders.borderWidth,
      // NativeWind uses elevation instead of boxShadow
      elevation: shadows.elevation,
      screens: breakpoints,
      fontFamily: typography.fontFamily,
      fontSize: typography.fontSize,
      fontWeight: typography.fontWeight,
      lineHeight: typography.lineHeight,
      letterSpacing: typography.letterSpacing,
    },
  },
  plugins: [],
};

export default config;
