/**
 * AuthNavigator.tsx
 *
 * React Native navigation stack for authentication flow.
 * Handles registration, login, verification, and password recovery screens.
 * Integrates with React Navigation stack navigator.
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import type { StackNavigationOptions } from '@react-navigation/stack';

// Import screens
import { LoginScreen } from '../screens/auth/LoginScreen';
import { RegistrationScreen } from '../screens/auth/RegistrationScreen';
import { PhoneVerificationScreen } from '../screens/auth/PhoneVerificationScreen';
import { TOTPSetupScreen } from '../screens/mfa/TOTPSetupScreen';
import { RecoveryKeyScreen } from '../screens/mfa/RecoveryKeyScreen';

/**
 * Type definitions for auth stack navigation parameters.
 */
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  PhoneVerification: {
    phoneNumber: string;
    userId: string;
  };
  TOTPSetup: {
    userId: string;
  };
  RecoveryKey: {
    recoveryKey: string;
  };
};

const Stack = createStackNavigator<AuthStackParamList>();

/**
 * Default screen options for consistent styling across auth screens.
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
    backgroundColor: '#ffffff',
  },
};

/**
 * Authentication stack navigator component.
 *
 * Provides navigation between authentication-related screens including
 * login, registration, phone verification, TOTP setup, and recovery key.
 * Uses shared components from @syntek/shared for business logic.
 *
 * @returns React Navigation stack navigator for authentication flow
 */
export function AuthNavigator(): JSX.Element {
  return (
    <Stack.Navigator
      initialRouteName="Login"
      screenOptions={screenOptions}
    >
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{
          title: 'Sign In',
          headerShown: false, // Custom header in screen
        }}
      />
      <Stack.Screen
        name="Register"
        component={RegistrationScreen}
        options={{
          title: 'Create Account',
          headerShown: false, // Custom header in screen
        }}
      />
      <Stack.Screen
        name="PhoneVerification"
        component={PhoneVerificationScreen}
        options={{
          title: 'Verify Phone Number',
          headerBackTitle: 'Back',
        }}
      />
      <Stack.Screen
        name="TOTPSetup"
        component={TOTPSetupScreen}
        options={{
          title: 'Set Up Two-Factor Authentication',
          headerBackTitle: 'Back',
        }}
      />
      <Stack.Screen
        name="RecoveryKey"
        component={RecoveryKeyScreen}
        options={{
          title: 'Recovery Key',
          headerBackTitle: 'Back',
          headerLeft: () => null, // Prevent going back
        }}
      />
    </Stack.Navigator>
  );
}
