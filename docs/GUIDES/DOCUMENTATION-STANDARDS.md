# Documentation Standards for Syntek Modules

## Overview

All code files in the Syntek Modules repository **MUST** include docstrings and comments in their language-specific format. This ensures code maintainability, readability, and proper documentation generation.

---

## General Requirements

### File Header Documentation

**Every code file must have a header docstring** explaining:

- What the file does
- What it contains (functions, classes, exports)
- How to use it
- Any important notes or warnings

### Inline Comments

- Complex logic should be explained with inline comments
- Avoid obvious comments (e.g., `// increment i` for `i++`)
- Focus on the "why" rather than the "what"

### Exceptions

**These files do NOT require comments:**

- `package.json`
- `pnpm-lock.yaml`
- `uv.lock`
- `Cargo.lock`
- Other lock files

---

## Language-Specific Formats

### Python (Django)

**Module-level docstring:**

```python
"""Authentication module for user login and session management.

This module provides views, models, and utilities for handling user
authentication including:
- Login/logout views
- Session management
- Password reset functionality
- MFA support (TOTP, WebAuthn)

Example:
    from syntek_security_auth.authentication import login_user

    user = login_user(request, username, password)
"""

from django.contrib.auth import authenticate
```

**Function/method docstrings:**

```python
def authenticate_user(username: str, password: str, request: HttpRequest) -> Optional[User]:
    """Authenticate a user with username and password.

    Performs authentication and checks for:
    - Valid credentials
    - Account status (active, not locked)
    - MFA requirements

    Args:
        username: User's username or email
        password: User's password (will be hashed)
        request: HTTP request object for session management

    Returns:
        User object if authentication succeeds, None otherwise

    Raises:
        AccountLocked: If account is temporarily locked
        MFARequired: If MFA verification is needed

    Example:
        >>> user = authenticate_user('john@example.com', 'secret123', request)
        >>> if user:
        ...     login(request, user)
    """
    # Check if user exists and is active
    user = User.objects.filter(username=username, is_active=True).first()

    # Verify password
    if user and user.check_password(password):
        return user

    return None
```

**Class docstrings:**

```python
class UserProfile(models.Model):
    """Extended user profile with additional information.

    Attributes:
        user: OneToOne relationship to Django User
        bio: User biography (max 500 characters)
        avatar: Cloudinary image field for profile picture
        created_at: Profile creation timestamp
        updated_at: Last update timestamp
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    # ... more fields
```

### TypeScript/JavaScript (React/Next.js)

**Module-level JSDoc:**

````typescript
/**
 * Authentication hooks for React components.
 *
 * Provides custom hooks for authentication state management:
 * - useAuth: Current user and authentication status
 * - useLogin: Login functionality
 * - useLogout: Logout functionality
 * - useMFA: MFA verification
 *
 * @module hooks/auth
 * @example
 * ```tsx
 * import { useAuth } from '@syntek/ui-auth/hooks';
 *
 * function MyComponent() {
 *   const { user, isAuthenticated } = useAuth();
 *   // ...
 * }
 * ```
 */

import { useState, useEffect } from "react";
````

**Function JSDoc:**

````typescript
/**
 * Custom hook for managing authentication state.
 *
 * Provides access to current user, authentication status, and loading state.
 * Automatically updates when authentication state changes.
 *
 * @returns Authentication state object
 * @returns {User | null} user - Current authenticated user or null
 * @returns {boolean} isAuthenticated - Whether user is authenticated
 * @returns {boolean} isLoading - Whether authentication is being checked
 *
 * @example
 * ```tsx
 * function Dashboard() {
 *   const { user, isAuthenticated, isLoading } = useAuth();
 *
 *   if (isLoading) return <Spinner />;
 *   if (!isAuthenticated) return <Redirect to="/login" />;
 *
 *   return <div>Welcome, {user.name}</div>;
 * }
 * ```
 */
export function useAuth(): AuthState {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus()
      .then(setUser)
      .finally(() => setIsLoading(false));
  }, []);

  return {
    user,
    isAuthenticated: user !== null,
    isLoading,
  };
}
````

**Interface/Type JSDoc:**

```typescript
/**
 * User authentication state.
 *
 * @interface AuthState
 * @property {User | null} user - Current authenticated user
 * @property {boolean} isAuthenticated - Authentication status
 * @property {boolean} isLoading - Loading state
 */
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

### Rust

**Module-level documentation:**

````rust
//! Authentication utilities for the Syntek CLI.
//!
//! This module provides functions for checking authentication status,
//! managing API keys, and handling session tokens.
//!
//! # Examples
//!
//! ```no_run
//! use syntek_cli::auth;
//!
//! let token = auth::get_token()?;
//! auth::verify_token(&token)?;
//! ```
//!
//! # Security
//!
//! All tokens are stored securely in the system keychain.
//! Never log or print tokens to stdout.

use std::path::PathBuf;
````

**Function documentation:**

