/**
 * Type definitions for web authentication UI.
 *
 * Re-exports all shared types and adds web-specific type extensions.
 */

// Re-export all shared types
export * from '@syntek/shared-auth/types';

/**
 * Next.js-specific navigation options
 */
export interface WebNavigationOptions {
  /** Next.js router push with shallow routing */
  shallow?: boolean;
  /** Preserve scroll position */
  scroll?: boolean;
  /** Replace instead of push */
  replace?: boolean;
}

/**
 * Web-specific auth callback
 */
export interface WebAuthCallbackOptions {
  /** Redirect URL after authentication */
  redirectUrl?: string;
  /** Next.js navigation options */
  navigationOptions?: WebNavigationOptions;
}

/**
 * CAPTCHA provider types
 */
export type CaptchaProvider = 'recaptcha-v2' | 'recaptcha-v3' | 'hcaptcha';

/**
 * CAPTCHA configuration
 */
export interface CaptchaConfig {
  /** CAPTCHA provider */
  provider: CaptchaProvider;
  /** Site key */
  siteKey: string;
  /** Theme for CAPTCHA widget */
  theme?: 'light' | 'dark';
  /** Language code */
  language?: string;
}
