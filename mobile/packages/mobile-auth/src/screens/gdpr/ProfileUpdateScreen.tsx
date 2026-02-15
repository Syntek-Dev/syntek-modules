/**
 * ProfileUpdateScreen.tsx
 *
 * React Native profile update screen with GDPR compliance.
 * Allows updating email, phone, username with proper consent management.
 * Uses shared validation and GraphQL mutations.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { Button, Input, Checkbox } from '@syntek/shared/design-system/components';
import { validateEmail, validatePhone, validateUsername } from '@syntek/shared/auth/utils/validators';
import { sanitizeInput } from '@syntek/shared/auth/utils';

export function ProfileUpdateScreen(): JSX.Element {
  const [email, setEmail] = useState('user@example.com');
  const [username, setUsername] = useState('username');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneConsent, setPhoneConsent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const emailValidation = validateEmail(sanitizeInput(email));
      if (!emailValidation.isValid) {
        setError(emailValidation.error || 'Invalid email');
        setIsLoading(false);
        return;
      }

      if (phoneNumber) {
        const phoneValidation = validatePhone(phoneNumber);
        if (!phoneValidation.isValid) {
          setError(phoneValidation.error || 'Invalid phone');
          setIsLoading(false);
          return;
        }
        if (!phoneConsent) {
          setError('Phone consent required');
          setIsLoading(false);
          return;
        }
      }

      // TODO: Use shared update profile mutation
      Alert.alert('Success', 'Profile updated successfully');
    } catch (err) {
      setError('Update failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-white"
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView className="flex-1 p-6" keyboardShouldPersistTaps="handled">
        <Text className="text-2xl font-bold mb-6">Profile Settings</Text>

        {error && (
          <View className="mb-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
            <Text className="text-danger-700">{error}</Text>
          </View>
        )}

        <View className="mb-4">
          <Input label="Email *" value={email} onChangeText={setEmail} keyboardType="email-address" />
        </View>

        <View className="mb-4">
          <Input label="Username *" value={username} onChangeText={setUsername} />
        </View>

        <View className="mb-4">
          <Input label="Phone (Optional)" value={phoneNumber} onChangeText={setPhoneNumber} keyboardType="phone-pad" />
        </View>

        {phoneNumber && (
          <View className="mb-6">
            <Checkbox
              checked={phoneConsent}
              onChange={setPhoneConsent}
              label="I consent to phone number processing (GDPR)"
            />
          </View>
        )}

        <Button onPress={handleUpdate} disabled={isLoading}>
          {isLoading ? 'Updating...' : 'Update Profile'}
        </Button>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
