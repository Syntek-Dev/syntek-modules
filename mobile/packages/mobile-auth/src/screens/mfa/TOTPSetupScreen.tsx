/**
 * TOTPSetupScreen.tsx
 *
 * React Native TOTP (Time-based One-Time Password) setup screen.
 * Displays QR code for authenticator app and backup codes.
 * Uses shared TOTP generation logic for maximum code reuse.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
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

// Shared utilities
import { generateTOTPSecret, generateTOTPUri } from '@syntek/shared/auth/utils/totp-generator';

type TOTPSetupScreenNavigationProp = StackNavigationProp<
  AuthStackParamList,
  'TOTPSetup'
>;
type TOTPSetupScreenRouteProp = RouteProp<
  AuthStackParamList,
  'TOTPSetup'
>;

/**
 * TOTP setup screen component for React Native.
 *
 * Guides the user through setting up two-factor authentication.
 * Displays QR code for scanning with authenticator apps.
 * Generates and displays backup codes for account recovery.
 *
 * Features:
 * - QR code display (shared TOTP QR component)
 * - Manual secret key entry option
 * - Verification code input
 * - Backup code generation and display
 * - Secure backup code download/share
 *
 * @returns React Native TOTP setup screen component
 */
export function TOTPSetupScreen(): JSX.Element {
  const navigation = useNavigation<TOTPSetupScreenNavigationProp>();
  const route = useRoute<TOTPSetupScreenRouteProp>();

  const { userId } = route.params;

  // State
  const [totpSecret, setTotpSecret] = useState('');
  const [totpUri, setTotpUri] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [isVerified, setIsVerified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Generates TOTP secret and URI on component mount.
   */
  useEffect(() => {
    const secret = generateTOTPSecret();
    const uri = generateTOTPUri({
      secret,
      email: 'user@example.com', // TODO: Get from user context
      issuer: 'YourApp',
    });

    setTotpSecret(secret);
    setTotpUri(uri);
  }, []);

  /**
   * Generates backup codes.
   */
  const generateBackupCodes = (): string[] => {
    // Generate 10 random 8-character backup codes
    const codes: string[] = [];
    for (let i = 0; i < 10; i++) {
      const code = Math.random().toString(36).substring(2, 10).toUpperCase();
      codes.push(code);
    }
    return codes;
  };

  /**
   * Handles verification code submission.
   */
  const handleVerifyCode = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      // Validation
      if (!verificationCode || verificationCode.length !== 6) {
        setError('Please enter a 6-digit verification code');
        setIsLoading(false);
        return;
      }

      if (!/^\d{6}$/.test(verificationCode)) {
        setError('Verification code must contain only numbers');
        setIsLoading(false);
        return;
      }

      // TODO: Use shared TOTP verification mutation
      // const { data } = await verifyTOTP({ userId, code: verificationCode, secret: totpSecret });

      // Mock success - generate backup codes
      const codes = generateBackupCodes();
      setBackupCodes(codes);
      setIsVerified(true);

      Alert.alert(
        'Two-Factor Authentication Enabled',
        'Save your backup codes in a secure location. You will need them to recover your account if you lose access to your authenticator app.'
      );
    } catch (err) {
      setError('Invalid verification code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles completion of TOTP setup.
   */
  const handleComplete = (): void => {
    if (!isVerified) {
      Alert.alert('Verification Required', 'Please verify your TOTP code before continuing.');
      return;
    }

    // Navigate to recovery key screen to display backup codes
    navigation.navigate('RecoveryKey', {
      recoveryKey: backupCodes.join('\n'),
    });
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
        <View className="mb-6">
          <Text className="text-2xl font-bold text-neutral-900 mb-2">
            Set Up Two-Factor Authentication
          </Text>
          <Text className="text-base text-neutral-600">
            Scan the QR code with your authenticator app
          </Text>
        </View>

        {/* Step 1: QR Code */}
        {!isVerified && (
          <>
            <View className="mb-6">
              <Text className="text-lg font-semibold text-neutral-900 mb-3">
                Step 1: Scan QR Code
              </Text>

              {/* TODO: Replace with shared TOTPQRCode component */}
              <View className="bg-neutral-100 border border-neutral-200 rounded-lg p-6 items-center mb-4">
                <View className="w-48 h-48 bg-white items-center justify-center">
                  <Text className="text-neutral-500 text-center">
                    QR Code Placeholder
                  </Text>
                  <Text className="text-xs text-neutral-400 mt-2 text-center">
                    Use shared TOTPQRCode component
                  </Text>
                </View>
              </View>

              <Text className="text-sm text-neutral-600 mb-2">
                Or enter this code manually:
              </Text>
              <View className="bg-neutral-50 p-3 rounded-lg">
                <Text className="font-mono text-sm text-center">
                  {totpSecret}
                </Text>
              </View>
            </View>

            {/* Error Alert */}
            {error && (
              <View className="mb-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
                <Text className="text-danger-700">{error}</Text>
              </View>
            )}

            {/* Step 2: Verification */}
            <View className="mb-6">
              <Text className="text-lg font-semibold text-neutral-900 mb-3">
                Step 2: Verify Code
              </Text>
              <Input
                label="Enter 6-digit code from your app"
                value={verificationCode}
                onChangeText={(text) => {
                  const numericText = text.replace(/[^0-9]/g, '');
                  if (numericText.length <= 6) {
                    setVerificationCode(numericText);
                  }
                }}
                placeholder="000000"
                keyboardType="number-pad"
                maxLength={6}
              />
            </View>

            {/* Verify Button */}
            <Button
              onPress={handleVerifyCode}
              disabled={isLoading || verificationCode.length !== 6}
              className="mb-4"
            >
              {isLoading ? 'Verifying...' : 'Verify and Enable 2FA'}
            </Button>
          </>
        )}

        {/* Step 3: Backup Codes (shown after verification) */}
        {isVerified && (
          <>
            <View className="mb-6">
              <Text className="text-lg font-semibold text-success-700 mb-3">
                ✓ Two-Factor Authentication Enabled
              </Text>
              <Text className="text-base text-neutral-600 mb-4">
                Save these backup codes in a secure location. Each code can be used once
                to access your account if you lose access to your authenticator app.
              </Text>

              {/* Backup Codes Display */}
              <View className="bg-neutral-50 border border-neutral-200 rounded-lg p-4">
                {backupCodes.map((code, index) => (
                  <Text
                    key={index}
                    className="font-mono text-sm text-neutral-900 mb-2"
                  >
                    {index + 1}. {code}
                  </Text>
                ))}
              </View>
            </View>

            {/* Warning */}
            <View className="mb-6 p-4 bg-warning-50 border border-warning-200 rounded-lg">
              <Text className="text-warning-700 font-semibold mb-1">
                ⚠ Important
              </Text>
              <Text className="text-warning-700 text-sm">
                Store these codes securely. You will not be able to see them again.
              </Text>
            </View>

            {/* Complete Button */}
            <Button
              onPress={handleComplete}
              className="mb-4"
            >
              Continue
            </Button>
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
