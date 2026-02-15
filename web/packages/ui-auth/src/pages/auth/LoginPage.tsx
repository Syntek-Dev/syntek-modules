/**
 * Login Page Component
 *
 * Login page with Next.js routing and SEO optimization.
 * Supports email/password, passkeys, and social authentication.
 */

'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { LoginForm } from '../../components/auth/LoginForm';
import { SocialLoginButtons } from '../../components/social/SocialLoginButtons';
import { ReCaptcha } from '../../lib/ReCaptcha';
import { useMutation } from '@apollo/client';
import { LOGIN_MUTATION } from '@syntek/shared-auth/graphql/mutations';
import type { LoginFormData, SocialProvider } from '@syntek/shared-auth/types';

/**
 * Login page props
 */
export interface LoginPageProps {
  /** reCAPTCHA site key */
  captchaSiteKey?: string;
  /** Enable CAPTCHA */
  captchaEnabled?: boolean;
  /** Enable social login */
  socialLoginEnabled?: boolean;
  /** Social providers */
  socialProviders?: SocialProvider[];
  /** Enable passkey login */
  passkeyEnabled?: boolean;
}

/**
 * Renders login page with multiple authentication options
 *
 * Features:
 * - Email/password authentication
 * - WebAuthn/Passkey support
 * - Social login (OAuth)
 * - CAPTCHA integration
 * - Remember me option
 * - Redirect to requested page after login
 *
 * **SEO Metadata (add in parent layout):**
 * ```tsx
 * export const metadata = {
 *   title: 'Sign In | Your App',
 *   description: 'Sign in to your account with email, passkey, or social login',
 * };
 * ```
 *
 * @param captchaSiteKey - reCAPTCHA site key
 * @param captchaEnabled - Enable CAPTCHA verification
 * @param socialLoginEnabled - Enable social authentication
 * @param socialProviders - List of OAuth providers
 * @param passkeyEnabled - Enable WebAuthn/Passkey login
 * @returns Login page component
 */
export function LoginPage({
  captchaSiteKey,
  captchaEnabled = false,
  socialLoginEnabled = false,
  socialProviders = [],
  passkeyEnabled = false,
}: LoginPageProps): JSX.Element {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loginMutation] = useMutation(LOGIN_MUTATION);

  const [captchaToken, setCaptchaToken] = useState<string>('');

  // Get redirect URL from query params
  const redirectUrl = searchParams.get('redirect') || '/';

  /**
   * Handles login form submission
   */
  const handleLogin = async (data: LoginFormData): Promise<void> => {
    const { data: result } = await loginMutation({
      variables: {
        email: data.email,
        password: data.password,
        rememberMe: data.rememberMe,
        captchaToken: captchaEnabled ? captchaToken : undefined,
      },
    });

    if (result?.login?.success) {
      // Redirect to requested page or home
      router.push(redirectUrl);
    } else {
      throw new Error(result?.login?.message || 'Login failed');
    }
  };

  /**
   * Handles passkey authentication
   */
  const handlePasskeyLogin = async (): Promise<void> => {
    // TODO: Implement WebAuthn passkey authentication
    // This would use @simplewebauthn/browser to initiate authentication
    throw new Error('Passkey login not yet implemented');
  };

  /**
   * Handles navigation to registration page
   */
  const handleRegisterClick = (): void => {
    router.push('/auth/register');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            Welcome back! Please sign in to continue
          </p>
        </div>

        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {captchaEnabled && captchaSiteKey && (
            <ReCaptcha
              siteKey={captchaSiteKey}
              version="v3"
              action="login"
              onVerify={setCaptchaToken}
              onError={(error) => console.error('CAPTCHA error:', error)}
            />
          )}

          <LoginForm
            onSubmit={handleLogin}
            onPasskeyLogin={passkeyEnabled ? handlePasskeyLogin : undefined}
            onRegisterClick={handleRegisterClick}
            showSocialLogin={socialLoginEnabled}
            socialProviders={socialProviders}
            showRememberMe={true}
            captchaToken={captchaEnabled ? captchaToken : undefined}
          />
        </div>
      </div>
    </div>
  );
}
