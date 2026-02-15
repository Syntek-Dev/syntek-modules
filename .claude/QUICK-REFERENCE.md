# Syntek Modules - Agent Quick Reference Card

**Version:** 1.0 | **Date:** 15.02.2026

---

## 🎯 Golden Rules (NEVER BREAK THESE)

1. **Django is the source of truth** - All configuration lives in Django settings
2. **Frontend fetches from GraphQL** - NO hardcoded configuration values
3. **Default to `shared/` first** - 70-80% of frontend code goes here
4. **All layers must integrate** - Django → GraphQL → Shared → Web/Mobile
5. **Rust via Django only** - NO direct Rust calls from frontend

---

## 🏗️ Architecture Layers (How Everything Connects)

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: DJANGO BACKEND (Source of Truth)                  │
│ ├─ Configuration (SYNTEK_AUTH settings)                     │
│ ├─ Business logic & validation                              │
│ ├─ Database models (PostgreSQL)                             │
│ └─ Calls Rust via PyO3 ──┐                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────────┐
│ Layer 2: RUST SECURITY    │                                  │
│ ├─ Argon2 password hashing                                  │
│ ├─ AES-256-GCM encryption                                   │
│ ├─ HMAC constant-time operations                            │
│ └─ PyO3 bindings to Django                                  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ Layer 3: GRAPHQL API (Communication Only)                   │
│ ├─ Queries (authConfig, currentUser, etc.)                  │
│ ├─ Mutations (register, login, updateProfile, etc.)         │
│ ├─ Fragments (UserFields, SessionFields, etc.)              │
│ └─ Strawberry GraphQL 0.291.0                               │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ Layer 4: SHARED FRONTEND (70-80% of code)                   │
│ ├─ Types (100% shared)                                      │
│ ├─ GraphQL operations (100% shared)                         │
│ ├─ Hooks (70-80% shared, platform adapters)                 │
│ ├─ Components (70-80% shared)                               │
│ ├─ Utils (100% shared)                                      │
│ └─ TypeScript 5.9 + React 19.2.1                            │
└──────────────────────────────────────────────────────────────┘
           ↓                              ↓
