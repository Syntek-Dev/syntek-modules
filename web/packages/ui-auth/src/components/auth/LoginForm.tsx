/**
 * Login Form Component
 *
 * Login form with email/password, passkey support, and social authentication.
 * Integrates with shared authentication hooks and Next.js routing.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button, Input, Checkbox, Alert } from '@syntek/shared/design-system/components';
import { validateEmail } from '@syntek/shared-auth/utils/validators';
import { sanitizeInput } from '@syntek/shared-auth/utils';
import type { LoginFormData } from '@syntek/shared-auth/types';

/**
 * Login form props
 */
export interface LoginFormProps {
  /** Callback when form is submitted */
  onSubmit: (data: LoginFormData) => Promise<void>;
  /** Callback when passkey login is requested */
  onPasskeyLogin?: () => Promise<void>;
  /** Callback when navigating to registration */
  onRegisterClick?: () => void;
  /** Show social login buttons */
  showSocialLogin?: boolean;
  /** Social login providers */
  socialProviders?: Array<'google' | 'github' | 'microsoft' | 'apple'>;
  /** Enable "Remember Me" option */
  showRememberMe?: boolean;
  /** CAPTCHA token (if CAPTCHA is enabled) */
  captchaToken?: string;
}

/**
 * Renders login form with multiple authentication options
 *
 * Features:
 * - Email and password authentication
 * - WebAuthn/Passkey support
 * - Social authentication buttons
 * - Remember me option
 * - Forgot password link
 * - CAPTCHA integration support
 * - Accessibility (WCAG 2.1 AA)
 *
 * @param onSubmit - Form submission handler
 * @param onPasskeyLogin - Passkey authentication handler
 * @param onRegisterClick - Navigate to registration callback
 * @param showSocialLogin - Display social login buttons
 * @param socialProviders - List of enabled social providers
 * @param showRememberMe - Show "Remember Me" checkbox
 * @param captchaToken - CAPTCHA verification token
 * @returns Login form component
 */
export function LoginForm({
  onSubmit,
  onPasskeyLogin,
  onRegisterClick,
  showSocialLogin = false,
  socialProviders = [],
  showRememberMe = true,
  captchaToken,
}: LoginFormProps): JSX.Element {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
    rememberMe: false,
  });

  const [errors, setErrors] = useState<Partial<Record<keyof LoginFormData, string>>>({});
  const [generalError, setGeneralError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPasskeyLoading, setIsPasskeyLoading] = useState(false);

  /**
   * Handles input field changes with sanitization
   */
  const handleChange = (field: keyof LoginFormData, value: string | boolean): void => {
    if (field === 'rememberMe') {
      setFormData((prev) => ({ ...prev, [field]: value as boolean }));
    } else {
      const sanitized = sanitizeInput(value as string);
      setFormData((prev) => ({ ...prev, [field]: sanitized }));
    }

    // Clear field error on change
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  /**
   * Validates form fields before submission
   */
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof LoginFormData, string>> = {};

    // Email validation
    const emailError = validateEmail(formData.email);
    if (emailError) {
      newErrors.email = emailError;
    }

    // Password required
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handles form submission
   */
  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setGeneralError('');

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        ...formData,
        captchaToken,
      });
    } catch (error) {
      setGeneralError(
        error instanceof Error ? error.message : 'Login failed. Please check your credentials.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handles passkey authentication
   */
  const handlePasskeyLogin = async (): Promise<void> => {
    if (!onPasskeyLogin) return;

    setGeneralError('');
    setIsPasskeyLoading(true);

    try {
      await onPasskeyLogin();
    } catch (error) {
      setGeneralError(
        error instanceof Error ? error.message : 'Passkey login failed. Please try again.'
      );
    } finally {
      setIsPasskeyLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {generalError && (
        <Alert variant="error" title="Login Error">
          {generalError}
        </Alert>
      )}

      {onPasskeyLogin && (
        <Button
          type="button"
          variant="outline"
          fullWidth
          onClick={handlePasskeyLogin}
          disabled={isPasskeyLoading}
        >
          {isPasskeyLoading ? 'Authenticating...' : 'Sign in with Passkey'}
        </Button>
      )}

      {(showSocialLogin && socialProviders.length > 0) && (
        <div className="space-y-3">
          {socialProviders.map((provider) => (
            <Button
              key={provider}
              type="button"
              variant="outline"
              fullWidth
              onClick={() => {
                // Social login handler would go here
                window.location.href = `/auth/oauth/${provider}`;
              }}
            >
              Continue with {provider.charAt(0).toUpperCase() + provider.slice(1)}
            </Button>
          ))}
        </div>
      )}

      {(onPasskeyLogin || showSocialLogin) && (
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-white px-2 text-gray-500">Or continue with email</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          id="email"
          type="email"
          label="Email Address"
          value={formData.email}
          onChange={(e) => handleChange('email', e.target.value)}
          error={errors.email}
          required
          autoComplete="email"
          placeholder="you@example.com"
        />

        <Input
          id="password"
          type="password"
          label="Password"
          value={formData.password}
          onChange={(e) => handleChange('password', e.target.value)}
          error={errors.password}
          required
          autoComplete="current-password"
        />

        <div className="flex items-center justify-between">
          {showRememberMe && (
            <Checkbox
              id="rememberMe"
              checked={formData.rememberMe}
              onChange={(e) => handleChange('rememberMe', e.target.checked)}
              label="Remember me"
            />
          )}

          <Link
            href="/auth/forgot-password"
            className="text-sm text-blue-600 hover:underline font-medium"
          >
            Forgot password?
          </Link>
        </div>

        <Button type="submit" variant="primary" fullWidth disabled={isSubmitting}>
          {isSubmitting ? 'Signing in...' : 'Sign In'}
        </Button>
      </form>

      <div className="text-center text-sm text-gray-600">
        Don't have an account?{' '}
        {onRegisterClick ? (
          <button
            type="button"
            onClick={onRegisterClick}
            className="text-blue-600 hover:underline font-medium"
          >
            Create account
          </button>
        ) : (
          <Link href="/auth/register" className="text-blue-600 hover:underline font-medium">
            Create account
          </Link>
        )}
      </div>
    </div>
  );
}
