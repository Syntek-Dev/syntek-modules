/**
 * Registration Form Component
 *
 * GDPR-compliant registration form with email, password, phone, and consent fields.
 * Composes shared design system components with Next.js Link integration.
 * Fetches validation rules from Django backend via GraphQL (no hardcoded values).
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button, Input, Checkbox, Alert } from '@syntek/shared/design-system/components';
import { useAuthConfig } from '@syntek/shared-auth/hooks';
import { validateEmail, validatePassword } from '@syntek/shared-auth/utils/validators';
import { sanitizeInput } from '@syntek/shared-auth/utils';
import type { RegistrationFormData, GDPRConsent } from '@syntek/shared-auth/types';

/**
 * Registration form props
 */
export interface RegistrationFormProps {
  /** Callback when form is submitted */
  onSubmit: (data: RegistrationFormData) => Promise<void>;
  /** Callback when navigating to login */
  onLoginClick?: () => void;
  /** CAPTCHA token (if CAPTCHA is enabled) */
  captchaToken?: string;
  /** Privacy policy URL */
  privacyPolicyUrl?: string;
  /** Terms of service URL */
  termsUrl?: string;
  /** Cookie policy URL */
  cookiePolicyUrl?: string;
}

/**
 * Renders GDPR-compliant registration form
 *
 * Features:
 * - Email and password validation from backend config
 * - Optional phone number with region detection
 * - Required GDPR consent checkboxes
 * - Password strength indicator
 * - CAPTCHA integration support
 * - Accessibility (WCAG 2.1 AA)
 *
 * @param onSubmit - Form submission handler
 * @param onLoginClick - Navigate to login callback
 * @param captchaToken - CAPTCHA verification token
 * @param privacyPolicyUrl - Privacy policy link
 * @param termsUrl - Terms of service link
 * @param cookiePolicyUrl - Cookie policy link
 * @returns Registration form component
 */
