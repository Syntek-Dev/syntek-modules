/**
 * GDPR type definitions
 *
 * Types for consent management, data exports, and deletion requests.
 */

export type ConsentType = 'terms' | 'privacy' | 'marketing' | 'analytics' | 'enhanced_fingerprinting';

export type DataExportStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type DataExportFormat = 'json' | 'csv' | 'xml';

export interface ConsentRecord {
  id: string;
  userId: string;
  type: ConsentType;
  granted: boolean;
  grantedAt?: string;
  withdrawnAt?: string;
  ipAddress: string;
  userAgent: string;
}

export interface DataExportRequest {
  id: string;
  userId: string;
  status: DataExportStatus;
  format: DataExportFormat;
  requestedAt: string;
  completedAt?: string;
  downloadUrl?: string;
  expiresAt?: string;
  error?: string;
}

export interface DeletionRequest {
  id: string;
  userId: string;
  reason: string;
  requestedAt: string;
  scheduledFor: string;
  confirmedAt?: string;
  cancelledAt?: string;
  completedAt?: string;
}

export interface UpdateConsentInput {
  type: ConsentType;
  granted: boolean;
}

export interface ExportDataInput {
  format: DataExportFormat;
}

export interface DeleteAccountInput {
  reason: string;
  password: string;
  confirmDeletion: boolean;
}
