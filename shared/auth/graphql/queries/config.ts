/**
 * GraphQL queries for authentication configuration.
 *
 * Fetches configuration from Django backend SYNTEK_AUTH settings.
 */

import { gql } from '@apollo/client';

/**
 * Query to fetch authentication configuration.
 *
 * This query fetches all public-safe configuration values from Django
 * SYNTEK_AUTH settings. It can be called without authentication.
 *
 * Cache this query result for 5-10 minutes to reduce API calls.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_AUTH_CONFIG);
 * const sessionTimeout = data.authConfig.sessionTimeout;
 * ```
 */
export const GET_AUTH_CONFIG = gql`
  query GetAuthConfig {
    authConfig {
      # Password validation
      passwordMinLength
      passwordMaxLength
      specialCharsRequired
      uppercaseRequired
      lowercaseRequired
      numbersRequired
      passwordHistoryCount
      commonPasswordCheck

      # Login security
      maxLoginAttempts
      lockoutDuration
      lockoutIncrement

      # Session configuration
      sessionTimeout
      sessionTimeoutRememberMe
      sessionAbsoluteTimeout
      allowSimultaneousSessions

      # MFA configuration
      totpRequired
      totpIssuerName
      totpWindow
      backupCodeCount
      recoveryKeyCount

      # WebAuthn/Passkey
      webauthnTimeout
      attestationFormats

      # Session security
      fingerprintLevels
      concurrentSessionLimit

      # Social auth
      enabledOauthProviders

      # Notifications
      notifyFailedLogins
      notifyNewDeviceLogin
      logLoginAttempts

      # Auto-logout
      autoLogoutWarningTime
      sessionActivityCheckInterval
    }
  }
`;
