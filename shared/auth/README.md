# Shared Authentication Module

**Cross-platform authentication logic for web (Next.js) and mobile (React Native).**

## Overview

The shared authentication module provides 70-80% code reuse between web and mobile platforms through:

- **GraphQL Operations** - Queries, mutations, and fragments (100% shared)
- **TypeScript Types** - All authentication-related types (100% shared)
- **Business Logic Hooks** - Authentication, MFA, sessions, passkeys (90-95% shared)
- **Validation Utilities** - Form validation, password checking (100% shared)
- **UI Components** - Cross-platform components using Tailwind/NativeWind (70-80% shared)
- **Constants** - Timeouts, limits, regex patterns (100% shared)
- **Platform Adapters** - Storage, biometrics, WebAuthn abstraction (platform-specific)

## Structure

```
shared/auth/
├── components/           # Cross-platform UI components
│   ├── PasswordStrengthIndicator.tsx
│   ├── TOTPQRCode.tsx
│   ├── BackupCodeDisplay.tsx
│   ├── RecoveryKeyDownload.tsx
│   ├── LegalConsentCheckbox.tsx
│   ├── SocialLoginButton.tsx
│   ├── SessionCard.tsx
│   ├── PasskeyListItem.tsx
│   ├── PhoneInput.tsx
│   └── adapters/         # Platform-specific component adapters
│
├── hooks/                # Business logic hooks
│   ├── useAuth.ts
│   ├── useLogin.ts
│   ├── useLogout.ts
│   ├── useRegister.ts
│   ├── useSession.ts
│   ├── usePasswordValidation.ts
│   ├── useMFA.ts
│   ├── usePhoneVerification.ts
│   ├── usePasskey.ts
│   ├── useSessionSecurity.ts
│   ├── useGDPR.ts
│   ├── useProfileUpdate.ts
│   ├── useSocialAuth.ts
│   ├── useAutoLogout.ts
│   ├── useRememberMe.ts
│   └── adapters/         # Platform-specific hook adapters
│       ├── useWebAuthn.web.ts
│       ├── useBiometrics.native.ts
│       ├── useSecureStorage.web.ts
│       └── useSecureStorage.native.ts
│
├── utils/                # Shared utilities
│   ├── password-validator.ts
│   ├── hibp-checker.ts
│   ├── totp-generator.ts
│   ├── recovery-key-generator.ts
│   ├── fingerprint.ts
│   ├── validators/
│   │   ├── email.ts
│   │   ├── phone.ts
│   │   ├── username.ts
│   │   ├── password.ts
│   │   └── gdpr-consent.ts
│   ├── formatters/
│   │   ├── dates.ts
│   │   ├── phone.ts
│   │   └── session-device.ts
│   └── crypto/
│       ├── constant-time.ts
│       └── hash.ts
│
├── graphql/              # GraphQL operations (100% shared)
│   ├── client.ts
│   ├── fragments/
│   │   ├── user.ts
│   │   ├── session.ts
│   │   ├── passkey.ts
│   │   ├── social-account.ts
│   │   └── consent.ts
│   ├── queries/
│   │   ├── auth.ts
│   │   ├── mfa.ts
│   │   ├── passkey.ts
│   │   ├── session.ts
│   │   ├── social.ts
│   │   └── gdpr.ts
│   ├── mutations/
│   │   ├── auth.ts
│   │   ├── verification.ts
│   │   ├── mfa.ts
│   │   ├── passkey.ts
│   │   ├── session.ts
│   │   ├── social.ts
│   │   ├── profile.ts
│   │   └── gdpr.ts
│   └── types/
│       └── generated.ts
│
├── types/                # TypeScript types (100% shared)
│   ├── user.ts
│   ├── auth.ts
│   ├── mfa.ts
│   ├── passkey.ts
│   ├── session.ts
│   ├── social.ts
│   ├── gdpr.ts
│   ├── verification.ts
│   └── form-state.ts
│
└── constants/            # Shared constants (100% shared)
    ├── auth.ts
    ├── validation.ts
    ├── mfa.ts
    ├── passkey.ts
    ├── session.ts
    ├── social.ts
    └── routes.ts
```

## Usage

### Web (Next.js)

```typescript
import { useLogin } from '@syntek/shared/auth/hooks/useLogin';
import { PasswordStrengthIndicator } from '@syntek/shared/auth/components/PasswordStrengthIndicator';
import { loginMutation } from '@syntek/shared/auth/graphql/mutations/auth';

function LoginPage() {
  const { login, loading, error } = useLogin();

  const handleSubmit = async (email: string, password: string) => {
    await login({ email, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="email" name="email" />
      <input type="password" name="password" />
      <PasswordStrengthIndicator password={password} />
      <button disabled={loading}>Sign In</button>
    </form>
  );
}
```

### Mobile (React Native)

```typescript
import { useLogin } from '@syntek/shared/auth/hooks/useLogin';
import { PasswordStrengthIndicator } from '@syntek/shared/auth/components/PasswordStrengthIndicator';

function LoginScreen() {
  const { login, loading, error } = useLogin();

  const handleSubmit = async () => {
    await login({ email, password });
  };

  return (
    <View>
      <TextInput placeholder="Email" />
      <TextInput placeholder="Password" secureTextEntry />
      <PasswordStrengthIndicator password={password} />
      <Button title="Sign In" onPress={handleSubmit} disabled={loading} />
    </View>
  );
}
```

## Platform Adapters

Platform-specific functionality uses the adapter pattern:

```typescript
// Shared hook using adapter
import { useSecureStorage } from './adapters/useSecureStorage';

export const useAuth = () => {
  const storage = useSecureStorage(); // Platform-agnostic

  const saveToken = async (token: string) => {
    await storage.setItem('auth_token', token); // Works on both platforms
  };
};
```

Platform detection automatically loads the correct adapter:

- **Web:** `useSecureStorage.web.ts` → httpOnly cookies
- **Mobile:** `useSecureStorage.native.ts` → SecureStore (Expo)

## Security Features

- **httpOnly Cookies (Web)** - XSS protection for auth tokens
- **SecureStore (Mobile)** - Encrypted storage for auth tokens
- **Constant-Time Email Lookup** - Prevents timing attacks
- **DOMPurify Integration** - XSS prevention for user content
- **HIBP Integration** - Password breach detection
- **WebAuthn Attestation** - NIST AAL3 compliance
- **GDPR Consent** - Enhanced fingerprinting requires consent
- **PII Redaction** - Secure logging without sensitive data

## Dependencies

```json
{
  "dependencies": {
    "@apollo/client": "^3.11.11",
    "graphql": "^16.10.0",
    "zod": "^3.24.1",
    "libphonenumber-js": "^1.11.19",
    "dompurify": "^3.2.6",
    "qrcode": "^1.5.4",
    "otpauth": "^9.4.3"
  }
}
```

## Testing

```bash
# Run tests
pnpm test shared/auth

# Test on web
cd web/packages/ui-auth && pnpm dev

# Test on mobile
cd mobile/packages/mobile-auth && pnpm start
```

## Related Documentation

- **Design System:** `shared/design-system/README.md`
- **Security Compliance:** `.claude/SECURITY-COMPLIANCE.md`
- **Architecture Review:** `docs/REVIEWS/REVIEW-PHASE-3-4-AUTHENTICATION-UI-ARCHITECTURE.md`
- **Implementation Plan:** `docs/PLANS/PLAN-AUTHENTICATION-SYSTEM.md`
