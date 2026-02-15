/**
 * Cross-platform Badge component
 *
 * Status badge for displaying states (active, suspended, verified, etc.).
 */

import React from 'react';
import { View, Text } from 'react-native';

export interface BadgeProps {
  /**
   * Badge variant (determines colour scheme)
   */
  variant: 'success' | 'warning' | 'error' | 'info' | 'neutral';

  /**
   * Badge label text
   */
  label: string;

  /**
   * Badge size
   */
  size?: 'sm' | 'md';

  /**
   * Additional className
   */
  className?: string;
}

/**
 * Renders a status badge with colour-coded background.
 *
 * @param variant - Badge colour variant
 * @param label - Badge text
 * @param size - Badge size (sm, md)
 * @param className - Additional classes
 * @returns Badge component
 */
export const Badge: React.FC<BadgeProps> = ({
  variant,
  label,
  size = 'md',
  className = '',
}) => {
  const variantClasses = {
    success: 'bg-success-light text-success-dark border-success',
    warning: 'bg-warning-light text-warning-dark border-warning',
    error: 'bg-error-light text-error-dark border-error',
    info: 'bg-info-light text-info-dark border-info',
    neutral: 'bg-neutral-100 text-neutral-700 border-neutral-300',
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
  };

  const badgeClasses = `
    inline-flex items-center rounded-full font-medium border
    ${variantClasses[variant]} ${sizeClasses[size]} ${className}
  `.trim();

  return (
    <View className={badgeClasses}>
      <Text className="text-inherit">{label}</Text>
    </View>
  );
};
