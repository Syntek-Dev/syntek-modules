# Syntek Modules - Modular Repository

## Project Overview

**Syntek Modules** is a modular monorepo containing reusable Django, React, React Native, and Rust modules for installation into other projects.

## ⚠️ CRITICAL: NO SPRINTS OR STORIES

**This project does NOT use sprints or user stories.** We use implementation plans instead.

- ❌ **DO NOT** create sprint files (`docs/SPRINTS/`, `SPRINT-*.md`)
- ❌ **DO NOT** create user story files (`docs/STORIES/`, `STORY-*.md`)
- ❌ **DO NOT** use MoSCoW prioritisation or story points
- ❌ **DO NOT** invoke `/syntek-dev-suite:sprint` or `/syntek-dev-suite:stories` agents
- ✅ **DO** create implementation plans (`docs/PLANS/PLAN-*.md`)
- ✅ **DO** track completion by updating plan checkboxes
- ✅ **DO** use the EnterPlanMode tool for planning work

**All agents must follow this convention. If an agent tries to create sprints/stories, stop it immediately.**

This is NOT a deployable application - these are **library modules** designed to be:

- Installed via uv or pip (Django apps)
- Installed via npm/pnpm (React/React Native packages)
- Included via Cargo (Rust crates)

## ⚠️ CRITICAL: Architectural Principles

### Django Backend is the Source of Truth

**MANDATORY PRINCIPLE:** Django backend is the **authoritative source** for all configuration, business logic, and data.

- ✅ **DO** fetch all configuration from Django via GraphQL
- ✅ **DO** implement business logic in Django
- ✅ **DO** use Django settings as single source of truth
- ❌ **DO NOT** hardcode configuration values in frontend
- ❌ **DO NOT** duplicate business logic in frontend
- ❌ **DO NOT** create separate configuration systems

**Example (Authentication Configuration):**

```typescript
// ❌ WRONG: Hardcoded configuration
export const PASSWORD_MIN_LENGTH = 12;
export const SESSION_TIMEOUT = 1800;

// ✅ CORRECT: Fetch from Django via GraphQL
const { config } = useAuthConfig(); // Fetches from Django SYNTEK_AUTH settings
const minLength = config.passwordMinLength; // Always matches backend
```

**Reference:** See `docs/ARCHITECTURE-REVIEW-SHARED-AUTH.md` for implementation details.

---

### Full Stack Layer Integration

**ALL layers must be used correctly and in harmony:**

#### Layer 1: Django Backend (Source of Truth)

- **Purpose:** Business logic, data models, configuration, validation rules
- **Technologies:** Django 6.0.2, Python 3.14, PostgreSQL 18.1
- **Responsibilities:**
  - Define all configuration in Django settings (e.g., `SYNTEK_AUTH`)
  - Implement all business logic and validation
  - Manage database models and migrations
  - Use Rust layer for encryption/hashing via PyO3
- **Examples:** Password validation rules, session timeouts, rate limits, feature flags

#### Layer 2: Rust Security Layer

- **Purpose:** High-performance encryption, hashing, security operations
- **Technologies:** Rust, PyO3 bindings to Django
- **Responsibilities:**
  - Argon2 password hashing
  - AES-256-GCM encryption/decryption
  - HMAC generation for constant-time lookups
  - Cryptographic operations (TOTP, WebAuthn)
- **Integration:** Called from Django via PyO3, **NOT directly from frontend**
- **Examples:** `hash_password()`, `encrypt_field()`, `constant_time_compare()`

#### Layer 3: GraphQL API (Communication Layer)

- **Purpose:** Expose Django backend to frontend via type-safe GraphQL API
- **Technologies:** Strawberry GraphQL 0.291.0
- **Responsibilities:**
  - Define GraphQL schema matching Django models
  - Expose configuration via queries (e.g., `authConfig`)
  - Handle mutations (register, login, update profile)
  - Enforce permissions and rate limiting
