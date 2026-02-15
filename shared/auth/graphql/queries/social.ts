/**
 * GraphQL queries for social authentication (OAuth) operations.
 *
 * Queries for linked social accounts and OAuth provider configuration.
 */

import { gql } from '@apollo/client';
import { SOCIAL_ACCOUNT_FULL_FIELDS } from '../fragments';

/**
 * Query to get all linked social accounts for the current user.
 *
 * Returns list of OAuth accounts (Google, GitHub, Microsoft, etc.).
 * Cached for 5 minutes to reduce API calls.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_SOCIAL_ACCOUNTS);
 * const accounts = data.getSocialAccounts;
 * ```
 */
export const GET_SOCIAL_ACCOUNTS = gql`
  query GetSocialAccounts {
    getSocialAccounts {
      ...SocialAccountFullFields
    }
  }
  ${SOCIAL_ACCOUNT_FULL_FIELDS}
`;

/**
 * Query to get available OAuth providers.
 *
 * Returns list of enabled OAuth providers (from Django SYNTEK_AUTH settings).
 * Includes provider metadata (name, icon URL, authorization URL).
 *
 * @example
 * ```typescript
 * const { data } = useQuery(SOCIAL_PROVIDERS);
 * const providers = data.socialProviders;
 * ```
 */
export const SOCIAL_PROVIDERS = gql`
  query SocialProviders {
    socialProviders {
      provider
      displayName
      iconUrl
      authorizationUrl
      enabled
    }
  }
`;

/**
 * Query to get OAuth authorization URL for a specific provider.
 *
 * Returns URL to redirect user to for OAuth consent flow.
 * Includes state parameter for CSRF protection.
 *
 * @example
 * ```typescript
 * const { data } = await client.query({
 *   query: GET_OAUTH_URL,
 *   variables: { provider: 'google', redirectUri: window.location.origin }
 * });
 * window.location.href = data.getOAuthUrl.url;
 * ```
 */
export const GET_OAUTH_URL = gql`
  query GetOAuthUrl($provider: String!, $redirectUri: String!) {
    getOAuthUrl(provider: $provider, redirectUri: $redirectUri) {
      url
      state
    }
  }
`;
