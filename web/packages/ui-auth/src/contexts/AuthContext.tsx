/**
 * Auth Context Provider (Web)
 *
 * Provides authentication state and methods to Next.js application.
 * Wraps shared authentication hooks with Next.js router integration.
 */

'use client';

import { createContext, useContext, ReactNode } from 'react';
import { useAuth } from '../hooks/useAuth';
import type { AuthConfig } from '@syntek/shared-auth/types';

/**
 * Auth context value interface
 */
export interface AuthContextValue {
  /** Auth configuration from backend */
  config: AuthConfig | null;
  /** Login method */
  login: (data: any, callbackUrl?: string) => Promise<void>;
  /** Register method */
  register: (data: any, callbackUrl?: string) => Promise<void>;
  /** Logout method */
  logout: (redirectUrl?: string) => Promise<void>;
}

/**
 * Auth context
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Auth provider props
 */
export interface AuthProviderProps {
  /** Child components */
  children: ReactNode;
}

/**
 * Provides authentication context to application
 *
 * Usage:
 * ```tsx
 * <AuthProvider>
 *   <App />
 * </AuthProvider>
 * ```
 *
 * @param children - Child components
 * @returns Auth context provider
 */
export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const auth = useAuth();

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context
 *
 * Must be used within AuthProvider.
 *
 * @returns Auth context value
 * @throws Error if used outside AuthProvider
 */
export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }

  return context;
}
