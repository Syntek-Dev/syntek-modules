/**
 * PasskeyManagementScreen.tsx
 *
 * React Native passkey management screen.
 * Lists and manages passkeys using native platform authenticator.
 * Uses shared passkey logic for maximum code reuse.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, FlatList, Alert } from 'react-native';
import { Button } from '@syntek/shared/design-system/components';

interface Passkey {
  id: string;
  name: string;
  createdAt: string;
  lastUsed: string | null;
}

export function PasskeyManagementScreen(): JSX.Element {
  const [passkeys, setPasskeys] = useState<Passkey[]>([]);

  const handleAddPasskey = async (): Promise<void> => {
    Alert.alert('Add Passkey', 'Native platform authenticator integration required');
    // TODO: Implement native passkey registration
  };

  const handleDeletePasskey = (id: string): void => {
    Alert.alert('Delete Passkey', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => {
        setPasskeys(passkeys.filter(p => p.id !== id));
      }},
    ]);
  };

  return (
    <ScrollView className="flex-1 bg-white p-6">
      <Text className="text-2xl font-bold mb-2">Passkeys</Text>
      <Text className="text-neutral-600 mb-6">
        Manage your passwordless authentication methods
      </Text>

      <Button onPress={handleAddPasskey} className="mb-6">
        Add New Passkey
      </Button>

      {passkeys.length === 0 ? (
        <View className="p-8 items-center">
          <Text className="text-neutral-500">No passkeys configured</Text>
        </View>
      ) : (
        <FlatList
          data={passkeys}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View className="p-4 bg-neutral-50 rounded-lg mb-3">
              <Text className="font-semibold">{item.name}</Text>
              <Text className="text-sm text-neutral-600">
                Created: {new Date(item.createdAt).toLocaleDateString()}
              </Text>
              <Button
                onPress={() => handleDeletePasskey(item.id)}
                variant="outline"
                className="mt-2"
              >
                Delete
              </Button>
            </View>
          )}
        />
      )}
    </ScrollView>
  );
}
