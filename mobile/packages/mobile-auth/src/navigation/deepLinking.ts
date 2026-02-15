/**
 * deepLinking.ts
 *
 * Deep linking configuration for React Native authentication flows.
 * Handles OAuth callback URLs and email verification links.
 * Supports custom URL schemes (yourapp://) and universal links (https://).
 */

import type { LinkingOptions } from '@react-navigation/native';
import type { AuthStackParamList } from './AuthNavigator';
import type { AccountStackParamList } from './AccountNavigator';

/**
 * Combined navigation parameter list for deep linking.
 */
type RootStackParamList = AuthStackParamList & AccountStackParamList & {
  OAuthCallback: {
    provider: string;
    code?: string;
    state?: string;
    error?: string;
  };
  EmailVerification: {
    token: string;
  };
  PasswordReset: {
    token: string;
  };
};

/**
 * Deep linking configuration for React Navigation.
 *
 * Defines URL patterns for authentication flows including OAuth callbacks,
 * email verification, and password reset. Supports both custom URL schemes
 * and universal links for seamless authentication experiences.
 *
 * Custom URL scheme: yourapp://auth/callback/google
 * Universal link: https://yourapp.com/auth/callback/google
 */
export const deepLinkingConfig: LinkingOptions<RootStackParamList> = {
  prefixes: [
    'yourapp://', // Custom URL scheme
    'https://yourapp.com', // Universal link (replace with actual domain)
    'https://*.yourapp.com', // Wildcard for subdomains
  ],
  config: {
    screens: {
      // OAuth callback routes
      OAuthCallback: {
        path: 'auth/callback/:provider',
        parse: {
          provider: (provider: string) => provider.toLowerCase(),
          code: (code: string) => code,
          state: (state: string) => state,
          error: (error: string) => error,
        },
      },

      // Email verification route
      EmailVerification: {
        path: 'auth/verify-email/:token',
        parse: {
          token: (token: string) => token,
        },
      },

      // Password reset route
      PasswordReset: {
        path: 'auth/reset-password/:token',
        parse: {
          token: (token: string) => token,
        },
      },

      // Phone verification route
      PhoneVerification: {
        path: 'auth/verify-phone',
        parse: {
          phoneNumber: (phoneNumber: string) => decodeURIComponent(phoneNumber),
          userId: (userId: string) => userId,
        },
      },

      // Standard auth routes
      Login: 'auth/login',
      Register: 'auth/register',
      TOTPSetup: 'auth/totp-setup',
      RecoveryKey: 'auth/recovery-key',

      // Account management routes
      ProfileUpdate: 'account/profile',
      SessionSecurity: 'account/sessions',
      PasskeyManagement: 'account/passkeys',
      DataExport: 'account/export-data',
      AccountDeletion: 'account/delete',
      PrivacySettings: 'account/privacy',
    },
  },
};

/**
 * OAuth provider configuration for deep linking.
 *
 * Maps OAuth providers to their callback URL patterns and configuration.
 * Used to construct redirect URIs for OAuth flows.
 */
export const OAUTH_PROVIDERS = {
  google: {
    callbackPath: 'auth/callback/google',
    scopes: ['openid', 'profile', 'email'],
  },
  apple: {
    callbackPath: 'auth/callback/apple',
    scopes: ['name', 'email'],
  },
  microsoft: {
    callbackPath: 'auth/callback/microsoft',
    scopes: ['openid', 'profile', 'email'],
  },
  github: {
    callbackPath: 'auth/callback/github',
    scopes: ['user:email'],
  },
} as const;

/**
 * Constructs OAuth redirect URI for the current app.
 *
 * Generates the redirect URI that OAuth providers should redirect to
 * after authentication. Uses custom URL scheme for native apps.
 *
 * @param provider - OAuth provider identifier (google, apple, etc.)
 * @returns Complete redirect URI for OAuth callback
 *
 * @example
 * ```ts
 * const redirectUri = getOAuthRedirectUri('google');
 * // Returns: 'yourapp://auth/callback/google'
 * ```
 */
export function getOAuthRedirectUri(
  provider: keyof typeof OAUTH_PROVIDERS
): string {
  const callbackPath = OAUTH_PROVIDERS[provider].callbackPath;
  return `yourapp://${callbackPath}`;
}

/**
 * Extracts OAuth state from callback URL.
 *
 * Parses the OAuth callback URL to extract state, code, and error parameters.
 * Used to validate OAuth responses and complete the authentication flow.
 *
 * @param url - Complete callback URL from OAuth provider
 * @returns Parsed OAuth callback parameters
 *
 * @example
 * ```ts
 * const params = parseOAuthCallback('yourapp://auth/callback/google?code=abc&state=xyz');
 * // Returns: { provider: 'google', code: 'abc', state: 'xyz' }
 * ```
 */
export function parseOAuthCallback(url: string): {
  provider: string;
  code?: string;
  state?: string;
  error?: string;
  errorDescription?: string;
} | null {
  try {
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split('/');
    const provider = pathParts[pathParts.length - 1];

    const params = new URLSearchParams(urlObj.search);

    return {
      provider,
      code: params.get('code') || undefined,
      state: params.get('state') || undefined,
      error: params.get('error') || undefined,
      errorDescription: params.get('error_description') || undefined,
    };
  } catch (error) {
    console.error('Failed to parse OAuth callback URL:', error);
    return null;
  }
}

/**
 * Validates OAuth state parameter to prevent CSRF attacks.
 *
 * Compares the state parameter from the OAuth callback with the stored
 * state value to ensure the callback originated from this app.
 *
 * @param receivedState - State parameter from OAuth callback
 * @param expectedState - Expected state value stored before OAuth redirect
 * @returns True if state is valid, false otherwise
 */
export function validateOAuthState(
  receivedState: string,
  expectedState: string
): boolean {
  return receivedState === expectedState;
}
