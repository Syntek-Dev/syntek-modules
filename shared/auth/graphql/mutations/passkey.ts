/**
 * GraphQL mutations for WebAuthn/Passkey operations.
 *
 * Mutations for passkey registration, authentication, and management.
 */

import { gql } from '@apollo/client';
import { PASSKEY_FULL_FIELDS } from '../fragments';

/**
 * Mutation to register a new passkey.
 *
 * Registers a WebAuthn credential for the user account.
 * Requires attestation response from navigator.credentials.create().
 *
 * @example
 * ```typescript
 * const [registerPasskey] = useMutation(REGISTER_PASSKEY);
 * const { data } = await registerPasskey({
 *   variables: {
 *     name: 'My MacBook Touch ID',
 *     attestationResponse: credential.response,
 *   }
 * });
 * ```
 */
export const REGISTER_PASSKEY = gql`
  mutation RegisterPasskey(
    $name: String!
    $attestationResponse: AttestationResponseInput!
  ) {
    registerPasskey(name: $name, attestationResponse: $attestationResponse) {
      success
      message
      passkey {
        ...PasskeyFullFields
      }
    }
  }
  ${PASSKEY_FULL_FIELDS}
`;

/**
 * Mutation to authenticate with a passkey.
 *
 * Authenticates user using WebAuthn credential.
 * Requires assertion response from navigator.credentials.get().
 *
 * @example
 * ```typescript
 * const [authenticatePasskey] = useMutation(AUTHENTICATE_PASSKEY);
 * const { data } = await authenticatePasskey({
 *   variables: {
 *     email,
 *     assertionResponse: credential.response,
 *   }
 * });
 * ```
 */
export const AUTHENTICATE_PASSKEY = gql`
  mutation AuthenticatePasskey(
    $email: String!
    $assertionResponse: AssertionResponseInput!
  ) {
    authenticatePasskey(email: $email, assertionResponse: $assertionResponse) {
      success
      message
      token
      user {
        id
        email
      }
    }
  }
`;

/**
 * Mutation to delete a passkey.
 *
 * Removes a WebAuthn credential from the user account.
 * Requires password confirmation if this is the last authentication method.
 *
 * @example
 * ```typescript
 * const [deletePasskey] = useMutation(DELETE_PASSKEY);
 * await deletePasskey({
 *   variables: { passkeyId, password }
 * });
 * ```
 */
export const DELETE_PASSKEY = gql`
  mutation DeletePasskey($passkeyId: ID!, $password: String) {
    deletePasskey(passkeyId: $passkeyId, password: $password) {
      success
      message
    }
  }
`;

/**
 * Mutation to update passkey name.
 *
 * Renames a WebAuthn credential for easier identification.
 *
 * @example
 * ```typescript
 * const [updatePasskey] = useMutation(UPDATE_PASSKEY_NAME);
 * await updatePasskey({
 *   variables: { passkeyId, name: 'iPhone 14 Face ID' }
 * });
 * ```
 */
export const UPDATE_PASSKEY_NAME = gql`
  mutation UpdatePasskeyName($passkeyId: ID!, $name: String!) {
    updatePasskeyName(passkeyId: $passkeyId, name: $name) {
      success
      message
      passkey {
        ...PasskeyFullFields
      }
    }
  }
  ${PASSKEY_FULL_FIELDS}
`;
