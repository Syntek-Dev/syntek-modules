/**
 * Verification type definitions
 *
 * Types for email and phone verification.
 */

export type VerificationStatus = 'pending' | 'verified' | 'failed' | 'expired';

export type VerificationType = 'email' | 'phone';

export interface VerificationCode {
  id: string;
  userId: string;
  type: VerificationType;
  code: string;
  expiresAt: string;
  verified: boolean;
  verifiedAt?: string;
  attempts: number;
  maxAttempts: number;
}

export interface SendVerificationCodeInput {
  type: VerificationType;
  recipient: string; // Email address or phone number
}

export interface VerifyCodeInput {
  type: VerificationType;
  code: string;
}

export interface PhoneVerification {
  phone: string;
  verified: boolean;
  verifiedAt?: string;
  countryCode: string;
  formattedPhone: string;
}

export interface EmailVerification {
  email: string;
  verified: boolean;
  verifiedAt?: string;
}
