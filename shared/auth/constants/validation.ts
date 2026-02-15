/**
 * Validation constants
 *
 * ⚠️ DEPRECATION WARNING ⚠️
 *
 * Password validation constants are FALLBACK VALUES ONLY.
 * Real password rules should be fetched from Django backend via GraphQL
 * using the `useAuthConfig()` hook.
 *
 * Other validation patterns (email, phone, etc.) are safe to use as constants
 * since they follow standard formats (RFC 5322, E.164, etc.).
 *
 * @see {@link useAuthConfig} for fetching live password validation rules
 */

/**
 * Username validation
 */
export const USERNAME_MIN_LENGTH = 3;
export const USERNAME_MAX_LENGTH = 30;
export const USERNAME_PATTERN = /^[a-zA-Z0-9_]+$/;

/**
 * Password validation (basic fallback - backend provides comprehensive rules)
 *
 * @deprecated Use `useAuthConfig().config.passwordMinLength` instead
 */
export const PASSWORD_MIN_LENGTH = 12;

/**
 * Password maximum length (standard maximum)
 *
 * @deprecated Use `useAuthConfig().config.passwordMaxLength` instead
 */
export const PASSWORD_MAX_LENGTH = 128;

/**
 * Email validation (RFC 5322 compliant)
 *
 * This pattern is safe to use as a constant since it follows RFC 5322 standard.
 */
export const EMAIL_PATTERN = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

/**
 * Phone validation (E.164 format via libphonenumber-js)
 *
 * Length validation only - libphonenumber-js handles format validation.
 * These are safe to use as constants since they follow E.164 standard.
 */
export const PHONE_MIN_LENGTH = 8;
export const PHONE_MAX_LENGTH = 15;

/**
 * Name validation
 *
 * These are UI validation rules and safe to use as constants.
 */
export const NAME_MIN_LENGTH = 1;
export const NAME_MAX_LENGTH = 50;
export const NAME_PATTERN = /^[a-zA-Z\s'-]+$/;

/**
 * Verification code validation
 *
 * Standard 6-digit format, safe to use as constant.
 */
export const VERIFICATION_CODE_LENGTH = 6;
export const VERIFICATION_CODE_PATTERN = /^\d{6}$/;

/**
 * TOTP code validation
 *
 * Standard 6-digit TOTP format, safe to use as constant.
 */
export const TOTP_CODE_LENGTH = 6;
export const TOTP_CODE_PATTERN = /^\d{6}$/;

/**
 * Backup code validation
 *
 * Standard 10-character alphanumeric format.
 *
 * @deprecated Use `useAuthConfig().config.backupCodeCount` for count
 */
export const BACKUP_CODE_LENGTH = 10;
export const BACKUP_CODE_PATTERN = /^[A-Z0-9]{10}$/;

/**
 * Recovery key validation
 *
 * Standard 32-character alphanumeric format.
 */
export const RECOVERY_KEY_LENGTH = 32;
export const RECOVERY_KEY_PATTERN = /^[A-Z0-9]{32}$/;
