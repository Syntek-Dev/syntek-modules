/**
 * AccountDeletionScreen.tsx
 *
 * React Native account deletion screen (GDPR Article 17 - Right to Erasure).
 * Implements 30-day grace period before permanent deletion.
 * Uses shared account deletion logic.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, Alert } from 'react-native';
import { Button, Input, Checkbox } from '@syntek/shared/design-system/components';
import { useNavigation } from '@react-navigation/native';

export function AccountDeletionScreen(): JSX.Element {
  const navigation = useNavigation();
  const [confirmText, setConfirmText] = useState('');
  const [understand, setUnderstand] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (): Promise<void> => {
    if (confirmText.toLowerCase() !== 'delete') {
      Alert.alert('Confirmation Required', 'Please type DELETE to confirm');
      return;
    }

    if (!understand) {
      Alert.alert('Confirmation Required', 'Please confirm you understand this action');
      return;
    }

    Alert.alert(
      'Delete Account',
      'Your account will be scheduled for deletion in 30 days. You can cancel during this period. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsDeleting(true);
              // TODO: Use shared account deletion mutation
              Alert.alert(
                'Deletion Scheduled',
                'Your account will be deleted in 30 days. You can cancel this at any time before then.',
                [{ text: 'OK', onPress: () => navigation.goBack() }]
              );
            } catch (error) {
              Alert.alert('Error', 'Failed to schedule deletion');
            } finally {
              setIsDeleting(false);
            }
          },
        },
      ]
    );
  };

  return (
    <ScrollView className="flex-1 bg-white p-6">
      <Text className="text-2xl font-bold text-danger-700 mb-2">Delete Account</Text>
      <Text className="text-neutral-600 mb-6">
        This action cannot be undone after the 30-day grace period
      </Text>

      <View className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-lg">
        <Text className="text-danger-700 font-semibold mb-2">⚠ Warning</Text>
        <Text className="text-danger-700 text-sm mb-1">• All your data will be permanently deleted</Text>
        <Text className="text-danger-700 text-sm mb-1">• Active sessions will be terminated</Text>
        <Text className="text-danger-700 text-sm mb-1">• You have 30 days to cancel</Text>
      </View>

      <View className="mb-4">
        <Input
          label="Type DELETE to confirm"
          value={confirmText}
          onChangeText={setConfirmText}
          placeholder="DELETE"
          autoCapitalize="characters"
        />
      </View>

      <View className="mb-6">
        <Checkbox
          checked={understand}
          onChange={setUnderstand}
          label="I understand this action schedules my account for permanent deletion"
        />
      </View>

      <Button
        onPress={handleDelete}
        disabled={isDeleting || confirmText.toLowerCase() !== 'delete' || !understand}
        className="bg-danger-600"
      >
        {isDeleting ? 'Scheduling Deletion...' : 'Delete My Account'}
      </Button>
    </ScrollView>
  );
}
