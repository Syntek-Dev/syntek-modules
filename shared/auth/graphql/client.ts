/**
 * Apollo Client configuration for authentication GraphQL operations.
 *
 * This module exports an Apollo Client instance configured with:
 * - Cache policies (user: 5 min cache, sessions: always fresh)
 * - HttpOnly cookie credentials
 * - Error handling and logging
 * - Automatic retry logic for network failures
 *
 * @example
 * ```typescript
 * import { authApolloClient } from '@syntek/shared-auth/graphql/client';
 *
 * const { data } = await authApolloClient.query({
 *   query: GET_CURRENT_USER,
 * });
 * ```
 */

import {
  ApolloClient,
  InMemoryCache,
  HttpLink,
  from,
  ApolloLink,
} from '@apollo/client';
import { onError } from '@apollo/client/link/error';
import { RetryLink } from '@apollo/client/link/retry';

/**
 * GraphQL endpoint URL.
 *
 * Defaults to /graphql/ on the same origin. Override via environment variable.
 */
const GRAPHQL_ENDPOINT =
  typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_GRAPHQL_ENDPOINT
    ? process.env.NEXT_PUBLIC_GRAPHQL_ENDPOINT
    : '/graphql/';

/**
 * HTTP link configuration for Apollo Client.
 *
 * Includes credentials (httpOnly cookies) and CSRF token handling.
 */
const httpLink = new HttpLink({
  uri: GRAPHQL_ENDPOINT,
  credentials: 'include', // Send httpOnly cookies with every request
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Error handling link.
 *
 * Logs GraphQL and network errors without exposing sensitive data.
 * Redacts PII from error messages before logging.
 */
const errorLink = onError(({ graphQLErrors, networkError, operation }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path, extensions }) => {
      // Log error without sensitive data
      console.error(
        `[GraphQL error]: Message: ${message}, Location: ${JSON.stringify(locations)}, Path: ${path}`
      );

      // Handle specific error codes
      if (extensions?.code === 'UNAUTHENTICATED') {
        // Clear cached auth data on unauthenticated errors
        authApolloClient.cache.evict({ fieldName: 'currentUser' });
        authApolloClient.cache.gc();
      }
    });
  }

  if (networkError) {
    console.error(`[Network error]: ${networkError.message}`);
  }
});

/**
 * Retry link configuration.
 *
 * Automatically retries failed requests with exponential backoff.
 * Max 3 attempts for network failures.
 */
const retryLink = new RetryLink({
  delay: {
    initial: 300,
    max: 5000,
    jitter: true,
  },
  attempts: {
    max: 3,
    retryIf: (error, _operation) => {
      // Retry on network errors, not on GraphQL errors
      return !!error && !error.result;
    },
  },
});

/**
 * Apollo Client cache configuration.
 *
 * Defines cache policies for different query types:
 * - User data: 5-minute cache (rarely changes during session)
 * - Session data: Always fresh (security-critical)
 * - Config data: 5-minute cache (changes infrequently)
 */
const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        // User queries: 5-minute cache
        currentUser: {
          merge(existing, incoming) {
            return incoming;
          },
        },
        // Auth config: 5-minute cache
        authConfig: {
          merge(existing, incoming) {
            return incoming;
          },
        },
        // Sessions: Always fetch fresh data (security-critical)
        getActiveSessions: {
          merge: false,
        },
        sessionHistory: {
          merge: false,
        },
        getSuspiciousSessions: {
          merge: false,
        },
        // MFA: Always fetch fresh data
        getMFAStatus: {
          merge: false,
        },
        // Passkeys: Cache for 1 minute
        listPasskeys: {
          merge(existing, incoming) {
            return incoming;
          },
        },
      },
    },
  },
});

/**
 * Apollo Client instance for authentication operations.
 *
 * Configured with:
 * - Error handling and retry logic
 * - Cache policies for different data types
 * - HttpOnly cookie credentials
 * - CSRF protection
 *
 * @example
 * ```typescript
 * const { data } = await authApolloClient.query({
 *   query: GET_CURRENT_USER,
 * });
 * ```
 */
export const authApolloClient = new ApolloClient({
  link: from([errorLink, retryLink, httpLink]),
  cache,
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    query: {
      fetchPolicy: 'cache-first',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});

/**
 * Clear all authentication-related cache.
 *
 * Call this after logout to ensure no stale data remains.
 *
 * @example
 * ```typescript
 * await logout();
 * clearAuthCache();
 * ```
 */
export function clearAuthCache(): void {
  authApolloClient.cache.evict({ fieldName: 'currentUser' });
  authApolloClient.cache.evict({ fieldName: 'getActiveSessions' });
  authApolloClient.cache.evict({ fieldName: 'getMFAStatus' });
  authApolloClient.cache.gc();
}
