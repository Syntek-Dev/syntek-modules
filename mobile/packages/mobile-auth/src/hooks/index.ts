/**
 * hooks/index.ts
 *
 * Exports all mobile-specific authentication hooks.
 * Most hooks are imported directly from shared - only navigation wrappers are mobile-specific.
 */

// Mobile-specific wrappers
export { useAuth } from './useAuth';

// TODO: Add other mobile-specific wrappers as needed
// export { usePasskey } from './usePasskey';
// export { useSessionSecurity } from './useSessionSecurity';
// export { useAutoLogoutMobile } from './useAutoLogoutMobile';

// Re-export shared hooks directly (no wrapper needed)
// TODO: Uncomment when shared hooks are available
// export {
//   usePasswordValidation,
//   useMFA,
//   usePhoneVerification,
//   useGDPR,
//   useProfileUpdate,
//   useSocialAuth,
//   useRememberMe,
// } from '@syntek/shared/auth/hooks';
