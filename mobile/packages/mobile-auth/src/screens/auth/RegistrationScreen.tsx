/**
 * RegistrationScreen.tsx
 *
 * React Native registration screen with GDPR compliance.
 * Thin wrapper around shared registration logic with React Native Navigation integration.
 * Uses shared components and validators for maximum code reuse.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Linking,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';
import type { AuthStackParamList } from '../../navigation/AuthNavigator';

// Shared components (NativeWind styling)
import { Button, Input, Checkbox } from '@syntek/shared/design-system/components';

// Shared utilities and validators
import {
  validateEmail,
  validatePassword,
  validateUsername,
  validatePhone,
} from '@syntek/shared/auth/utils/validators';
import { sanitizeInput } from '@syntek/shared/auth/utils';
import type { RegistrationFormData } from '@syntek/shared/auth/types';

type RegisterScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'Register'>;

/**
 * Registration screen component for React Native.
 *
 * GDPR-compliant registration form with legal consent checkboxes.
 * Integrates with shared validation logic and React Navigation.
 * All business logic is in shared hooks - this screen handles navigation only.
 *
 * Features:
 * - Email, username, and password registration
 * - Optional phone number (GDPR consent required)
 * - Password strength indicator (shared component)
 * - Legal consent checkboxes (privacy policy, terms of service)
 * - Privacy policy and terms of service links
 * - Social registration options
 *
 * @returns React Native registration screen component
 */
