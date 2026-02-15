/**
 * useAuth Hook (Web)
 *
 * Thin wrapper around shared useAuth hook with Next.js router integration.
 * Adds web-specific navigation after authentication actions.
 */

'use client';

import { useRouter } from 'next/navigation';
import { useAuthConfig } from '@syntek/shared-auth/hooks';
import { useMutation } from '@apollo/client';
import {
  LOGIN_MUTATION,
  REGISTER_MUTATION,
  LOGOUT_MUTATION,
} from '@syntek/shared-auth/graphql/mutations';
import type { LoginFormData, RegistrationFormData } from '@syntek/shared-auth/types';

/**
 * Authentication hook with Next.js routing
 *
 * Wraps shared authentication logic with Next.js-specific navigation.
 * Uses Next.js router to redirect after login/logout/registration.
 *
 * @returns Authentication methods with Next.js router integration
 */
export function useAuth() {
  const router = useRouter();
  const { config } = useAuthConfig();

  const [loginMutation] = useMutation(LOGIN_MUTATION);
  const [registerMutation] = useMutation(REGISTER_MUTATION);
  const [logoutMutation] = useMutation(LOGOUT_MUTATION);

  /**
   * Logs in user and redirects to callback URL
   */
  const login = async (
    data: LoginFormData,
    callbackUrl: string = '/'
  ): Promise<void> => {
    const { data: result } = await loginMutation({
      variables: {
        email: data.email,
        password: data.password,
        rememberMe: data.rememberMe,
        captchaToken: data.captchaToken,
      },
    });

    if (result?.login?.success) {
      // Store token (handled by httpOnly cookie on server)
      // Redirect using Next.js router
      router.push(callbackUrl);
    } else {
      throw new Error(result?.login?.message || 'Login failed');
    }
  };

  /**
   * Registers user and redirects to verification or callback URL
   */
  const register = async (
    data: RegistrationFormData,
    callbackUrl: string = '/auth/verify-email'
  ): Promise<void> => {
    const { data: result } = await registerMutation({
      variables: {
        email: data.email,
        password: data.password,
        firstName: data.firstName,
        lastName: data.lastName,
        phoneNumber: data.phoneNumber,
        consents: data.consents,
        captchaToken: data.captchaToken,
      },
    });

    if (result?.register?.success) {
      // Redirect to email verification
      router.push(callbackUrl);
    } else {
      throw new Error(result?.register?.message || 'Registration failed');
    }
  };

  /**
   * Logs out user and redirects to login page
   */
  const logout = async (redirectUrl: string = '/auth/login'): Promise<void> => {
    await logoutMutation();

    // Clear client-side state
    // Redirect to login
    router.push(redirectUrl);
  };

  return {
    config,
    login,
    register,
    logout,
  };
}
