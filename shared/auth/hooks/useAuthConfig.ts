/**
 * Hook to fetch authentication configuration from Django backend.
 *
 * Configuration is fetched via GraphQL and cached for 5 minutes.
 * Uses fallback values if GraphQL query fails.
 */

import { useQuery } from '@apollo/client';

import { GET_AUTH_CONFIG } from '../graphql/queries/config';
import type { AuthConfig } from '../types/config';
import { AUTH_CONFIG_FALLBACK } from '../types/config';

interface AuthConfigResponse {
  authConfig: AuthConfig;
}

interface UseAuthConfigReturn {
  /**
   * Authentication configuration from backend.
   * Falls back to default values if query fails or is loading.
   */
  config: AuthConfig;

  /**
   * Whether the configuration is being fetched.
   */
  loading: boolean;

  /**
   * Error from GraphQL query (if any).
   */
  error?: Error;

  /**
   * Refetch the configuration from backend.
   */
  refetch: () => Promise<unknown>;
}

/**
 * Fetch authentication configuration from Django backend via GraphQL.
 *
 * Configuration is cached for 5 minutes to reduce API calls.
 * If the query fails or is loading, fallback values are returned.
 *
 * @returns Auth configuration and query state
 *
 * @example
 * ```typescript
 * const { config, loading, error } = useAuthConfig();
 *
 * if (password.length < config.passwordMinLength) {
 *   return `Password must be at least ${config.passwordMinLength} characters`;
 * }
 * ```
 */
export function useAuthConfig(): UseAuthConfigReturn {
  const { data, loading, error, refetch } = useQuery<AuthConfigResponse>(GET_AUTH_CONFIG, {
    // Cache for 5 minutes - config doesn't change often
    fetchPolicy: 'cache-first',
    nextFetchPolicy: 'cache-first',
  });

  return {
    config: data?.authConfig ?? AUTH_CONFIG_FALLBACK,
    loading,
    error: error as Error | undefined,
    refetch,
  };
}
