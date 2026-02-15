/**
 * Registration Page Component
 *
 * GDPR-compliant registration page with Next.js metadata and SEO optimization.
 * Includes region detection for GDPR compliance and CAPTCHA integration.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { RegistrationForm } from '../../components/auth/RegistrationForm';
import { ReCaptcha } from '../../lib/ReCaptcha';
import { useAuthConfig } from '@syntek/shared-auth/hooks';
import { useMutation } from '@apollo/client';
import { REGISTER_MUTATION } from '@syntek/shared-auth/graphql/mutations';
import type { RegistrationFormData } from '@syntek/shared-auth/types';

/**
 * Registration page props
 */
export interface RegisterPageProps {
  /** reCAPTCHA site key (from environment) */
  captchaSiteKey?: string;
  /** Enable CAPTCHA */
  captchaEnabled?: boolean;
}

/**
 * Renders registration page with GDPR compliance and SEO
 *
 * Features:
 * - GDPR region detection
 * - CAPTCHA integration (reCAPTCHA v3)
 * - Email verification flow
 * - Next.js metadata for SEO
 * - Accessibility optimized
 *
 * **SEO Metadata (add in parent layout):**
 * ```tsx
 * export const metadata = {
 *   title: 'Create Account | Your App',
 *   description: 'Create a secure account with email verification and GDPR compliance',
 * };
 * ```
 *
 * @param captchaSiteKey - reCAPTCHA site key
 * @param captchaEnabled - Enable CAPTCHA verification
 * @returns Registration page component
 */
export function RegisterPage({
  captchaSiteKey,
  captchaEnabled = false,
}: RegisterPageProps): JSX.Element {
  const router = useRouter();
  const { config } = useAuthConfig();
  const [registerMutation] = useMutation(REGISTER_MUTATION);

  const [captchaToken, setCaptchaToken] = useState<string>('');

  /**
   * Handles registration form submission
   */
  const handleRegister = async (data: RegistrationFormData): Promise<void> => {
    const { data: result } = await registerMutation({
      variables: {
        email: data.email,
        password: data.password,
        firstName: data.firstName,
        lastName: data.lastName,
        phoneNumber: data.phoneNumber,
        consents: data.consents,
        captchaToken: captchaEnabled ? captchaToken : undefined,
      },
    });

    if (result?.register?.success) {
      // Redirect to email verification
      router.push('/auth/verify-email');
    } else {
      throw new Error(result?.register?.message || 'Registration failed');
    }
  };

  /**
   * Handles navigation to login page
   */
  const handleLoginClick = (): void => {
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            Join us today and get started
          </p>
        </div>

        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {captchaEnabled && captchaSiteKey && (
            <ReCaptcha
              siteKey={captchaSiteKey}
              version="v3"
              action="register"
              onVerify={setCaptchaToken}
              onError={(error) => console.error('CAPTCHA error:', error)}
            />
          )}

          <RegistrationForm
            onSubmit={handleRegister}
            onLoginClick={handleLoginClick}
            captchaToken={captchaEnabled ? captchaToken : undefined}
          />
        </div>
      </div>
    </div>
  );
}
