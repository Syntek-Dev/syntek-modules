/**
 * GraphQL fragments for Passkey/WebAuthn fields.
 *
 * Reusable fragments for passkey credential data.
 */

import { gql } from '@apollo/client';

/**
 * Core passkey fields fragment.
 *
 * Essential passkey information for credential list display.
 */
export const PASSKEY_CORE_FIELDS = gql`
  fragment PasskeyCoreFields on Passkey {
    id
    credentialId
    name
    createdAt
    lastUsed
    aaguid
  }
`;

/**
 * Passkey device fields fragment.
 *
 * Device and authenticator information for passkey management views.
 */
export const PASSKEY_DEVICE_FIELDS = gql`
  fragment PasskeyDeviceFields on Passkey {
    ...PasskeyCoreFields
    authenticatorType
    transports
    backupEligible
    backupState
    deviceType
  }
  ${PASSKEY_CORE_FIELDS}
`;

/**
 * Full passkey fields fragment.
 *
 * Complete passkey information including device metadata.
 */
export const PASSKEY_FULL_FIELDS = gql`
  fragment PasskeyFullFields on Passkey {
    ...PasskeyCoreFields
    ...PasskeyDeviceFields
  }
  ${PASSKEY_CORE_FIELDS}
  ${PASSKEY_DEVICE_FIELDS}
`;