- **Integration:** Frontend communicates with Django **ONLY** through GraphQL
- **Examples:** `mutation { register }`, `query { authConfig }`, `mutation { updateProfile }`

#### Layer 4: Shared Frontend (Cross-Platform Code)

- **Purpose:** Maximum code reuse between web and mobile
- **Location:** `shared/` directory
- **Technologies:** TypeScript 5.9, React 19.2.1
- **Responsibilities:**
  - Business logic hooks (70-80% shared)
  - GraphQL operations (100% shared)
  - TypeScript types (100% shared)
  - Utilities and validators (100% shared)
  - Cross-platform UI components (70-80% shared)
- **Rule:** **Default to `shared/` first**, only use `web/` or `mobile/` for platform-specific code

**What goes in `shared/`:**

- ✅ GraphQL queries and mutations
- ✅ TypeScript types
- ✅ React hooks (useAuth, useMFA, usePasskey, etc.)
- ✅ Utilities (validators, formatters, crypto helpers)
- ✅ Cross-platform components (Button, Input, Modal, etc.)
- ✅ Design system tokens
- ✅ Constants (as fallbacks, fetching from GraphQL)

**What goes in `web/` or `mobile/`:**

- ✅ Platform-specific adapters (storage, biometrics, WebAuthn)
- ✅ Platform-specific UI composition (Next.js pages, React Native screens)
- ✅ Platform-specific navigation (Next.js router, React Native navigation)
- ✅ Platform-specific HOCs and providers

#### Layer 5: Web Frontend (Next.js/React)

- **Purpose:** Web-specific implementation
- **Location:** `web/packages/`
- **Technologies:** Next.js 16.1.16, React 19.2.1, TypeScript 5.9, Tailwind v4
- **Responsibilities:**
  - Import from `shared/` (70-80% of code)
  - Web-specific adapters (httpOnly cookies, localStorage)
  - Next.js pages and routing
  - Tailwind v4 styling
  - Server-side rendering (SSR) when needed

#### Layer 6: Mobile Frontend (React Native)

- **Purpose:** Mobile-specific implementation
- **Location:** `mobile/packages/`
- **Technologies:** React Native 0.83.x, TypeScript 5.9, NativeWind 4
- **Responsibilities:**
  - Import from `shared/` (70-80% of code)
  - Mobile-specific adapters (SecureStore, biometrics)
  - React Native screens and navigation
  - NativeWind 4 styling (Tailwind classes for mobile)
  - Native module integration (iOS/Android)

---

### Code Sharing Strategy

**CRITICAL:** Maximize code reuse by defaulting to `shared/` for all frontend code.

**Code Sharing Hierarchy:**

1. **100% Shared (Always in `shared/`):**
   - TypeScript types
   - GraphQL operations (queries, mutations, fragments)
   - Constants (as fallbacks, fetch from GraphQL)
   - Utilities (validators, formatters, crypto)

2. **70-80% Shared (Mostly in `shared/`, adapters in `web/`/`mobile/`):**
   - Business logic hooks (useAuth, useMFA, usePasskey, etc.)
   - UI components (Button, Input, Modal, etc.)
   - Form validation

3. **Platform-Specific (In `web/` or `mobile/` only):**
   - Platform adapters (storage, biometrics, WebAuthn)
   - Routing and navigation
   - Platform-specific UI composition (pages, screens)
   - Platform-specific native integrations

**Example: Authentication Hook**

```typescript
// ✅ CORRECT: Shared business logic
// Location: shared/auth/hooks/useAuth.ts
export function useAuth() {
  const { config } = useAuthConfig(); // Fetches from Django
  const [login] = useMutation(LOGIN_MUTATION);

  const handleLogin = async (email: string, password: string) => {
    // Business logic (100% shared)
    const { data } = await login({ variables: { email, password } });

    // Store token via platform adapter
    await secureStorage.setItem("token", data.login.token);
  };

  return { handleLogin };
}

// Platform-specific adapter
// Location: shared/auth/hooks/adapters/useSecureStorage.web.ts
export const secureStorage = {
  async setItem(key: string, value: string) {
    // Web: httpOnly cookies (handled by server)
    document.cookie = `${key}=${value}; Secure; HttpOnly`;
  },
};

// Location: shared/auth/hooks/adapters/useSecureStorage.native.ts
export const secureStorage = {
  async setItem(key: string, value: string) {
    // Mobile: SecureStore
    await SecureStore.setItemAsync(key, value);
  },
};
```

