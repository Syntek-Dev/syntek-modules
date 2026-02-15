/**
 * GraphQL fragments for Session fields.
 *
 * Reusable fragments for session data across queries and mutations.
 */

import { gql } from '@apollo/client';

/**
 * Core session fields fragment.
 *
 * Essential session information for session list display.
 */
export const SESSION_CORE_FIELDS = gql`
  fragment SessionCoreFields on Session {
    id
    createdAt
    lastActivity
    expiresAt
    ipAddress
    userAgent
    isCurrent
  }
`;

/**
 * Session device fields fragment.
 *
 * Detailed device and location information for session security views.
 */
export const SESSION_DEVICE_FIELDS = gql`
  fragment SessionDeviceFields on Session {
    ...SessionCoreFields
    deviceType
    deviceName
    browser
    browserVersion
    os
    osVersion
    city
    region
    country
    countryCode
  }
  ${SESSION_CORE_FIELDS}
`;

/**
 * Session security fields fragment.
 *
 * Security-related session information (risk score, fingerprint).
 */
export const SESSION_SECURITY_FIELDS = gql`
  fragment SessionSecurityFields on Session {
    ...SessionCoreFields
    fingerprintHash
    riskScore
    isSuspicious
    mfaVerified
  }
  ${SESSION_CORE_FIELDS}
`;

/**
 * Full session fields fragment.
 *
 * Complete session information including device and security data.
 */
export const SESSION_FULL_FIELDS = gql`
  fragment SessionFullFields on Session {
    ...SessionCoreFields
    ...SessionDeviceFields
    ...SessionSecurityFields
  }
  ${SESSION_CORE_FIELDS}
  ${SESSION_DEVICE_FIELDS}
  ${SESSION_SECURITY_FIELDS}
`;
