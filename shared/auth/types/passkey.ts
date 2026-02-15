/**
 * Passkey/WebAuthn type definitions
 *
 * Types for passkey credentials and WebAuthn challenges.
 */

export interface PasskeyCredential {
  id: string;
  credentialId: string;
  publicKey: string;
  deviceName: string;
  deviceType: 'platform' | 'cross-platform';
  attestationFormat?: string;
  counter: number;
  createdAt: string;
  lastUsedAt?: string;
}

export interface WebAuthnChallenge {
  challenge: string;
  timeout: number;
  rpId: string;
  rpName: string;
  userId: string;
  userName: string;
  userDisplayName: string;
}

export interface RegisterPasskeyInput {
  deviceName: string;
  attestation: string;
  clientDataJSON: string;
  authenticatorData: string;
  publicKey: string;
}

export interface AuthenticatePasskeyInput {
  credentialId: string;
  authenticatorData: string;
  clientDataJSON: string;
  signature: string;
}

export interface BrowserSupport {
  webAuthnSupported: boolean;
  platformAuthenticatorSupported: boolean;
  conditionalMediationSupported: boolean;
}

export type AttestationFormat = 'packed' | 'fido-u2f' | 'android-key' | 'apple' | 'tpm' | 'none';
