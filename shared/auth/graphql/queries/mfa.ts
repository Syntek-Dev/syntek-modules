/**
 * GraphQL queries for Multi-Factor Authentication (MFA) operations.
 *
 * Queries for TOTP, backup codes, and recovery keys.
 */

import { gql } from '@apollo/client';

/**
 * Query to get current MFA status for the user.
 *
 * Returns whether TOTP is enabled, number of backup codes remaining, etc.
 * Always fetches fresh data (not cached) for security.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_MFA_STATUS);
 * const { totpEnabled, backupCodesRemaining } = data.getMFAStatus;
 * ```
 */
export const GET_MFA_STATUS = gql`
  query GetMFAStatus {
    getMFAStatus {
      totpEnabled
      totpQrCode
      totpSecret
      backupCodesRemaining
      recoveryKeysRemaining
      lastTotpVerified
    }
  }
`;

/**
 * Query to get backup codes for MFA recovery.
 *
 * Returns list of unused backup codes.
 * Only returns codes once (after generation or regeneration).
 *
 * Security: This query requires recent authentication or MFA verification.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_BACKUP_CODES);
 * const codes = data.getBackupCodes.codes;
 * ```
 */
export const GET_BACKUP_CODES = gql`
  query GetBackupCodes {
    getBackupCodes {
      codes
      generatedAt
    }
  }
`;

/**
 * Query to get recovery keys for account recovery.
 *
 * Returns list of unused recovery keys.
 * Only returns keys once (after generation or regeneration).
 *
 * Security: This query requires recent authentication or MFA verification.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_RECOVERY_KEYS);
 * const keys = data.getRecoveryKeys.keys;
 * ```
 */
export const GET_RECOVERY_KEYS = gql`
  query GetRecoveryKeys {
    getRecoveryKeys {
      keys
      generatedAt
    }
  }
`;