┌─────────────────────────┐  ┌────────────────────────────────┐
│ Layer 5: WEB            │  │ Layer 6: MOBILE                │
│ ├─ Next.js 16.1.16      │  │ ├─ React Native 0.83.x         │
│ ├─ Tailwind v4         │  │ ├─ NativeWind 4                │
│ ├─ Platform adapters    │  │ ├─ Platform adapters           │
│ └─ 20-30% web code      │  │ └─ 20-30% mobile code          │
└─────────────────────────┘  └────────────────────────────────┘
```

---

## 📁 Where Does Code Go? (Decision Tree)

### Is it configuration or business logic?

→ **YES**: Django backend (settings.py)

### Is it TypeScript types?

→ **YES**: `shared/{module}/types/`

### Is it a GraphQL operation?

→ **YES**: `shared/{module}/graphql/`

### Is it a utility function?

→ **YES**: `shared/{module}/utils/`

### Is it a React hook?

→ **Shared logic**: `shared/{module}/hooks/`
→ **Platform adapter**: `shared/{module}/hooks/adapters/*.{web|native}.ts`

### Is it a UI component?

→ **Cross-platform**: `shared/design-system/components/`
→ **Feature-specific**: `shared/{module}/components/`
→ **Platform-specific UI**: `web/packages/` or `mobile/packages/`

### Is it encryption/hashing?

→ **Backend only**: `rust/{crate}/` (called via Django PyO3)

### Is it a page/screen?

→ **Web page**: `web/packages/{package}/src/pages/`
→ **Mobile screen**: `mobile/packages/{package}/src/screens/`

---

## ✅ DO This (Good Patterns)

### Configuration

```typescript
// ✅ Fetch from Django via GraphQL
const { config } = useAuthConfig();
if (password.length < config.passwordMinLength) {
  // Error
}
```

### Code Location

```
✅ shared/auth/types/user.ts          (100% shared)
✅ shared/auth/graphql/queries/auth.ts (100% shared)
✅ shared/auth/hooks/useAuth.ts        (70% shared logic)
✅ shared/auth/hooks/adapters/useSecureStorage.web.ts (platform adapter)
✅ shared/design-system/components/Button.tsx (cross-platform)
```

### Layer Integration

```
✅ Django defines SYNTEK_AUTH settings
✅ GraphQL exposes authConfig query
✅ Shared hook fetches: useAuthConfig()
✅ Components use: const { config } = useAuthConfig()
```

### Styling

```typescript
// ✅ Same Tailwind classes on web and mobile
// Web
<button className="bg-primary px-4 py-2 rounded">Login</button>

// Mobile (NativeWind)
<Pressable className="bg-primary px-4 py-2 rounded">
  <Text className="text-white">Login</Text>
</Pressable>
```

---

## ❌ DON'T Do This (Anti-Patterns)

### Configuration

```typescript
// ❌ Hardcoded configuration
export const PASSWORD_MIN_LENGTH = 12;
export const SESSION_TIMEOUT = 1800;
```

### Code Location

```
❌ web/packages/ui-auth/types/user.ts           (should be shared)
❌ mobile/packages/mobile-auth/utils/validators.ts (should be shared)
❌ web/packages/ui-auth/graphql/queries.ts      (should be shared)
❌ Duplicating code between web and mobile
```

### Layer Integration

```
❌ Frontend calling Rust directly
❌ Frontend implementing business logic
❌ Frontend creating separate configuration
❌ Skipping GraphQL layer
```

### Styling

```typescript
// ❌ Platform-specific styling libraries
import styled from "styled-components"; // Wrong for web
import { StyleSheet } from "react-native"; // Wrong for mobile

// ✅ Use Tailwind v4 / NativeWind 4 instead
```

---

## 🔧 Technology Stack At-a-Glance

| Layer        | Technology         | Version | Purpose                         |
| ------------ | ------------------ | ------- | ------------------------------- |
| **Backend**  | Django             | 6.0.2   | Source of truth, business logic |
|              | Python             | 3.14    | Backend language                |
|              | PostgreSQL         | 18.1    | Database                        |
|              | uv                 | latest  | Package manager                 |
| **Security** | Rust               | latest  | Encryption, hashing (PyO3)      |
| **API**      | Strawberry GraphQL | 0.291.0 | Communication layer             |
| **Shared**   | TypeScript         | 5.9     | Type safety                     |
|              | React              | 19.2.1  | UI library (shared)             |
| **Web**      | Next.js            | 16.1.16 | Web framework                   |
|              | Tailwind CSS       | 4.1     | Web styling                     |
|              | Node.js            | 24.13   | Runtime                         |
| **Mobile**   | React Native       | 0.83.x  | Mobile framework                |
|              | NativeWind         | 4.x     | Mobile styling (Tailwind)       |
| **Tools**    | pnpm               | latest  | Node package manager            |

---

## 🎨 Styling Quick Reference

### Design Tokens (Shared)

```typescript
// shared/design-system/tokens/colors.ts
export const colors = {
  primary: "#3b82f6",
  danger: "#ef4444",
  // ...
};
```

### Tailwind v4 (Web)

```css
/* shared/design-system/theme.css */
@theme {
  --color-primary: #3b82f6;
  --spacing-4: 1rem;
}
```

### Components (Cross-Platform)

```typescript
// shared/design-system/components/Button.tsx
export function Button({ children, variant = 'primary' }) {
  return (
    <Pressable className={`px-4 py-2 rounded bg-${variant}`}>
      <Text className="text-white">{children}</Text>
    </Pressable>
  );
}
```

**Works on both web and mobile!**

---

## 🔍 Configuration Pattern (Step-by-Step)

### Step 1: Define in Django

```python
# backend/settings.py
SYNTEK_AUTH = {
    'PASSWORD_LENGTH': 12,
    'UPPERCASE_REQUIRED': True,
    'SESSION_TIMEOUT': 1800,
}
```

### Step 2: Expose via GraphQL

```python
# graphql/auth/queries/config.py
@strawberry.field
def auth_config(self, info: Info) -> AuthConfigType:
    config = settings.SYNTEK_AUTH
    return AuthConfigType(
        password_min_length=config['PASSWORD_LENGTH'],
        uppercase_required=config['UPPERCASE_REQUIRED'],
        session_timeout=config['SESSION_TIMEOUT'],
    )
