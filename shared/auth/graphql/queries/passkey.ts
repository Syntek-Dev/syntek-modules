/**
 * GraphQL queries for WebAuthn/Passkey operations.
 *
 * Queries for passkey management and authentication challenges.
 */

import { gql } from '@apollo/client';
import { PASSKEY_FULL_FIELDS } from '../fragments';

/**
 * Query to list all passkeys for the current user.
 *
 * Returns all registered WebAuthn credentials.
 * Cached for 1 minute to reduce API calls.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(LIST_PASSKEYS);
 * const passkeys = data.listPasskeys;
 * ```
 */
export const LIST_PASSKEYS = gql`
  query ListPasskeys {
    listPasskeys {
      ...PasskeyFullFields
    }
  }
  ${PASSKEY_FULL_FIELDS}
`;

/**
 * Query to get a WebAuthn authentication challenge.
 *
 * Returns a challenge object required for passkey authentication.
 * Challenge is valid for 60 seconds (server-side enforced).
 *
 * @example
 * ```typescript
 * const { data } = await client.query({
 *   query: PASSKEY_CHALLENGE,
 *   variables: { email }
 * });
 * const challenge = data.passkeyChallenge;
 * ```
 */
export const PASSKEY_CHALLENGE = gql`
  query PasskeyChallenge($email: String!) {
    passkeyChallenge(email: $email) {
      challenge
      timeout
      rpId
      allowedCredentials {
        id
        type
        transports
      }
      userVerification
    }
  }
`;

/**
 * Query to get a WebAuthn registration challenge.
 *
 * Returns a challenge object required for passkey registration.
 * Challenge is valid for 60 seconds (server-side enforced).
 *
 * Requires authentication to prevent registration for other users.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(PASSKEY_REGISTRATION_CHALLENGE);
 * const options = data.passkeyRegistrationChallenge;
 * ```
 */
export const PASSKEY_REGISTRATION_CHALLENGE = gql`
  query PasskeyRegistrationChallenge {
    passkeyRegistrationChallenge {
      challenge
      timeout
      rp {
        id
        name
      }
      user {
        id
        name
        displayName
      }
      pubKeyCredParams {
        type
        alg
      }
      authenticatorSelection {
        authenticatorAttachment
        residentKey
        requireResidentKey
        userVerification
      }
      attestation
    }
  }
`;
