/**
 * withAuth Higher-Order Component
 *
 * Protected route wrapper for Next.js pages. Redirects unauthenticated users
 * to login page and displays loading state during authentication check.
 */

'use client';

import { ComponentType, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Spinner } from '@syntek/shared/design-system/components';

/**
 * withAuth options
 */
export interface WithAuthOptions {
  /** Redirect URL for unauthenticated users */
  redirectTo?: string;
  /** Show loading spinner during auth check */
  showLoading?: boolean;
}

/**
 * Higher-order component for protected routes
 *
 * Checks authentication status and redirects to login if not authenticated.
 * Displays loading state while checking authentication.
 *
 * Usage:
 * ```tsx
 * const ProtectedPage = withAuth(MyPage, {
 *   redirectTo: '/auth/login',
 * });
 * ```
 *
 * @param Component - Component to protect
 * @param options - withAuth options
 * @returns Protected component
 */
export function withAuth<P extends object>(
  Component: ComponentType<P>,
  options: WithAuthOptions = {}
): ComponentType<P> {
  const { redirectTo = '/auth/login', showLoading = true } = options;

  return function ProtectedComponent(props: P): JSX.Element | null {
    const router = useRouter();
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

    useEffect(() => {
      /**
       * Checks authentication status
       *
       * In a real implementation, this would:
       * 1. Check for httpOnly auth cookie
       * 2. Validate token with backend
       * 3. Set authentication state
       *
       * For now, we'll use a placeholder that checks localStorage
       * (real implementation would use server-side session validation)
       */
      async function checkAuth(): Promise<void> {
        try {
          // TODO: Replace with actual authentication check via GraphQL
          // const { data } = await client.query({ query: ME_QUERY });
          // setIsAuthenticated(!!data?.me);

          // Placeholder: Check for auth token
          const hasToken = document.cookie.includes('auth_token');
          setIsAuthenticated(hasToken);

          if (!hasToken) {
            router.push(`${redirectTo}?redirect=${encodeURIComponent(window.location.pathname)}`);
          }
        } catch (error) {
          setIsAuthenticated(false);
          router.push(redirectTo);
        }
      }

      checkAuth();
    }, [router]);

    // Loading state
    if (isAuthenticated === null && showLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <Spinner size="lg" />
        </div>
      );
    }

    // Not authenticated (redirect in progress)
    if (!isAuthenticated) {
      return null;
    }

    // Authenticated - render component
    return <Component {...props} />;
  };
}
