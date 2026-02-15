/**
 * GraphQL mutations for user profile operations.
 *
 * Mutations for updating email, phone, username, password, and profile data.
 */

import { gql } from '@apollo/client';
import { USER_FULL_FIELDS } from '../fragments';

/**
 * Mutation to update user email address.
 *
 * Changes primary email and sends verification to new address.
 * Requires password confirmation for security.
 *
 * @example
 * ```typescript
 * const [updateEmail] = useMutation(UPDATE_EMAIL);
 * await updateEmail({
 *   variables: { newEmail, password }
 * });
 * ```
 */
export const UPDATE_EMAIL = gql`
  mutation UpdateEmail($newEmail: String!, $password: String!) {
    updateEmail(newEmail: $newEmail, password: $password) {
      success
      message
      requiresVerification
    }
  }
`;

/**
 * Mutation to update user phone number.
 *
 * Changes phone number and sends verification to new number.
 * Requires password confirmation for security.
 *
 * @example
 * ```typescript
 * const [updatePhone] = useMutation(UPDATE_PHONE);
 * await updatePhone({
 *   variables: { newPhone: '+447700900000', password }
 * });
 * ```
 */
export const UPDATE_PHONE = gql`
  mutation UpdatePhone($newPhone: String!, $password: String!) {
    updatePhone(newPhone: $newPhone, password: $password) {
      success
      message
      requiresVerification
    }
  }
`;

/**
 * Mutation to update username.
 *
 * Changes username (must be unique across platform).
 * Rate-limited to prevent abuse (max 1 change per 30 days).
 *
 * @example
 * ```typescript
 * const [updateUsername] = useMutation(UPDATE_USERNAME);
 * await updateUsername({
 *   variables: { newUsername, password }
 * });
 * ```
 */
export const UPDATE_USERNAME = gql`
  mutation UpdateUsername($newUsername: String!, $password: String!) {
    updateUsername(newUsername: $newUsername, password: $password) {
      success
      message
      user {
        ...UserFullFields
      }
    }
  }
  ${USER_FULL_FIELDS}
`;

/**
 * Mutation to update password.
 *
 * Changes user password (requires current password).
 * Terminates all other sessions after password change.
 *
 * @example
 * ```typescript
 * const [updatePassword] = useMutation(UPDATE_PASSWORD);
 * await updatePassword({
 *   variables: { currentPassword, newPassword }
 * });
 * ```
 */
export const UPDATE_PASSWORD = gql`
  mutation UpdatePassword($currentPassword: String!, $newPassword: String!) {
    updatePassword(currentPassword: $currentPassword, newPassword: $newPassword) {
      success
      message
      terminatedSessions
    }
  }
`;

/**
 * Mutation to update user profile information.
 *
 * Updates non-sensitive profile data (name, bio, avatar, locale, etc.).
 * Does not require password confirmation.
 *
 * @example
 * ```typescript
 * const [updateProfile] = useMutation(UPDATE_PROFILE);
 * await updateProfile({
 *   variables: {
 *     firstName: 'John',
 *     lastName: 'Doe',
 *     bio: 'Software developer',
 *     locale: 'en-GB'
 *   }
 * });
 * ```
 */
export const UPDATE_PROFILE = gql`
  mutation UpdateProfile($input: ProfileUpdateInput!) {
    updateProfile(input: $input) {
      success
      message
      user {
        ...UserFullFields
      }
    }
  }
  ${USER_FULL_FIELDS}
`;

/**
 * Mutation to request password reset.
 *
 * Sends password reset email to user's registered email address.
 * Rate-limited to prevent abuse (max 1 request per 60 seconds).
 *
 * @example
 * ```typescript
 * const [requestPasswordReset] = useMutation(REQUEST_PASSWORD_RESET);
 * await requestPasswordReset({
 *   variables: { email }
 * });
 * ```
 */
export const REQUEST_PASSWORD_RESET = gql`
  mutation RequestPasswordReset($email: String!) {
    requestPasswordReset(email: $email) {
      success
      message
    }
  }
`;

/**
 * Mutation to reset password using reset token.
 *
 * Changes password using token from password reset email.
 * Token is valid for 1 hour and single-use only.
 *
 * @example
 * ```typescript
 * const [resetPassword] = useMutation(RESET_PASSWORD);
 * await resetPassword({
 *   variables: { token, newPassword }
 * });
 * ```
 */
export const RESET_PASSWORD = gql`
  mutation ResetPassword($token: String!, $newPassword: String!) {
    resetPassword(token: $token, newPassword: $newPassword) {
      success
      message
    }
  }
`;
