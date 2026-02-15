/**
 * Web authentication hooks
 *
 * Thin wrappers around shared hooks with Next.js integration.
 * Most hooks are re-exported directly from shared package.
 */

// Web-specific hooks with Next.js integration
export * from './useAuth';

// Re-export all shared hooks directly (no wrappers needed)
export { useAuthConfig } from '@syntek/shared-auth/hooks';

// Note: Additional hooks like usePasswordValidation, useMFA, usePhoneVerification,
// useGDPR, useProfileUpdate, useSocialAuth, useAutoLogout, useRememberMe are
// imported directly from @syntek/shared-auth/hooks as they don't need web-specific wrappers.
