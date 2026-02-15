/**
 * Multi-Factor Authentication type definitions
 *
 * Types for TOTP, backup codes, and recovery keys.
 */

export type MFAStatus = 'enabled' | 'disabled' | 'pending_setup';

export interface TOTPSetup {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
  recoveryKeys: string[];
}

export interface TOTPVerificationInput {
  code: string;
}

export interface BackupCode {
  id: string;
  code: string;
  used: boolean;
  usedAt?: string;
}

export interface RecoveryKey {
  id: string;
  key: string;
  used: boolean;
  usedAt?: string;
}

export interface MFAStatusResponse {
  enabled: boolean;
  totpEnabled: boolean;
  backupCodesRemaining: number;
  recoveryKeysRemaining: number;
}

export interface RegenerateBackupCodesResponse {
  backupCodes: string[];
}

export interface GenerateRecoveryKeysResponse {
  recoveryKeys: string[];
}
