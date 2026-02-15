/**
 * Cross-platform Card component
 *
 * Container component with elevation/shadow for grouping content.
 * Supports elevated and flat variants.
 */

import React from 'react';
import { View, type ViewProps } from 'react-native';

export interface CardProps extends ViewProps {
  /**
   * Card variant
   * - elevated: With shadow (default)
   * - flat: No shadow
   */
  variant?: 'elevated' | 'flat';

  /**
   * Additional className
   */
  className?: string;

  /**
   * Card content
   */
  children: React.ReactNode;
}

/**
 * Renders a card container with optional elevation.
 *
 * Provides consistent spacing and visual grouping for content.
 *
 * @param variant - Visual style (elevated, flat)
 * @param className - Additional classes
 * @param children - Card content
 * @param props - Additional View props
 * @returns Card component
 */
export const Card: React.FC<CardProps> = ({
  variant = 'elevated',
  className = '',
  children,
  ...props
}) => {
  const baseClasses = 'rounded-lg bg-white p-6';

  const variantClasses = {
    elevated: 'shadow-md', // Web: box-shadow, Mobile: elevation
    flat: 'border border-neutral-200',
  };

  const cardClasses = `${baseClasses} ${variantClasses[variant]} ${className}`.trim();

  return (
    <View {...props} className={cardClasses}>
      {children}
    </View>
  );
};
