# @syntek/ui-auth

Web authentication UI components for Next.js/React with WebAuthn, MFA, and GDPR compliance.

## Overview

This package provides a complete authentication UI for Next.js applications, built on top of `@syntek/shared-auth` for maximum code reuse (70-80% shared). It includes:

- **Registration and login forms** with GDPR compliance
- **WebAuthn/Passkey support** for passwordless authentication
- **Multi-factor authentication (MFA)** with TOTP and backup codes
- **Social authentication** (OAuth) with Google, GitHub, Microsoft, Apple, Facebook, LinkedIn, X
- **Session management** with auto-logout and activity tracking
- **CAPTCHA integration** (reCAPTCHA and hCaptcha)
- **Next.js page components** with SEO optimization
- **Accessibility** (WCAG 2.1 AA compliant)

## Features

### ✅ **Architecture Compliance**

- ✅ Django backend is source of truth (fetches config via GraphQL)
- ✅ NO hardcoded configuration values
- ✅ Maximum code reuse from `@syntek/shared-auth` (70-80%)
- ✅ Web-specific code ONLY for Next.js routing, SEO, HOCs
- ✅ TypeScript strict mode enabled
- ✅ Tailwind v4 CSS patterns

### 🔐 **Security Features**

- Password strength validation (from backend config)
- CAPTCHA bot protection (reCAPTCHA v2/v3, hCaptcha)
- WebAuthn/Passkey support
- Multi-factor authentication (TOTP)
- Session security (fingerprinting, auto-logout)
- Social authentication (OAuth 2.0)
- CSRF and XSS protection

### 📱 **User Experience**

- Mobile-first responsive design
- Real-time validation feedback
- Password strength indicators
- Auto-logout warnings with countdown
- Remember me functionality
- Accessible (keyboard navigation, screen readers)

## Installation

```bash
pnpm add @syntek/ui-auth @syntek/shared
```

## Dependencies

This package requires:

- `@syntek/shared` - Shared authentication logic and components
- `next` - Next.js framework
- `react` - React library
- `@apollo/client` - GraphQL client
- `@simplewebauthn/browser` - WebAuthn client
- `@hcaptcha/react-hcaptcha` - hCaptcha integration
- `react-google-recaptcha-v3` - reCAPTCHA v3 integration

## Usage

### 1. Setup Apollo Client

```tsx
// app/layout.tsx
import { ApolloProvider } from '@apollo/client';
import { createApolloClient } from '@syntek/shared-auth/graphql';

const client = createApolloClient({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URI,
});

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ApolloProvider client={client}>
          {children}
        </ApolloProvider>
      </body>
    </html>
  );
}
```

### 2. Add Auth Context Provider

```tsx
// app/providers.tsx
'use client';

import { AuthProvider } from '@syntek/ui-auth';

export function Providers({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
```

### 3. Create Login Page

```tsx
// app/auth/login/page.tsx
import { LoginPage } from '@syntek/ui-auth/pages';

export const metadata = {
  title: 'Sign In | Your App',
  description: 'Sign in to your account',
};

export default function Login() {
  return (
    <LoginPage
      captchaEnabled={true}
      captchaSiteKey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}
      socialLoginEnabled={true}
      socialProviders={['google', 'github', 'microsoft']}
      passkeyEnabled={true}
    />
  );
}
```

### 4. Create Registration Page

```tsx
// app/auth/register/page.tsx
import { RegisterPage } from '@syntek/ui-auth/pages';

export const metadata = {
  title: 'Create Account | Your App',
  description: 'Create a secure account with GDPR compliance',
};

export default function Register() {
  return (
    <RegisterPage
      captchaEnabled={true}
      captchaSiteKey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}
    />
  );
}
```

### 5. Protect Routes with withAuth HOC

```tsx
// app/dashboard/page.tsx
'use client';

import { withAuth } from '@syntek/ui-auth';

function DashboardPage() {
  return <div>Protected Dashboard Content</div>;
}

export default withAuth(DashboardPage, {
  redirectTo: '/auth/login',
  showLoading: true,
});
```

