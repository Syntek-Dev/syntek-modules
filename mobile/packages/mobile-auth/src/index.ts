/**
 * @syntek/mobile-auth
 *
 * React Native authentication module for Syntek with maximum code reuse.
 * Implements Phase 4 (Mobile Frontend) with 70-80% shared code from @syntek/shared.
 *
 * Features:
 * - Email/password authentication with biometric support
 * - Multi-factor authentication (TOTP, SMS, passkey)
 * - Social authentication (Google, Apple, Microsoft, GitHub)
 * - Session security and management
 * - GDPR compliance (data export, account deletion, consent management)
 * - React Native Navigation integration
 * - Native biometric authentication
 * - Native secure storage
 *
 * Code Sharing:
 * - TypeScript types: 100% shared
 * - GraphQL operations: 100% shared
 * - Business logic hooks: 90-95% shared
 * - UI components: 70-80% shared
 * - Utilities: 100% shared
 * - Mobile-specific: Navigation, native adapters, platform integrations
 */

// Navigation
export {
  AuthNavigator,
  AccountNavigator,
  withAuthGuard,
  useAuthGuard,
  deepLinkingConfig,
  OAUTH_PROVIDERS,
  getOAuthRedirectUri,
  parseOAuthCallback,
  validateOAuthState,
} from './navigation';

export type {
  AuthStackParamList,
  AccountStackParamList,
  WithAuthGuardProps,
} from './navigation';

// Screens - Authentication
export { LoginScreen } from './screens/auth/LoginScreen';
export { RegistrationScreen } from './screens/auth/RegistrationScreen';
export { PhoneVerificationScreen } from './screens/auth/PhoneVerificationScreen';

// Screens - MFA
export { TOTPSetupScreen } from './screens/mfa/TOTPSetupScreen';
export { RecoveryKeyScreen } from './screens/mfa/RecoveryKeyScreen';

// Screens - Security
export { PasskeyManagementScreen } from './screens/security/PasskeyManagementScreen';
export { SessionSecurityScreen } from './screens/security/SessionSecurityScreen';

// Screens - GDPR
export { ProfileUpdateScreen } from './screens/gdpr/ProfileUpdateScreen';
export { DataExportScreen } from './screens/gdpr/DataExportScreen';
export { AccountDeletionScreen } from './screens/gdpr/AccountDeletionScreen';
export { PrivacySettingsScreen } from './screens/gdpr/PrivacySettingsScreen';

// Hooks (mobile-specific wrappers)
export { useAuth } from './hooks';

// Re-export shared types, components, and utilities
// This ensures consumers only need to import from @syntek/mobile-auth
export type {
  User,
  Session,
  LoginFormData,
  RegistrationFormData,
  TOTPSetupData,
  PasskeyCredential,
} from '@syntek/shared/auth/types';

export {
  Button,
  Input,
  Checkbox,
  Alert,
  Card,
  Badge,
  Spinner,
} from '@syntek/shared/design-system/components';

export {
  validateEmail,
  validatePassword,
  validateUsername,
  validatePhone,
  sanitizeInput,
} from '@syntek/shared/auth/utils';

// Re-export native adapters
export {
  authenticateWithBiometrics,
} from '@syntek/shared/auth/hooks/adapters/useBiometrics.native';

export {
  secureStorage,
} from '@syntek/shared/auth/hooks/adapters/useSecureStorage.native';