````rust
/// Authenticate a user with API key
///
/// Verifies the API key against the backend and returns a session token.
/// The token is automatically stored in the system keychain.
///
/// # Arguments
///
/// * `api_key` - User's API key from the web dashboard
///
/// # Returns
///
/// * `Ok(String)` - Session token if authentication succeeds
/// * `Err` - If API key is invalid or backend is unreachable
///
/// # Errors
///
/// This function will return an error if:
/// * The API key is malformed
/// * The backend server is unreachable
/// * The API key is invalid or expired
///
/// # Examples
///
/// ```no_run
/// use syntek_cli::auth::authenticate;
///
/// let token = authenticate("sk_live_abc123")?;
/// println!("Authenticated successfully");
/// ```
///
/// # Security
///
/// The API key is transmitted over HTTPS. The returned token is
/// stored in the system keychain and expires after 24 hours.
pub fn authenticate(api_key: &str) -> anyhow::Result<String> {
    // Validate API key format
    if !api_key.starts_with("sk_") {
        anyhow::bail!("Invalid API key format");
    }

    // Call backend API
    let response = client.post("/api/auth")
        .body(json!({ "api_key": api_key }))
        .send()?;

    // Parse and store token
    let token = response.json::<AuthResponse>()?.token;
    store_token(&token)?;

    Ok(token)
}
````

**Struct documentation:**

````rust
/// User profile information
///
/// Contains basic user information retrieved from the API.
/// All fields are optional as they may not be set by the user.
///
/// # Examples
///
/// ```
/// use syntek_cli::models::UserProfile;
///
/// let profile = UserProfile {
///     name: Some("John Doe".to_string()),
///     email: "john@example.com".to_string(),
///     avatar_url: None,
/// };
/// ```
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserProfile {
    /// User's display name
    pub name: Option<String>,

    /// User's email address (required)
    pub email: String,

    /// URL to user's avatar image
    pub avatar_url: Option<String>,
}
````

---

## File Length Limits

### Strict Limits for Code Files

**Maximum 750-800 lines per file** for:

- Python (`.py`)
- TypeScript/JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`)
- Rust (`.rs`)

**Why:**

- Improves maintainability
- Easier code review
- Reduces merge conflicts
- Encourages modular design

**If a file approaches 750 lines:**

1. Identify logical components
2. Extract into separate modules
3. Keep related functionality together
4. Use clear module boundaries

### No Limits for Documentation

**These files can be longer:**

- Markdown files (`.md`)
- Package files (`package.json`, `pyproject.toml`, `Cargo.toml`)
- Configuration files

---

## Script Organization

### All Scripts in Rust

**Location:** `rust/project-cli/src/`

**Structure:**

```
rust/project-cli/src/
├── main.rs              # CLI definition (< 200 lines)
├── commands/            # Command implementations
│   ├── mod.rs
│   ├── dev.rs
│   ├── test.rs
│   └── ...
└── utils/               # Shared utilities
    ├── mod.rs
    ├── exec.rs
    └── ...
```

**Exception:** Only `install-cli.sh` (bootstraps the CLI) is allowed as bash.

**Adding a new command:**

1. Create `src/commands/my_command.rs` with doc comments
2. Add to `src/commands/mod.rs`
3. Add enum variant in `main.rs`
4. Add match arm calling `commands::my_command::run()`

---

## Documentation Generation

### Python (Sphinx)

```bash
# Generate HTML docs from docstrings
cd backend/
sphinx-build -b html docs/ docs/_build/
```

### TypeScript (TypeDoc)

```bash
# Generate HTML docs from JSDoc
pnpm typedoc --out docs web/packages/*/src
```

### Rust (rustdoc)

```bash
# Generate HTML docs from doc comments
cargo doc --no-deps --open
```

---

## Best Practices

### DO

- ✅ Write docstrings for ALL modules, classes, and functions
- ✅ Include usage examples in docstrings
- ✅ Document function arguments and return values
- ✅ Explain WHY code does something, not just WHAT
- ✅ Keep files under 800 lines
- ✅ Use language-specific documentation formats

### DON'T

- ❌ Write obvious comments (e.g., `// add 1 to x`)
- ❌ Comment out old code (use git instead)
- ❌ Let files exceed 800 lines
- ❌ Write bash scripts (use Rust in `rust/project-cli/`)
- ❌ Skip docstrings (except for lock files/package.json)

---

## Enforcement

**Pre-commit hooks check for:**

- Missing module docstrings
- Files exceeding 800 lines
- Bash scripts outside `install-cli.sh`

**CI/CD fails if:**

- Documentation generation fails
- Line count limits exceeded
- Non-Rust scripts detected

---

## Examples from Codebase

See these files for good examples:

- `rust/project-cli/src/main.rs` - Module and function docs
- `rust/project-cli/src/commands/init.rs` - Comprehensive command docs
- `rust/project-cli/src/utils/exec.rs` - Utility function docs

---

## Questions?

See:

- `.claude/CLAUDE.md` - Full agent guidelines
- `rust/project-cli/README.md` - CLI documentation
- Individual module READMEs for module-specific docs
