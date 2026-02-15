/**
 * Social Login Buttons Component
 *
 * Displays OAuth provider login buttons (Google, GitHub, Microsoft, Apple, etc.).
 * Initiates OAuth flow by redirecting to backend OAuth endpoints.
 */

'use client';

import { Button } from '@syntek/shared/design-system/components';
import type { SocialProvider } from '@syntek/shared-auth/types';

/**
 * Social login buttons props
 */
export interface SocialLoginButtonsProps {
  /** List of enabled providers */
  providers: SocialProvider[];
  /** Callback URL after OAuth success */
  callbackUrl?: string;
  /** Show buttons as compact list */
  compact?: boolean;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * Provider display configuration
 */
const PROVIDER_CONFIG: Record<
  SocialProvider,
  {
    label: string;
    icon: string;
    color: string;
  }
> = {
  google: {
    label: 'Google',
    icon: '🔵',
    color: 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50',
  },
  github: {
    label: 'GitHub',
    icon: '⚫',
    color: 'bg-gray-900 text-white hover:bg-gray-800',
  },
  microsoft: {
    label: 'Microsoft',
    icon: '🟦',
    color: 'bg-blue-600 text-white hover:bg-blue-700',
  },
  apple: {
    label: 'Apple',
    icon: '⚫',
    color: 'bg-black text-white hover:bg-gray-900',
  },
  facebook: {
    label: 'Facebook',
    icon: '🔵',
    color: 'bg-blue-600 text-white hover:bg-blue-700',
  },
  linkedin: {
    label: 'LinkedIn',
    icon: '🔵',
    color: 'bg-blue-700 text-white hover:bg-blue-800',
  },
  x: {
    label: 'X',
    icon: '⚫',
    color: 'bg-black text-white hover:bg-gray-900',
  },
};

/**
 * Renders social login provider buttons
 *
 * Initiates OAuth 2.0 flow by redirecting to backend OAuth endpoints:
 * - GET /auth/oauth/{provider} - Redirects to provider login
 * - Provider redirects back to /auth/callback/{provider}
 * - Backend handles token exchange and creates session
 * - Frontend redirects to callbackUrl on success
 *
 * @param providers - List of enabled OAuth providers
 * @param callbackUrl - URL to redirect after successful login
 * @param compact - Show buttons in compact mode
 * @param disabled - Disable all buttons
 * @returns Social login buttons component
 */
export function SocialLoginButtons({
  providers,
  callbackUrl = '/',
  compact = false,
  disabled = false,
}: SocialLoginButtonsProps): JSX.Element {
  /**
   * Initiates OAuth flow by redirecting to backend
   */
  const handleProviderClick = (provider: SocialProvider): void => {
    const params = new URLSearchParams({
      callback_url: callbackUrl,
    });

    window.location.href = `/auth/oauth/${provider}?${params.toString()}`;
  };

  return (
    <div className={compact ? 'flex gap-2' : 'space-y-3'}>
      {providers.map((provider) => {
        const config = PROVIDER_CONFIG[provider];

        return (
          <Button
            key={provider}
            type="button"
            variant="outline"
            fullWidth={!compact}
            onClick={() => handleProviderClick(provider)}
            disabled={disabled}
            className={config.color}
          >
            <span className="mr-2">{config.icon}</span>
            Continue with {config.label}
          </Button>
        );
      })}
    </div>
  );
}
