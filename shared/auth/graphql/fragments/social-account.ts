/**
 * GraphQL fragments for Social Account (OAuth) fields.
 *
 * Reusable fragments for linked social account data.
 */

import { gql } from '@apollo/client';

/**
 * Core social account fields fragment.
 *
 * Essential social account information for account linking display.
 */
export const SOCIAL_ACCOUNT_CORE_FIELDS = gql`
  fragment SocialAccountCoreFields on SocialAccount {
    id
    provider
    providerAccountId
    email
    displayName
    avatarUrl
    createdAt
    lastUsed
  }
`;

/**
 * Full social account fields fragment.
 *
 * Complete social account information including OAuth tokens metadata.
 * Note: Never expose actual OAuth tokens via GraphQL (security risk).
 */
export const SOCIAL_ACCOUNT_FULL_FIELDS = gql`
  fragment SocialAccountFullFields on SocialAccount {
    ...SocialAccountCoreFields
    tokenExpiresAt
    scope
  }
  ${SOCIAL_ACCOUNT_CORE_FIELDS}
`;
