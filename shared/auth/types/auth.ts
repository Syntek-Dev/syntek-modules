/**
 * Authentication type definitions
 *
 * Types for login, registration, and authentication tokens.
 */

import type { User } from './user';

export interface LoginInput {
  email: string;
  password: string;
  rememberMe?: boolean;
  totpCode?: string;
  backupCode?: string;
  captchaToken?: string;
}

export interface RegisterInput {
  email: string;
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  phone?: string;
  agreedToTerms: boolean;
  agreedToPrivacy: boolean;
  agreedToMarketing?: boolean;
  captchaToken?: string;
  language?: string;
  timezone?: string;
}

export interface AuthToken {
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
  tokenType: 'Bearer';
}

export interface AuthResponse {
  success: boolean;
  user?: User;
  token?: AuthToken;
  requiresMFA?: boolean;
  requiresEmailVerification?: boolean;
  requiresPhoneVerification?: boolean;
  error?: AuthError;
}

export interface AuthError {
  code: string;
  message: string;
  field?: string;
}

export type AuthErrorCode =
  | 'invalid_credentials'
  | 'account_suspended'
  | 'account_not_verified'
  | 'mfa_required'
  | 'invalid_mfa_code'
  | 'rate_limit_exceeded'
  | 'captcha_required'
  | 'captcha_invalid'
  | 'email_already_exists'
  | 'username_already_exists'
  | 'weak_password'
  | 'compromised_password'
  | 'session_expired';
