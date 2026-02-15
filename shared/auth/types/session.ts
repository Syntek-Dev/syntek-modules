/**
 * Session type definitions
 *
 * Types for sessions, device fingerprints, and session activity.
 */

export type SessionStatus = 'active' | 'expired' | 'suspicious' | 'terminated';

export type FingerprintLevel = 'minimal' | 'balanced' | 'aggressive';

export interface Session {
  id: string;
  userId: string;
  deviceName: string;
  deviceType: 'desktop' | 'mobile' | 'tablet' | 'unknown';
  browser: string;
  browserVersion: string;
  os: string;
  osVersion: string;
  ipAddress: string;
  country?: string;
  city?: string;
  status: SessionStatus;
  createdAt: string;
  lastActivityAt: string;
  expiresAt: string;
  isCurrent: boolean;
  fingerprint?: DeviceFingerprint;
}

export interface DeviceFingerprint {
  level: FingerprintLevel;
  hash: string;
  userAgent: string;
  language: string;
  timezone: string;
  screenResolution?: string;
  colorDepth?: number;
  webglRenderer?: string;
  audioContext?: string;
  fonts?: string[];
  createdAt: string;
}

export interface SessionActivity {
  id: string;
  sessionId: string;
  action: string;
  timestamp: string;
  ipAddress: string;
  suspicious: boolean;
}

export interface UpdateFingerprintInput {
  level: FingerprintLevel;
  consentGiven: boolean;
}

export interface TerminateSessionInput {
  sessionId: string;
}
