/**
 * GraphQL mutations for core authentication operations.
 *
 * Mutations for registration, login, and logout.
 */

import { gql } from '@apollo/client';
import { USER_FULL_FIELDS } from '../fragments';

/**
 * Mutation to register a new user account.
 *
 * Creates a new user with email/password authentication.
 * Returns user data and authentication token on success.
 *
 * @example
 * ```typescript
 * const [register] = useMutation(REGISTER);
 * const { data } = await register({
 *   variables: {
 *     input: {
 *       email,
 *       username,
 *       password,
 *       firstName,
 *       lastName,
 *       termsAccepted: true,
 *       privacyAccepted: true
 *     }
 *   }
 * });
 * ```
 */
export const REGISTER = gql`
  mutation Register($input: RegisterInput!) {
    register(input: $input) {
      success
      message
      user {
        ...UserFullFields
      }
      token
      requiresEmailVerification
    }
  }
  ${USER_FULL_FIELDS}
`;

/**
 * Mutation to log in with email and password.
 *
 * Returns user data and authentication token on success.
 * May require MFA verification (check requiresMFA field).
 *
 * @example
 * ```typescript
 * const [login] = useMutation(LOGIN);
 * const { data } = await login({
 *   variables: { email, password, rememberMe: true }
 * });
 * if (data.login.requiresMFA) {
 *   // Redirect to MFA verification
 * }
 * ```
 */
export const LOGIN = gql`
  mutation Login($email: String!, $password: String!, $rememberMe: Boolean) {
    login(email: $email, password: $password, rememberMe: $rememberMe) {
      success
      message
      user {
        ...UserFullFields
      }
      token
      requiresMFA
      mfaToken
    }
  }
  ${USER_FULL_FIELDS}
`;

/**
 * Mutation to log out the current user.
 *
 * Terminates the current session and clears authentication tokens.
 *
 * @example
 * ```typescript
 * const [logout] = useMutation(LOGOUT);
 * await logout();
 * // Clear client-side cache
 * clearAuthCache();
 * ```
 */
export const LOGOUT = gql`
  mutation Logout {
    logout {
      success
      message
    }
  }
`;

/**
 * Mutation to refresh authentication token.
 *
 * Extends session timeout without requiring re-authentication.
 * Returns new token with extended expiry.
 *
 * @example
 * ```typescript
 * const [refreshToken] = useMutation(REFRESH_TOKEN);
 * const { data } = await refreshToken();
 * const newToken = data.refreshToken.token;
 * ```
 */
export const REFRESH_TOKEN = gql`
  mutation RefreshToken {
    refreshToken {
      success
      token
      expiresAt
    }
  }
`;