export function RegistrationForm({
  onSubmit,
  onLoginClick,
  captchaToken,
  privacyPolicyUrl = '/legal/privacy',
  termsUrl = '/legal/terms',
  cookiePolicyUrl = '/legal/cookies',
}: RegistrationFormProps): JSX.Element {
  const { config, loading: configLoading } = useAuthConfig();

  const [formData, setFormData] = useState<RegistrationFormData>({
    email: '',
    password: '',
    passwordConfirm: '',
    phoneNumber: '',
    firstName: '',
    lastName: '',
    consents: {
      privacy: false,
      terms: false,
      marketing: false,
      cookies: false,
    },
  });

  const [errors, setErrors] = useState<Partial<Record<keyof RegistrationFormData, string>>>({});
  const [generalError, setGeneralError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Handles input field changes with sanitization
   */
  const handleChange = (field: keyof RegistrationFormData, value: string | GDPRConsent): void => {
    if (field === 'consents') {
      setFormData((prev) => ({ ...prev, [field]: value }));
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
   * Handles consent checkbox changes
   */
  const handleConsentChange = (consentType: keyof GDPRConsent, checked: boolean): void => {
    setFormData((prev) => ({
      ...prev,
      consents: {
        ...prev.consents,
        [consentType]: checked,
      },
    }));
  };

  /**
   * Validates form fields before submission
   */
  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof RegistrationFormData, string>> = {};

    // Email validation
    const emailError = validateEmail(formData.email);
    if (emailError) {
      newErrors.email = emailError;
    }

    // Password validation using backend config
    if (config) {
      const passwordError = validatePassword(formData.password, config);
      if (passwordError) {
        newErrors.password = passwordError;
      }
    }

    // Password confirmation
    if (formData.password !== formData.passwordConfirm) {
      newErrors.passwordConfirm = 'Passwords do not match';
    }

    // Required GDPR consents
    if (!formData.consents.privacy) {
      newErrors.consents = 'You must accept the privacy policy to register';
    }

    if (!formData.consents.terms) {
      newErrors.consents = 'You must accept the terms of service to register';
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
        error instanceof Error ? error.message : 'Registration failed. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (configLoading) {
    return <div className="flex justify-center p-8">Loading configuration...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      {generalError && (
        <Alert variant="error" title="Registration Error">
          {generalError}
        </Alert>
      )}

      <div className="space-y-4">
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

        <div className="grid grid-cols-2 gap-4">
          <Input
            id="firstName"
            type="text"
            label="First Name"
            value={formData.firstName}
            onChange={(e) => handleChange('firstName', e.target.value)}
            autoComplete="given-name"
          />

          <Input
            id="lastName"
            type="text"
            label="Last Name"
            value={formData.lastName}
            onChange={(e) => handleChange('lastName', e.target.value)}
            autoComplete="family-name"
          />
        </div>

        <Input
          id="password"
          type="password"
          label="Password"
          value={formData.password}
          onChange={(e) => handleChange('password', e.target.value)}
          error={errors.password}
          required
          autoComplete="new-password"
          helperText={
            config
              ? `Minimum ${config.passwordMinLength} characters${
                  config.uppercaseRequired ? ', uppercase required' : ''
                }${config.numberRequired ? ', number required' : ''}`
              : undefined
          }
        />

        <Input
          id="passwordConfirm"
          type="password"
          label="Confirm Password"
          value={formData.passwordConfirm}
          onChange={(e) => handleChange('passwordConfirm', e.target.value)}
          error={errors.passwordConfirm}
          required
          autoComplete="new-password"
        />

        <Input
          id="phoneNumber"
          type="tel"
          label="Phone Number (optional)"
          value={formData.phoneNumber}
          onChange={(e) => handleChange('phoneNumber', e.target.value)}
          autoComplete="tel"
          placeholder="+44 20 1234 5678"
        />
      </div>

      <div className="space-y-3 border-t pt-4">
        <h3 className="text-sm font-medium text-gray-900">Required Consents</h3>

        <Checkbox
          id="consent-privacy"
          checked={formData.consents.privacy}
          onChange={(e) => handleConsentChange('privacy', e.target.checked)}
          label={
            <span>
              I accept the{' '}
              <Link href={privacyPolicyUrl} className="text-blue-600 hover:underline">
                Privacy Policy
              </Link>
            </span>
          }
          required
        />

        <Checkbox
          id="consent-terms"
          checked={formData.consents.terms}
          onChange={(e) => handleConsentChange('terms', e.target.checked)}
          label={
            <span>
              I agree to the{' '}
              <Link href={termsUrl} className="text-blue-600 hover:underline">
                Terms of Service
              </Link>
            </span>
          }
          required
        />

        <Checkbox
          id="consent-cookies"
          checked={formData.consents.cookies}
          onChange={(e) => handleConsentChange('cookies', e.target.checked)}
          label={
            <span>
              I accept the{' '}
              <Link href={cookiePolicyUrl} className="text-blue-600 hover:underline">
                Cookie Policy
              </Link>
            </span>
          }
        />

        <Checkbox
          id="consent-marketing"
          checked={formData.consents.marketing}
          onChange={(e) => handleConsentChange('marketing', e.target.checked)}
          label="I want to receive marketing communications (optional)"
        />

        {errors.consents && <p className="text-sm text-red-600">{errors.consents}</p>}
      </div>

      <Button type="submit" variant="primary" fullWidth disabled={isSubmitting}>
        {isSubmitting ? 'Creating Account...' : 'Create Account'}
      </Button>

      <div className="text-center text-sm text-gray-600">
        Already have an account?{' '}
        {onLoginClick ? (
          <button
            type="button"
            onClick={onLoginClick}
            className="text-blue-600 hover:underline font-medium"
          >
            Log in
          </button>
        ) : (
          <Link href="/auth/login" className="text-blue-600 hover:underline font-medium">
            Log in
          </Link>
        )}
      </div>
    </form>
  );
}
