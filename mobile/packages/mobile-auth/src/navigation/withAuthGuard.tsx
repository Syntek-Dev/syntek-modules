/**
 * withAuthGuard.tsx
 *
 * Higher-order component for protecting React Native screens with authentication.
 * Redirects unauthenticated users to the login screen.
 * Uses shared authentication state from @syntek/shared.
 */

import React, { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { ComponentType } from 'react';

// Import shared auth hook (placeholder - will use actual hook)
// TODO: Import from @syntek/shared/auth/hooks once available
interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
}

/**
 * Temporary placeholder for authentication state.
 * Replace with actual import from @syntek/shared/auth/hooks.
 */
function useAuthState(): AuthState {
  // TODO: Replace with actual useAuth() from shared
  return {
    isAuthenticated: false,
    isLoading: true,
  };
}

/**
 * Props for components wrapped with authentication guard.
 */
export interface WithAuthGuardProps {
  // Additional props can be added here
}

/**
 * Higher-order component that protects screens with authentication.
 *
 * Wraps a React Native screen component and ensures the user is authenticated
 * before rendering. If unauthenticated, redirects to the login screen.
 * Shows loading spinner while checking authentication status.
 *
 * @param Component - The screen component to protect
 * @param options - Optional configuration for the guard
 * @param options.redirectTo - Route name to redirect unauthenticated users (default: 'Login')
 * @param options.requirePermissions - Optional permission checks
 * @returns Protected component that requires authentication
 *
 * @example
 * ```tsx
 * const ProtectedDashboard = withAuthGuard(DashboardScreen);
 * ```
 */
export function withAuthGuard<P extends object>(
  Component: ComponentType<P>,
  options: {
    redirectTo?: string;
    requirePermissions?: string[];
  } = {}
): ComponentType<P & WithAuthGuardProps> {
  const { redirectTo = 'Login' } = options;

  return function AuthGuardedComponent(props: P & WithAuthGuardProps): JSX.Element {
    const navigation = useNavigation();
    const { isAuthenticated, isLoading } = useAuthState();

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        // Redirect to login screen
        navigation.navigate(redirectTo as never);
      }
    }, [isAuthenticated, isLoading, navigation]);

    // Show loading spinner while checking authentication
    if (isLoading) {
      return (
        <View className="flex-1 items-center justify-center bg-white">
          <ActivityIndicator size="large" color="#3b82f6" />
        </View>
      );
    }

    // Don't render component if not authenticated
    if (!isAuthenticated) {
      return (
        <View className="flex-1 bg-white" />
      );
    }

    // Render protected component
    return <Component {...props} />;
  };
}

/**
 * Hook version of auth guard for use within functional components.
 *
 * Provides authentication state and redirect functionality.
 * Use this hook when you need conditional rendering based on auth state
 * within a component rather than wrapping the entire component.
 *
 * @param options - Optional configuration
 * @param options.redirectTo - Route name to redirect unauthenticated users
 * @returns Authentication state and redirect handler
 *
 * @example
 * ```tsx
 * function MyScreen() {
 *   const { isAuthenticated, isLoading } = useAuthGuard();
 *
 *   if (isLoading) return <Spinner />;
 *   if (!isAuthenticated) return null;
 *
 *   return <Content />;
 * }
 * ```
 */
export function useAuthGuard(options: {
  redirectTo?: string;
} = {}): {
  isAuthenticated: boolean;
  isLoading: boolean;
  checkAuth: () => void;
} {
  const navigation = useNavigation();
  const { redirectTo = 'Login' } = options;
  const { isAuthenticated, isLoading } = useAuthState();

  const checkAuth = React.useCallback(() => {
    if (!isLoading && !isAuthenticated) {
      navigation.navigate(redirectTo as never);
    }
  }, [isAuthenticated, isLoading, navigation, redirectTo]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return {
    isAuthenticated,
    isLoading,
    checkAuth,
  };
}
