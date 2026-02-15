/**
 * DataExportScreen.tsx
 *
 * React Native data export screen (GDPR Article 20 - Right to Data Portability).
 * Allows users to export their authentication data in JSON or CSV format.
 * Uses shared data export logic and React Native Share API.
 */

import React, { useState } from 'react';
import { View, Text, ScrollView, Share, Alert } from 'react-native';
import { Button } from '@syntek/shared/design-system/components';

export function DataExportScreen(): JSX.Element {
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json');

  const handleExport = async (format: 'json' | 'csv'): Promise<void> => {
    try {
      setIsExporting(true);
      setExportFormat(format);

      // TODO: Use shared data export mutation
      const mockData = {
        email: 'user@example.com',
        username: 'username',
        phoneNumber: '+44 7123 456789',
        createdAt: new Date().toISOString(),
        sessions: [],
        passkeys: [],
      };

      const data = format === 'json'
        ? JSON.stringify(mockData, null, 2)
        : 'Email,Username,Phone\nuser@example.com,username,+44 7123 456789';

      await Share.share({
        message: data,
        title: `Authentication Data Export (${format.toUpperCase()})`,
      });

      Alert.alert('Export Complete', `Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      Alert.alert('Export Failed', 'Unable to export data');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <ScrollView className="flex-1 bg-white p-6">
      <Text className="text-2xl font-bold mb-2">Export Your Data</Text>
      <Text className="text-neutral-600 mb-6">
        Download a copy of your authentication data (GDPR Article 20)
      </Text>

      <View className="mb-6 p-4 bg-neutral-50 rounded-lg">
        <Text className="font-semibold mb-2">Data Included:</Text>
        <Text className="text-sm text-neutral-700">• Email address</Text>
        <Text className="text-sm text-neutral-700">• Username</Text>
        <Text className="text-sm text-neutral-700">• Phone number (if provided)</Text>
        <Text className="text-sm text-neutral-700">• Account creation date</Text>
        <Text className="text-sm text-neutral-700">• Active sessions</Text>
        <Text className="text-sm text-neutral-700">• Registered passkeys</Text>
      </View>

      <Button
        onPress={() => handleExport('json')}
        disabled={isExporting}
        className="mb-3"
      >
        {isExporting && exportFormat === 'json' ? 'Exporting...' : 'Export as JSON'}
      </Button>

      <Button
        onPress={() => handleExport('csv')}
        disabled={isExporting}
        variant="outline"
      >
        {isExporting && exportFormat === 'csv' ? 'Exporting...' : 'Export as CSV'}
      </Button>
    </ScrollView>
  );
}
