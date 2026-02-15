/**
 * RecoveryKeyScreen.tsx
 *
 * React Native recovery key display screen.
 * Shows backup codes with native share functionality.
 * Uses shared components for maximum code reuse.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, Share, Alert } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';
import type { RouteProp } from '@react-navigation/native';
import type { AuthStackParamList } from '../../navigation/AuthNavigator';
import { Button } from '@syntek/shared/design-system/components';

type RecoveryKeyScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'RecoveryKey'>;
type RecoveryKeyScreenRouteProp = RouteProp<AuthStackParamList, 'RecoveryKey'>;

export function RecoveryKeyScreen(): JSX.Element {
  const navigation = useNavigation<RecoveryKeyScreenNavigationProp>();
  const route = useRoute<RecoveryKeyScreenRouteProp>();
  const { recoveryKey } = route.params;
  const [acknowledged, setAcknowledged] = useState(false);

  const handleShare = async (): Promise<void> => {
    try {
      await Share.share({
        message: `Your Recovery Codes:\n\n${recoveryKey}\n\nStore these securely.`,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share recovery codes');
    }
  };

  const handleComplete = (): void => {
    if (!acknowledged) {
      Alert.alert('Confirmation Required', 'Please confirm you have saved your recovery codes.');
      return;
    }
    navigation.navigate('Login');
  };

  return (
    <ScrollView className="flex-1 bg-white p-6">
      <View className="mb-6">
        <Text className="text-2xl font-bold text-neutral-900 mb-2">Recovery Codes</Text>
        <Text className="text-base text-neutral-600">
          Save these codes in a secure location
        </Text>
      </View>

      <View className="bg-neutral-50 border border-neutral-200 rounded-lg p-4 mb-6">
        <Text className="font-mono text-sm">{recoveryKey}</Text>
      </View>

      <View className="mb-6 p-4 bg-warning-50 border border-warning-200 rounded-lg">
        <Text className="text-warning-700">⚠ These codes will not be shown again</Text>
      </View>

      <Button onPress={handleShare} variant="outline" className="mb-4">
        Share Codes
      </Button>

      <Button onPress={() => setAcknowledged(!acknowledged)} variant="outline" className="mb-4">
        {acknowledged ? '✓ ' : ''}I have saved my codes
      </Button>

      <Button onPress={handleComplete} disabled={!acknowledged}>
        Complete Setup
      </Button>
    </ScrollView>
  );
}
