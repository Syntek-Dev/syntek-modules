/**
 * Multi-Factor Authentication constants
 *
 * ⚠️ DEPRECATION WARNING ⚠️
 *
 * Some MFA constants are FALLBACK VALUES ONLY.
 * Real configuration values should be fetched from Django backend via GraphQL
 * using the `useAuthConfig()` hook.
 *
 * @see {@link useAuthConfig} for fetching live configuration
 */

/**
 * TOTP time window in seconds (30 seconds)
 *
 * Standard TOTP window, safe to use as constant.
 */
export const TOTP_WINDOW = 30;

/**
 * TOTP validity window (number of time steps before/after current)
 *
 * @deprecated Use `useAuthConfig().config.totpWindow` instead
 */
export const TOTP_VALIDITY_WINDOW = 1;

/**
 * Number of backup codes to generate
 *
 * @deprecated Use `useAuthConfig().config.backupCodeCount` instead
 */
export const BACKUP_CODE_COUNT = 10;

/**
 * Number of recovery keys to generate
 *
 * Note: Backend defaults to 1 recovery key per user
 *
 * @deprecated Use `useAuthConfig().config.recoveryKeyCount` instead
 */
export const RECOVERY_KEY_COUNT = 1;

/**
 * TOTP issuer name (displayed in authenticator app)
 *
 * @deprecated Use `useAuthConfig().config.totpIssuerName` instead
 */
export const TOTP_ISSUER = 'Syntek Platform';

/**
 * TOTP algorithm
 *
 * Standard TOTP algorithm (SHA1), safe to use as constant.
 */
export const TOTP_ALGORITHM = 'SHA1';

/**
 * TOTP digits
 *
 * Standard 6-digit TOTP format, safe to use as constant.
 */
export const TOTP_DIGITS = 6;