```

### Step 3: Create TypeScript Type

```typescript
// shared/auth/types/config.ts
export interface AuthConfig {
  passwordMinLength: number;
  uppercaseRequired: boolean;
  sessionTimeout: number;
}
```

### Step 4: Create GraphQL Query

```typescript
// shared/auth/graphql/queries/config.ts
export const GET_AUTH_CONFIG = gql`
  query GetAuthConfig {
    authConfig {
      passwordMinLength
      uppercaseRequired
      sessionTimeout
    }
  }
`;
```

### Step 5: Create React Hook

```typescript
// shared/auth/hooks/useAuthConfig.ts
export function useAuthConfig() {
  const { data } = useQuery(GET_AUTH_CONFIG);
  return { config: data?.authConfig };
}
```

### Step 6: Use in Component

```typescript
// web/packages/ui-auth/src/components/PasswordInput.tsx
const { config } = useAuthConfig();
if (password.length < config.passwordMinLength) {
  return "Too short";
}
```

---

## 📋 Pre-Implementation Checklist

Before writing ANY code, verify:

- [ ] ✅ Is configuration in Django settings?
- [ ] ✅ Is GraphQL query/mutation defined?
- [ ] ✅ Are TypeScript types in `shared/`?
- [ ] ✅ Is business logic in Django (not frontend)?
- [ ] ✅ Is code in `shared/` by default?
- [ ] ✅ Are platform adapters needed?
- [ ] ✅ Is Rust called via Django (not direct)?
- [ ] ✅ Is Tailwind v4/NativeWind 4 used for styling?

---

## 🚨 Common Mistakes (Watch Out!)

### Mistake #1: Hardcoded Configuration

```typescript
❌ const SESSION_TIMEOUT = 1800;
✅ const { config } = useAuthConfig();
   const timeout = config.sessionTimeout;
```

### Mistake #2: Duplicated Code

```typescript
❌ web/packages/ui-auth/hooks/useAuth.ts
❌ mobile/packages/mobile-auth/hooks/useAuth.ts
✅ shared/auth/hooks/useAuth.ts (one shared hook)
```

### Mistake #3: Frontend Business Logic

```typescript
❌ // Frontend password validation
   if (password.length < 12 && /[A-Z]/.test(password)) {
     // Complex validation logic
   }

✅ // Backend validation via GraphQL
   const { data } = useMutation(REGISTER, {
     variables: { password }
   });
   // Django validates, frontend displays errors
```

### Mistake #4: Direct Rust Calls

```typescript
❌ import { hashPassword } from 'rust-crypto';
   const hash = hashPassword(password);

✅ // Rust called via Django backend
   const { data } = useMutation(REGISTER, {
     variables: { password } // Django calls Rust
   });
```

### Mistake #5: Platform-Specific Styling

```typescript
❌ import styled from 'styled-components';
❌ const styles = StyleSheet.create({ ... });

✅ <button className="bg-primary px-4 py-2 rounded">
     Login
   </button>
```

---

## 🔗 Quick Links

- **Main Guide:** `.claude/CLAUDE.md`
- **Security:** `.claude/SECURITY-COMPLIANCE.md`
- **Architecture Review:** `docs/ARCHITECTURE-REVIEW-SHARED-AUTH.md`
- **Implementation Summary:** `docs/ARCHITECTURE-FIX-IMPLEMENTATION-SUMMARY.md`
- **Phase 3-4 Review:** `docs/REVIEWS/REVIEW-PHASE-3-4-AUTHENTICATION-UI-ARCHITECTURE.md`

---

## 💡 When In Doubt

1. **Check Django first** - Is it in Django settings?
2. **Check GraphQL** - Is there a query for this?
3. **Check `shared/`** - Can this be shared?
4. **Check examples** - Look at existing auth implementation
5. **Ask user** - When architectural decision needed

---

## 📊 Code Sharing Target Metrics

| Code Type          | Target          | Location                                            |
| ------------------ | --------------- | --------------------------------------------------- |
| TypeScript types   | 100% shared     | `shared/{module}/types/`                            |
| GraphQL operations | 100% shared     | `shared/{module}/graphql/`                          |
| Utilities          | 100% shared     | `shared/{module}/utils/`                            |
| React hooks        | 70-80% shared   | `shared/{module}/hooks/` + adapters                 |
| UI components      | 70-80% shared   | `shared/design-system/components/`                  |
| Platform adapters  | 20-30% platform | `shared/{module}/hooks/adapters/*.{web\|native}.ts` |
| Pages/Screens      | 0% shared       | `web/` or `mobile/` only                            |

**If you're below these targets, refactor to increase sharing!**

---

## ✅ Success Criteria

Your code is correct when:

1. ✅ Django settings are the only configuration source
2. ✅ GraphQL is the only communication layer
3. ✅ `shared/` contains 70-80% of frontend code
4. ✅ TypeScript types match GraphQL schema exactly
5. ✅ Rust is only called via Django (PyO3)
6. ✅ Tailwind v4 (web) and NativeWind 4 (mobile) are used
7. ✅ Zero hardcoded configuration values
8. ✅ Zero duplicate code between web and mobile
9. ✅ All layers integrate correctly
10. ✅ Code passes architectural compliance checklist

---

**Remember:** Django is the source of truth. GraphQL is the bridge. Shared is the default. All layers must integrate.

**Last Updated:** 15.02.2026 | **Version:** 1.0
