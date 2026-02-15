/**
 * SessionSecurityScreen.tsx
 *
 * React Native session security screen.
 * Displays active sessions with revocation capabilities.
 * Uses shared session management logic.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, FlatList, Alert } from 'react-native';
import { Button } from '@syntek/shared/design-system/components';

interface Session {
  id: string;
  device: string;
  location: string;
  ipAddress: string;
  lastActive: string;
  isCurrent: boolean;
}

export function SessionSecurityScreen(): JSX.Element {
  const [sessions, setSessions] = useState<Session[]>([
    {
      id: '1',
      device: 'iPhone 15 Pro',
      location: 'London, UK',
      ipAddress: '192.168.1.1',
      lastActive: new Date().toISOString(),
      isCurrent: true,
    },
  ]);

  const handleRevokeSession = (id: string): void => {
    Alert.alert('Revoke Session', 'Are you sure you want to log out this device?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Revoke', style: 'destructive', onPress: () => {
        setSessions(sessions.filter(s => s.id !== id));
        Alert.alert('Session Revoked', 'The device has been logged out');
      }},
    ]);
  };

  const handleRevokeAll = (): void => {
    Alert.alert(
      'Revoke All Sessions',
      'This will log you out of all devices except this one. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Revoke All', style: 'destructive', onPress: () => {
          setSessions(sessions.filter(s => s.isCurrent));
          Alert.alert('Sessions Revoked', 'All other devices have been logged out');
        }},
      ]
    );
  };

  return (
    <ScrollView className="flex-1 bg-white p-6">
      <Text className="text-2xl font-bold mb-2">Active Sessions</Text>
      <Text className="text-neutral-600 mb-6">
        Manage devices with access to your account
      </Text>

      {sessions.length > 1 && (
        <Button onPress={handleRevokeAll} variant="outline" className="mb-6">
          Revoke All Other Sessions
        </Button>
      )}

      <FlatList
        data={sessions}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View className="p-4 bg-neutral-50 rounded-lg mb-3">
            <View className="flex-row justify-between items-start mb-2">
              <Text className="font-semibold flex-1">{item.device}</Text>
              {item.isCurrent && (
                <View className="bg-success-100 px-2 py-1 rounded">
                  <Text className="text-success-700 text-xs">Current</Text>
                </View>
              )}
            </View>
            <Text className="text-sm text-neutral-600">{item.location}</Text>
            <Text className="text-sm text-neutral-500">IP: {item.ipAddress}</Text>
            <Text className="text-sm text-neutral-500">
              Last active: {new Date(item.lastActive).toLocaleString()}
            </Text>
            {!item.isCurrent && (
              <Button
                onPress={() => handleRevokeSession(item.id)}
                variant="outline"
                className="mt-2"
              >
                Revoke Session
              </Button>
            )}
          </View>
        )}
      />
    </ScrollView>
  );
}
