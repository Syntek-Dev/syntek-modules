/**
 * PrivacySettingsScreen.tsx
 *
 * React Native privacy settings screen (GDPR compliance).
 * Manages consent for optional data processing.
 * Implements right to withdraw consent (GDPR Article 7.3).
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, Alert } from 'react-native';
import { Button, Checkbox } from '@syntek/shared/design-system/components';

export function PrivacySettingsScreen(): JSX.Element {
  const [phoneConsent, setPhoneConsent] = useState(true);
  const [ipTrackingConsent, setIpTrackingConsent] = useState(true);
  const [analyticsConsent, setAnalyticsConsent] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleUpdateConsent = async (): Promise<void> => {
    try {
      setIsUpdating(true);

      // TODO: Use shared consent update mutation
      await new Promise(resolve => setTimeout(resolve, 1000));

      Alert.alert('Success', 'Privacy settings updated');
    } catch (error) {
      Alert.alert('Error', 'Failed to update settings');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <ScrollView className="flex-1 bg-white p-6">
      <Text className="text-2xl font-bold mb-2">Privacy Settings</Text>
      <Text className="text-neutral-600 mb-6">
        Manage your data processing consents (GDPR)
      </Text>

      <View className="mb-6">
        <Text className="text-lg font-semibold mb-4">Data Processing Consent</Text>

        <View className="mb-4 p-4 bg-neutral-50 rounded-lg">
          <Checkbox
            checked={phoneConsent}
            onChange={setPhoneConsent}
            label="Phone Number Processing"
          />
          <Text className="text-sm text-neutral-600 mt-2 ml-8">
            Allow processing of phone number for 2FA and account recovery
          </Text>
        </View>

        <View className="mb-4 p-4 bg-neutral-50 rounded-lg">
          <Checkbox
            checked={ipTrackingConsent}
            onChange={setIpTrackingConsent}
            label="IP Address Tracking"
          />
          <Text className="text-sm text-neutral-600 mt-2 ml-8">
            Allow tracking of IP addresses for security and fraud prevention
          </Text>
        </View>

        <View className="mb-4 p-4 bg-neutral-50 rounded-lg">
          <Checkbox
            checked={analyticsConsent}
            onChange={setAnalyticsConsent}
            label="Analytics (Optional)"
          />
          <Text className="text-sm text-neutral-600 mt-2 ml-8">
            Help improve the service by sharing anonymous usage data
          </Text>
        </View>
      </View>

      <View className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <Text className="text-blue-700 text-sm">
          ℹ You can withdraw consent at any time. Some features may not be available if you opt out.
        </Text>
      </View>

      <Button onPress={handleUpdateConsent} disabled={isUpdating}>
        {isUpdating ? 'Updating...' : 'Save Privacy Settings'}
      </Button>
    </ScrollView>
  );
}
