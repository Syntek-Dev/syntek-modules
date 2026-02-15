/**
 * Passkey/WebAuthn constants
 *
 * ⚠️ DEPRECATION WARNING ⚠️
 *
 * Some WebAuthn constants are FALLBACK VALUES ONLY.
 * Real configuration values should be fetched from Django backend via GraphQL
 * using the `useAuthConfig()` hook.
 *
 * Most WebAuthn constants are safe to use as they define standard WebAuthn behavior.
 *
 * @see {@link useAuthConfig} for fetching live configuration
 */

/**
 * WebAuthn timeout in milliseconds (60 seconds)
 *
 * @deprecated Use `useAuthConfig().config.webauthnTimeout` instead
 */
export const WEBAUTHN_TIMEOUT = 60000;

/**
 * Supported attestation formats
 *
 * @deprecated Use `useAuthConfig().config.attestationFormats` instead
 */
export const ATTESTATION_FORMATS = [
  'packed',
  'fido-u2f',
  'android-key',
  'android-safetynet',
  'apple',
  'tpm',
  'none',
] as const;

/**
 * Relying Party ID (domain)
 *
 * Should be configured per environment via environment variables.
 * Safe to use as constant since it's environment-specific.
 */
export const DEFAULT_RP_ID = process.env.NEXT_PUBLIC_WEBAUTHN_RP_ID || 'localhost';

/**
 * Relying Party name (displayed to user)
 *
 * Safe to use as constant since it's a display name.
 */
export const RP_NAME = 'Syntek Authentication';

/**
 * User verification requirement
 *
 * - required: Always require user verification (PIN, biometric)
 * - preferred: Prefer user verification but allow fallback
 * - discouraged: Don't require user verification
 *
 * Safe to use as constant since it defines WebAuthn behavior.
 */
export const USER_VERIFICATION = 'preferred' as const;

/**
 * Authenticator attachment
 *
 * - platform: Device-bound authenticator (e.g., Touch ID, Face ID)
 * - cross-platform: Removable authenticator (e.g., security key)
 * - undefined: Allow both
 *
 * Safe to use as constant since it defines WebAuthn behavior.
 */
export const AUTHENTICATOR_ATTACHMENT = undefined;

/**
 * Attestation conveyance
 *
 * - none: No attestation (fastest, most privacy-preserving)
 * - indirect: Attestation with anonymization
 * - direct: Full attestation (required for NIST AAL3)
 *
 * Safe to use as constant since it defines WebAuthn security level.
 */
export const ATTESTATION_CONVEYANCE = 'direct' as const;

/**
 * Maximum number of passkeys per user
 *
 * Safe to use as constant for client-side validation.
 */
export const MAX_PASSKEYS_PER_USER = 10;