---

### Frontend Configuration Rules

**CRITICAL:** Nothing in the frontend should be hardcoded. All configuration comes from Django via GraphQL.

#### ✅ DO: Fetch Configuration from Django

```typescript
// Fetch auth configuration from Django SYNTEK_AUTH settings
const { config } = useAuthConfig();

// Use backend configuration
if (password.length < config.passwordMinLength) {
  return `Password must be at least ${config.passwordMinLength} characters`;
}

if (config.uppercaseRequired && !/[A-Z]/.test(password)) {
  return "Password must contain an uppercase letter";
}
```

#### ❌ DO NOT: Hardcode Configuration

```typescript
// ❌ WRONG: Hardcoded configuration
const PASSWORD_MIN_LENGTH = 12;
const UPPERCASE_REQUIRED = true;

if (password.length < PASSWORD_MIN_LENGTH) {
  return "Password must be at least 12 characters";
}
```

#### Configuration Fetching Pattern

1. **Add configuration to Django settings:**

   ```python
   # backend/settings.py
   SYNTEK_AUTH = {
       'PASSWORD_LENGTH': 12,
       'UPPERCASE_REQUIRED': True,
       'SESSION_TIMEOUT': 1800,
   }
   ```

2. **Expose via GraphQL query:**

   ```python
   # graphql/auth/queries/config.py
   @strawberry.field
   def auth_config(self, info: Info) -> AuthConfigType:
       config = settings.SYNTEK_AUTH
       return AuthConfigType(
           password_min_length=config['PASSWORD_LENGTH'],
           uppercase_required=config['UPPERCASE_REQUIRED'],
       )
   ```

3. **Fetch in frontend via hook:**

   ```typescript
   // shared/auth/hooks/useAuthConfig.ts
   export function useAuthConfig() {
     const { data } = useQuery(GET_AUTH_CONFIG);
     return { config: data.authConfig };
   }
   ```

4. **Use in components:**

   ```typescript
   const { config } = useAuthConfig();
   // config.passwordMinLength always matches Django backend
   ```

---

### Styling Strategy

**Web:** Tailwind CSS v4 (CSS-first approach)
**Mobile:** NativeWind 4 (Tailwind classes for React Native)
**Shared:** Design tokens and theme configuration

#### Design System Structure

```
shared/design-system/
├── tokens/              # Design tokens (colors, spacing, typography)
├── components/          # Primitive components (Button, Input, etc.)
├── theme.css            # Tailwind v4 CSS variables
├── theme.ts             # Unified theme object
├── tailwind.config.ts   # Tailwind v4 config (web)
└── nativewind.config.ts # NativeWind config (mobile)
```

#### Tailwind v4 (Web)

```css
/* shared/design-system/theme.css */
@theme {
  --color-primary: #3b82f6;
  --color-danger: #ef4444;
  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
}
```

```typescript
// web/packages/ui-auth/src/components/LoginForm.tsx
<button className="bg-primary text-white px-4 py-2 rounded">
  Login
</button>
```

#### NativeWind 4 (Mobile)

```typescript
// mobile/packages/mobile-auth/src/screens/LoginScreen.tsx
<Pressable className="bg-primary px-4 py-2 rounded">
  <Text className="text-white">Login</Text>
</Pressable>
```

**Same Tailwind classes work on both web and mobile!**

---

### Summary: Architectural Checklist

When implementing any feature, ensure:

