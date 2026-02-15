/**
 * Cross-platform Spinner component
 *
 * Loading indicator with multiple sizes.
 */

import React from 'react';
import { ActivityIndicator, View, type ActivityIndicatorProps } from 'react-native';

export interface SpinnerProps extends Omit<ActivityIndicatorProps, 'size'> {
  /**
   * Spinner size
   * - small: 16px
   * - medium: 24px (default)
   * - large: 32px
   */
  size?: 'small' | 'medium' | 'large';

  /**
   * Spinner colour (defaults to primary-600)
   */
  color?: string;

  /**
   * Additional className
   */
  className?: string;
}

/**
 * Renders a loading spinner with consistent sizing.
 *
 * @param size - Spinner size (small, medium, large)
 * @param color - Spinner colour
 * @param className - Additional classes
 * @param props - Additional ActivityIndicator props
 * @returns Spinner component
 */
export const Spinner: React.FC<SpinnerProps> = ({
  size = 'medium',
  color = '#3b82f6', // primary-600
  className = '',
  ...props
}) => {
  const sizeMap = {
    small: 'small' as const,
    medium: 'large' as const, // ActivityIndicator only has 'small' and 'large'
    large: 'large' as const,
  };

  const scaleMap = {
    small: 'scale-75',
    medium: 'scale-100',
    large: 'scale-125',
  };

  return (
    <View className={`${scaleMap[size]} ${className}`.trim()}>
      <ActivityIndicator {...props} size={sizeMap[size]} color={color} />
    </View>
  );
};