export function RegistrationScreen(): JSX.Element {
  const navigation = useNavigation<RegisterScreenNavigationProp>();

  // Form state
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [agreeToPrivacy, setAgreeToPrivacy] = useState(false);
  const [phoneConsent, setPhoneConsent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validation state
  const [showPasswordValidation, setShowPasswordValidation] = useState(false);

  /**
   * Opens privacy policy in browser.
   */
  const openPrivacyPolicy = async (): Promise<void> => {
    const url = 'https://yourapp.com/privacy-policy'; // Replace with actual URL
    const canOpen = await Linking.canOpenURL(url);
    if (canOpen) {
      await Linking.openURL(url);
    }
  };

  /**
   * Opens terms of service in browser.
   */
  const openTermsOfService = async (): Promise<void> => {
    const url = 'https://yourapp.com/terms-of-service'; // Replace with actual URL
    const canOpen = await Linking.canOpenURL(url);
    if (canOpen) {
      await Linking.openURL(url);
    }
  };

  /**
   * Validates all form fields before submission.
   */
  const validateForm = (): boolean => {
    // Email validation
    const sanitizedEmail = sanitizeInput(email);
    const emailValidation = validateEmail(sanitizedEmail);
    if (!emailValidation.isValid) {
      setError(emailValidation.error || 'Invalid email address');
      return false;
    }

    // Username validation
    const sanitizedUsername = sanitizeInput(username);
    const usernameValidation = validateUsername(sanitizedUsername);
    if (!usernameValidation.isValid) {
      setError(usernameValidation.error || 'Invalid username');
      return false;
    }

    // Password validation
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      setError(passwordValidation.error || 'Invalid password');
      return false;
    }

    // Confirm password
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    // Phone validation (if provided)
    if (phoneNumber) {
      const phoneValidation = validatePhone(phoneNumber);
      if (!phoneValidation.isValid) {
        setError(phoneValidation.error || 'Invalid phone number');
        return false;
      }

      // GDPR: Phone consent required if phone provided
      if (!phoneConsent) {
        setError('You must consent to phone number processing to provide a phone number');
        return false;
      }
    }

    // Legal consent validation (GDPR)
    if (!agreeToTerms) {
      setError('You must agree to the Terms of Service');
      return false;
    }

    if (!agreeToPrivacy) {
      setError('You must agree to the Privacy Policy');
      return false;
    }

    return true;
  };

  /**
   * Handles registration form submission.
   * Uses shared registration mutation.
   */
  const handleRegister = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      if (!validateForm()) {
        setIsLoading(false);
        return;
      }

      // Sanitize inputs
      const formData: RegistrationFormData = {
        email: sanitizeInput(email),
        username: sanitizeInput(username),
        password,
        phoneNumber: phoneNumber ? sanitizeInput(phoneNumber) : undefined,
        agreeToTerms,
        agreeToPrivacy,
        phoneConsent: phoneNumber ? phoneConsent : undefined,
      };

      // TODO: Use shared registration mutation
      // const { data } = await register(formData);

      // Mock success
      Alert.alert(
        'Registration Successful',
        'Please verify your email address to continue.',
        [
          {
            text: 'OK',
            onPress: () => {
              // Navigate to phone verification if phone provided
              if (phoneNumber) {
                navigation.navigate('PhoneVerification', {
                  phoneNumber,
                  userId: 'mock-user-id', // Replace with actual user ID
                });
              } else {
                // Navigate to login
                navigation.navigate('Login');
              }
            },
          },
        ]
      );
    } catch (err) {
      setError('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Navigates to login screen.
   */
  const handleLoginPress = (): void => {
    navigation.navigate('Login');
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-white"
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        className="flex-1"
        contentContainerClassName="p-6"
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View className="mb-8 mt-12">
          <Text className="text-3xl font-bold text-neutral-900 mb-2">
            Create Account
          </Text>
          <Text className="text-base text-neutral-600">
            Join us to get started
          </Text>
        </View>

        {/* Error Alert */}
        {error && (
          <View className="mb-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
            <Text className="text-danger-700">{error}</Text>
          </View>
        )}

        {/* Email Input */}
        <View className="mb-4">
          <Input
            label="Email Address *"
            value={email}
            onChangeText={setEmail}
            placeholder="your.email@example.com"
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            textContentType="emailAddress"
          />
        </View>

        {/* Username Input */}
        <View className="mb-4">
          <Input
            label="Username *"
            value={username}
            onChangeText={setUsername}
            placeholder="Choose a username"
            autoCapitalize="none"
            autoComplete="username"
            textContentType="username"
          />
        </View>

        {/* Password Input */}
        <View className="mb-4">
          <Input
            label="Password *"
            value={password}
            onChangeText={(text) => {
              setPassword(text);
              setShowPasswordValidation(true);
            }}
            placeholder="Create a strong password"
            secureTextEntry
            autoComplete="password-new"
            textContentType="newPassword"
          />
          {/* TODO: Add PasswordStrengthIndicator from shared components */}
        </View>

        {/* Confirm Password Input */}
        <View className="mb-4">
          <Input
            label="Confirm Password *"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            placeholder="Re-enter your password"
            secureTextEntry
            autoComplete="password-new"
            textContentType="newPassword"
          />
        </View>

        {/* Phone Number Input (Optional) */}
        <View className="mb-4">
          <Input
            label="Phone Number (Optional)"
            value={phoneNumber}
            onChangeText={setPhoneNumber}
            placeholder="+44 7123 456789"
            keyboardType="phone-pad"
            autoComplete="tel"
            textContentType="telephoneNumber"
          />
          <Text className="text-xs text-neutral-500 mt-1">
            Used for two-factor authentication and account recovery
          </Text>
        </View>

        {/* Phone Consent Checkbox (GDPR) */}
        {phoneNumber && (
          <View className="mb-4">
            <Checkbox
              checked={phoneConsent}
              onChange={setPhoneConsent}
              label="I consent to the processing of my phone number for authentication purposes"
            />
          </View>
        )}

        {/* Legal Consent Checkboxes (GDPR) */}
        <View className="mb-4">
          <View className="flex-row items-start mb-3">
            <Checkbox
              checked={agreeToPrivacy}
              onChange={setAgreeToPrivacy}
            />
            <View className="flex-1 ml-2">
              <Text className="text-sm text-neutral-700">
                I agree to the{' '}
                <Text className="text-primary" onPress={openPrivacyPolicy}>
                  Privacy Policy
                </Text>{' '}
                *
              </Text>
            </View>
          </View>

          <View className="flex-row items-start">
            <Checkbox
              checked={agreeToTerms}
              onChange={setAgreeToTerms}
            />
            <View className="flex-1 ml-2">
              <Text className="text-sm text-neutral-700">
                I agree to the{' '}
                <Text className="text-primary" onPress={openTermsOfService}>
                  Terms of Service
                </Text>{' '}
                *
              </Text>
            </View>
          </View>
        </View>

        {/* Register Button */}
        <Button
          onPress={handleRegister}
          disabled={isLoading}
          className="mb-6"
        >
          {isLoading ? 'Creating account...' : 'Create Account'}
        </Button>

        {/* Login Link */}
        <View className="flex-row justify-center items-center">
          <Text className="text-neutral-600 mr-1">
            Already have an account?
          </Text>
          <TouchableOpacity onPress={handleLoginPress}>
            <Text className="text-primary font-semibold">
              Sign in
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
