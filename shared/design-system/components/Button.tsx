/**
 * Cross-platform Button component
 *
 * Works with Tailwind v4 (web) and NativeWind 4 (mobile).
 * Uses design tokens for consistency. Meets WCAG 2.1 AA standards
 * and iOS/Android touch target requirements (44px minimum).
 */

import React from 'react';
import { Pressable, Text, ActivityIndicator, type PressableProps } from 'react-native';

export interface ButtonProps extends Omit<PressableProps, 'children'> {
  /**
   * Button content (text or elements)
   */
  children: React.ReactNode;

  /**
   * Visual style variant
   * - primary: Brand colour, high prominence
   * - secondary: Neutral colour, medium prominence
   * - danger: Error colour, destructive actions
   * - ghost: Transparent, low prominence
   */
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';

  /**
   * Button size (affects padding and font size)
   * - sm: Small (32px height)
   * - md: Medium (44px height, meets iOS touch target)
   * - lg: Large (56px height)
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Loading state - shows spinner instead of content
   */
  loading?: boolean;

  /**
   * Disabled state - prevents interaction
   */
  disabled?: boolean;

  /**
   * Additional className for custom styling
   */
  className?: string;
}

/**
 * Renders a cross-platform button with consistent styling.
 *
 * Automatically handles loading states, disabled states, and accessibility.
 * Uses Pressable from react-native for cross-platform compatibility.
 *
 * @param children - Button content
 * @param variant - Visual style (primary, secondary, danger, ghost)
 * @param size - Button size (sm, md, lg)
 * @param loading - Show loading spinner
 * @param disabled - Disable interaction
 * @param className - Additional Tailwind/NativeWind classes
 * @param props - Additional Pressable props
 * @returns Styled button component
 */
export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  ...props
}) => {
  const baseClasses = 'rounded-lg font-semibold transition-colors flex items-center justify-center';

  const variantClasses = {
    primary: 'bg-primary-600 active:bg-primary-700 disabled:bg-primary-300',
    secondary: 'bg-neutral-200 active:bg-neutral-300 disabled:bg-neutral-100',
    danger: 'bg-error active:bg-error-dark disabled:bg-error-light',
    ghost: 'bg-transparent active:bg-primary-50 disabled:bg-transparent',
  };

  const textColorClasses = {
    primary: 'text-white',
    secondary: 'text-neutral-900',
    danger: 'text-white',
    ghost: 'text-primary-600',
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm min-h-8',
    md: 'px-4 py-3 text-base min-h-11', // 44px - iOS minimum touch target
    lg: 'px-6 py-4 text-lg min-h-14',
  };

  const disabledClasses = 'opacity-50';

  const buttonClasses = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${
    disabled || loading ? disabledClasses : ''
  } ${className}`.trim();

  const textClasses = textColorClasses[variant];

  return (
    <Pressable
      {...props}
      disabled={disabled || loading}
      className={buttonClasses}
      accessibilityRole="button"
      accessibilityState={{
        disabled: disabled || loading,
        busy: loading,
      }}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' || variant === 'danger' ? 'white' : '#3b82f6'} />
      ) : (
        <Text className={textClasses}>{children}</Text>
      )}
    </Pressable>
  );
};
