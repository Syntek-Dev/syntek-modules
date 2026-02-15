# @syntek/mobile-auth

React Native authentication module for Syntek with maximum code reuse from shared architecture.

## Overview

This package implements **Phase 4: Mobile Frontend (React Native)** of the Syntek authentication system, achieving **70-80% code sharing** with the web frontend through the `@syntek/shared` architecture.

## Features

### Authentication Methods

- ✅ Email and password authentication
- ✅ **Biometric authentication** (fingerprint, Face ID, Touch ID)
- ✅ **Passkey authentication** (platform authenticator)
- ✅ Social authentication (Google, Apple, Microsoft, GitHub)
- ✅ Remember me functionality
- ✅ Auto-logout on inactivity

### Multi-Factor Authentication (MFA)

- ✅ TOTP (Time-based One-Time Password) with authenticator apps
- ✅ SMS verification
- ✅ Backup codes for account recovery
- ✅ QR code scanning for TOTP setup

### Session Security

- ✅ Active session management
- ✅ Session revocation
- ✅ Device fingerprinting
- ✅ IP address tracking
- ✅ Auto-logout on app background (configurable)

### GDPR Compliance

- ✅ **Data export** (JSON, CSV) - Article 20
- ✅ **Account deletion** with 30-day grace period - Article 17
- ✅ **Consent management** (phone, IP tracking, analytics) - Article 7
- ✅ **Privacy settings** with consent withdrawal - Article 7.3
- ✅ Legal document links (privacy policy, terms of service)

### Mobile-Specific Features

- ✅ **Native biometric integration** (Expo Local Authentication)
- ✅ **Secure storage** (Expo Secure Store)
- ✅ **Deep linking** for OAuth callbacks
- ✅ **React Native Navigation** integration
- ✅ **NativeWind 4** styling (same Tailwind classes as web)
- ✅ **App state tracking** for auto-logout
- ✅ **Screen capture prevention** on sensitive screens
- ✅ **Root/jailbreak detection**
- ✅ **Certificate pinning** for API security

## Installation

```bash
# Install the package
npm install @syntek/mobile-auth

# Install peer dependencies
npm install react-native@^0.83.0 react@^19.2.1
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install expo-local-authentication expo-secure-store expo-auth-session expo-web-browser
npm install react-native-screens react-native-safe-area-context
npm install nativewind@^4.1.23
```

## Quick Start

### 1. Set up Navigation

```tsx
import { NavigationContainer } from '@react-navigation/native';
import {
  AuthNavigator,
  deepLinkingConfig,
} from '@syntek/mobile-auth';

export default function App() {
  return (
    <NavigationContainer linking={deepLinkingConfig}>
      <AuthNavigator />
    </NavigationContainer>
  );
}
```

### 2. Use Authentication Hook

```tsx
import { useAuth } from '@syntek/mobile-auth';

function LoginScreen() {
  const { login, isLoading } = useAuth();

  const handleLogin = async () => {
    try {
      await login(email, password);
      // Automatically navigates to dashboard on success
    } catch (error) {
      // Handle error
    }
  };

  return (
    <Button onPress={handleLogin} disabled={isLoading}>
      {isLoading ? 'Signing in...' : 'Sign In'}
    </Button>
  );
}
```

### 3. Protect Screens with Auth Guard

```tsx
import { withAuthGuard, ProfileUpdateScreen } from '@syntek/mobile-auth';

// Wrap screen with authentication requirement
const ProtectedProfile = withAuthGuard(ProfileUpdateScreen);

// Use in navigator
<Stack.Screen name="Profile" component={ProtectedProfile} />
```

### 4. Use Biometric Authentication

```tsx
import { authenticateWithBiometrics } from '@syntek/mobile-auth';

async function handleBiometricLogin() {
  const success = await authenticateWithBiometrics();
  if (success) {
    // Complete login
  }
}
```

## Architecture

### Code Sharing Strategy

This package achieves **70-80% code reuse** from `@syntek/shared`:

| Component Type | Shared % | Location |
|----------------|----------|----------|
| TypeScript types | 100% | `@syntek/shared/auth/types` |
| GraphQL operations | 100% | `@syntek/shared/auth/graphql` |
| Business logic hooks | 90-95% | `@syntek/shared/auth/hooks` |
| UI components | 70-80% | `@syntek/shared/design-system` |
| Utilities | 100% | `@syntek/shared/auth/utils` |
| Constants | 100% | `@syntek/shared/auth/constants` |

**Mobile-specific code** (~20-30%):
- React Native screens (navigation wrappers)
- React Native Navigation setup
- Native biometric adapter
- Native secure storage adapter
- Deep linking configuration
- App state tracking

### Django is Source of Truth

**CRITICAL:** All configuration is fetched from Django backend via GraphQL. No values are hardcoded.

```tsx
// ✅ CORRECT: Fetch from Django
const { config } = useAuthConfig(); // From @syntek/shared
if (password.length < config.passwordMinLength) {
  // ...
}

// ❌ WRONG: Hardcoded values
const PASSWORD_MIN_LENGTH = 12; // Never hardcode
```

## Screens

### Authentication Screens

| Screen | Path | Description |
|--------|------|-------------|
| `LoginScreen` | `/src/screens/auth/LoginScreen.tsx` | Email/password, biometric, passkey login |
| `RegistrationScreen` | `/src/screens/auth/RegistrationScreen.tsx` | GDPR-compliant registration |
| `PhoneVerificationScreen` | `/src/screens/auth/PhoneVerificationScreen.tsx` | SMS verification |

