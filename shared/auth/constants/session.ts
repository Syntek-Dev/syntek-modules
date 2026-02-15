/**
 * Session constants
 *
 * ⚠️ DEPRECATION WARNING ⚠️
 *
 * Some session constants are FALLBACK VALUES ONLY.
 * Real configuration values should be fetched from Django backend via GraphQL
 * using the `useAuthConfig()` hook.
 *
 * Fingerprint levels and components are safe to use as constants since they
 * define client-side behavior.
 *
 * @see {@link useAuthConfig} for fetching live configuration
 */

import type { FingerprintLevel } from '../types/session';

/**
 * Default device fingerprint level
 *
 * Privacy-first default (no GDPR consent required).
 * Safe to use as constant since it defines client-side behavior.
 */
export const DEFAULT_FINGERPRINT_LEVEL: FingerprintLevel = 'balanced';

/**
 * Fingerprint components by level
 *
 * Safe to use as constant since it defines client-side fingerprinting behavior.
 * Available levels are also exposed via `useAuthConfig().config.fingerprintLevels`.
 */
export const FINGERPRINT_LEVELS: Record<FingerprintLevel, string[]> = {
  minimal: ['userAgent', 'language', 'timezone'],
  balanced: ['userAgent', 'language', 'timezone', 'screenResolution', 'colorDepth'],
  aggressive: [
    'userAgent',
    'language',
    'timezone',
    'screenResolution',
    'colorDepth',
    'webgl',
    'audioContext',
    'fonts',
  ],
};

/**
 * Maximum concurrent sessions per user
 *
 * Note: Backend defaults to 3 concurrent sessions
 *
 * @deprecated Use `useAuthConfig().config.concurrentSessionLimit` instead
 */
export const CONCURRENT_SESSION_LIMIT = 3;

/**
 * Session fingerprint mismatch threshold
 *
 * Number of fingerprint component mismatches before flagging session as suspicious.
 * Safe to use as constant since it defines client-side security behavior.
 */
export const FINGERPRINT_MISMATCH_THRESHOLD = 2;

/**
 * Suspicious activity detection window in hours
 *
 * Safe to use as constant since it defines client-side detection window.
 */
export const SUSPICIOUS_ACTIVITY_WINDOW = 24;

/**
 * Maximum IP address changes per session
 *
 * Safe to use as constant since it defines client-side threshold.
 */
export const MAX_IP_CHANGES_PER_SESSION = 3;
