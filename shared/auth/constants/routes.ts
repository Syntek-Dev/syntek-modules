/**
 * Route constants
 *
 * API endpoints and OAuth callback paths.
 */

/**
 * GraphQL API endpoint
 * Should be configured per environment
 */
export const GRAPHQL_ENDPOINT = process.env.NEXT_PUBLIC_GRAPHQL_ENDPOINT || '/graphql';

/**
 * OAuth callback base path
 */
export const OAUTH_CALLBACK_BASE = '/auth/callback';

/**
 * OAuth callback paths by provider
 */
export const OAUTH_CALLBACK_PATHS = {
  google: `${OAUTH_CALLBACK_BASE}/google`,
  github: `${OAUTH_CALLBACK_BASE}/github`,
  microsoft: `${OAUTH_CALLBACK_BASE}/microsoft`,
  apple: `${OAUTH_CALLBACK_BASE}/apple`,
} as const;

/**
 * Authentication routes
 */
export const AUTH_ROUTES = {
  login: '/auth/login',
  register: '/auth/register',
  verifyEmail: '/auth/verify-email',
  verifyPhone: '/auth/verify-phone',
  setupMFA: '/auth/setup-mfa',
  recovery: '/auth/recovery',
  setupPasskey: '/auth/setup-passkey',
  managePasskeys: '/auth/manage-passkeys',
  sessions: '/auth/sessions',
  security: '/auth/security',
} as const;

/**
 * Account management routes
 */
export const ACCOUNT_ROUTES = {
  profile: '/account/profile',
  exportData: '/account/export-data',
  deleteAccount: '/account/delete',
  privacy: '/account/privacy',
  socialAccounts: '/profile/social-accounts',
} as const;
