/**
 * Authentication configuration types.
 *
 * These types match the GraphQL AuthConfigType from the backend.
 * Configuration is fetched from Django SYNTEK_AUTH settings via GraphQL.
 */

/**
 * Authentication configuration from backend.
 *
 * Fetched via GraphQL query. All values come from Django SYNTEK_AUTH settings.
 * Use `useAuthConfig()` hook to access these values.
 */
export interface AuthConfig {
  // Password validation
  passwordMinLength: number;
  passwordMaxLength: number;
  specialCharsRequired: boolean;
  uppercaseRequired: boolean;
  lowercaseRequired: boolean;
  numbersRequired: boolean;
  passwordHistoryCount: number;
  commonPasswordCheck: boolean;

  // Login security
  maxLoginAttempts: number;
  lockoutDuration: number; // seconds
  lockoutIncrement: boolean;

  // Session configuration
  sessionTimeout: number; // seconds (without remember me)
  sessionTimeoutRememberMe: number; // seconds (with remember me)
  sessionAbsoluteTimeout: number; // seconds
  allowSimultaneousSessions: boolean;

  // MFA configuration
  totpRequired: boolean;
  totpIssuerName: string;
  totpWindow: number;
  backupCodeCount: number;
  recoveryKeyCount: number;

  // WebAuthn/Passkey
  webauthnTimeout: number; // milliseconds
  attestationFormats: string[];

  // Session security
  fingerprintLevels: string[];
  concurrentSessionLimit: number;

  // Social auth providers (enabled list)
  enabledOauthProviders: string[];

  // Notifications
  notifyFailedLogins: boolean;
  notifyNewDeviceLogin: boolean;
  logLoginAttempts: boolean;

  // Auto-logout
  autoLogoutWarningTime: number; // seconds
  sessionActivityCheckInterval: number; // milliseconds
}

/**
 * Fallback auth configuration.
 *
 * Used when GraphQL query fails or during initial load.
 * These values should match backend defaults.
 */
export const AUTH_CONFIG_FALLBACK: AuthConfig = {
  // Password validation
  passwordMinLength: 12,
  passwordMaxLength: 128,
  specialCharsRequired: true,
  uppercaseRequired: true,
  lowercaseRequired: true,
  numbersRequired: true,
  passwordHistoryCount: 5,
  commonPasswordCheck: true,

  // Login security
  maxLoginAttempts: 5,
  lockoutDuration: 300,
  lockoutIncrement: true,

  // Session configuration
  sessionTimeout: 1800,
  sessionTimeoutRememberMe: 2592000,
  sessionAbsoluteTimeout: 43200,
  allowSimultaneousSessions: false,

  // MFA configuration
  totpRequired: false,
  totpIssuerName: 'Syntek Platform',
  totpWindow: 1,
  backupCodeCount: 10,
  recoveryKeyCount: 1,

  // WebAuthn/Passkey
  webauthnTimeout: 60000,
  attestationFormats: ['packed', 'fido-u2f', 'android-key', 'android-safetynet', 'tpm', 'apple', 'none'],

  // Session security
  fingerprintLevels: ['minimal', 'balanced', 'aggressive'],
  concurrentSessionLimit: 3,

  // Social auth providers
  enabledOauthProviders: ['google', 'github', 'microsoft'],

  // Notifications
  notifyFailedLogins: true,
  notifyNewDeviceLogin: true,
  logLoginAttempts: true,

  // Auto-logout
  autoLogoutWarningTime: 120,
  sessionActivityCheckInterval: 60000,
};