### MFA Screens

| Screen | Path | Description |
|--------|------|-------------|
| `TOTPSetupScreen` | `/src/screens/mfa/TOTPSetupScreen.tsx` | QR code, backup codes |
| `RecoveryKeyScreen` | `/src/screens/mfa/RecoveryKeyScreen.tsx` | Display and share backup codes |

### Security Screens

| Screen | Path | Description |
|--------|------|-------------|
| `SessionSecurityScreen` | `/src/screens/security/SessionSecurityScreen.tsx` | Active sessions, revocation |
| `PasskeyManagementScreen` | `/src/screens/security/PasskeyManagementScreen.tsx` | Manage passkeys |

### GDPR Screens

| Screen | Path | Description |
|--------|------|-------------|
| `ProfileUpdateScreen` | `/src/screens/gdpr/ProfileUpdateScreen.tsx` | Update email, phone, username |
| `DataExportScreen` | `/src/screens/gdpr/DataExportScreen.tsx` | Export data (JSON/CSV) |
| `AccountDeletionScreen` | `/src/screens/gdpr/AccountDeletionScreen.tsx` | Delete account (30-day grace) |
| `PrivacySettingsScreen` | `/src/screens/gdpr/PrivacySettingsScreen.tsx` | Manage consent, withdraw consent |

## Navigation

### Deep Linking

OAuth callbacks and email verification use deep linking:

```
Custom scheme: yourapp://auth/callback/google
Universal link: https://yourapp.com/auth/callback/google
```

Configure in `app.json`:

```json
{
  "expo": {
    "scheme": "yourapp",
    "ios": {
      "associatedDomains": ["applinks:yourapp.com"]
    },
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "data": {
            "scheme": "https",
            "host": "yourapp.com"
          }
        }
      ]
    }
  }
}
```

## Security

### Biometric Authentication

```tsx
import { authenticateWithBiometrics } from '@syntek/mobile-auth';

const success = await authenticateWithBiometrics();
// Uses Face ID (iOS), Touch ID (iOS), Fingerprint (Android)
```

### Secure Storage

```tsx
import { secureStorage } from '@syntek/mobile-auth';

// Store sensitive data
await secureStorage.setItem('token', accessToken);

// Retrieve sensitive data
const token = await secureStorage.getItem('token');

// Remove sensitive data
await secureStorage.removeItem('token');
```

### Root/Jailbreak Detection

```tsx
import { detectRootedDevice } from '@syntek/security-core/utils';

const result = await detectRootedDevice();
if (result.isRooted && result.confidence === 'high') {
  Alert.alert('Security Warning', 'This device may be compromised');
}
```

### Screen Capture Prevention

```tsx
import { usePreventScreenCapture } from '@syntek/security-core/utils';

function BackupCodesScreen() {
  usePreventScreenCapture(); // Prevents screenshots
  return <BackupCodes />;
}
```

## Styling

Uses **NativeWind 4** - same Tailwind classes work on mobile and web:

```tsx
<View className="flex-1 bg-white p-6">
  <Text className="text-2xl font-bold text-neutral-900 mb-2">
    Welcome Back
  </Text>
  <Button className="bg-primary text-white px-4 py-2 rounded-lg">
    Sign In
  </Button>
</View>
```

## Examples

### Complete Login Flow

```tsx
import { useAuth, LoginScreen } from '@syntek/mobile-auth';

function LoginExample() {
  const { login, isLoading, error } = useAuth();

  const handleLogin = async (email: string, password: string) => {
    try {
      await login(email, password);
      // Automatically navigates to dashboard
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return <LoginScreen onSubmit={handleLogin} />;
}
```

### Biometric Login with Fallback

```tsx
import { authenticateWithBiometrics, useAuth } from '@syntek/mobile-auth';

async function loginWithBiometric() {
  const biometricSuccess = await authenticateWithBiometrics();

  if (biometricSuccess) {
    // Retrieve saved credentials from secure storage
    const email = await secureStorage.getItem('email');
    const token = await secureStorage.getItem('token');

    // Complete authentication
    await auth.loginWithToken(token);
  } else {
    // Fallback to password
    navigation.navigate('Login');
  }
}
```

## Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
npm run lint:fix

# Type check
npm run typecheck

# Run tests
npm test
npm run test:watch
```

## Dependencies

### Required

- `react-native` ^0.83.0
- `react` ^19.2.1
- `@syntek/shared` (workspace)
- `@react-navigation/native` ^7.0.19
- `@react-navigation/stack` ^7.2.13
- `@react-navigation/bottom-tabs` ^7.2.13
- `expo-local-authentication` ~15.0.2
- `expo-secure-store` ~14.0.0
- `expo-auth-session` ~6.1.7
- `expo-web-browser` ~14.0.1
- `react-native-blur` ^4.4.1
- `react-native-screens` ^4.6.0
- `react-native-safe-area-context` ^5.1.5
- `nativewind` ^4.1.23

## License

MIT

## Related Packages

- `@syntek/shared` - Shared authentication logic (70-80% of code)
- `@syntek/ui-auth` - Web authentication UI (Phase 3)
- `@syntek/security-core` - Mobile security utilities
- `syntek-graphql-auth` - GraphQL authentication layer (backend)
- `syntek-authentication` - Django authentication backend (source of truth)

## Support

For issues and questions:
- GitHub Issues: https://github.com/syntek/syntek-modules/issues
- Documentation: https://docs.syntek.com/mobile-auth
