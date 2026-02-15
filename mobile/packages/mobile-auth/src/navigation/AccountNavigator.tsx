/**
 * AccountNavigator.tsx
 *
 * React Native navigation stack for account management and GDPR compliance.
 * Handles profile updates, security settings, data export, account deletion,
 * and privacy settings screens.
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import type { StackNavigationOptions } from '@react-navigation/stack';

// Import screens
import { ProfileUpdateScreen } from '../screens/gdpr/ProfileUpdateScreen';
import { SessionSecurityScreen } from '../screens/security/SessionSecurityScreen';
import { PasskeyManagementScreen } from '../screens/security/PasskeyManagementScreen';
import { DataExportScreen } from '../screens/gdpr/DataExportScreen';
import { AccountDeletionScreen } from '../screens/gdpr/AccountDeletionScreen';
import { PrivacySettingsScreen } from '../screens/gdpr/PrivacySettingsScreen';

/**
 * Type definitions for account stack navigation parameters.
 */
export type AccountStackParamList = {
  ProfileUpdate: undefined;
  SessionSecurity: undefined;
  PasskeyManagement: undefined;
  DataExport: undefined;
  AccountDeletion: undefined;
  PrivacySettings: undefined;
};

const Stack = createStackNavigator<AccountStackParamList>();

/**
 * Default screen options for consistent styling across account screens.
 */
const screenOptions: StackNavigationOptions = {
  headerStyle: {
    backgroundColor: '#3b82f6', // primary color
  },
  headerTintColor: '#ffffff',
  headerTitleStyle: {
    fontWeight: '600',
  },
  cardStyle: {
    backgroundColor: '#f9fafb', // neutral-50
  },
};

/**
 * Account management stack navigator component.
 *
 * Provides navigation between account-related screens including profile
 * updates, security settings, passkey management, GDPR data export,
 * account deletion, and privacy settings. All screens use shared
 * components from @syntek/shared for GDPR compliance.
 *
 * @returns React Navigation stack navigator for account management
 */
export function AccountNavigator(): JSX.Element {
  return (
    <Stack.Navigator
      initialRouteName="ProfileUpdate"
      screenOptions={screenOptions}
    >
      <Stack.Screen
        name="ProfileUpdate"
        component={ProfileUpdateScreen}
        options={{
          title: 'Profile Settings',
        }}
      />
      <Stack.Screen
        name="SessionSecurity"
        component={SessionSecurityScreen}
        options={{
          title: 'Active Sessions',
        }}
      />
      <Stack.Screen
        name="PasskeyManagement"
        component={PasskeyManagementScreen}
        options={{
          title: 'Passkeys',
        }}
      />
      <Stack.Screen
        name="DataExport"
        component={DataExportScreen}
        options={{
          title: 'Export Data',
        }}
      />
      <Stack.Screen
        name="AccountDeletion"
        component={AccountDeletionScreen}
        options={{
          title: 'Delete Account',
          headerStyle: {
            backgroundColor: '#ef4444', // danger color
          },
        }}
      />
      <Stack.Screen
        name="PrivacySettings"
        component={PrivacySettingsScreen}
        options={{
          title: 'Privacy Settings',
        }}
      />
    </Stack.Navigator>
  );
}