- [ ] ✅ Django backend defines all configuration in settings
- [ ] ✅ GraphQL exposes configuration via queries
- [ ] ✅ Frontend fetches configuration via `useConfig()` hooks
- [ ] ✅ No hardcoded configuration in frontend
- [ ] ✅ Rust layer used for encryption/hashing (via Django)
- [ ] ✅ Business logic in Django, not frontend
- [ ] ✅ Maximum code sharing via `shared/` directory
- [ ] ✅ TypeScript types match GraphQL schema
- [ ] ✅ Tailwind v4 (web) and NativeWind 4 (mobile) for styling
- [ ] ✅ All layers working in harmony

**Reference Documents:**

- `docs/ARCHITECTURE-REVIEW-SHARED-AUTH.md` - Configuration integration
- `docs/ARCHITECTURE-FIX-IMPLEMENTATION-SUMMARY.md` - Implementation examples
- `docs/REVIEWS/REVIEW-PHASE-3-4-AUTHENTICATION-UI-ARCHITECTURE.md` - Code sharing strategy

## Language and Formatting

Please use UK English for all documentation and user-facing content. Dates must be formatted as dd.mm.yyyy.

Keep coding language identifiers (keywords, variable names, etc.) in American English where required by the language specification.

## Tech Stack

### Backend (Django)

- Django 6.0.2 (Python 3.14), GraphQL (Strawberry 0.291.0)
- PostgreSQL 18.1, uv package manager
- Structure: Django apps packaged as pip/uv installables

### Web (Next.js)

- Next.js 16.1.16, React 19.2.1, TypeScript 5.9
- Node.js 24.13, Tailwind 4.1
- Structure: NPM packages

### Mobile (React Native)

- React Native 0.83.x, TypeScript 5.9, NativeWind 4
- Structure: NPM packages

### Shared UI

- Cross-platform components for web and mobile

### Security & Infrastructure

- Rust: Encryption/decryption via PyO3 bindings
- OpenBao: Secrets management
- GlitchTip: External logging
- Cloudinary: Media storage
- Rust CLI: Package installation tool that enables bundled installation across backend, web, mobile, shared, GraphQL, and Rust security modules (e.g., all auth-related packages can be installed together)

## Repository Structure

```
syntek-modules/
├── backend/                    # Django modules (security bundles + features)
│   ├── security-core/          # Middleware, headers, CORS, CSRF, rate limiting
│   ├── security-auth/          # Auth, sessions, cookies, JWT, API keys
│   ├── security-input/         # Validation, SQL injection prevention
│   ├── security-network/       # IP filtering, request signing, OpenBao
│   └── [27+ feature modules]   # profiles, media, payments, etc.
│
├── web/packages/               # Next.js/React modules
│   ├── security-core/          # Client-side security
│   ├── security-auth/          # Client auth & sessions
│   └── ui-*/                   # UI components
│
├── mobile/packages/            # React Native modules
│   ├── security-core/          # Mobile security (cert pinning, secure storage)
│   ├── security-auth/          # Mobile auth & biometrics
│   └── mobile-*/               # Mobile features
│
├── shared/                     # Cross-platform components, hooks, utils
├── rust/                       # Encryption, hashing, LLM gateway, PyO3 bindings
├── graphql/                    # GraphQL modules (core, auth, audit, compliance)
│   ├── core/                   # Security foundation (errors, permissions, middleware)
│   ├── auth/                   # Authentication & sessions GraphQL layer
│   ├── audit/                  # Audit logging queries
│   └── compliance/             # GDPR & legal document GraphQL operations
|-- cli/                        # All packages can be installed by Rust CLI
├── examples/                   # Example integrations
├── tests/                      # Integration tests
└── docs/                       # Architecture & security docs
```

## Module Categories

### Security Bundles (Backend)

- **security-core**: HTTP security (middleware, headers, CORS, CSRF, rate limiting, cache)
- **security-auth**: Authentication & sessions (MFA, TOTP, JWT, API keys)
- **security-input**: Input protection (validation, SQL injection prevention)
- **security-network**: Network security (IP filtering, OpenBao secrets)

