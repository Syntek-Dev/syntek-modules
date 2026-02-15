/**
 * Social authentication constants
 *
 * ⚠️ PARTIAL DEPRECATION WARNING ⚠️
 *
 * OAuth providers list should be fetched from Django backend via GraphQL
 * using `useAuthConfig().config.enabledOauthProviders`.
 *
 * OAuth URLs and scopes are safe to use as constants since they are
 * defined by OAuth provider specifications.
 *
 * @see {@link useAuthConfig} for fetching enabled OAuth providers
 */

import type { SocialProvider } from '../types/social';

/**
 * Supported OAuth providers
 *
 * @deprecated Use `useAuthConfig().config.enabledOauthProviders` instead
 */
export const OAUTH_PROVIDERS: SocialProvider[] = ['google', 'github', 'microsoft', 'apple'];

/**
 * OAuth scopes by provider
 *
 * Safe to use as constant since these are defined by OAuth provider specifications.
 */
export const PROVIDER_SCOPES: Record<SocialProvider, string[]> = {
  google: ['openid', 'email', 'profile'],
  github: ['user:email'],
  microsoft: ['openid', 'email', 'profile'],
  apple: ['name', 'email'],
};

/**
 * OAuth authorize URLs by provider
 *
 * Safe to use as constant since these are official OAuth provider URLs.
 */
export const PROVIDER_AUTHORIZE_URLS: Record<SocialProvider, string> = {
  google: 'https://accounts.google.com/o/oauth2/v2/auth',
  github: 'https://github.com/login/oauth/authorize',
  microsoft: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
  apple: 'https://appleid.apple.com/auth/authorize',
};

/**
 * OAuth token URLs by provider
 *
 * Safe to use as constant since these are official OAuth provider URLs.
 */
export const PROVIDER_TOKEN_URLS: Record<SocialProvider, string> = {
  google: 'https://oauth2.googleapis.com/token',
  github: 'https://github.com/login/oauth/access_token',
  microsoft: 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
  apple: 'https://appleid.apple.com/auth/token',
};

/**
 * OAuth provider display names
 *
 * Safe to use as constant since these are official provider names.
 */
export const PROVIDER_NAMES: Record<SocialProvider, string> = {
  google: 'Google',
  github: 'GitHub',
  microsoft: 'Microsoft',
  apple: 'Apple',
};
