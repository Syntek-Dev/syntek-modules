/**
 * Social authentication type definitions
 *
 * Types for OAuth providers and social account linking.
 */

export type SocialProvider = 'google' | 'github' | 'microsoft' | 'apple';

export interface SocialAccount {
  id: string;
  provider: SocialProvider;
  providerAccountId: string;
  email: string;
  name: string;
  avatar?: string;
  linkedAt: string;
}

export interface OAuthState {
  state: string;
  redirectUrl: string;
  provider: SocialProvider;
  codeChallenge?: string;
  codeChallengeMethod?: 'S256' | 'plain';
}

export interface LinkSocialAccountInput {
  provider: SocialProvider;
  code: string;
  state: string;
}

export interface UnlinkSocialAccountInput {
  provider: SocialProvider;
}

export interface SocialProvidersConfig {
  provider: SocialProvider;
  enabled: boolean;
  clientId: string;
  scopes: string[];
  authorizeUrl: string;
  tokenUrl: string;
}
