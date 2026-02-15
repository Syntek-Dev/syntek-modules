/**
 * Authentication constants
 *
 * ⚠️ DEPRECATION WARNING ⚠️
 *
 * These constants are FALLBACK VALUES ONLY.
 * Real configuration values should be fetched from Django backend via GraphQL
 * using the `useAuthConfig()` hook.
 *
 * These fallbacks are used:
 * - During initial load before GraphQL response
 * - If GraphQL query fails
 * - In non-React contexts (pure utilities)
 *
 * @see {@link useAuthConfig} for fetching live configuration
 * @see {@link AuthConfig} for type definitions
 */

/**
 * Session timeout in seconds (30 minutes)
 *
 * @deprecated Use `useAuthConfig().config.sessionTimeout` instead
 */
export const SESSION_TIMEOUT = 1800;

/**
 * Session timeout with "remember me" in seconds (30 days)
 *
 * @deprecated Use `useAuthConfig().config.sessionTimeoutRememberMe` instead
 */
export const SESSION_TIMEOUT_REMEMBER_ME = 2592000;

/**
 * Maximum login attempts before account lockout
 *
 * @deprecated Use `useAuthConfig().config.maxLoginAttempts` instead
 */
export const MAX_LOGIN_ATTEMPTS = 5;

/**
 * Account lockout duration in seconds (5 minutes)
 *
 * Note: Default changed from 15 to 5 minutes to match backend
 *
 * @deprecated Use `useAuthConfig().config.lockoutDuration` instead
 */
export const LOCKOUT_DURATION = 300;

/**
 * Token refresh interval in seconds (5 minutes before expiry)
 */
export const TOKEN_REFRESH_INTERVAL = 300;

/**
 * Auto-logout warning time in seconds (2 minutes before expiry)
 *
 * @deprecated Use `useAuthConfig().config.autoLogoutWarningTime` instead
 */
export const AUTO_LOGOUT_WARNING_TIME = 120;

/**
 * Session activity check interval in milliseconds (1 minute)
 *
 * @deprecated Use `useAuthConfig().config.sessionActivityCheckInterval` instead
 */
export const SESSION_ACTIVITY_CHECK_INTERVAL = 60000;
