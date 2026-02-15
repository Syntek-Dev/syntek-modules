/**
 * navigation/index.ts
 *
 * Exports all navigation components, types, and utilities for mobile authentication.
 */

export { AuthNavigator } from './AuthNavigator';
export type { AuthStackParamList } from './AuthNavigator';

export { AccountNavigator } from './AccountNavigator';
export type { AccountStackParamList } from './AccountNavigator';

export { withAuthGuard, useAuthGuard } from './withAuthGuard';
export type { WithAuthGuardProps } from './withAuthGuard';

export {
  deepLinkingConfig,
  OAUTH_PROVIDERS,
  getOAuthRedirectUri,
  parseOAuthCallback,
  validateOAuthState,
} from './deepLinking';