### Security Bundles (Web/Mobile)

- Similar structure for client-side security

### Feature Modules (Backend)

groups, profiles, media, logging, accounting, ai_integration, email_marketing, payments, notifications, search, audit, forms_surveys, contact, bookings, comments_ratings, analytics, reporting, uploads, feature_flags, webhooks, i18n, cms_primitives

### UI Modules (Web/Mobile)

Authentication, profiles, media, notifications, search, forms, comments, analytics, bookings, payments, webhooks, feature flags

### GraphQL Modules

- **syntek-graphql-core**: Security foundation - errors, permissions, auth middleware, query limiting
- **syntek-graphql-auth**: Authentication & sessions - register, login, JWT, TOTP/2FA
- **syntek-graphql-audit**: Audit logging - user/org audit logs, session queries
- **syntek-graphql-compliance**: GDPR & legal - data export, consent, legal documents

## Installation

### Django Modules

```bash
# Install security bundles (recommended)
uv pip install syntek-security-core
uv pip install syntek-security-auth

# Or individual modules
uv pip install syntek-authentication
uv pip install syntek-profiles
```

### Web/Mobile Modules

```json
{
  "dependencies": {
    "@syntek/security-core": "^1.0.0",
    "@syntek/ui-auth": "^1.0.0",
    "@syntek/mobile-auth": "^1.0.0"
  }
}
```

### Rust Modules

```toml
[dependencies]
syntek-encryption = { path = "../syntek-modules/rust/encryption" }
```

### GraphQL Modules

```bash
# Minimal (Auth only)
uv pip install syntek-graphql-core syntek-graphql-auth

# Auth + Audit
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-audit

# Full (All modules)
uv pip install syntek-graphql-core \
               syntek-graphql-auth \
               syntek-graphql-audit \
               syntek-graphql-compliance
```

**Module Descriptions:**

- `syntek-graphql-core` - Security foundation (errors, permissions, middleware)
- `syntek-graphql-auth` - Authentication, sessions, JWT, TOTP/2FA
- `syntek-graphql-audit` - Audit log queries, session management
- `syntek-graphql-compliance` - GDPR operations, legal document management

**See:** `docs/GRAPHQL-INSTALLATION.md` for detailed installation guide

## Configuration

### Django Settings

```python
INSTALLED_APPS = [
    'syntek_security_core',      # Auto-includes all sub-modules
    'syntek_security_auth',
    'syntek_profiles',
    # ... other modules
]

SYNTEK_SECURITY_CORE = {
    'RATE_LIMITING': {'BACKEND': 'redis', 'DEFAULT_RATE': '100/hour'},
    'CSRF': {'TOKEN_ROTATION': True},
}

SYNTEK_SECURITY_AUTH = {
    'AUTHENTICATION': {'TOTP_REQUIRED': True},
    'JWT': {'ACCESS_TOKEN_LIFETIME': 900},
}
```

### GraphQL Schema

```python
# myproject/schema.py
import strawberry
from syntek_graphql_core.security import (
    QueryDepthLimitExtension,
    QueryComplexityLimitExtension,
    IntrospectionControlExtension,
)
from syntek_graphql_auth.mutations.auth import AuthMutations
from syntek_graphql_auth.queries.user import UserQueries

@strawberry.type
class Query(UserQueries):
    pass

@strawberry.type
class Mutation(AuthMutations):
    pass

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimitExtension(max_depth=10),
        QueryComplexityLimitExtension(max_complexity=1000),
        IntrospectionControlExtension(),
    ],
)
```

```python
# urls.py
from django.urls import path
from strawberry.django.views import AsyncGraphQLView
from myproject.schema import schema

urlpatterns = [
    path('graphql/', AsyncGraphQLView.as_view(schema=schema)),
]
```

**See:** `docs/GRAPHQL-SCHEMA-COMPOSITION.md` for schema composition examples

