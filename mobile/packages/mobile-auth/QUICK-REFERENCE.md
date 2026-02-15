# @syntek/mobile-auth - Quick Reference

One-page guide for developers working with the mobile authentication module.

## Installation

```bash
npm install @syntek/mobile-auth
npm install @react-navigation/native @react-navigation/stack
npm install expo-local-authentication expo-secure-store
npm install nativewind@^4.1.23
```

## Basic Setup

### 1. App.tsx

```tsx
import { NavigationContainer } from '@react-navigation/native';
import { AuthNavigator, deepLinkingConfig } from '@syntek/mobile-auth';

export default function App() {
  return (
    <NavigationContainer linking={deepLinkingConfig}>
      <AuthNavigator />
    </NavigationContainer>
  );
}
```

### 2. Configure Deep Linking (app.json)

```json
{
  "expo": {
    "scheme": "yourapp",
    "ios": {
      "associatedDomains": ["applinks:yourapp.com"]
    }
  }
}
```

## Common Patterns

### Login

```tsx
import { useAuth, LoginScreen } from '@syntek/mobile-auth';

function Login() {
  const { login, isLoading } = useAuth();

  const handleLogin = async () => {
    await login(email, password);
    // Auto-navigates to dashboard
  };

  return <LoginScreen onSubmit={handleLogin} />;
}
```

### Biometric Login

```tsx
import { authenticateWithBiometrics } from '@syntek/mobile-auth';

const success = await authenticateWithBiometrics();
if (success) {
  // Complete login
}
```

### Protected Routes

```tsx
import { withAuthGuard, ProfileUpdateScreen } from '@syntek/mobile-auth';

const ProtectedProfile = withAuthGuard(ProfileUpdateScreen);
```

### Secure Storage

```tsx
import { secureStorage } from '@syntek/mobile-auth';

await secureStorage.setItem('token', accessToken);
const token = await secureStorage.getItem('token');
await secureStorage.removeItem('token');
```

## Code Sharing

### ✅ Use Shared (70-80%)

```tsx
// Import from shared
import { Button, Input, Checkbox } from '@syntek/mobile-auth';
import { validateEmail, validatePassword } from '@syntek/mobile-auth';
import type { User, Session } from '@syntek/mobile-auth';
```

### ❌ Don't Duplicate

```tsx
// ❌ WRONG: Don't create duplicate validators
function validateEmail(email: string) { /* ... */ }

// ✅ CORRECT: Use shared validators
import { validateEmail } from '@syntek/mobile-auth';
```

## Architecture Rules

### 1. Django is Source of Truth

```tsx
// ✅ CORRECT
const { config } = useAuthConfig(); // Fetch from Django
if (password.length < config.passwordMinLength) { /* ... */ }

// ❌ WRONG
const PASSWORD_MIN_LENGTH = 12; // Don't hardcode
```

### 2. Code Sharing Priority

1. **100% Shared:** Types, GraphQL, utilities, constants
2. **70-80% Shared:** Hooks, components
3. **Mobile-Only:** Navigation, native adapters, deep linking

### 3. Styling (NativeWind 4)

Same Tailwind classes as web:

```tsx
<View className="flex-1 bg-white p-6">
  <Text className="text-2xl font-bold">Hello</Text>
  <Button className="bg-primary px-4 py-2 rounded-lg">
    Click Me
  </Button>
</View>
```

## Screens Reference

| Screen | Import | Use Case |
|--------|--------|----------|
| `LoginScreen` | `@syntek/mobile-auth` | Email/password, biometric, passkey |
| `RegistrationScreen` | `@syntek/mobile-auth` | GDPR-compliant registration |
| `PhoneVerificationScreen` | `@syntek/mobile-auth` | SMS verification |
| `TOTPSetupScreen` | `@syntek/mobile-auth` | 2FA setup with QR code |
| `RecoveryKeyScreen` | `@syntek/mobile-auth` | Display backup codes |
| `PasskeyManagementScreen` | `@syntek/mobile-auth` | Manage passkeys |
| `SessionSecurityScreen` | `@syntek/mobile-auth` | Active sessions |
| `ProfileUpdateScreen` | `@syntek/mobile-auth` | Update email, phone, username |
| `DataExportScreen` | `@syntek/mobile-auth` | GDPR data export |
| `AccountDeletionScreen` | `@syntek/mobile-auth` | Delete account (30-day grace) |
| `PrivacySettingsScreen` | `@syntek/mobile-auth` | Manage consent |

## Security Features

### Root Detection

```tsx
import { detectRootedDevice } from '@syntek/security-core/utils';

const result = await detectRootedDevice();
if (result.isRooted) {
  Alert.alert('Warning', 'Device may be compromised');
}
```

### Screen Capture Prevention

```tsx
import { usePreventScreenCapture } from '@syntek/security-core/utils';

function SensitiveScreen() {
  usePreventScreenCapture(); // Prevents screenshots
  return <Content />;
}
```

### App State Tracking

```tsx
import { useAppStateTracking } from '@syntek/security-core/utils';

useAppStateTracking({
  onBackground: () => console.log('App backgrounded'),
  onForeground: () => console.log('App foregrounded'),
});
```

## GDPR Compliance

| Feature | Component | GDPR Article |
|---------|-----------|--------------|
| Data Export | `DataExportScreen` | Article 20 |
| Account Deletion | `AccountDeletionScreen` | Article 17 |
| Consent Management | `PrivacySettingsScreen` | Article 7 |
| Withdraw Consent | `PrivacySettingsScreen` | Article 7.3 |

## Navigation

### Auth Stack

```tsx
Login → Register → PhoneVerification → TOTPSetup → RecoveryKey
```

### Account Stack

```tsx
ProfileUpdate
SessionSecurity
PasskeyManagement
DataExport
AccountDeletion
PrivacySettings
```

## Troubleshooting

### Issue: "Cannot find module '@syntek/shared'"

**Solution:** Ensure workspace is properly configured:

```json
{
  "dependencies": {
    "@syntek/shared": "workspace:*"
  }
}
```

### Issue: NativeWind classes not working

**Solution:** Configure NativeWind in `tailwind.config.js`:

```js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  presets: [require('nativewind/preset')],
};
```

### Issue: Biometric authentication not available

**Solution:** Check device capabilities:

```tsx
import * as LocalAuthentication from 'expo-local-authentication';

const hasHardware = await LocalAuthentication.hasHardwareAsync();
const isEnrolled = await LocalAuthentication.isEnrolledAsync();
```

## File Structure

```
mobile/packages/mobile-auth/
├── src/
│   ├── navigation/          # React Navigation setup
│   ├── screens/
│   │   ├── auth/            # Login, Registration, Phone Verification
│   │   ├── mfa/             # TOTP Setup, Recovery Key
│   │   ├── security/        # Passkey, Sessions
│   │   └── gdpr/            # Profile, Data Export, Deletion, Privacy
│   ├── hooks/               # Mobile-specific hook wrappers
│   └── index.ts             # Main exports
├── package.json
├── tsconfig.json
├── README.md
└── COMPLETION-SUMMARY.md
```

## Related Documentation

- Main README: `./README.md`
- Completion Summary: `./COMPLETION-SUMMARY.md`
- Shared Auth: `../../../shared/auth/README.md`
- Web Auth: `../../../web/packages/ui-auth/README.md`

## Support

- GitHub: https://github.com/syntek/syntek-modules
- Docs: https://docs.syntek.com/mobile-auth
