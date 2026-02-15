/**
 * GraphQL mutations for Multi-Factor Authentication (MFA) operations.
 *
 * Mutations for TOTP setup/verification and backup code management.
 */

import { gql } from '@apollo/client';

/**
 * Mutation to set up TOTP (Time-based One-Time Password).
 *
 * Initialises TOTP for the user account.
 * Returns QR code and secret for authenticator app setup.
 *
 * @example
 * ```typescript
 * const [setupTOTP] = useMutation(SETUP_TOTP);
 * const { data } = await setupTOTP();
 * const { qrCode, secret } = data.setupTOTP;
 * ```
 */
export const SETUP_TOTP = gql`
  mutation SetupTOTP {
    setupTOTP {
      success
      message
      qrCode
      secret
      backupCodes
    }
  }
`;

/**
 * Mutation to verify TOTP code.
 *
 * Confirms TOTP setup by verifying code from authenticator app.
 * Activates TOTP for the account after successful verification.
 *
 * @example
 * ```typescript
 * const [verifyTOTP] = useMutation(VERIFY_TOTP);
 * const { data } = await verifyTOTP({
 *   variables: { code: '123456' }
 * });
 * ```
 */
export const VERIFY_TOTP = gql`
  mutation VerifyTOTP($code: String!) {
    verifyTOTP(code: $code) {
      success
      message
      backupCodes
    }
  }
`;

/**
 * Mutation to disable TOTP.
 *
 * Removes TOTP requirement from the account.
 * Requires password confirmation for security.
 *
 * @example
 * ```typescript
 * const [disableTOTP] = useMutation(DISABLE_TOTP);
 * await disableTOTP({ variables: { password } });
 * ```
 */
export const DISABLE_TOTP = gql`
  mutation DisableTOTP($password: String!) {
    disableTOTP(password: $password) {
      success
      message
    }
  }
`;

/**
 * Mutation to regenerate backup codes.
 *
 * Invalidates old backup codes and generates new ones.
 * Requires password confirmation for security.
 *
 * @example
 * ```typescript
 * const [regenerateCodes] = useMutation(REGENERATE_BACKUP_CODES);
 * const { data } = await regenerateCodes({
 *   variables: { password }
 * });
 * const newCodes = data.regenerateBackupCodes.codes;
 * ```
 */
export const REGENERATE_BACKUP_CODES = gql`
  mutation RegenerateBackupCodes($password: String!) {
    regenerateBackupCodes(password: $password) {
      success
      message
      codes
      generatedAt
    }
  }
`;

/**
 * Mutation to use a backup code for authentication.
 *
 * Authenticates user using a single-use backup code.
 * Code is invalidated after successful use.
 *
 * @example
 * ```typescript
 * const [useBackupCode] = useMutation(USE_BACKUP_CODE);
 * const { data } = await useBackupCode({
 *   variables: { code: 'ABCD-1234-EFGH-5678', mfaToken }
 * });
 * ```
 */
export const USE_BACKUP_CODE = gql`
  mutation UseBackupCode($code: String!, $mfaToken: String!) {
    useBackupCode(code: $code, mfaToken: $mfaToken) {
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
 * Mutation to regenerate recovery keys.
 *
 * Invalidates old recovery keys and generates new ones.
 * Recovery keys are used for account recovery if all MFA methods are lost.
 *
 * Requires password confirmation for security.
 *
 * @example
 * ```typescript
 * const [regenerateKeys] = useMutation(REGENERATE_RECOVERY_KEYS);
 * const { data } = await regenerateKeys({
 *   variables: { password }
 * });
 * const newKeys = data.regenerateRecoveryKeys.keys;
 * ```
 */
export const REGENERATE_RECOVERY_KEYS = gql`
  mutation RegenerateRecoveryKeys($password: String!) {
    regenerateRecoveryKeys(password: $password) {
      success
      message
      keys
      generatedAt
    }
  }
`;
