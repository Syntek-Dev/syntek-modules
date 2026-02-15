/**
 * Cross-platform Checkbox component
 *
 * Checkbox for GDPR consent and form selections.
 * Meets WCAG 2.1 AA accessibility standards.
 */

import React from 'react';
import { Pressable, View, Text } from 'react-native';

export interface CheckboxProps {
  /**
   * Checkbox label text
   */
  label: string | React.ReactNode;

  /**
   * Checked state
   */
  checked: boolean;

  /**
   * onChange callback
   */
  onChange: (checked: boolean) => void;

  /**
   * Disabled state
   */
  disabled?: boolean;

  /**
   * Error state
   */
  error?: boolean;

  /**
   * Additional className
   */
  className?: string;
}

/**
 * Renders a cross-platform checkbox with label.
 *
 * Supports checked, disabled, and error states.
 * Meets iOS/Android touch target requirements (44px).
 *
 * @param label - Checkbox label
 * @param checked - Checked state
 * @param onChange - Change handler
 * @param disabled - Disabled state
 * @param error - Error state
 * @param className - Additional classes
 * @returns Checkbox component
 */
export const Checkbox: React.FC<CheckboxProps> = ({
  label,
  checked,
  onChange,
  disabled = false,
  error = false,
  className = '',
}) => {
  const containerClasses = `flex flex-row items-center gap-3 min-h-11 ${className}`.trim();

  const boxClasses = `
    w-6 h-6 rounded border-2 flex items-center justify-center
    ${checked ? 'bg-primary-600 border-primary-600' : 'bg-white border-neutral-300'}
    ${error ? 'border-error' : ''}
    ${disabled ? 'opacity-50' : ''}
  `.trim();

  return (
    <Pressable
      className={containerClasses}
      onPress={() => !disabled && onChange(!checked)}
      disabled={disabled}
      accessibilityRole="checkbox"
      accessibilityState={{
        checked,
        disabled,
      }}
    >
      <View className={boxClasses}>
        {checked && (
          <Text className="text-white text-sm font-bold">✓</Text>
        )}
      </View>

      <Text className={`flex-1 text-base ${error ? 'text-error' : 'text-neutral-900'} ${disabled ? 'opacity-50' : ''}`}>
        {label}
      </Text>
    </Pressable>
  );
};