## Components

### Authentication Forms

#### `<RegistrationForm />`

GDPR-compliant registration form with consent checkboxes.

```tsx
import { RegistrationForm } from '@syntek/ui-auth';

<RegistrationForm
  onSubmit={handleRegister}
  onLoginClick={() => router.push('/auth/login')}
  captchaToken={captchaToken}
  privacyPolicyUrl="/legal/privacy"
  termsUrl="/legal/terms"
  cookiePolicyUrl="/legal/cookies"
/>
```

#### `<LoginForm />`

Login form with email/password, passkey, and social login support.

```tsx
import { LoginForm } from '@syntek/ui-auth';

<LoginForm
  onSubmit={handleLogin}
  onPasskeyLogin={handlePasskeyLogin}
  showSocialLogin={true}
  socialProviders={['google', 'github']}
  showRememberMe={true}
/>
```

### Social Authentication

#### `<SocialLoginButtons />`

OAuth provider login buttons.

```tsx
import { SocialLoginButtons } from '@syntek/ui-auth';

<SocialLoginButtons
  providers={['google', 'github', 'microsoft', 'apple']}
  callbackUrl="/dashboard"
/>
```

#### `<SocialAccountsList />`

Manage linked social accounts.

```tsx
import { SocialAccountsList } from '@syntek/ui-auth';

<SocialAccountsList
  accounts={linkedAccounts}
  availableProviders={['google', 'github', 'microsoft']}
  onUnlink={handleUnlink}
  onLink={handleLink}
/>
```

### Session Management

#### `<AutoLogoutWarning />`

Warning modal with countdown before auto-logout.

```tsx
import { AutoLogoutWarning } from '@syntek/ui-auth';

<AutoLogoutWarning
  secondsRemaining={300}
  onExtendSession={handleExtendSession}
  onSessionExpired={handleLogout}
  show={showWarning}
/>
```

#### `<SessionActivityTracker />`

Tracks user activity for auto-logout functionality.

```tsx
import { SessionActivityTracker } from '@syntek/ui-auth';

<SessionActivityTracker
  onActivity={handleActivity}
  throttleMs={1000}
  enabled={true}
/>
```

#### `<RememberMeCheckbox />`

"Keep me logged in" checkbox with session info tooltip.

```tsx
import { RememberMeCheckbox } from '@syntek/ui-auth';

<RememberMeCheckbox
  checked={rememberMe}
  onChange={setRememberMe}
  defaultSessionDuration={30}
  extendedSessionDuration={30}
/>
```

### CAPTCHA Integration

#### `<ReCaptcha />`

reCAPTCHA v2/v3 wrapper.

```tsx
import { ReCaptcha } from '@syntek/ui-auth';

<ReCaptcha
  siteKey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY}
  version="v3"
  action="register"
  onVerify={setCaptchaToken}
/>
```

#### `<HCaptcha />`

hCaptcha wrapper (privacy-focused).

```tsx
import { HCaptcha } from '@syntek/ui-auth';

<HCaptcha
  siteKey={process.env.NEXT_PUBLIC_HCAPTCHA_SITE_KEY}
  theme="light"
  onVerify={setCaptchaToken}
/>
```

## Hooks

### `useAuth()`

Authentication hook with Next.js routing.

```tsx
import { useAuth } from '@syntek/ui-auth';

function LoginComponent() {
  const { config, login, logout } = useAuth();

  const handleLogin = async (data) => {
    await login(data, '/dashboard');
  };

  return <LoginForm onSubmit={handleLogin} />;
}
```

### `useAuthConfig()`

Fetches authentication configuration from Django backend.

```tsx
import { useAuthConfig } from '@syntek/ui-auth';

function PasswordInput() {
  const { config, loading } = useAuthConfig();

  return (
    <Input
      type="password"
      helperText={`Minimum ${config.passwordMinLength} characters`}
    />
  );
}
```

