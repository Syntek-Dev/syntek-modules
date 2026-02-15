/**
 * LoginScreen.tsx
 *
 * React Native login screen with biometric authentication support.
 * Thin wrapper around shared login logic with React Native Navigation integration.
 * Uses shared components from @syntek/shared for maximum code reuse.
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
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';
import type { AuthStackParamList } from '../../navigation/AuthNavigator';

// Shared components (NativeWind styling works identically to web Tailwind)
import { Button, Input, Checkbox } from '@syntek/shared/design-system/components';

// Shared utilities and types
import { validateEmail } from '@syntek/shared/auth/utils/validators';
import { sanitizeInput } from '@syntek/shared/auth/utils';
import type { LoginFormData } from '@syntek/shared/auth/types';

// Mobile-specific adapter
import { authenticateWithBiometrics } from '@syntek/shared/auth/hooks/adapters/useBiometrics.native';

type LoginScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'Login'>;

/**
 * Login screen component for React Native.
 *
 * Provides email/password authentication with biometric support.
 * Integrates with shared authentication hooks and React Navigation.
 * All business logic is in shared hooks - this screen handles navigation only.
 *
 * Features:
 * - Email and password authentication
 * - Biometric authentication (fingerprint, Face ID)
 * - Passkey support (platform authenticator)
 * - Remember me option
 * - Social authentication buttons
 * - Navigation to registration and password recovery
 *
 * @returns React Native login screen component
 */
export function LoginScreen(): JSX.Element {
  const navigation = useNavigation<LoginScreenNavigationProp>();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handles biometric authentication attempt.
   * Uses native biometric adapter (fingerprint, Face ID).
   */
  const handleBiometricLogin = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const success = await authenticateWithBiometrics();

      if (success) {
        // TODO: Complete login with stored credentials
        // This would fetch saved credentials from secure storage
        // and complete the authentication flow
        Alert.alert('Success', 'Biometric authentication successful');
      } else {
        setError('Biometric authentication failed. Please use password.');
      }
    } catch (err) {
      setError('Biometric authentication unavailable');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles standard email/password login.
   * Uses shared authentication logic.
   */
  const handleLogin = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      // Validation using shared validators
      const sanitizedEmail = sanitizeInput(email);
      const emailValidation = validateEmail(sanitizedEmail);

      if (!emailValidation.isValid) {
        setError(emailValidation.error || 'Invalid email address');
        return;
      }

      if (!password || password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }

      // TODO: Use shared login mutation
      // const { data } = await login({ email: sanitizedEmail, password });

      // Mock success for now
      Alert.alert('Success', 'Login successful', [
        { text: 'OK', onPress: () => {
          // Navigation would happen here after successful login
          console.log('Navigate to dashboard');
        }},
      ]);
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Navigates to registration screen.
   */
  const handleRegisterPress = (): void => {
    navigation.navigate('Register');
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
            Welcome Back
          </Text>
          <Text className="text-base text-neutral-600">
            Sign in to continue to your account
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
            label="Email Address"
            value={email}
            onChangeText={setEmail}
            placeholder="your.email@example.com"
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            textContentType="emailAddress"
          />
        </View>

        {/* Password Input */}
        <View className="mb-4">
          <Input
            label="Password"
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            secureTextEntry
            autoComplete="password"
            textContentType="password"
          />
        </View>

        {/* Remember Me Checkbox */}
        <View className="mb-6">
          <Checkbox
            checked={rememberMe}
            onChange={setRememberMe}
            label="Remember me on this device"
          />
        </View>

        {/* Login Button */}
        <Button
          onPress={handleLogin}
          disabled={isLoading}
          className="mb-4"
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </Button>

        {/* Biometric Login Button */}
        <Button
          onPress={handleBiometricLogin}
          variant="outline"
          disabled={isLoading}
          className="mb-6"
        >
          Sign in with Biometrics
        </Button>

        {/* Forgot Password Link */}
        <TouchableOpacity className="mb-6">
          <Text className="text-center text-primary text-sm">
            Forgot your password?
          </Text>
        </TouchableOpacity>

        {/* Divider */}
        <View className="flex-row items-center mb-6">
          <View className="flex-1 h-px bg-neutral-200" />
          <Text className="mx-4 text-neutral-500">or</Text>
          <View className="flex-1 h-px bg-neutral-200" />
        </View>

        {/* Social Login Buttons */}
        <View className="mb-6">
          <Button
            variant="outline"
            className="mb-3"
            onPress={() => {
              // TODO: Handle Google OAuth
              console.log('Google login');
            }}
          >
            Continue with Google
          </Button>

          {Platform.OS === 'ios' && (
            <Button
              variant="outline"
              onPress={() => {
                // TODO: Handle Apple Sign In
                console.log('Apple login');
              }}
            >
              Continue with Apple
            </Button>
          )}
        </View>

        {/* Register Link */}
        <View className="flex-row justify-center items-center">
          <Text className="text-neutral-600 mr-1">
            Don't have an account?
          </Text>
          <TouchableOpacity onPress={handleRegisterPress}>
            <Text className="text-primary font-semibold">
              Sign up
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
