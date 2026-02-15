/**
 * PhoneVerificationScreen.tsx
 *
 * React Native phone verification screen with SMS code input.
 * Thin wrapper around shared phone verification logic.
 * Uses shared components for maximum code reuse.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';
import type { RouteProp } from '@react-navigation/native';
import type { AuthStackParamList } from '../../navigation/AuthNavigator';

// Shared components
import { Button, Input } from '@syntek/shared/design-system/components';

type PhoneVerificationScreenNavigationProp = StackNavigationProp<
  AuthStackParamList,
  'PhoneVerification'
>;
type PhoneVerificationScreenRouteProp = RouteProp<
  AuthStackParamList,
  'PhoneVerification'
>;

/**
 * Phone verification screen component for React Native.
 *
 * Displays SMS code input for phone number verification.
 * Supports code resend with rate limiting.
 * Uses shared phone verification logic.
 *
 * Features:
 * - 6-digit SMS code input
 * - Code resend with countdown timer
 * - Rate limiting (1 minute between resends)
 * - Auto-navigation on success
 *
 * @returns React Native phone verification screen component
 */
export function PhoneVerificationScreen(): JSX.Element {
  const navigation = useNavigation<PhoneVerificationScreenNavigationProp>();
  const route = useRoute<PhoneVerificationScreenRouteProp>();

  const { phoneNumber, userId } = route.params;

  // Form state
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [canResend, setCanResend] = useState(false);
  const [resendCountdown, setResendCountdown] = useState(60);

  /**
   * Countdown timer for resend button.
   */
  useEffect(() => {
    if (resendCountdown > 0) {
      const timer = setTimeout(() => {
        setResendCountdown(resendCountdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [resendCountdown]);

  /**
   * Handles verification code submission.
   */
  const handleVerifyCode = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      // Validation
      if (!code || code.length !== 6) {
        setError('Please enter a 6-digit verification code');
        setIsLoading(false);
        return;
      }

      if (!/^\d{6}$/.test(code)) {
        setError('Verification code must contain only numbers');
        setIsLoading(false);
        return;
      }

      // TODO: Use shared phone verification mutation
      // const { data } = await verifyPhone({ userId, code });

      // Mock success
      Alert.alert(
        'Phone Verified',
        'Your phone number has been successfully verified.',
        [
          {
            text: 'OK',
            onPress: () => {
              // Navigate to TOTP setup or login
              navigation.navigate('Login');
            },
          },
        ]
      );
    } catch (err) {
      setError('Invalid verification code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles code resend request.
   */
  const handleResendCode = async (): Promise<void> => {
    if (!canResend) return;

    try {
      setCanResend(false);
      setResendCountdown(60);
      setError(null);

      // TODO: Use shared resend code mutation
      // await resendPhoneVerificationCode({ userId });

      Alert.alert('Code Sent', 'A new verification code has been sent to your phone.');
    } catch (err) {
      setError('Failed to resend code. Please try again.');
      setCanResend(true);
    }
  };

  /**
   * Formats phone number for display (masks middle digits).
   */
  const formatPhoneNumber = (phone: string): string => {
    if (phone.length < 10) return phone;
    const lastFour = phone.slice(-4);
    return `***-***-${lastFour}`;
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
            Verify Phone Number
          </Text>
          <Text className="text-base text-neutral-600">
            Enter the 6-digit code sent to {formatPhoneNumber(phoneNumber)}
          </Text>
        </View>

        {/* Error Alert */}
        {error && (
          <View className="mb-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
            <Text className="text-danger-700">{error}</Text>
          </View>
        )}

        {/* Code Input */}
        <View className="mb-6">
          <Input
            label="Verification Code"
            value={code}
            onChangeText={(text) => {
              // Only allow numbers
              const numericText = text.replace(/[^0-9]/g, '');
              if (numericText.length <= 6) {
                setCode(numericText);
              }
            }}
            placeholder="000000"
            keyboardType="number-pad"
            maxLength={6}
            autoComplete="sms-otp"
            textContentType="oneTimeCode"
          />
          <Text className="text-xs text-neutral-500 mt-1">
            The code expires in 10 minutes
          </Text>
        </View>

        {/* Verify Button */}
        <Button
          onPress={handleVerifyCode}
          disabled={isLoading || code.length !== 6}
          className="mb-4"
        >
          {isLoading ? 'Verifying...' : 'Verify Code'}
        </Button>

        {/* Resend Code Button */}
        <View className="items-center">
          <Text className="text-neutral-600 mb-2">
            Didn't receive the code?
          </Text>
          {canResend ? (
            <TouchableOpacity onPress={handleResendCode}>
              <Text className="text-primary font-semibold">
                Resend Code
              </Text>
            </TouchableOpacity>
          ) : (
            <Text className="text-neutral-500">
              Resend in {resendCountdown}s
            </Text>
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
