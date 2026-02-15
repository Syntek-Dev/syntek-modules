/**
 * Cross-platform Input component
 *
 * Text input with support for different input types (text, password, email, phone).
 * Handles validation states, error messages, and accessibility.
 */

import React, { useState } from 'react';
import { View, TextInput, Text, type TextInputProps } from 'react-native';

export interface InputProps extends Omit<TextInputProps, 'secureTextEntry'> {
  /**
   * Input label text
   */
  label?: string;

  /**
   * Input type (affects keyboard and validation)
   */
  type?: 'text' | 'password' | 'email' | 'phone' | 'number';

  /**
   * Error message to display below input
   */
  error?: string;

  /**
   * Helper text to display below input
   */
  helperText?: string;

  /**
   * Show/hide password toggle (for password inputs)
   */
  showPasswordToggle?: boolean;

  /**
   * Additional className for container
   */
  className?: string;

  /**
   * Additional className for input field
   */
  inputClassName?: string;
}

/**
 * Renders a cross-platform text input with label, error, and helper text.
 *
 * Automatically configures keyboard type and auto-complete based on input type.
 * Supports password visibility toggle for password inputs.
 *
 * @param label - Input label text
 * @param type - Input type (text, password, email, phone, number)
 * @param error - Error message
 * @param helperText - Helper text
 * @param showPasswordToggle - Enable password visibility toggle
 * @param className - Container classes
 * @param inputClassName - Input field classes
 * @param props - Additional TextInput props
 * @returns Styled input component
 */
export const Input: React.FC<InputProps> = ({
  label,
  type = 'text',
  error,
  helperText,
  showPasswordToggle = false,
  className = '',
  inputClassName = '',
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);

  // Determine keyboard type based on input type
  const keyboardType = {
    text: 'default',
    password: 'default',
    email: 'email-address',
    phone: 'phone-pad',
    number: 'numeric',
  }[type] as TextInputProps['keyboardType'];

  // Determine auto-complete type
  const autoCompleteType = {
    text: 'off',
    password: 'password',
    email: 'email',
    phone: 'tel',
    number: 'off',
  }[type] as TextInputProps['autoComplete'];

  // Text content type for iOS autofill
  const textContentType = {
    text: 'none',
    password: 'password',
    email: 'emailAddress',
    phone: 'telephoneNumber',
    number: 'none',
  }[type] as TextInputProps['textContentType'];

  const hasError = Boolean(error);

  const containerClasses = `flex flex-col gap-1 ${className}`.trim();

  const inputClasses = `
    px-4 py-3 rounded-lg border text-base
    ${hasError ? 'border-error bg-error-light/10' : 'border-neutral-300 bg-white'}
    ${hasError ? 'focus:border-error' : 'focus:border-primary-600'}
    disabled:bg-neutral-100 disabled:text-neutral-500
    ${inputClassName}
  `.trim();

  return (
    <View className={containerClasses}>
      {label && (
        <Text className="text-sm font-medium text-neutral-700">
          {label}
        </Text>
      )}

      <View className="relative">
        <TextInput
          {...props}
          className={inputClasses}
          keyboardType={keyboardType}
          autoComplete={autoCompleteType}
          textContentType={textContentType}
          secureTextEntry={type === 'password' && !showPassword}
          accessibilityLabel={label || props.placeholder}
          accessibilityState={{
            disabled: props.editable === false,
          }}
        />

        {/* TODO: Add password visibility toggle button */}
        {/* Requires Pressable positioned absolute right */}
      </View>

      {error && (
        <Text className="text-sm text-error">
          {error}
        </Text>
      )}

      {helperText && !error && (
        <Text className="text-sm text-neutral-600">
          {helperText}
        </Text>
      )}
    </View>
  );
};
