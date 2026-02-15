# @syntek/ui-auth - Quick Reference

## Components

### Authentication Forms

```tsx
import { RegistrationForm, LoginForm } from '@syntek/ui-auth';

<RegistrationForm onSubmit={handleRegister} />
<LoginForm onSubmit={handleLogin} onPasskeyLogin={handlePasskey} />
```

### Social Authentication

```tsx
import { SocialLoginButtons, SocialAccountsList } from '@syntek/ui-auth';

<SocialLoginButtons providers={['google', 'github']} />
<SocialAccountsList accounts={accounts} onUnlink={handleUnlink} />
```

### Session Management

```tsx
import { AutoLogoutWarning, SessionActivityTracker, RememberMeCheckbox } from '@syntek/ui-auth';

<AutoLogoutWarning secondsRemaining={300} onExtendSession={extend} />
<SessionActivityTracker onActivity={handleActivity} />
<RememberMeCheckbox checked={rememberMe} onChange={setRememberMe} />
```

### CAPTCHA

```tsx
import { ReCaptcha, HCaptcha } from '@syntek/ui-auth';

<ReCaptcha siteKey="..." version="v3" onVerify={setToken} />
<HCaptcha siteKey="..." onVerify={setToken} />
```

## Hooks

```tsx
import { useAuth, useAuthConfig } from '@syntek/ui-auth';

const { config, login, logout } = useAuth();
const { config, loading } = useAuthConfig();
```

## Pages

```tsx
import { LoginPage, RegisterPage } from '@syntek/ui-auth/pages';

<LoginPage captchaEnabled socialLoginEnabled passkeyEnabled />
<RegisterPage captchaEnabled />
```

## HOCs

```tsx
import { withAuth } from '@syntek/ui-auth';

const Protected = withAuth(MyComponent, { redirectTo: '/auth/login' });
```

## Context

```tsx
import { AuthProvider } from '@syntek/ui-auth';

<AuthProvider>
  <App />
</AuthProvider>
```

## Shared Imports

All shared types, hooks, GraphQL, and utilities:

```tsx
// Types
import type { User, AuthConfig, Session } from '@syntek/shared-auth/types';

// GraphQL
import { LOGIN_MUTATION, REGISTER_MUTATION } from '@syntek/shared-auth/graphql/mutations';
import { ME_QUERY, AUTH_CONFIG_QUERY } from '@syntek/shared-auth/graphql/queries';

// Utilities
import { validateEmail, validatePassword } from '@syntek/shared-auth/utils/validators';
import { sanitizeInput } from '@syntek/shared-auth/utils';

// Design System
import { Button, Input, Checkbox, Alert } from '@syntek/shared/design-system/components';
```
