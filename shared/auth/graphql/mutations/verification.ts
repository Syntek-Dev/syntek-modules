/**
 * GraphQL mutations for email and phone verification operations.
 *
 * Mutations for sending and verifying verification codes.
 */

import { gql } from '@apollo/client';

/**
 * Mutation to verify email address.
 *
 * Confirms email ownership using verification code sent via email.
 *
 * @example
 * ```typescript
 * const [verifyEmail] = useMutation(VERIFY_EMAIL);
 * const { data } = await verifyEmail({
 *   variables: { code: '123456' }
 * });
 * ```
 */
export const VERIFY_EMAIL = gql`
  mutation VerifyEmail($code: String!) {
    verifyEmail(code: $code) {
      success
      message
    }
  }
`;

/**
 * Mutation to verify phone number.
 *
 * Confirms phone ownership using verification code sent via SMS.
 *
 * @example
 * ```typescript
 * const [verifyPhone] = useMutation(VERIFY_PHONE);
 * const { data } = await verifyPhone({
 *   variables: { code: '123456' }
 * });
 * ```
 */
export const VERIFY_PHONE = gql`
  mutation VerifyPhone($code: String!) {
    verifyPhone(code: $code) {
      success
      message
    }
  }
`;

/**
 * Mutation to send verification code.
 *
 * Sends verification code to email or phone number.
 * Rate-limited to prevent abuse (max 1 request per 60 seconds).
 *
 * @example
 * ```typescript
 * const [sendCode] = useMutation(SEND_VERIFICATION_CODE);
 * const { data } = await sendCode({
 *   variables: { method: 'EMAIL' }
 * });
 * ```
 */
export const SEND_VERIFICATION_CODE = gql`
  mutation SendVerificationCode($method: VerificationMethod!) {
    sendVerificationCode(method: $method) {
      success
      message
      expiresAt
    }
  }
`;

/**
 * Mutation to resend verification email.
 *
 * Resends email verification link to user's registered email.
 * Rate-limited to prevent abuse (max 1 request per 60 seconds).
 *
 * @example
 * ```typescript
 * const [resendEmail] = useMutation(RESEND_VERIFICATION_EMAIL);
 * await resendEmail();
 * ```
 */
export const RESEND_VERIFICATION_EMAIL = gql`
  mutation ResendVerificationEmail {
    resendVerificationEmail {
      success
      message
      expiresAt
    }
  }
`;