## Pages

All pages include Next.js metadata for SEO.

| Page | Path | Description |
|------|------|-------------|
| `LoginPage` | `/auth/login` | Login with email, passkey, or social |
| `RegisterPage` | `/auth/register` | GDPR-compliant registration |

**Future pages (not yet implemented):**

- `VerifyEmailPage` - Email verification
- `VerifyPhonePage` - Phone verification
- `SetupMFAPage` - MFA setup wizard
- `ManagePasskeysPage` - Passkey management
- `SessionsPage` - Active session dashboard
- `SecuritySettingsPage` - Security settings
- `SocialAccountsPage` - Social account management
- `ProfilePage` - User profile editor
- `ExportDataPage` - GDPR data export
- `DeleteAccountPage` - Account deletion
- `PrivacySettingsPage` - Privacy preferences

## Higher-Order Components

### `withAuth(Component, options)`

Protected route wrapper.

```tsx
import { withAuth } from '@syntek/ui-auth';

const ProtectedPage = withAuth(MyPage, {
  redirectTo: '/auth/login',
  showLoading: true,
});
```

## Environment Variables

```env
# GraphQL API
NEXT_PUBLIC_GRAPHQL_URI=https://api.example.com/graphql

# reCAPTCHA
NEXT_PUBLIC_RECAPTCHA_SITE_KEY=your-recaptcha-site-key

# hCaptcha (alternative)
NEXT_PUBLIC_HCAPTCHA_SITE_KEY=your-hcaptcha-site-key
```

## Code Sharing

This package maximizes code reuse from `@syntek/shared-auth`:

| Category | Shared % | Notes |
|----------|----------|-------|
| TypeScript Types | 100% | All types from shared |
| GraphQL Operations | 100% | All queries/mutations from shared |
| Utilities | 100% | All validators/helpers from shared |
| Business Logic Hooks | 95% | Thin wrappers with Next.js routing |
| UI Components | 70-80% | Composed from shared design system |

**Web-Specific Code (~500-800 lines):**

- Next.js page components with SEO
- `useAuth` hook wrapper with Next.js router
- `withAuth` HOC for protected routes
- CAPTCHA script loaders
- reCAPTCHA/hCaptcha wrappers
- AuthContext provider

**Shared Code Reused (~3,500-4,000 lines):**

- All TypeScript types
- All GraphQL operations
- All validation utilities
- All design system components
- All authentication constants

## Accessibility

All components are WCAG 2.1 AA compliant:

- ✅ Semantic HTML (`<nav>`, `<main>`, `<button>`)
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ ARIA labels and roles
- ✅ Focus management
- ✅ Color contrast (4.5:1 minimum)
- ✅ Screen reader support
- ✅ Form labels and error announcements

## Styling

Uses **Tailwind v4** CSS-first approach:

```css
/* globals.css */
@theme {
  --color-primary: #3b82f6;
  --color-danger: #ef4444;
}
```

All components use Tailwind utility classes for styling.

## Security

- ✅ CSRF protection (via Django backend)
- ✅ XSS protection (input sanitization)
- ✅ CAPTCHA bot protection
- ✅ WebAuthn/Passkey support
- ✅ Session fingerprinting
- ✅ Auto-logout on inactivity
- ✅ httpOnly cookies for session tokens
- ✅ GDPR compliance (consent management)

## Testing

```bash
# Run tests
pnpm test

# Run tests with coverage
pnpm test:coverage

# Type checking
pnpm typecheck

# Linting
pnpm lint
pnpm lint:fix
```

## Development

```bash
# Install dependencies
pnpm install

# Build package
pnpm build

# Watch mode (for development)
pnpm dev
```

## License

MIT

## Related Packages

- `@syntek/shared-auth` - Shared authentication logic (70-80% code reuse)
- `@syntek/shared` - Shared design system components
- `@syntek/mobile-auth` - React Native authentication UI

## Support

For issues and questions, please open an issue on GitHub.
