/**
 * GraphQL mutations for social authentication (OAuth) operations.
 *
 * Mutations for linking/unlinking social accounts and OAuth callbacks.
 */

import { gql } from '@apollo/client';
import { SOCIAL_ACCOUNT_FULL_FIELDS } from '../fragments';

/**
 * Mutation to link a social account to the user.
 *
 * Links OAuth account (Google, GitHub, etc.) to existing user account.
 * Requires OAuth authorization code from provider callback.
 *
 * @example
 * ```typescript
 * const [linkSocialAccount] = useMutation(LINK_SOCIAL_ACCOUNT);
 * const { data } = await linkSocialAccount({
 *   variables: {
 *     provider: 'google',
 *     code: 'oauth_code_from_callback',
 *     state: 'csrf_state_token'
 *   }
 * });
 * ```
 */
export const LINK_SOCIAL_ACCOUNT = gql`
  mutation LinkSocialAccount(
    $provider: String!
    $code: String!
    $state: String!
  ) {
    linkSocialAccount(provider: $provider, code: $code, state: $state) {
      success
      message
      socialAccount {
        ...SocialAccountFullFields
      }
    }
  }
  ${SOCIAL_ACCOUNT_FULL_FIELDS}
`;

/**
 * Mutation to unlink a social account from the user.
 *
 * Removes OAuth account link from user account.
 * Requires password confirmation if this is the only login method.
 *
 * @example
 * ```typescript
 * const [unlinkSocialAccount] = useMutation(UNLINK_SOCIAL_ACCOUNT);
 * await unlinkSocialAccount({
 *   variables: { socialAccountId, password }
 * });
 * ```
 */
export const UNLINK_SOCIAL_ACCOUNT = gql`
  mutation UnlinkSocialAccount($socialAccountId: ID!, $password: String) {
    unlinkSocialAccount(socialAccountId: $socialAccountId, password: $password) {
      success
      message
    }
  }
`;

/**
 * Mutation to authenticate with social account (login).
 *
 * Logs in user using OAuth provider (Google, GitHub, etc.).
 * Requires OAuth authorization code from provider callback.
 *
 * @example
 * ```typescript
 * const [socialLogin] = useMutation(SOCIAL_LOGIN);
 * const { data } = await socialLogin({
 *   variables: {
 *     provider: 'google',
 *     code: 'oauth_code_from_callback',
 *     state: 'csrf_state_token'
 *   }
 * });
 * ```
 */
export const SOCIAL_LOGIN = gql`
  mutation SocialLogin($provider: String!, $code: String!, $state: String!) {
    socialLogin(provider: $provider, code: $code, state: $state) {
      success
      message
      token
      user {
        id
        email
      }
      isNewUser
    }
  }
`;