## Security Compliance

**ALL code must comply with:**

- OWASP Top 10
- NIST Cybersecurity Framework
- NCSC Guidelines
- GDPR (EU/UK/Global)
- CIS Benchmarks
- SOC 2

See `.claude/SECURITY-COMPLIANCE.md` for detailed requirements.

## Development

### Using Rust CLI

```bash
# Install CLI
cd rust/project-cli && cargo install --path .

# Commands
syntek dev           # Start development
syntek test          # Run tests
syntek lint --fix    # Lint and fix
syntek format        # Format code
syntek build         # Build for production
```

### Lock Files

- Python: `uv.lock` (committed)
- Rust: `Cargo.lock` (committed)
- Node: `pnpm-lock.yaml` (gitignored for libraries)

## Key Principles

1. **Modularity** - Each module is independently installable
2. **No Coupling** - Modules don't depend on each other unless explicitly declared
3. **Version Control** - Semantic versioning for each module
4. **Documentation** - Every module MUST have comprehensive README.md
5. **Security** - All sensitive data encrypted via Rust layer
6. **Testing** - Comprehensive tests for each module

## Agent Guidelines

**CRITICAL:** All agents MUST follow the architectural principles defined above. Review the "Architectural Principles" section before starting any work.

**📋 Quick Reference:** See `.claude/QUICK-REFERENCE.md` for a concise one-page guide to all architectural rules.

**Key Requirements:**

- ✅ Django backend is the source of truth for all configuration
- ✅ Frontend fetches configuration from Django via GraphQL (no hardcoded values)
- ✅ Default to `shared/` for all frontend code (70-80% code reuse)
- ✅ Use all layers correctly: Django → GraphQL → Shared → Web/Mobile
- ✅ Rust layer for encryption/hashing (via Django PyO3, not direct frontend access)
- ✅ Tailwind v4 (web) and NativeWind 4 (mobile) for styling

### When Creating/Modifying Modules

1. **Follow architectural principles** - Django is source of truth, fetch config via GraphQL, maximize `shared/` code reuse
2. **Understand bundling** - Security modules are bundled but can be installed individually
3. **Keep modules independent** - Avoid cross-dependencies
4. **Write comprehensive README.md FIRST** - Include installation, configuration, usage examples, API reference
5. **Provide examples** - Show real-world usage (Django → GraphQL → Frontend flow)
6. **Test thoroughly** - Unit + integration tests for all layers
7. **Version properly** - Semantic versioning
8. **Security first** - Use Rust encryption layer for sensitive data (via Django)

### Security Checklist (ALL code)

- [ ] Input validation and sanitization
- [ ] Parameterized queries (no SQL injection)
- [ ] Strong authentication (MFA support)
- [ ] Authorization checks on all operations
- [ ] Encryption for sensitive data (at rest and in transit via Rust layer)
- [ ] Security logging (no sensitive data in logs)
- [ ] Error messages don't leak information
- [ ] Rate limiting implemented
- [ ] CSRF/XSS protection
- [ ] Security headers configured
- [ ] Dependencies scanned for vulnerabilities
- [ ] GDPR data subject rights supported

### Architectural Compliance Checklist (ALL frontend code)

- [ ] Configuration fetched from Django via GraphQL (no hardcoded values)
- [ ] Code in `shared/` directory by default (only platform-specific in `web/`/`mobile/`)
- [ ] TypeScript types match GraphQL schema
- [ ] Business logic hooks in `shared/auth/hooks/`
- [ ] GraphQL operations in `shared/auth/graphql/`
- [ ] Utilities in `shared/auth/utils/`
- [ ] Components in `shared/design-system/components/` or `shared/auth/components/`
- [ ] Platform adapters for storage/biometrics in `shared/auth/hooks/adapters/`
- [ ] Rust encryption called via Django backend (not directly from frontend)
- [ ] Tailwind v4 classes for web, NativeWind 4 for mobile

### Documentation & Code Quality Requirements

