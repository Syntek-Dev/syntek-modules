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

### When Creating/Modifying Modules

1. **Understand bundling** - Security modules are bundled but can be installed individually
2. **Keep modules independent** - Avoid cross-dependencies
3. **Write comprehensive README.md FIRST** - Include installation, configuration, usage examples, API reference
4. **Provide examples** - Show real-world usage
5. **Test thoroughly** - Unit + integration tests
6. **Version properly** - Semantic versioning
7. **Security first** - Use Rust encryption layer for sensitive data

### Security Checklist (ALL code)

- [ ] Input validation and sanitization
- [ ] Parameterized queries (no SQL injection)
- [ ] Strong authentication (MFA support)
- [ ] Authorization checks on all operations
- [ ] Encryption for sensitive data (at rest and in transit)
- [ ] Security logging (no sensitive data in logs)
- [ ] Error messages don't leak information
- [ ] Rate limiting implemented
- [ ] CSRF/XSS protection
- [ ] Security headers configured
- [ ] Dependencies scanned for vulnerabilities
- [ ] GDPR data subject rights supported

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
