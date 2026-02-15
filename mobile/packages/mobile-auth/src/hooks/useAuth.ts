/**
 * useAuth.ts
 *
 * Mobile-specific authentication hook wrapper.
 * Thin wrapper around shared useAuth with React Native Navigation integration.
 * Most logic is in shared hooks - this only adds navigation.
 */

import { useNavigation } from '@react-navigation/native';
import type { StackNavigationProp } from '@react-navigation/stack';

// TODO: Import shared useAuth once available
// import { useAuth as useSharedAuth } from '@syntek/shared/auth/hooks';

/**
 * Authentication hook for React Native.
 *
 * Provides authentication state and methods with React Native Navigation integration.
 * Wraps shared authentication logic with mobile-specific navigation.
 *
 * @returns Authentication state and methods
 *
 * @example
 * ```tsx
 * function LoginScreen() {
 *   const { login, isLoading } = useAuth();
 *
 *   const handleLogin = async () => {
 *     await login(email, password);
 *     // Automatically navigates to Dashboard on success
 *   };
 *
 *   return <Button onPress={handleLogin}>Login</Button>;
 * }
 * ```
 */
export function useAuth() {
  const navigation = useNavigation<StackNavigationProp<any>>();

  // TODO: Use shared auth hook
  // const sharedAuth = useSharedAuth();

  /**
   * Logs in the user and navigates to dashboard on success.
   */
  const login = async (email: string, password: string): Promise<void> => {
    try {
      // TODO: Call shared login mutation
      // await sharedAuth.login(email, password);

      // Navigate to dashboard after successful login
      navigation.navigate('Dashboard' as never);
    } catch (error) {
      // Error handling is done by shared hook
      throw error;
    }
  };

  /**
   * Logs out the user and navigates to login screen.
   */
  const logout = async (): Promise<void> => {
    try {
      // TODO: Call shared logout mutation
      // await sharedAuth.logout();

      // Navigate to login screen
      navigation.navigate('Login' as never);
    } catch (error) {
      throw error;
    }
  };

  /**
   * Registers a new user and navigates to phone verification or login.
   */
  const register = async (data: any): Promise<void> => {
    try {
      // TODO: Call shared register mutation
      // const result = await sharedAuth.register(data);

      // Navigate based on whether phone verification is needed
      if (data.phoneNumber) {
        navigation.navigate('PhoneVerification' as never, {
          phoneNumber: data.phoneNumber,
          userId: 'mock-user-id', // Replace with actual user ID
        } as never);
      } else {
        navigation.navigate('Login' as never);
      }
    } catch (error) {
      throw error;
    }
  };

  return {
    login,
    logout,
    register,
    // TODO: Spread shared auth methods
    // ...sharedAuth,
    isLoading: false, // TODO: Get from shared hook
    isAuthenticated: false, // TODO: Get from shared hook
    user: null, // TODO: Get from shared hook
  };
}
