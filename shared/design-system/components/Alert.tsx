/**
 * Cross-platform Alert component
 *
 * Alert/banner for displaying messages (success, error, warning, info).
 */

import React from 'react';
import { View, Text } from 'react-native';

export interface AlertProps {
  /**
   * Alert type (determines colour scheme)
   */
  type: 'success' | 'error' | 'warning' | 'info';

  /**
   * Alert title (optional)
   */
  title?: string;

  /**
   * Alert message
   */
  message: string;

  /**
   * Additional className
   */
  className?: string;
}

/**
 * Renders an alert banner with icon and message.
 *
 * @param type - Alert type (success, error, warning, info)
 * @param title - Alert title
 * @param message - Alert message
 * @param className - Additional classes
 * @returns Alert component
 */
export const Alert: React.FC<AlertProps> = ({
  type,
  title,
  message,
  className = '',
}) => {
  const typeConfig = {
    success: {
      bg: 'bg-success-light',
      border: 'border-success',
      text: 'text-success-dark',
      icon: '✓',
    },
    error: {
      bg: 'bg-error-light',
      border: 'border-error',
      text: 'text-error-dark',
      icon: '✕',
    },
    warning: {
      bg: 'bg-warning-light',
      border: 'border-warning',
      text: 'text-warning-dark',
      icon: '⚠',
    },
    info: {
      bg: 'bg-info-light',
      border: 'border-info',
      text: 'text-info-dark',
      icon: 'ℹ',
    },
  };

  const config = typeConfig[type];

  const containerClasses = `
    flex flex-row gap-3 p-4 rounded-lg border-l-4
    ${config.bg} ${config.border} ${className}
  `.trim();

  return (
    <View className={containerClasses}>
      <Text className={`text-xl ${config.text}`}>{config.icon}</Text>

      <View className="flex-1">
        {title && (
          <Text className={`font-semibold text-base ${config.text} mb-1`}>
            {title}
          </Text>
        )}
        <Text className={`text-sm ${config.text}`}>
          {message}
        </Text>
      </View>
    </View>
  );
};