**ALL code files MUST have docstrings and comments in their language-specific format:**

#### Python (Django)

```python
"""Module docstring at top of file.

Explains what the module does, what it contains, and how to use it.
"""

def function_name(arg: str) -> bool:
    """Function docstring explaining purpose.

    Args:
        arg: Description of argument

    Returns:
        Description of return value
    """
    # Inline comments for complex logic
    pass
```

#### TypeScript/JavaScript

```typescript
/**
 * Module docstring at top of file.
 *
 * Explains what the module does, exports, and usage examples.
 */

/**
 * Function docstring explaining purpose.
 *
 * @param arg - Description of argument
 * @returns Description of return value
 */
function functionName(arg: string): boolean {
  // Inline comments for complex logic
  return true;
}
```

#### Rust

```rust
//! Module-level documentation at top of file.
//!
//! Explains what the module does, what it contains, and usage examples.

/// Function documentation explaining purpose.
///
/// # Arguments
///
/// * `arg` - Description of argument
///
/// # Returns
///
/// * Description of return value
pub fn function_name(arg: &str) -> bool {
    // Inline comments for complex logic
    true
}
```

**Exceptions:** `package.json`, lock files (`uv.lock`, `pnpm-lock.yaml`, `Cargo.lock`) do not require comments.

#### File Length Limits

**CRITICAL:** No coding file should exceed **750-800 lines**.

- **Coding files** (`.py`, `.ts`, `.tsx`, `.rs`, `.js`, `.jsx`): **MAX 800 lines**
- **Documentation files** (`.md`): No limit (can be longer for comprehensive docs)
- **Package files** (`package.json`, `pyproject.toml`, `Cargo.toml`): No limit (can be longer for dependencies)

**If a file approaches 750 lines:** Refactor into modules/smaller files.

### Script Organization

**ALL script files MUST be written in Rust** and placed in `rust/project-cli/`:

- **Location:** `rust/project-cli/src/`
- **Structure:** Follow modular architecture:
  - `main.rs` - CLI definition and dispatch
  - `commands/<command>.rs` - Individual command implementations
  - `utils/<utility>.rs` - Shared helper functions

**Example:**

```rust
// rust/project-cli/src/commands/my_command.rs
//! My command documentation
//!
//! Explains what this command does and how to use it.

use crate::utils::exec;

/// Run the command
pub fn run(args: Args) -> anyhow::Result<()> {
    // Implementation
    Ok(())
}
```

**Call commands in main.rs:**

```rust
// rust/project-cli/src/main.rs
Commands::MyCommand { args } => commands::my_command::run(args),
```

**Exception:** Only `install-cli.sh` is allowed as a bash script (for bootstrapping the CLI).

### File Locations

- Backend bundles: `backend/security-<bundle>/`
- Backend modules: `backend/<module>/`
- Web bundles: `web/packages/security-<bundle>/`
- Web UI: `web/packages/ui-<component>/`
- Mobile bundles: `mobile/packages/security-<bundle>/`
- Mobile features: `mobile/packages/mobile-<feature>/`
- Shared: `shared/{components,hooks,utils}/`
- Rust: `rust/<crate>/`
- **Scripts: `rust/project-cli/src/{commands,utils}/`**
- GraphQL: `graphql/{middleware,schema}/`

## README Requirements

Every module MUST include:

1. Overview
2. Features
3. Installation
4. Configuration (all options in table format)
5. Usage Examples
6. API Reference
7. Security Considerations
8. Testing
9. Development

See `backend/security-auth/authentication/README.md` for reference.

## Related Documentation

- `.claude/SYNTEK-GUIDE.md` - Agent command reference
- `.claude/SECURITY-COMPLIANCE.md` - MANDATORY compliance requirements
- `.claude/SYNTEK-RUST-SECURITY-GUIDE.md` - Rust security guidelines
- `docs/security/` - OWASP, NIST, NCSC, GDPR, CIS documentation
- Individual module READMEs - Module-specific docs
