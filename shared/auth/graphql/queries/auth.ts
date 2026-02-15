/**
 * GraphQL queries for authentication operations.
 *
 * Core authentication queries for user data and email/username checks.
 */

import { gql } from '@apollo/client';
import { USER_FULL_FIELDS, USER_SECURITY_FIELDS } from '../fragments';

/**
 * Query to fetch current authenticated user.
 *
 * Returns full user information including profile and security data.
 * Cached for 5 minutes to reduce API calls.
 *
 * @example
 * ```typescript
 * const { data, loading } = useQuery(GET_CURRENT_USER);
 * const user = data?.currentUser;
 * ```
 */
export const GET_CURRENT_USER = gql`
  query GetCurrentUser {
    currentUser {
      ...UserFullFields
    }
  }
  ${USER_FULL_FIELDS}
`;

/**
 * Query to check if an email address already exists.
 *
 * Used during registration to provide real-time feedback.
 * Uses client-side SHA-256 hashing for privacy (see useEmailLookup hook).
 *
 * @example
 * ```typescript
 * const { data } = await client.query({
 *   query: CHECK_EMAIL_EXISTS,
 *   variables: { emailHash: sha256(email) }
 * });
 * const exists = data.checkEmailExists;
 * ```
 */
export const CHECK_EMAIL_EXISTS = gql`
  query CheckEmailExists($emailHash: String!) {
    checkEmailExists(emailHash: $emailHash)
  }
`;

/**
 * Query to check if a username already exists.
 *
 * Used during registration to provide real-time feedback.
 *
 * @example
 * ```typescript
 * const { data } = await client.query({
 *   query: CHECK_USERNAME_EXISTS,
 *   variables: { username }
 * });
 * const exists = data.checkUsernameExists;
 * ```
 */
export const CHECK_USERNAME_EXISTS = gql`
  query CheckUsernameExists($username: String!) {
    checkUsernameExists(username: $username)
  }
`;

/**
 * Query to get minimal user security information.
 *
 * Lightweight query for security dashboards and settings pages.
 * Returns only security-related fields (MFA status, passkey count, etc.).
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_USER_SECURITY_INFO);
 * const { totpEnabled, passkeyCount } = data.currentUser;
 * ```
 */
export const GET_USER_SECURITY_INFO = gql`
  query GetUserSecurityInfo {
    currentUser {
      ...UserSecurityFields
    }
  }
  ${USER_SECURITY_FIELDS}
`;
