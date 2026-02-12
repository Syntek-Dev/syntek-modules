# Full-Stack Authentication System Implementation Plan

## Feature: Complete Authentication Module

### Overview

Comprehensive authentication system spanning backend (Django), API (GraphQL/Strawberry), frontend (Next.js/React), mobile (React Native), and Rust security layer. Provides user registration, email/SMS verification, TOTP/MFA, password management, passkeys, account recovery, and modular configuration with encryption at the API layer.

### Requirements Clarification

Before proceeding with implementation, the following information is needed:

#### 1. Verification Methods

- **Primary verification**: Email (confirmed)
- **SMS verification**: Twilio (recommended)
  - **Why Twilio**: Industry standard, excellent reliability, 190+ countries coverage, comprehensive SDK
  - **Fallback options**: AWS SNS (AWS-native), Vonage (alternative provider)
  - **Regional support**: Modular configuration per deployment
- **Alternative methods**:
  - Authenticator app (Google Authenticator, Authy) - TOTP-based
  - Phone call verification (voice call with code)
  - Backup email address (secondary email verification)
  - Push notifications (future consideration)

#### 2. CAPTCHA Implementation

- **reCAPTCHA**: All versions supported (modular configuration)
  - **v2 Checkbox**: Explicit user interaction, high security
  - **v3**: Invisible, score-based (0.0-1.0), better UX
  - **hCaptcha**: Privacy-focused alternative
- **Where applied**: Registration, Password Change, Forgotten Password
- **Site keys**: Generate from Google reCAPTCHA admin console
  - **Setup steps**:
    1. Visit <https://www.google.com/recaptcha/admin>
    2. Register your domains (localhost, staging, production)
    3. Generate site keys for each version (v2, v3)
    4. Store in environment variables: `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY`
    5. NEVER commit keys to repository
  - **Recommendation**: Use v3 for better UX, fallback to v2 if score < 0.5

#### 3. Passkey Scope

- **Priority**: MVP (WebAuthn implementation)
- **Platforms**: Modular - web and/or mobile based on deployment needs
  - **Web**: WebAuthn API (broad browser support)
  - **Mobile**: Platform authenticators (Face ID, Touch ID, Android Biometric)
- **Fallback**: Modular configuration - password login always available by default
  - **Recommendation**: Enable password fallback for accessibility and device compatibility
  - **Security consideration**: Passkeys are phishing-resistant, more secure than passwords

#### 4. User Registration Fields

Confirmed fields:

- First name, last name, username, email, phone number, password, verify password

**Clarifications:**

- **Username**: Modular configuration (unique identifier OR display name)
  - **Unique identifier mode**: Requires uniqueness validation, used for login
  - **Display name mode**: Non-unique, cosmetic only, login via email
  - **Recommendation**: Default to unique identifier for better UX (memorable login)
  - **Validation**: 3-30 characters, alphanumeric + underscore/hyphen
- **Phone number**: Modular (required OR optional)
  - **Format validation**: libphonenumber library for international support
  - **Storage format**: E.164 (e.g., +441234567890)
  - **Usage**: SMS verification AND account recovery (if enabled)
  - **Recommendation**: Optional by default, required only if SMS 2FA is mandatory
  - **Regional support**: Configurable per deployment
- **Organisation assignment**: Modular based on project needs
  - **Self-select**: User chooses from available organisations during registration
  - **Invitation-based**: User receives invite link with pre-assigned organisation
  - **Admin-assigned**: User registers, admin assigns post-registration
  - **Multi-tenant**: User can belong to multiple organisations
  - **Recommendation**: Invitation-based for B2B, self-select for B2C

#### 5. Account Recovery Keys

- **Format**: All formats supported (modular)
  - **Printable PDF**: Formatted document with clear instructions for physical storage
  - **Downloadable file**: Plain text (.txt) or JSON (.json) for digital storage
  - **On-screen display**: With copy-to-clipboard button
  - **Recommendation**: Offer all three, user chooses preferred method
- **Count**: Configurable (minimum 6, recommended 10-12)
  - **Default**: 12 recovery keys
  - **Standard**: 10-12 keys provides balance between usability and security
  - **Modular**: Admin can configure count per deployment
- **Storage**: Hybrid approach (server-side hashing + user responsibility)
  - **Server-side**: Store Argon2id hash of each key (NOT plaintext)
  - **User-side**: User must save keys securely (printed, password manager, encrypted file)
  - **Security model**: Keys shown once during generation, user must acknowledge storage
  - **Validation**: Constant-time comparison of user-provided key against hash

#### 6. Phasing Preferences

Can this be delivered incrementally?

- All for MVP

Please confirm or provide alternatives.

---

### Technical Design (Assuming MVP Scope)

#### Database Schema Changes

**New Tables:**

1. **`auth_phone_verification_token`**
   - `id` (UUID, PK)
   - `user_id` (FK → core_user)
   - `phone_number` (encrypted binary)
   - `token_hash` (text)
   - `code` (encrypted binary, 6-digit)
   - `attempts` (integer, default 0)
   - `verified` (boolean, default false)
   - `created_at` (timestamp)
   - `expires_at` (timestamp)
   - `verified_at` (timestamp, nullable)
   - Indexes: `user_id`, `phone_number`, `expires_at`

2. **`auth_recovery_key`**
   - `id` (UUID, PK)
   - `user_id` (FK → core_user)
   - `key_hash` (text, Argon2id)
   - `used` (boolean, default false)
   - `used_at` (timestamp, nullable)
   - `created_at` (timestamp)
   - Indexes: `user_id`, `used`
   - **Note**: Uses Argon2id (not bcrypt) for consistency with password hashing

3. **`auth_passkey`** (Phase 2)
   - `id` (UUID, PK)
   - `user_id` (FK → core_user)
   - `credential_id` (binary, unique)
   - `public_key` (binary)
   - `counter` (bigint)
   - `device_name` (text)
   - `created_at` (timestamp)
   - `last_used_at` (timestamp, nullable)
   - Indexes: `user_id`, `credential_id`

4. **`auth_ip_tracking`**
   - `id` (UUID, PK)
   - `user_id` (FK → core_user, nullable) - nullable for failed login attempts
   - `ip_address` (encrypted binary) - encrypted via Rust
   - `ip_hash` (text) - HMAC-SHA256 hash for lookups (cannot reverse to IP)
   - `action` (varchar 50) - 'login_success', 'login_failed', 'registration', 'password_change', 'mfa_setup', etc.
   - `user_agent` (text, nullable) - browser/device information
   - `location_data` (jsonb, nullable) - city, country (from IP geolocation, optional)
   - `is_suspicious` (boolean, default false) - flagged by security rules
   - `created_at` (timestamp)
   - Indexes: `user_id`, `ip_hash`, `action`, `is_suspicious`, `created_at`
   - **Security Note**: IP addresses encrypted at rest, hash used for whitelist/blacklist lookups

5. **`auth_ip_whitelist`**
   - `id` (UUID, PK)
   - `organisation_id` (FK → core_organisation) - for multi-tenant IP restrictions
   - `ip_address` (encrypted binary) - encrypted via Rust
   - `ip_hash` (text, unique) - HMAC-SHA256 hash for lookups
   - `ip_range` (cidr, nullable) - for IP range whitelisting (e.g., 192.168.1.0/24)
   - `description` (text) - "Head Office", "VPN Gateway", etc.
   - `created_by` (FK → core_user)
   - `created_at` (timestamp)
   - `expires_at` (timestamp, nullable) - for temporary whitelist entries
   - Indexes: `organisation_id`, `ip_hash`, `expires_at`

6. **`auth_ip_blacklist`**
   - `id` (UUID, PK)
   - `ip_address` (encrypted binary) - encrypted via Rust
   - `ip_hash` (text, unique) - HMAC-SHA256 hash for lookups
   - `reason` (text) - "Brute force attempt", "Known malicious IP", etc.
   - `severity` (varchar 20) - 'low', 'medium', 'high', 'critical'
   - `auto_blocked` (boolean, default false) - automatically blocked by system
   - `block_count` (integer, default 1) - number of times this IP triggered blocks
   - `created_at` (timestamp)
   - `expires_at` (timestamp, nullable) - for temporary blocks (e.g., 24-hour lockout)
   - `last_attempt_at` (timestamp, nullable) - last time this IP attempted access
   - Indexes: `ip_hash`, `severity`, `expires_at`, `auto_blocked`

7. **`auth_login_attempt`**
   - `id` (UUID, PK)
   - `user_id` (FK → core_user, nullable) - nullable if email doesn't exist
   - `email` (varchar 254) - attempted login email
   - `ip_address` (encrypted binary) - encrypted via Rust
   - `ip_hash` (text) - HMAC-SHA256 hash
   - `success` (boolean)
   - `failure_reason` (varchar 100, nullable) - 'invalid_password', 'account_locked', 'ip_blocked', etc.
   - `user_agent` (text, nullable)
   - `created_at` (timestamp)
   - Indexes: `user_id`, `email`, `ip_hash`, `success`, `created_at`
   - **Purpose**: Track failed login attempts for rate limiting and security analysis

**Modified Tables:**

1. **`core_user`**
   - Add `username` (varchar 150, unique, nullable) - phase in gradually
   - Add `phone_number` (binary, nullable) - encrypted
   - Add `phone_verified` (boolean, default false)
   - Add `phone_verified_at` (timestamp, nullable)
   - Add indexes: `username`, `phone_number`

2. **`syntek_totp_device`** (existing)
   - No changes required

3. **`syntek_backup_code`** (existing)
   - Confirm structure matches requirements

#### API Contracts (GraphQL)

**Registration Flow:**

| Mutation                  | Input                                                                                                               | Output                                                                           | Notes                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------- |
| `register`                | `{ email, password, verifyPassword, firstName, lastName, username?, phoneNumber?, organisationId?, captchaToken? }` | `{ success, message, user { id, email, emailVerified, phoneVerified }, errors }` | Creates user, sends email verification |
| `verifyEmail`             | `{ token }`                                                                                                         | `{ success, message, errors }`                                                   | Verifies email token                   |
| `resendEmailVerification` | `{ email }`                                                                                                         | `{ success, message }`                                                           | Resends verification email             |
| `sendPhoneVerification`   | `{ phoneNumber }`                                                                                                   | `{ success, message, expiresIn }`                                                | Sends SMS code                         |
| `verifyPhone`             | `{ code }`                                                                                                          | `{ success, message, errors }`                                                   | Verifies SMS code                      |

**Authentication Flow:**

| Mutation               | Input                                           | Output                                                               | Notes                         |
| ---------------------- | ----------------------------------------------- | -------------------------------------------------------------------- | ----------------------------- |
| `login`                | `{ email, password, totpCode?, captchaToken? }` | `{ success, accessToken, refreshToken, user, requiresTOTP, errors }` | Returns tokens or 2FA prompt  |
| `loginWithRecoveryKey` | `{ email, recoveryKey }`                        | `{ success, accessToken, refreshToken, message }`                    | Bypass TOTP with recovery key |
| `logout`               | `{}`                                            | `{ success, message }`                                               | Invalidates current session   |
| `logoutAllDevices`     | `{ password }`                                  | `{ success, message, sessionsTerminated }`                           | Terminates all sessions       |

**Password Management:**

| Mutation               | Input                                              | Output                         | Notes                                       |
| ---------------------- | -------------------------------------------------- | ------------------------------ | ------------------------------------------- |
| `changePassword`       | `{ currentPassword, newPassword, verifyPassword }` | `{ success, message, errors }` | Changes password, terminates other sessions |
| `requestPasswordReset` | `{ email, captchaToken? }`                         | `{ success, message }`         | Sends reset email (always success)          |
| `resetPassword`        | `{ token, newPassword, verifyPassword }`           | `{ success, message, errors }` | Resets password via token                   |
| `validatePassword`     | `{ password }`                                     | `{ valid, errors, strength }`  | Client-side validation helper               |

**MFA/TOTP Flow:**

| Mutation                | Input                     | Output                                                | Notes                           |
| ----------------------- | ------------------------- | ----------------------------------------------------- | ------------------------------- |
| `setupTOTP`             | `{}`                      | `{ success, secret, qrCodeUrl, backupCodes, errors }` | Generates TOTP secret           |
| `verifyTOTPSetup`       | `{ code }`                | `{ success, message, errors }`                        | Confirms TOTP setup             |
| `disableTOTP`           | `{ password, totpCode? }` | `{ success, message, errors }`                        | Disables TOTP                   |
| `regenerateBackupCodes` | `{ password, totpCode? }` | `{ success, backupCodes, errors }`                    | Generates new backup codes      |
| `generateRecoveryKeys`  | `{ password }`            | `{ success, recoveryKeys, errors }`                   | Generates account recovery keys |

**User Queries:**

| Query          | Input | Output                                                         | Notes                      |
| -------------- | ----- | -------------------------------------------------------------- | -------------------------- |
| `currentUser`  | `{}`  | `UserType`                                                     | Returns authenticated user |
| `userSessions` | `{}`  | `[SessionType]`                                                | Lists active sessions      |
| `mfaStatus`    | `{}`  | `{ totpEnabled, backupCodesRemaining, recoveryKeysRemaining }` | MFA status                 |

**IP Tracking & Management:**

| Mutation            | Input                                        | Output                        | Notes                                     | Permission Required |
| ------------------- | -------------------------------------------- | ----------------------------- | ----------------------------------------- | ------------------- |
| `addIpWhitelist`    | `{ ipAddress, ipRange?, description }`       | `{ success, message, entry }` | Add IP to whitelist (organisation-level)  | Admin               |
| `removeIpWhitelist` | `{ id }`                                     | `{ success, message }`        | Remove IP from whitelist                  | Admin               |
| `addIpBlacklist`    | `{ ipAddress, reason, severity, duration? }` | `{ success, message, entry }` | Block IP address (temporary or permanent) | Admin               |
| `removeIpBlacklist` | `{ id }`                                     | `{ success, message }`        | Unblock IP address                        | Admin               |

| Query                | Input                                      | Output                      | Notes                                      | Permission Required |
| -------------------- | ------------------------------------------ | --------------------------- | ------------------------------------------ | ------------------- |
| `ipWhitelist`        | `{ organisationId? }`                      | `[IpWhitelistEntry]`        | List whitelisted IPs (encrypted displayed) | Admin               |
| `ipBlacklist`        | `{ includeExpired? }`                      | `[IpBlacklistEntry]`        | List blocked IPs                           | Admin               |
| `ipTrackingHistory`  | `{ userId?, ipAddress?, action?, limit? }` | `[IpTrackingEntry]`         | View IP tracking history                   | Admin/Self          |
| `loginAttempts`      | `{ userId?, email?, success?, limit? }`    | `[LoginAttemptEntry]`       | View login attempts (security analysis)    | Admin/Self          |
| `suspiciousActivity` | `{ limit? }`                               | `[SuspiciousActivityEntry]` | Flagged suspicious login attempts          | Admin               |

#### Rust Security Module Specifications

**1. Field Encryption Module (`rust/encryption/src/field_level.rs`)**

Extend existing encryption module:

```rust
/// Encrypt phone number for database storage
pub fn encrypt_phone_number(phone: &str, key: &SecretKey) -> Result<Vec<u8>, Error> {
    // E.164 format validation
    // AES-256-GCM encryption
    // Zeroize plaintext after encryption
}

/// Decrypt phone number from database
pub fn decrypt_phone_number(ciphertext: &[u8], key: &SecretKey) -> Result<String, Error> {
    // AES-256-GCM decryption
    // Zeroize decrypted data on drop
}

/// Encrypt SMS verification code
pub fn encrypt_verification_code(code: &str, key: &SecretKey) -> Result<Vec<u8>, Error> {
    // ChaCha20-Poly1305 encryption
    // Constant-time comparison support
}

/// Encrypt IP address for database storage
pub fn encrypt_ip_address(ip: &str, key: &SecretKey) -> Result<Vec<u8>, Error> {
    // Validate IP format (IPv4 or IPv6)
    // AES-256-GCM encryption
    // Zeroize plaintext after encryption
    // Use case: IP whitelisting, security tracking
}

/// Decrypt IP address from database
pub fn decrypt_ip_address(ciphertext: &[u8], key: &SecretKey) -> Result<String, Error> {
    // AES-256-GCM decryption
    // Zeroize decrypted data on drop
    // Returns IPv4 or IPv6 string
}

/// Generate HMAC-SHA256 hash of IP address for lookups
pub fn hash_ip_address(ip: &str, key: &SecretKey) -> Result<String, Error> {
    // HMAC-SHA256 hash (keyed hash for security)
    // Used for whitelist/blacklist lookups without decrypting
    // Cannot reverse hash to original IP (one-way with key)
    // Constant-time comparison support
}
```

**2. Password Verification Module (`rust/security/src/password.rs`)**

New module for password operations using **Argon2id** (most modern password hashing algorithm):

```rust
/// Hash password using Argon2id (Password Hashing Competition winner 2015)
///
/// Why Argon2id:
/// - Resistant to GPU cracking attacks
/// - Resistant to side-channel attacks
/// - Memory-hard (prevents ASIC attacks)
/// - Combines Argon2d (data-dependent) and Argon2i (data-independent)
/// - OWASP recommended for password storage
///
/// Superior to:
/// - bcrypt (older, less memory-hard)
/// - scrypt (older, less tunable)
/// - PBKDF2 (much older, less secure)
pub fn hash_password(password: SecretString) -> Result<String, Error> {
    // Argon2id with OWASP recommended params:
    // - m=19456 KiB (19 MiB memory cost)
    // - t=2 (iterations)
    // - p=1 (parallelism)
    // - Output length: 32 bytes
    // Zeroize password after hashing
}

/// Verify password against hash (constant-time)
pub fn verify_password(password: SecretString, hash: &str) -> Result<bool, Error> {
    // Constant-time comparison prevents timing attacks
    // Zeroize password after verification
}

/// Validate password strength
pub fn validate_password_strength(password: &str) -> ValidationResult {
    // Length, complexity, common password check
    // No plaintext logging
}
```

**3. Token Generation Module (`rust/security/src/tokens.rs`)**

New module for secure token generation:

```rust
/// Generate cryptographically secure token
pub fn generate_token(length: usize) -> String {
    // Uses ring::rand::SystemRandom
    // URL-safe base64 encoding
}

/// Generate verification code (6-digit)
pub fn generate_verification_code() -> String {
    // Cryptographically secure 6-digit code
    // No sequential or repeated patterns
}

/// Hash token for database storage using HMAC-SHA256
pub fn hash_token(token: &str, key: &SecretKey) -> String {
    // HMAC-SHA256 hash (keyed hash prevents rainbow table attacks)
    // Even with DB access, attacker cannot compute valid hashes without key
    // Constant-time comparison support
}
```

**4. PyO3 Bindings (`rust/pyo3_bindings/src/auth.rs`)**

New Python bindings:

```rust
#[pyfunction]
fn encrypt_phone_number_py(phone: &str, key: &[u8]) -> PyResult<Vec<u8>> {
    // Python wrapper for encrypt_phone_number
}

#[pyfunction]
fn decrypt_phone_number_py(ciphertext: &[u8], key: &[u8]) -> PyResult<String> {
    // Python wrapper for decrypt_phone_number
}

#[pyfunction]
fn hash_password_py(password: &str) -> PyResult<String> {
    // Python wrapper for hash_password
}

#[pyfunction]
fn verify_password_py(password: &str, hash: &str) -> PyResult<bool> {
    // Python wrapper for verify_password
}

#[pyfunction]
fn generate_token_py(length: usize) -> PyResult<String> {
    // Python wrapper for generate_token
}
```

#### Modern Cryptography Standards

All Rust security modules use **state-of-the-art cryptographic algorithms** (2025+ standards):

| Purpose                  | Algorithm                    | Why This Choice                                                                                                                            | Superior To                  |
| ------------------------ | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- |
| **Password Hashing**     | **Argon2id**                 | Winner of Password Hashing Competition 2015. Memory-hard, resistant to GPU/ASIC attacks, side-channel resistant. OWASP recommended.        | bcrypt, scrypt, PBKDF2       |
| **Field Encryption**     | **AES-256-GCM**              | NIST approved, authenticated encryption (prevents tampering), hardware-accelerated on modern CPUs. Industry standard.                      | AES-CBC, AES-CTR (no auth)   |
| **Stream Cipher**        | **ChaCha20-Poly1305**        | Modern IETF standard (RFC 8439). Faster than AES on mobile/IoT devices without hardware acceleration. Constant-time implementation.        | Salsa20, RC4                 |
| **Token Hashing**        | **HMAC-SHA256**              | Keyed hash prevents rainbow tables. Even with DB access, attacker cannot compute valid hashes without HMAC key. Defense-in-depth security. | Plain SHA-256, SHA-1, MD5    |
| **Random Generation**    | **ring::rand::SystemRandom** | Cryptographically secure PRNG using OS entropy sources (/dev/urandom, CryptGenRandom). Timing-attack resistant.                            | rand crate (not crypto-safe) |
| **Key Derivation**       | **HKDF-SHA256**              | HMAC-based Key Derivation Function (RFC 5869). Extracts cryptographically strong keys from source material.                                | Simple hashing               |
| **Recovery Key Hashing** | **Argon2id**                 | Same as password hashing for consistency. Prevents brute-force attacks on recovery keys.                                                   | Plain HMAC-SHA256 (too fast) |

**Parameters (Argon2id):**

```rust
// OWASP recommended parameters (2025)
Argon2id {
    memory: 19456,      // 19 MiB (balance between security and performance)
    iterations: 2,      // Time cost
    parallelism: 1,     // Number of threads
    output_length: 32,  // 256 bits
    version: 0x13,      // Argon2 version 1.3
}
```

**AES-256-GCM Configuration:**

```rust
// NIST SP 800-38D compliant
AES_256_GCM {
    key_size: 256,       // bits
    nonce_size: 96,      // bits (12 bytes, NIST recommended)
    tag_size: 128,       // bits (authentication tag)
}
```

**ChaCha20-Poly1305 Configuration:**

```rust
// RFC 8439 compliant
ChaCha20Poly1305 {
    key_size: 256,       // bits
    nonce_size: 96,      // bits (12 bytes)
    tag_size: 128,       // bits (authentication tag)
}
```

**HMAC-SHA256 Configuration:**

```rust
// RFC 2104 compliant
HMAC_SHA256 {
    key_size: 256,       // bits (minimum 256-bit key from OpenBao)
    output_size: 256,    // bits
    // Key rotation: Every 90 days via OpenBao
    // Stored alongside encrypted data: NEVER in database
}
```

**Security Guarantees:**

- ✅ All sensitive data zeroized after use (no memory leaks)
- ✅ Constant-time operations (prevents timing attacks)
- ✅ Authenticated encryption (prevents tampering)
- ✅ Forward secrecy support (via key rotation)
- ✅ Post-quantum resistant key sizes (256-bit minimum)
- ✅ FIPS 140-2 compliant algorithms
- ✅ Defense-in-depth: compromised DB ≠ compromised tokens (requires HMAC key)

**Compliance:**

- OWASP ASVS Level 3 (Advanced)
- NIST Cybersecurity Framework
- PCI DSS 4.0 requirements
- GDPR encryption requirements
- SOC 2 Type II controls

#### CLI Installation Workflow

**Command: `syntek install auth --full`**

Installs complete authentication stack:

1. **Backend modules:**
   - `syntek-authentication` (core auth logic)
   - `syntek-sessions` (session management)
   - `syntek-jwt` (JWT tokens)
   - `syntek-mfa` (TOTP/2FA)
   - `syntek-ip-tracking` (IP encryption, whitelist/blacklist)
   - `syntek-auth-logging` (modular logging: GlitchTip, Grafana, Sentry, etc.)
   - `syntek-monitoring` (suspicious activity detection)

2. **GraphQL modules:**
   - `syntek-graphql-core` (security foundation)
   - `syntek-graphql-auth` (auth API)

3. **Rust modules:**
   - `syntek-encryption` (field encryption)
   - `syntek-security` (password hashing, tokens)
   - `syntek-pyo3-bindings` (Python bindings)

4. **Web packages:**
   - `@syntek/security-core`
   - `@syntek/security-auth`
   - `@syntek/ui-auth` (login/register forms)

5. **Mobile packages:**
   - `@syntek/mobile-security-core`
   - `@syntek/mobile-security-auth`
   - `@syntek/mobile-auth` (biometric integration)

**CLI Implementation (`rust/project-cli/src/commands/install_auth.rs`):**

```rust
/// Install authentication modules across all layers
pub fn install_auth(args: InstallAuthArgs) -> anyhow::Result<()> {
    // 1. Validate project structure
    // 2. Install backend dependencies (uv pip install)
    // 3. Install GraphQL dependencies
    // 4. Build Rust modules (cargo build)
    // 5. Install web dependencies (pnpm install)
    // 6. Install mobile dependencies (pnpm install)
    // 7. Run database migrations
    // 8. Generate configuration template
    // 9. Display setup instructions
}
```

**Command: `syntek install auth --minimal`**

MVP installation (email auth, TOTP only):

- Skips SMS verification
- Skips passkeys
- Basic configuration

**Command: `syntek install auth --web-only`**

Web-only installation (no mobile):

- Backend + GraphQL + Web
- Skips mobile packages

#### Configuration Architecture

**Django Settings (`settings/auth.py`):**

```python
SYNTEK_AUTHENTICATION = {
    # Registration
    'REGISTRATION_ENABLED': True,
    'REQUIRE_EMAIL_VERIFICATION': True,
    'REQUIRE_PHONE_VERIFICATION': False,  # Optional
    'ALLOW_USERNAME': True,
    'USERNAME_REQUIRED': False,
    'PHONE_NUMBER_REQUIRED': False,

    # Password Requirements
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_NUMBERS': True,
    'PASSWORD_REQUIRE_SPECIAL': True,
    'PASSWORD_HISTORY_COUNT': 5,
    'CHECK_COMMON_PASSWORDS': True,

    # Login Security
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 minutes
    'LOCKOUT_INCREMENT': True,
    'CAPTCHA_ON_REGISTRATION': False,
    'CAPTCHA_ON_LOGIN': False,
    'CAPTCHA_PROVIDER': 'recaptcha_v2',  # 'recaptcha_v2', 'recaptcha_v3', 'hcaptcha'

    # Verification
    'EMAIL_VERIFICATION_TOKEN_LIFETIME': 86400,  # 24 hours
    'PHONE_VERIFICATION_CODE_LIFETIME': 600,  # 10 minutes
    'MAX_VERIFICATION_ATTEMPTS': 3,

    # MFA
    'TOTP_REQUIRED': False,
    'TOTP_ISSUER': 'Syntek Platform',
    'BACKUP_CODE_COUNT': 10,
    'RECOVERY_KEY_COUNT': 12,

    # Sessions
    'MAX_CONCURRENT_SESSIONS': 5,
    'SESSION_TIMEOUT': 1800,  # 30 minutes
    'TERMINATE_OTHER_SESSIONS_ON_PASSWORD_CHANGE': True,

    # External Services
    'SMS_PROVIDER': None,  # 'twilio', 'aws_sns', 'vonage'
    'SMS_FROM_NUMBER': env('SMS_FROM_NUMBER', default=None),

    # IP Tracking & Security
    'ENABLE_IP_TRACKING': True,
    'ENABLE_IP_WHITELIST': False,  # Enable for organisation-level IP restrictions
    'ENABLE_IP_BLACKLIST': True,   # Enable automatic IP blocking
    'IP_GEOLOCATION_ENABLED': False,  # Store city/country from IP (optional)
    'IP_GEOLOCATION_PROVIDER': None,  # 'maxmind', 'ipapi', 'ipstack'
    'AUTO_BLOCK_AFTER_FAILED_ATTEMPTS': 10,  # Auto-blacklist after N failed logins
    'AUTO_BLOCK_DURATION': 86400,  # 24 hours (in seconds)
    'SUSPICIOUS_LOGIN_CHECKS': True,  # Flag suspicious patterns
    'TRACK_USER_AGENTS': True,  # Store browser/device info
}

# SMS Provider Configuration (example for Twilio)
SYNTEK_SMS = {
    'TWILIO_ACCOUNT_SID': env('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': env('TWILIO_AUTH_TOKEN'),
    'TWILIO_FROM_NUMBER': env('TWILIO_FROM_NUMBER'),
}

# CAPTCHA Configuration
SYNTEK_CAPTCHA = {
    'RECAPTCHA_SITE_KEY': env('RECAPTCHA_SITE_KEY'),
    'RECAPTCHA_SECRET_KEY': env('RECAPTCHA_SECRET_KEY'),
    'RECAPTCHA_MIN_SCORE': 0.5,  # For v3
}

# Authentication Logging Configuration (Modular)
SYNTEK_AUTH_LOGGING = {
    # Logging Provider
    'PROVIDER': 'glitchtip',  # 'glitchtip', 'grafana', 'sentry', 'datadog', 'splunk', 'elk', 'standard'

    # Log Levels
    'LOG_LEVEL': 'INFO',  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    'LOG_FAILED_LOGINS': True,
    'LOG_SUCCESSFUL_LOGINS': True,
    'LOG_PASSWORD_CHANGES': True,
    'LOG_MFA_EVENTS': True,
    'LOG_IP_BLOCKS': True,
    'LOG_SUSPICIOUS_ACTIVITY': True,

    # Log Destinations (can enable multiple)
    'DESTINATIONS': {
        'CONSOLE': True,  # Standard output (Django logging)
        'FILE': True,     # File-based logging
        'REMOTE': True,   # External service (GlitchTip, Grafana, etc.)
    },

    # File Logging (if DESTINATIONS['FILE'] = True)
    'FILE_PATH': '/var/log/syntek/auth.log',
    'FILE_MAX_BYTES': 10485760,  # 10 MB
    'FILE_BACKUP_COUNT': 5,
    'FILE_FORMAT': 'json',  # 'json' or 'text'

    # Sensitive Data Handling
    'SANITIZE_LOGS': True,  # Remove passwords, tokens from logs
    'LOG_IP_ADDRESSES': True,  # Log encrypted IP addresses
    'LOG_USER_AGENTS': True,
    'LOG_REQUEST_HEADERS': False,  # Avoid logging sensitive headers

    # Retention
    'LOG_RETENTION_DAYS': 90,  # Keep logs for 90 days (GDPR compliance)
    'ARCHIVE_OLD_LOGS': True,
    'ARCHIVE_PATH': '/var/log/syntek/archive/',
}

# GlitchTip Configuration (if PROVIDER = 'glitchtip')
SYNTEK_GLITCHTIP = {
    'DSN': env('GLITCHTIP_DSN'),  # GlitchTip project DSN
    'ENVIRONMENT': env('ENVIRONMENT', default='production'),
    'SEND_DEFAULT_PII': False,  # Don't send personally identifiable info
    'TRACES_SAMPLE_RATE': 0.1,  # 10% of transactions
    'PROFILES_SAMPLE_RATE': 0.1,
    'ENABLE_TRACING': True,
    'INTEGRATIONS': [
        'django',
        'celery',  # If using Celery
        'redis',
    ],
}

# Grafana Configuration (if PROVIDER = 'grafana')
SYNTEK_GRAFANA = {
    'LOKI_URL': env('GRAFANA_LOKI_URL'),  # Grafana Loki endpoint
    'LOKI_USERNAME': env('GRAFANA_LOKI_USERNAME', default=None),
    'LOKI_PASSWORD': env('GRAFANA_LOKI_PASSWORD', default=None),
    'PROMETHEUS_METRICS_PORT': 9090,  # Metrics endpoint for Prometheus
    'ENABLE_METRICS': True,
    'LABELS': {
        'application': 'syntek-auth',
        'environment': env('ENVIRONMENT', default='production'),
    },
}

# Sentry Configuration (alternative to GlitchTip)
SYNTEK_SENTRY = {
    'DSN': env('SENTRY_DSN', default=None),
    'ENVIRONMENT': env('ENVIRONMENT', default='production'),
    'SEND_DEFAULT_PII': False,
    'TRACES_SAMPLE_RATE': 0.1,
}

# Custom Logging Handlers (for other providers)
SYNTEK_CUSTOM_LOGGING = {
    'HANDLER_CLASS': None,  # e.g., 'myapp.logging.CustomHandler'
    'HANDLER_CONFIG': {},   # Custom configuration dict
}

# Standard Django Logging (fallback if no provider configured)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': SYNTEK_AUTH_LOGGING['FILE_PATH'],
            'maxBytes': SYNTEK_AUTH_LOGGING['FILE_MAX_BYTES'],
            'backupCount': SYNTEK_AUTH_LOGGING['FILE_BACKUP_COUNT'],
            'formatter': 'json' if SYNTEK_AUTH_LOGGING['FILE_FORMAT'] == 'json' else 'verbose',
        },
    },
    'loggers': {
        'syntek.auth': {
            'handlers': ['console', 'file'],
            'level': SYNTEK_AUTH_LOGGING['LOG_LEVEL'],
            'propagate': False,
        },
    },
}
```

**Web Configuration (`packages/ui-auth/config.ts`):**

```typescript
export interface AuthConfig {
  // Registration
  enableRegistration: boolean;
  requireEmailVerification: boolean;
  requirePhoneVerification: boolean;
  enableUsername: boolean;
  usernameRequired: boolean;
  phoneNumberRequired: boolean;

  // Password
  passwordMinLength: number;
  showPasswordStrengthIndicator: boolean;

  // CAPTCHA
  enableCaptcha: boolean;
  captchaProvider: "recaptcha_v2" | "recaptcha_v3" | "hcaptcha";
  captchaSiteKey: string;

  // MFA
  enableTOTP: boolean;
  enablePasskeys: boolean;

  // UI
  theme: "light" | "dark" | "system";
  logo?: string;
  brandColor?: string;
}

// Default configuration
export const defaultAuthConfig: AuthConfig = {
  enableRegistration: true,
  requireEmailVerification: true,
  requirePhoneVerification: false,
  enableUsername: true,
  usernameRequired: false,
  phoneNumberRequired: false,
  passwordMinLength: 12,
  showPasswordStrengthIndicator: true,
  enableCaptcha: false,
  captchaProvider: "recaptcha_v2",
  captchaSiteKey: "",
  enableTOTP: true,
  enablePasskeys: false,
  theme: "system",
};
```

**Mobile Configuration (`packages/mobile-auth/config.ts`):**

```typescript
export interface MobileAuthConfig {
  // Biometric
  enableBiometric: boolean;
  biometricPrompt: string;
  fallbackToPassword: boolean;

  // Security
  enableRootDetection: boolean;
  enableCertificatePinning: boolean;

  // Storage
  secureStorageKey: string;

  // API
  apiBaseUrl: string;
  apiTimeout: number;
}
```

#### Authentication Logging Implementation

**Overview:**

Modular logging system supporting multiple providers (GlitchTip, Grafana, Sentry, Datadog, Splunk, ELK, or standard framework logging). All authentication events are logged with configurable levels, destinations, and sensitive data sanitization.

**Logging Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                  Authentication Event                        │
│  (login, registration, password change, MFA setup, etc.)     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │   Logging Service (Django)      │
         │   - Sanitize sensitive data     │
         │   - Add context (user, IP, UA)  │
         │   - Format log entry            │
         └────────┬───────────┬────────────┘
                  │           │
        ┌─────────┴───┐   ┌───┴─────────┐
        │   Console    │   │    File     │
        │   (stdout)   │   │  (rotating) │
        └──────────────┘   └─────────────┘
                  │
          ┌───────┴────────────────────┐
          │   Remote Logger (modular)   │
          ├─────────────────────────────┤
          │ • GlitchTip (default)       │
          │ • Grafana Loki              │
          │ • Sentry                    │
          │ • Datadog                   │
          │ • Splunk                    │
          │ • ELK Stack                 │
          │ • Custom Handler            │
          └─────────────────────────────┘
```

**What Gets Logged:**

| Event Type              | Log Level | Data Logged (Sanitized)                                           | IP Tracked |
| ----------------------- | --------- | ----------------------------------------------------------------- | ---------- |
| **Successful Login**    | INFO      | User ID, email, timestamp, IP hash, user agent, MFA used          | Yes        |
| **Failed Login**        | WARNING   | Email (attempted), IP hash, failure reason, timestamp, user agent | Yes        |
| **Registration**        | INFO      | User ID, email, timestamp, IP hash, verification method           | Yes        |
| **Password Change**     | INFO      | User ID, timestamp, IP hash, sessions terminated                  | Yes        |
| **Password Reset**      | INFO      | User ID (if exists), email, timestamp, IP hash                    | Yes        |
| **MFA Setup**           | INFO      | User ID, MFA method (TOTP, passkey), timestamp, IP hash           | Yes        |
| **MFA Disabled**        | WARNING   | User ID, timestamp, IP hash, reason                               | Yes        |
| **Recovery Key Used**   | WARNING   | User ID, timestamp, IP hash, recovery key ID (not key itself)     | Yes        |
| **IP Blocked**          | WARNING   | IP hash, reason, severity, block duration, auto-blocked flag      | Yes        |
| **IP Whitelisted**      | INFO      | IP hash, organisation ID, added by user ID, description           | Yes        |
| **Suspicious Activity** | ERROR     | User ID (if exists), IP hash, patterns detected, risk score       | Yes        |
| **Account Lockout**     | WARNING   | User ID, email, IP hash, lockout duration, failed attempt count   | Yes        |

**Log Format (JSON):**

```json
{
  "timestamp": "2026-02-12T14:30:00.123Z",
  "level": "INFO",
  "event": "login_success",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "ip_hash": "a7f3b8c9d2e1f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
  "location": {
    "city": "London",
    "country": "GB"
  },
  "mfa_used": true,
  "session_id": "abc123",
  "request_id": "req-456",
  "environment": "production"
}
```

**Provider Integrations:**

**1. GlitchTip (Default)**

```python
# backend/logging/providers/glitchtip.py
import sentry_sdk  # GlitchTip uses Sentry SDK
from sentry_sdk.integrations.django import DjangoIntegration

def setup_glitchtip(config):
    sentry_sdk.init(
        dsn=config['DSN'],
        environment=config['ENVIRONMENT'],
        integrations=[DjangoIntegration()],
        send_default_pii=False,  # Don't send PII
        traces_sample_rate=config['TRACES_SAMPLE_RATE'],
    )

def log_auth_event(event_type, data):
    # Sanitize data
    sanitized = sanitize_log_data(data)

    # Send to GlitchTip
    sentry_sdk.capture_message(
        f"auth.{event_type}",
        level=get_log_level(event_type),
        extras=sanitized
    )
```

**2. Grafana Loki**

```python
# backend/logging/providers/grafana.py
import logging_loki

def setup_grafana_loki(config):
    handler = logging_loki.LokiHandler(
        url=config['LOKI_URL'],
        tags=config['LABELS'],
        auth=(config['LOKI_USERNAME'], config['LOKI_PASSWORD']),
        version="1",
    )

    logger = logging.getLogger('syntek.auth')
    logger.addHandler(handler)

def log_auth_event(event_type, data):
    logger = logging.getLogger('syntek.auth')
    sanitized = sanitize_log_data(data)
    logger.info(f"auth.{event_type}", extra=sanitized)
```

**3. Sentry (Alternative)**

```python
# backend/logging/providers/sentry.py
import sentry_sdk

def setup_sentry(config):
    sentry_sdk.init(
        dsn=config['DSN'],
        environment=config['ENVIRONMENT'],
        send_default_pii=False,
    )

def log_auth_event(event_type, data):
    sanitized = sanitize_log_data(data)
    sentry_sdk.capture_message(
        f"auth.{event_type}",
        level=get_log_level(event_type),
        extras=sanitized
    )
```

**4. Standard Django Logging (Fallback)**

```python
# backend/logging/providers/standard.py
import logging
import json

def setup_standard_logging(config):
    # Uses LOGGING configuration from settings
    pass

def log_auth_event(event_type, data):
    logger = logging.getLogger('syntek.auth')
    sanitized = sanitize_log_data(data)

    if config['FILE_FORMAT'] == 'json':
        logger.info(json.dumps({
            'event': event_type,
            **sanitized
        }))
    else:
        logger.info(f"{event_type}: {sanitized}")
```

**Data Sanitization:**

```python
# backend/logging/sanitizer.py
def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive data from logs."""
    sensitive_fields = [
        'password',
        'new_password',
        'current_password',
        'verify_password',
        'token',
        'secret',
        'totp_code',
        'backup_code',
        'recovery_key',
        'access_token',
        'refresh_token',
        'api_key',
    ]

    sanitized = data.copy()

    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '[REDACTED]'

    # Keep only IP hash, not encrypted IP
    if 'ip_address' in sanitized:
        sanitized.pop('ip_address')

    return sanitized
```

**Grafana Dashboard Queries (Example):**

```promql
# Failed login attempts in last hour
count_over_time({application="syntek-auth", event="login_failed"}[1h])

# Successful logins by user
sum by (user_id) (count_over_time({application="syntek-auth", event="login_success"}[24h]))

# Suspicious activity count
count_over_time({application="syntek-auth", event="suspicious_activity"}[1h])

# IP blocks over time
rate({application="syntek-auth", event="ip_blocked"}[5m])
```

---

### Encryption Strategy: Individual vs Batch Encryption

This section defines which fields are encrypted individually vs batch-encrypted for performance optimization.

#### Individual Encryption (One Field Per Call)

These fields are encrypted individually because they are:

- Created/modified independently
- Required for real-time operations
- Low-frequency operations (not performance-critical)

| Field                   | Rust Function                | Use Case                                                       | Frequency     |
| ----------------------- | ---------------------------- | -------------------------------------------------------------- | ------------- |
| **Email (user.email)**  | `encrypt_field(email, key)`  | User registration, email update (one user at a time)           | Low (1/user)  |
| **Phone (user.phone)**  | `encrypt_field(phone, key)`  | User registration, phone update (one user at a time)           | Low (1/user)  |
| **Recovery Keys**       | `encrypt_field(key, key)`    | MFA setup (12 keys encrypted sequentially, acceptable latency) | Low (12/user) |
| **TOTP Secret**         | `encrypt_field(secret, key)` | MFA setup (one secret per user)                                | Low (1/user)  |
| **Verification Tokens** | `encrypt_field(token, key)`  | Email/SMS verification (real-time generation)                  | Medium        |
| **Session Cookies**     | `encrypt_field(cookie, key)` | Login (one session per user, real-time)                        | Medium        |

**Rationale:** These operations are user-initiated, infrequent, and latency-tolerant (50-100ms encryption time acceptable).

#### Batch Encryption (Multiple Fields Per Call)

These fields are batch-encrypted because they are:

- Created together in bulk operations
- Performance-critical (high-frequency)
- Benefit from reduced PyO3 FFI overhead

| Fields Encrypted Together                  | Rust Function                                      | Use Case                                         | Frequency   | Performance Gain        |
| ------------------------------------------ | -------------------------------------------------- | ------------------------------------------------ | ----------- | ----------------------- |
| **IP + Location (city + country)**         | `encrypt_batch([ip, city, country], key)`          | IP tracking on every login/request               | Very High   | 3x faster (1 FFI call)  |
| **User Registration (email + phone)**      | `encrypt_batch([email, phone], key)`               | User registration (both fields created together) | Medium      | 2x faster (1 FFI call)  |
| **IP Tracking History Export**             | `encrypt_batch([ip1, ip2, ..., ip100], key)`       | Admin export of IP history (100+ IPs)            | Low (admin) | 50x faster (1 FFI call) |
| **GDPR Data Export (email + phone + ...)** | `encrypt_batch([email, phone, backup_email], key)` | GDPR DSAR export (decrypt user's encrypted data) | Low (user)  | 3x faster (1 FFI call)  |

**Rationale:** These operations happen in bulk or are high-frequency. Batch encryption reduces:

- PyO3 FFI overhead (1 FFI call instead of N calls)
- Nonce generation overhead (shared RNG acquisition)
- Key derivation overhead (if using key derivation)

**Example Performance:**

```rust
// Individual encryption (3 FFI calls)
ip_encrypted = encrypt_field_py(ip, key)          // 5µs FFI overhead
city_encrypted = encrypt_field_py(city, key)      // 5µs FFI overhead
country_encrypted = encrypt_field_py(country, key) // 5µs FFI overhead
// Total FFI overhead: 15µs

// Batch encryption (1 FFI call)
[ip_encrypted, city_encrypted, country_encrypted] = encrypt_batch_py([ip, city, country], key)
// Total FFI overhead: 5µs (3x faster)
```

#### Implementation Details

**Batch Encryption Function:**

```rust
// rust/encryption/src/field_level.rs
pub fn encrypt_batch(fields: Vec<&str>, key: &[u8]) -> Result<Vec<Vec<u8>>> {
    let rng = SystemRandom::new(); // Acquire RNG once
    let cipher = ChaCha20Poly1305::new(key.into());

    fields.iter().map(|field| {
        let mut nonce_bytes = [0u8; 12];
        rng.fill(&mut nonce_bytes)?;
        let nonce = Nonce::from_slice(&nonce_bytes);

        let ciphertext = cipher.encrypt(nonce, field.as_bytes())?;

        // Prepend nonce to ciphertext
        let mut result = nonce_bytes.to_vec();
        result.extend_from_slice(&ciphertext);

        Ok(result)
    }).collect()
}
```

**PyO3 Binding:**

```rust
// rust/pyo3_bindings/src/auth.rs
#[pyfunction]
fn encrypt_batch_py(py: Python<'_>, fields: Vec<&str>, key: &[u8]) -> PyResult<Vec<Py<PyBytes>>> {
    let encrypted_fields = encrypt_batch(fields, key)
        .map_err(|e| PyValueError::new_err(format!("Batch encryption failed: {}", e)))?;

    Ok(encrypted_fields
        .into_iter()
        .map(|data| PyBytes::new(py, &data).into())
        .collect())
}
```

**Django Usage:**

```python
# Individual encryption (user registration, one user)
email_encrypted = encrypt_field(user.email, settings.ENCRYPTION_KEY)
phone_encrypted = encrypt_field(user.phone, settings.ENCRYPTION_KEY)

# Batch encryption (IP tracking, high-frequency)
ip_encrypted, city_encrypted, country_encrypted = encrypt_batch(
    [request.ip, geo.city, geo.country],
    settings.ENCRYPTION_KEY
)
```

#### When to Use Each Strategy

**Use Individual Encryption When:**

- ✅ User-initiated operations (registration, profile update)
- ✅ Low-frequency operations (< 1000/day)
- ✅ Real-time operations requiring immediate response
- ✅ Single field updates (e.g., email change only)

**Use Batch Encryption When:**

- ✅ Multiple fields created together (IP + location on login)
- ✅ High-frequency operations (> 10,000/day)
- ✅ Bulk admin operations (export 100+ IPs)
- ✅ GDPR data exports (decrypt all user data at once)

**Performance Target:**

- Individual encryption: < 100µs per field (50µs encryption + 5µs FFI overhead)
- Batch encryption: < 100µs total for 3 fields (50µs encryption + 5µs FFI overhead, amortized)

---

### Implementation Phases

#### Phase 1: Backend Foundation (Week 1-2)

**Tasks:**

- [x] **1.1** Create database migrations for new tables
  - `auth_phone_verification_token`
  - `auth_recovery_key` **[CRITICAL]** Add `algorithm_version`, `algorithm_metadata` fields for versioning
  - `auth_ip_tracking` **[CRITICAL]** Ensure `location_data` is stored as encrypted jsonb
  - `auth_ip_whitelist`
  - `auth_ip_blacklist`
  - `auth_login_attempt`
  - `auth_session_security` **[NEW]** Track session fingerprints, device changes, suspicious patterns
  - Modify `core_user` **[CRITICAL]** Add:
    - `email_encrypted` (binary) - encrypted email for secure storage
    - `email_hash` (varchar 64, UNIQUE) **[DB-P0]** - HMAC-SHA256 hash for constant-time lookups (prevents timing attacks)
    - `phone_hash` (varchar 64, UNIQUE) **[DB-P0]** - HMAC-SHA256 hash for constant-time lookups
    - `username` - unique username field
    - `phone_number` (encrypted) - encrypted phone storage
    - `deleted_at` (timestamp, nullable) **[DB-P0]** - soft delete for GDPR 30-day grace period
    - `deletion_scheduled_date` (date, nullable) **[DB-P0]** - scheduled permanent deletion date
    - Keep `email` plain for lookups (non-sensitive domain info)
  - **[PERFORMANCE]** Add composite indexes:
    - `(user_id, created_at)` on `auth_ip_tracking`
    - `(email, success, created_at)` on `auth_login_attempt`
    - `(user_id, used, created_at)` on `auth_recovery_key`
    - `(ip_hash, expires_at)` on `auth_ip_blacklist`
  - **[DB-P0] Critical Database Optimizations:**
    - Create `UNIQUE INDEX idx_core_user_email_hash ON core_user(email_hash)` - prevents timing attacks
    - Create `UNIQUE INDEX idx_core_user_phone_hash ON core_user(phone_hash)` - prevents phone enumeration
    - Create `INDEX idx_login_attempt_email_recent ON auth_login_attempt(email, created_at DESC) WHERE success = FALSE` - rate limiting
    - Create `INDEX idx_login_attempt_ip_recent ON auth_login_attempt(ip_hash, created_at DESC)` - IP-based rate limiting
  - **[DB-P0] Table Partitioning Setup:**
    - Implement monthly partitioning for `auth_ip_tracking` by `created_at`
    - Implement monthly partitioning for `auth_login_attempt` by `created_at`
    - Create automated partition creation script (Celery beat task)
    - Create partition dropping script for data retention (90 days default)
    - Migration: `CREATE TABLE auth_ip_tracking_partitioned ... PARTITION BY RANGE (created_at)`

- [x] **1.2** Implement Rust security modules
  - **[RS-P0-2] HMAC-SHA256 Implementation** (6 hours):
    - Create `rust/security/src/hmac.rs`
    - Implement `hash_for_lookup(data, key) -> String` for constant-time lookups
    - Implement `verify_hmac(data, key, hash) -> bool` with `subtle::ConstantTimeEq`
    - Unit tests: correctness, constant-time behavior, property-based tests
    - Usage: Email hashing, phone hashing, IP hashing for database lookups
  - **[RS-P0-3] Token Generation Functions** (4 hours):
    - Create `rust/security/src/tokens.rs`
    - Implement `generate_token(length) -> String` with URL-safe base64
    - Implement `generate_verification_code() -> String` (6-digit, zero-padded)
    - Use `ring::rand::SystemRandom` for cryptographic security
    - Unit tests: randomness, no sequential patterns, statistical uniformity
  - **[RS-P0-5] Input Validation Functions** (4 hours):
    - Create `rust/encryption/src/validators.rs`
    - Implement `validate_email(email) -> Result<()>` (RFC 5322, max 254 chars)
    - Implement `validate_phone_number(phone) -> Result<()>` (E.164 format validation)
    - Implement `validate_ip_address(ip) -> Result<()>` (IPv4/IPv6 via std::net::IpAddr)
    - Call validators before encryption to prevent invalid data storage
  - **[CRITICAL]** Email encryption/decryption functions (ChaCha20-Poly1305 with zeroization):
    - Use existing `encrypt_field()` from `rust/encryption/src/field_level.rs`
    - Validate email format before encryption
    - **Encryption Strategy:** Individual encryption (one email per call)
  - **[CRITICAL]** Phone encryption/decryption functions:
    - Use existing `encrypt_field()` with phone number validation
    - **Encryption Strategy:** Individual encryption
  - **[CRITICAL]** IP address encryption/decryption functions:
    - Use existing `encrypt_field()` with IP address validation
    - **Encryption Strategy:** Batch encryption for IP tracking (multiple IPs per request)
  - **[CRITICAL]** Geolocation data encryption (encrypt city/country if stored):
    - Use existing `encrypt_field()` for location data
    - **Encryption Strategy:** Batch encryption (city + country encrypted together)
  - **[RS-P0-6] Argon2 OWASP 2025 Configuration** (2 hours):
    - Modify `rust/hashing/src/lib.rs` to use explicit parameters
    - Set memory=19456 KiB (19 MiB), iterations=2, parallelism=1, output=32 bytes
    - Replace `Argon2::default()` with explicit `Params::new()` and `Argon2::new()`
    - Verify backward compatibility with existing hashes
    - Add benchmarks (target: 100-200ms per hash)
  - **[IMPROVEMENT]** Advanced password pattern detection:
    - Keyboard patterns (qwerty, asdf, 12345)
    - Character sequences (abc, 123, zzz)
    - Common substitutions (@ for a, 3 for e, $ for s)
    - Date patterns (DDMMYYYY, YYYYMMDD)
    - Dictionary words with l33t speak
  - **[CRITICAL]** Algorithm-versioned hashing (support Argon2id v1.3, future algorithms)
  - **[CRITICAL]** Key rotation functions:
    - Re-encrypt with new key (batch operations)
    - Key versioning and metadata storage
    - Background re-encryption support
  - **[PERFORMANCE]** Batch encryption operations (encrypt multiple fields in one call)
  - **[RS-P0-1] PyO3 Password Hashing Bindings** (4 hours):
    - Implement `hash_password_py(password: &str) -> PyResult<String>`
    - Implement `verify_password_py(password: &str, hash: &str) -> PyResult<bool>`
    - Copy password to owned memory, zeroize after use
    - Add Python integration tests
  - **[RS-P0-4] PyO3 Authentication Bindings** (8 hours):
    - Create `rust/pyo3_bindings/src/auth.rs`
    - Email functions: `encrypt_email_py()`, `decrypt_email_py()`, `hash_email_py()`
    - Phone functions: `encrypt_phone_number_py()`, `decrypt_phone_number_py()`, `hash_phone_py()`
    - IP functions: `encrypt_ip_address_py()`, `decrypt_ip_address_py()`, `hash_ip_address_py()`
    - Token functions: `generate_token_py()`, `generate_verification_code_py()`, `hash_token_py()`
    - Register all functions in `rust/pyo3_bindings/src/lib.rs`
    - Add Python integration tests for each function
  - **[RS-LIMITATION] FFI Zeroization Documentation**:
    - Document that Rust cannot zeroize Python's heap memory
    - Python layer must use `SecureString` or similar for passwords
    - Rust zeroizes its own copies, but Python's original string remains

- [x] **1.3** Implement Django authentication services (`backend/security-auth/authentication/`)
  - **Module Location:** All services in `backend/security-auth/authentication/services/`
  - **[CRITICAL]** Email encryption service (encrypt on write, decrypt on read, maintain plain email for lookups)
  - Phone verification service (send SMS, verify code)
  - **[SECURITY] M-2:** Global SMS rate limiting service (prevent cost attacks):
    - Global SMS counter (across all IPs, not just per-IP)
    - Daily budget monitoring ($500/day default, configurable)
    - Automatic SMS blocking when budget exceeded
    - Alert system for approaching budget limits
    - CAPTCHA escalation after threshold (100 SMS/hour globally)
  - **[CRITICAL]** Recovery key service with versioning (generate with algorithm metadata, validate with version routing)
  - **[SECURITY] L-1:** Recovery key service with database locking (prevent race conditions):
    - Use PostgreSQL `SELECT FOR UPDATE` for atomic operations
    - Implement distributed locking with Redis for multi-instance deployments
    - Concurrency testing (100 simultaneous requests must result in single success)
  - Username validation service
  - **[IMPROVEMENT]** Enhanced password validation service:
    - Integrate advanced pattern detection from Rust
    - Check against Have I Been Pwned API (k-anonymity)
    - Enforce password history (last 5 passwords)
    - Keyboard pattern detection
  - **[IMPROVEMENT]** Session security service:
    - Device fingerprinting (user agent, screen resolution, timezone, canvas fingerprint)
    - Session hijacking detection (IP change, user agent change)
    - Device change notifications
    - Suspicious pattern detection (impossible travel, unusual hours)
  - IP tracking service (encrypt, store, retrieve)
  - IP whitelist/blacklist service (add, remove, check)
  - **[DB-P0] Redis caching layer for IP blacklist:**
    - Cache IP blacklist status (TTL: 1 hour)
    - Cache key format: `ip_blacklist:{ip_hash}`
    - 99% reduction in database queries for IP checks
    - Automatic cache invalidation on blacklist updates
    - Fallback to database if Redis unavailable
  - Login attempt tracking service
  - Suspicious activity detection service
  - **[IMPROVEMENT]** Backup code management service:
    - Expiry dates (default 1 year)
    - Low-code count notifications (< 3 remaining)
    - Auto-regeneration prompt
  - **[CRITICAL]** Key rotation service:
    - Background job for re-encrypting data with new keys
    - Key versioning and migration
    - Zero-downtime rotation strategy
  - **[ARCHITECTURE]** Standardized service layer pattern:
    - Consistent error handling (custom exceptions)
    - Automatic logging with sanitization
    - Transaction management
    - Input validation
  - Authentication logging service (modular: GlitchTip, Grafana, Sentry, standard)
  - **[GDPR] GAP-07:** Account deletion service:
    - Soft delete with 30-day grace period
    - Hard delete workflow (permanent PII removal)
    - Anonymize audit logs after deletion
    - Scheduled deletion job (Celery task)
  - **[GDPR] GAP-08:** PII access audit logging service:
    - Log all admin access to encrypted PII (emails, phone numbers, IP addresses)
    - PIIAccessLog model with admin user, action, timestamp, IP address
    - Automatic logging middleware for Django admin
  - **[GDPR] GAP-14:** Consent audit trail service:
    - ConsentLog model for phone consent history
    - Track consent granted, withdrawn, version changes

- [x] **1.4** Create GDPR compliance models (`backend/security-auth/authentication/`)
  - **Module Location:** All models in `backend/security-auth/authentication/models/`
  - **[GDPR] GAP-03:** Update `User` model with legal acceptance tracking:
    - `privacy_policy_accepted_at` (DateTimeField) - GDPR requirement
    - `privacy_policy_version` (CharField, max 20) - e.g., "1.2-EU", "1.3-USA"
    - `privacy_policy_region` (CharField, max 10) - e.g., "EU", "USA", "CA", "AU"
    - `terms_accepted_at` (DateTimeField) - Terms of Service acceptance
    - `terms_version` (CharField, max 20) - e.g., "2.1-EU", "2.0-USA"
    - `terms_region` (CharField, max 10) - Region-specific terms
    - Note: Track versions AND regions because legal requirements differ by jurisdiction
  - **[GDPR] GAP-07:** `AccountDeletion` model:
    - Track deletion requests, scheduled date, completion status
  - **[GDPR] GAP-08:** `PIIAccessLog` model:
    - admin_user, action, resource_type, resource_id, ip_address, timestamp
  - **[GDPR] GAP-14:** `ConsentLog` model:
    - user, consent_type (phone, marketing, etc.), granted, version, timestamp
  - **[GDPR] GAP-06:** Data retention policy documents (regional variants):
    - Create `backend/security-auth/authentication/DATA_RETENTION_POLICY.md` (global default)
    - Create `backend/security-auth/authentication/DATA_RETENTION_POLICY_EU.md` (GDPR-specific)
    - Create `backend/security-auth/authentication/DATA_RETENTION_POLICY_USA.md` (CCPA-specific)
    - Document retention periods for all authentication data types per region
    - Define deletion triggers and procedures

- [x] **1.5** Write unit tests
  - **[CRITICAL]** Rust crypto functions (100% coverage):
    - Email encryption/decryption with zeroization
    - Algorithm versioning (multiple versions)
    - Key rotation (re-encryption)
    - Advanced password pattern detection
    - Argon2id auto-tuning
    - Batch encryption operations
  - **[CRITICAL]** Django service layer tests:
    - Email encryption (encrypt/decrypt cycle)
    - Recovery key versioning (upgrade scenarios)
    - Session fingerprinting (device change detection)
    - Backup code expiry (notification triggers)
    - Key rotation (background job)
  - **[PERFORMANCE]** Integration tests:
    - Encryption/decryption performance benchmarks
    - Composite index query performance
    - Batch operation efficiency
    - Rate limiting under load
  - **[SECURITY]** Security tests:
    - Timing attack resistance (constant-time responses)
    - Password pattern rejection
    - Algorithm downgrade attack prevention

- [x] **1.6** Set up module-scoped penetration testing infrastructure
  - **[PENTEST-SETUP]** Create pentest directory structure:
    - Create `backend/security-auth/pentests/` directory
    - Create `backend/security-auth/pentests/fixtures/` for test data
    - Create `backend/security-auth/pentests/README.md` with usage instructions
  - **[PENTEST-SETUP]** Set up Python testing infrastructure:
    - Create `backend/security-auth/pentests/conftest.py` with pytest fixtures
    - Add `graphql_client` fixture for GraphQL testing
    - Add `test_user`, `test_admin` fixtures
    - Add `blacklisted_ip`, `whitelisted_ip` fixtures
  - **[PENTEST-SETUP]** Install testing dependencies:
    - Add `pytest-asyncio`, `pytest-django`, `requests` to test requirements
    - Add `faker` for generating test data
    - Add `pytest-cov` for coverage reporting
  - **[PENTEST-DOC]** Document relationship with syntek-infrastructure:
    - Note: Heavy Rust pentest scanners located in `syntek-infrastructure/security/pentest/scanners/`
    - Note: Module pentests focus on authentication-specific vulnerabilities
    - Note: Integration with DefectDojo via syntek-infrastructure CI/CD
  - **Effort:** 4-6 hours

- [x] **1.7** Implement Social Authentication Backend (`backend/security-auth/authentication/`)
  - **Module Location:** Services in `backend/security-auth/authentication/services/oauth/`, Models in `backend/security-auth/authentication/models/`
  - **[SOCIAL-AUTH] Database:**
    - Create `auth_social_account` table with OAuth token encryption
    - Create `auth_oauth_state` table for CSRF protection
    - Create `auth_social_login_attempt` table for audit logging
    - Add `social_registration`, `social_provider` columns to `core_user`
  - **[SOCIAL-AUTH] Rust Security:**
    - Implement OAuth token encryption (AES-256-GCM)
    - Implement OAuth token decryption with zeroization
    - Add PKCE code challenge/verifier generation
    - Add state token generation (cryptographically secure random)
  - **[SOCIAL-AUTH] Django Services:**
    - `GoogleOAuthService` - Google OAuth 2.0 + OIDC integration
    - `GitHubOAuthService` - GitHub OAuth 2.0 integration
    - `MicrosoftOAuthService` - Microsoft OAuth 2.0 + OIDC integration
    - `AppleOAuthService` - Apple Sign In integration (Post-MVP)
    - `OAuthStateManager` - CSRF state validation
    - `SocialAccountLinker` - Account linking/unlinking logic
    - `SocialProfileSyncService` - Sync profile photo/name from social accounts
  - **[SOCIAL-AUTH] Email Conflict Resolution:**
    - Implement email conflict detection (existing user with same email)
    - Block auto-login if email exists (require password login + account linking)
    - Auto-link social accounts if email verified and user authenticated
  - **[SOCIAL-AUTH] Unit Tests:**
    - Test OAuth flows (initiate, callback, token exchange)
    - Test CSRF state validation
    - Test email conflict scenarios
    - Test PKCE flows (mobile)
    - Test account linking/unlinking
  - **Effort:** 20-24 hours

- [x] **1.8** Implement Enhanced Auto-Logout (`backend/security-auth/authentication/`)
  - **Module Location:** Services in `backend/security-auth/authentication/services/`, Models in `backend/security-auth/authentication/models/`
  - **[AUTO-LOGOUT] Database:**
    - Add `last_activity_at`, `idle_timeout_seconds`, `absolute_timeout_at` to `auth_session`
    - Add `remember_me`, `auto_logout_warned_at`, `activity_count` to `auth_session`
    - Add indexes for session timeout queries
  - **[AUTO-LOGOUT] Django Services:**
    - `AutoLogoutService` - Session timeout checking and activity updates
    - `RememberMeService` - "Keep me logged in" functionality
    - `SessionActivityTracker` - Track user activity events
  - **[AUTO-LOGOUT] Background Tasks:**
    - Celery task: Cleanup expired sessions (runs every 5 minutes)
    - Celery task: Send auto-logout warnings (runs every 1 minute)
  - **[AUTO-LOGOUT] Configuration:**
    - Add `SESSION.IDLE_TIMEOUT`, `SESSION.ABSOLUTE_TIMEOUT` settings
    - Add `SESSION.WARNING_BEFORE_LOGOUT`, `SESSION.REMEMBER_ME_DURATION` settings
  - **[AUTO-LOGOUT] Unit Tests:**
    - Test idle timeout calculation
    - Test absolute timeout
    - Test warning generation
    - Test remember me functionality
  - **Effort:** 12-16 hours

**Deliverable:** Backend services ready for GraphQL integration. Can create users, hash passwords, encrypt emails/phone numbers/IPs, generate tokens, detect advanced password patterns, track sessions, rotate keys, **handle OAuth flows with 7 social providers, manage auto-logout with activity tracking and warnings**. **Pentest infrastructure ready for module-specific security testing.**

**Testing Criteria:**

```bash
# Rust tests
cargo test --package syntek-security
cargo test --package syntek-encryption

# Python tests
pytest backend/security-auth/authentication/tests/test_phone_verification.py
pytest backend/security-auth/authentication/tests/test_recovery_keys.py
```

#### Phase 2: GraphQL API Layer (Week 2-3)

**Tasks:**

- [ ] **2.1** Create GraphQL types (`graphql/auth/`)
  - **Module Location:** Types in `graphql/auth/types/`, Queries in `graphql/auth/queries/`, Mutations in `graphql/auth/mutations/`
  - `PhoneVerificationType`
  - **[IMPROVEMENT]** `RecoveryKeyType` (add `algorithm_version`, `created_at`, `expires_at`)
  - **[IMPROVEMENT]** `MFAStatusType` (add backup codes remaining, recovery keys remaining, expiry warnings)
  - `IpTrackingEntryType`
  - `IpWhitelistEntryType`
  - `IpBlacklistEntryType`
  - `LoginAttemptEntryType`
  - `SuspiciousActivityEntryType`
  - **[NEW]** `SessionSecurityType` (device fingerprint, suspicious patterns, device changes)
  - **[NEW]** `BackupCodeStatusType` (count remaining, expiry date, low-code warning)
  - Enhanced `UserType` **[CRITICAL]** Return decrypted email, never expose encrypted field

- [ ] **2.2** Implement GraphQL mutations (`graphql/auth/mutations/`)
  - **Module Location:** All mutations in `graphql/auth/mutations/`, using services from `backend/security-auth/authentication/services/`
  - **[CRITICAL]** `sendPhoneVerification` with rate limiting (`@rate_limit('3/hour', scope='ip')`)
  - **[SECURITY] M-2:** Enhanced `sendPhoneVerification` with global rate limiting:
    - Per-IP limit: 3/hour (existing)
    - Global limit: 1000/hour across all IPs
    - Daily budget enforcement: $500/day (configurable)
    - CAPTCHA escalation after 100 SMS/hour globally
    - Cost monitoring and alerting
  - **[CRITICAL]** `verifyPhone` with rate limiting (`@rate_limit('5/15min', scope='ip')`)
  - **[IMPROVEMENT]** `generateRecoveryKeys` (with versioning, expiry dates, format options)
  - `loginWithRecoveryKey`
  - **[SECURITY] M-1:** Enhanced `requestPasswordReset` with constant-time delays:
    - Fixed response time (250ms minimum) for all outcomes
    - Constant-time whether user exists or not
    - Generic success message ("If account exists, reset email sent")
    - Logging without timing information leakage
  - **[GDPR] GAP-03:** Enhanced `register` mutation with legal compliance:
    - Add `acceptPrivacyPolicy: Boolean!` (required - GDPR/CCPA/legal requirement)
    - Add `acceptTerms: Boolean!` (required - Terms of Service/contractual agreement)
    - Add `phoneConsent: Boolean` (optional, required if phone provided)
    - Store acceptance timestamps and document versions (per region)
    - Note: Both Privacy Policy AND Terms of Service are legally required:
      - Privacy Policy: GDPR Art. 13/14 (data processing transparency)
      - Terms of Service: Contractual agreement (service rules, liability, disputes)
    - Support regional variants: EU/UK (GDPR), USA (CCPA), Canada (PIPEDA), Australia (Privacy Act), etc.
  - **[GDPR] GAP-04:** `updateEmail` mutation:
    - Require password verification
    - Send verification email to new address
    - Atomic email change after verification
  - **[GDPR] GAP-04:** `updatePhoneNumber` mutation:
    - Require password verification
    - Send verification SMS to new number
    - Atomic phone change after verification
  - **[GDPR] GAP-05:** `updateUsername` mutation:
    - Require password verification
    - Check username availability
  - **[GDPR] GAP-07:** `deleteAccount` mutation:
    - Soft delete with 30-day grace period
    - Immediate session invalidation
    - Schedule hard delete job
  - **[GDPR] GAP-13:** `withdrawPhoneConsent` mutation:
    - Remove phone number from account
    - Log consent withdrawal in ConsentLog
    - Disable SMS-based features
  - **[GDPR] GAP-16:** `optOutOfIPTracking` mutation:
    - Stop collecting IP addresses for user
    - Delete existing IP tracking data
    - Log opt-out decision
  - `addIpWhitelist`, `removeIpWhitelist`
  - `addIpBlacklist`, `removeIpBlacklist`
  - **[NEW]** `getSessionSecurity` (view current session fingerprint and security status)
  - **[NEW]** `terminateSuspiciousSessions` (kill sessions flagged as suspicious)
  - **[IMPROVEMENT]** `regenerateBackupCodes` (track generation date, set expiry)
  - **[CRITICAL]** Enhanced `register`:
    - Encrypt email before storage
    - Add username, phone, track IP
    - **Constant-time response** (sleep to fixed duration regardless of outcome)
    - Generic error messages (no "email already exists")
  - **[CRITICAL]** Enhanced `login`:
    - Support recovery key
    - Check IP whitelist/blacklist
    - Track attempt with encrypted IP
    - Session fingerprinting
    - **Constant-time response** (fixed duration for valid/invalid credentials)
    - Generic error messages ("Invalid credentials")
  - **[CRITICAL]** All authentication mutations:
    - Implement constant-time middleware
    - Consistent error messages (prevent enumeration)
    - Comprehensive logging with sanitization

- [ ] **2.3** Implement GraphQL queries (`graphql/auth/queries/`)
  - **Module Location:** All queries in `graphql/auth/queries/`, using services from `backend/security-auth/authentication/services/`
  - **[IMPROVEMENT]** `mfaStatus` (TOTP enabled, backup codes remaining with expiry, recovery keys with expiry)
  - `ipWhitelist`, `ipBlacklist`
  - `ipTrackingHistory` (user's IP history, decrypted for authorized users)
  - `loginAttempts` (successful and failed login attempts)
  - `suspiciousActivity` (flagged login attempts)
  - **[NEW]** `sessionSecurity` (current session fingerprint, device changes, risk score)
  - **[NEW]** `activeSessions` (all active sessions with device info, last activity, location)
  - Enhanced `currentUser` (include phone verification status, current IP, session security)
  - **[GDPR] GAP-15:** `exportMyData` query (DSAR - Data Subject Access Request):
    - Export all authentication data in JSON/CSV format
    - Include: email, username, phone, registration date, login history, IP tracking, sessions, MFA devices
    - Decrypt all encrypted fields for user's own data
    - Support download as JSON or CSV

- [ ] **2.4** Add security extensions (`graphql/core/`)
  - **Module Location:** Security middleware in `graphql/core/middleware/`, using extensions from `graphql/core/extensions/`
  - **[CRITICAL]** Granular rate limiting per endpoint:
    - `sendPhoneVerification`: 3/hour per IP (prevent SMS cost attacks)
    - `verifyPhone`: 5/15min per IP
    - `sendEmailVerification`: 3/hour per IP
    - `requestPasswordReset`: 3/hour per IP
    - `login`: 5/15min per IP
    - `totpVerify`: 5/15min per IP
    - All other endpoints: see detailed config in Critical Issue #3
  - **[SECURITY] M-2:** Global SMS cost attack prevention:
    - Global rate limit counter (Redis-based, shared across instances)
    - 1000 SMS/hour global limit (across all IPs)
    - Daily budget tracking ($500/day default)
    - Automatic blocking when budget exceeded
    - CAPTCHA escalation after threshold
    - Alert system (email/Slack) for approaching limits
    - Cost analytics dashboard integration
  - **[CRITICAL]** Constant-time response middleware:
    - Apply to all authentication endpoints
    - Fixed response time (e.g., 200ms minimum)
    - Sleep to target duration if response faster
    - Log timing to detect anomalies
  - CAPTCHA validation middleware (apply after rate limit violations)
  - Input sanitisation (XSS, SQL injection prevention)
  - **[NEW]** Session fingerprint middleware (capture device info on each request)
  - **[NEW]** Suspicious activity detection middleware (flag unusual patterns)

- [ ] **2.5** Database Optimizations - High Priority (P1)
  - **[DB-P1] Extract JSON Fields for Efficient Querying:**
    - Add `country_code VARCHAR(2)` to `auth_ip_tracking` (extracted from location_data)
    - Add `city_encrypted BYTEA` to `auth_ip_tracking` (encrypted city name)
    - Create `INDEX idx_ip_tracking_country ON auth_ip_tracking(country_code)` - enables filtering by country
    - Populate fields from existing location_data JSONB (data migration)
    - Benefit: Enables efficient country/city filtering without JSONB queries (4x faster)
  - **[DB-P1] Bloom Filter for IP Blacklist:**
    - Implement in-memory Bloom filter (probabilistic data structure)
    - 1M IP capacity with 1% false positive rate
    - Fast path: If Bloom filter says "not blacklisted", skip Redis/DB (50% query reduction)
    - Update Bloom filter when blacklist changes
    - Fallback to Redis/DB for possible blacklisted IPs
    - Package: `django-bloom-filter` or custom implementation
  - **[DB-P1] Query Optimization:**
    - Add `select_related()` and `prefetch_related()` to prevent N+1 queries in GDPR data export
    - Optimize `exportMyData` query (fetch user + related data in 3-5 queries max)

- [ ] **2.6** Rust Security Enhancements - High Priority (P1)
  - **[RS-P1-1] AES-256-GCM Implementation** (8 hours):
    - Add AES-256-GCM support to `rust/encryption/src/field_level.rs`
    - Implement algorithm selection enum: `EncryptionAlgorithm { AES256GCM, ChaCha20Poly1305 }`
    - Implement `encrypt_field_with_algo(plaintext, key, algo) -> Vec<u8>`
    - Use `aes-gcm` crate with hardware acceleration on x86_64
    - Or document ChaCha20-Poly1305 as acceptable (equally secure, better on ARM/mobile)
  - **[RS-P1-2] Key Versioning Support** (12 hours):
    - Modify encrypted data format: `version (1 byte) || key_id (4 bytes) || nonce (12 bytes) || ciphertext`
    - Implement `encrypt_field_with_version(plaintext, key, key_id) -> Vec<u8>`
    - Implement `decrypt_field_with_version(ciphertext, keys: HashMap<u32, &[u8]>) -> Result<String>`
    - Support multi-key decryption (lookup key by ID, fallback to current key)
    - Migration script: re-encrypt existing data with version header
    - Add key rotation tests (encrypt with key v1, decrypt with key v2)
  - **[RS-P1-4] Constant-Time Utilities** (4 hours):
    - Create `rust/security/src/constant_time.rs`
    - Implement `compare_tokens(a: &str, b: &str) -> bool` using `subtle::ConstantTimeEq`
    - Implement `compare_hmac(a: &[u8], b: &[u8]) -> bool`
    - Add PyO3 bindings: `compare_tokens_py()`, `compare_hmac_py()`
    - Add timing attack tests (measure variance < 1µs across 10,000 comparisons)
  - **[RS-P1-5] FFI Security Documentation** (2 hours):
    - Document FFI limitation: Rust cannot zeroize Python's heap memory
    - Provide Python examples using `SecureString` or similar
    - Document `decrypt_field_secure()` for high-security operations (returns SecretString)
    - Add security considerations section to README
    - Explain zeroization strategy: Rust zeroizes owned data, Python must handle its own
    - Add query profiling middleware (log queries > 100ms)

- [ ] **2.7** Module-scoped penetration testing - GraphQL & Authentication
  - **[PENTEST-GRAPHQL]** Create GraphQL security test suite (`pentests/test_graphql_security.py`):
    - Test introspection disabled in production
    - Test query depth limiting (reject queries > 10 levels deep)
    - Test query complexity limiting (reject queries > 1000 complexity)
    - Test batch mutation limiting (reject > 10 mutations in single request)
    - Test authentication required for protected queries
  - **[PENTEST-PASSWORD]** Create password security test suite (`pentests/test_password_security.py`):
    - Test weak password rejection (common patterns, keyboard sequences, repeated chars)
    - Test password breach detection (Have I Been Pwned integration)
    - Test password history enforcement (cannot reuse last 5 passwords)
    - Test password pattern detection (dates, l33t speak, common substitutions)
  - **[PENTEST-AUTH]** Create authentication flow test suite (`pentests/test_auth_flows.py`):
    - Test registration flow (email enumeration prevention, CAPTCHA validation)
    - Test login flow (brute force protection, rate limiting, timing attack resistance)
    - Test TOTP flow (brute force protection, time drift handling)
    - Test recovery flow (token prediction resistance, rate limiting)
  - **[PENTEST-CI]** Integrate pentests into PR checks:
    - Add `pytest backend/security-auth/pentests/` to CI workflow
    - Add pentest coverage reporting (target: > 90%)
    - Add GitHub Actions workflow for PR security checks
  - **Effort:** 8-12 hours
  - **Note:** Heavy scanners (auth_brute_force, mfa_bypass, crypto_side_channel) located in syntek-infrastructure

- [ ] **2.8** Implement Social Authentication GraphQL API (`graphql/auth/`)
  - **Module Location:** Mutations in `graphql/auth/mutations/social.py`, Queries in `graphql/auth/queries/social.py`, Types in `graphql/auth/types/social.py`
  - **[SOCIAL-AUTH-GRAPHQL] Mutations:**
    - `initiateSocialLogin` - Generate OAuth authorization URL
    - `handleSocialCallback` - Exchange code for tokens, create/link account
    - `linkSocialAccount` - Link social account to authenticated user
    - `unlinkSocialAccount` - Unlink social account (requires password)
    - `refreshSocialToken` - Manually refresh OAuth token
    - `setSocialAccountPrimary` - Set primary social login method
    - `syncSocialProfile` - Sync profile photo/name from social account
  - **[SOCIAL-AUTH-GRAPHQL] Queries:**
    - `socialAccounts` - List linked social accounts
    - `availableSocialProviders` - List enabled providers with UI config
    - `socialLoginHistory` - View social login attempt history
  - **[SOCIAL-AUTH-GRAPHQL] Types:**
    - `SocialAccountType`, `SocialProviderType`, `SocialLoginAttemptType`
  - **[SOCIAL-AUTH-GRAPHQL] Security:**
    - Rate limiting: 10 OAuth callbacks per IP per hour
    - Rate limiting: 5 link/unlink operations per user per hour
    - CSRF validation on all OAuth callbacks
  - **[SOCIAL-AUTH-GRAPHQL] GDPR:**
    - Add social account data to DSAR export
    - Revoke OAuth tokens on account deletion
    - Track consent for profile photo sync
  - **Effort:** 16-20 hours

- [ ] **2.9** Implement Auto-Logout GraphQL API (`graphql/auth/`)
  - **Module Location:** Mutations in `graphql/auth/mutations/session.py`, Queries in `graphql/auth/queries/session.py`, Types in `graphql/auth/types/session.py`
  - **[AUTO-LOGOUT-GRAPHQL] Mutations:**
    - `updateSessionActivity` - Update last activity timestamp
    - `enableRememberMe` - Enable "Keep me logged in"
    - `disableRememberMe` - Disable "Keep me logged in"
  - **[AUTO-LOGOUT-GRAPHQL] Queries:**
    - `sessionStatus` - Check session timeout status
  - **[AUTO-LOGOUT-GRAPHQL] Types:**
    - `SessionStatusType`, `UpdateSessionActivityResponse`
  - **Effort:** 4-6 hours

**Deliverable:** Complete GraphQL API for authentication **including social OAuth flows (7 providers) and session activity management**. All mutations/queries tested via GraphiQL. **Module-scoped pentests integrated into PR checks.**

**Testing Criteria:**

```graphql
# Test registration with phone
mutation {
  register(
    email: "test@example.com"
    password: "SecureP@ssw0rd123"
    username: "testuser"
    phoneNumber: "+441234567890"
  ) {
    success
    user {
      id
      email
      username
      phoneVerified
    }
  }
}

# Test phone verification
mutation {
  sendPhoneVerification(phoneNumber: "+441234567890") {
    success
    expiresIn
  }
}
```

#### Phase 3: Web Frontend (Next.js/React) (Week 3-4)

**Tasks:**

- [ ] **3.1** Create UI components (`web/packages/ui-auth/`)
  - **Module Location:** All components in `web/packages/ui-auth/src/components/`
  - **[GDPR] GAP-01, GAP-03:** Registration form (with username, phone fields):
    - Phone consent checkbox (required if phone provided - GDPR data processing consent)
    - **Privacy Policy acceptance checkbox (required - GDPR Art. 13/14 transparency requirement)**
    - **Terms of Service acceptance checkbox (required - contractual agreement for service use)**
    - Links to regional legal documents:
      - `/legal/privacy-policy-{region}` (e.g., privacy-policy-eu, privacy-policy-usa)
      - `/legal/terms-of-service-{region}` (e.g., terms-of-service-eu, terms-of-service-usa)
    - Auto-detect user region (IP geolocation) and show appropriate documents
    - Allow manual region selection if auto-detection incorrect
    - NO pre-checked boxes (GAP-12 - GDPR requires affirmative action)
    - Note: Both Privacy Policy AND Terms of Service are required:
      - Privacy Policy: Legal requirement (GDPR/CCPA) - explains data processing
      - Terms of Service: Business requirement - defines service rules, liability, disputes
  - Login form (with recovery key option)
  - Phone verification modal
  - TOTP setup wizard
  - **[IMPROVEMENT]** Recovery key display/download component:
    - Printable PDF format
    - Downloadable text/JSON
    - Copy-to-clipboard
    - Expiry date display
    - "I have saved my keys" confirmation checkbox
  - **[IMPROVEMENT]** Password strength indicator:
    - Real-time pattern detection
    - Strength meter (weak/fair/good/strong)
    - Specific feedback (e.g., "Contains keyboard pattern", "Too similar to email")
    - Have I Been Pwned check (optional, client-side API call)
  - **[NEW]** WebAuthn/Passkey components:
    - Passkey registration wizard (browser compatibility check, step-by-step guide)
    - Passkey authentication button (with fallback to password)
    - Passkey management UI (list, rename, delete passkeys)
    - Device name input (e.g., "iPhone 13", "MacBook Pro")
  - **[NEW]** Session security dashboard:
    - Active sessions list with device info
    - Current session fingerprint display
    - Device change alerts
    - "Terminate suspicious sessions" button
  - **[NEW]** Backup code status indicator:
    - Codes remaining count
    - Expiry date warning
    - "Regenerate codes" button

- [ ] **3.2** Implement authentication hooks (`web/packages/ui-auth/`)
  - **Module Location:** All hooks in `web/packages/ui-auth/src/hooks/`
  - `useAuth` (login, logout, register)
  - `usePhoneVerification` (send code, verify)
  - **[IMPROVEMENT]** `useMFA` (setup TOTP, manage recovery keys, backup code status, expiry warnings)
  - **[IMPROVEMENT]** `usePasswordValidation` (real-time validation with pattern detection, strength scoring, HIBP check)
  - **[NEW]** `usePasskey` (WebAuthn implementation):
    - `registerPasskey()` - Create new passkey credential
    - `authenticateWithPasskey()` - Login with passkey
    - `listPasskeys()` - Get user's passkeys
    - `deletePasskey()` - Remove passkey
    - Browser compatibility detection
    - Fallback handling
    - **[SECURITY] M-3:** WebAuthn attestation validation:
      - Verify authenticator attestation during registration
      - Document attestation formats (packed, fido-u2f, android-key, etc.)
      - Implement attestation validation for NIST AAL3 compliance
      - Log attestation results for security audit
      - Optional: Restrict to specific authenticator types (hardware keys only)
  - **[NEW]** `useSessionSecurity`:
    - `getActiveSessions()` - List all active sessions
    - `terminateSession(sessionId)` - Kill specific session
    - `terminateSuspiciousSessions()` - Kill flagged sessions
    - `getCurrentFingerprint()` - Get current device fingerprint
    - **[SECURITY] L-2:** Enhanced fingerprinting with additional entropy:
      - WebGL vendor and renderer detection
      - Audio context fingerprinting
      - Font detection (installed fonts)
      - Hardware concurrency (CPU cores)
      - Device memory (RAM, Chrome only)
      - Browser features detection
      - Configurable fingerprint levels: minimal, balanced, aggressive
      - GDPR consent mechanism for enhanced fingerprinting
      - Privacy-first approach (balanced level by default)
  - **[GDPR] GAP-04, GAP-05:** `useProfileUpdate`:
    - `updateEmail(newEmail, password)` - Update email with verification
    - `updatePhone(newPhone, password)` - Update phone with verification
    - `updateUsername(newUsername, password)` - Update username
  - **[GDPR] GAP-07, GAP-13, GAP-15, GAP-16:** `useGDPR`:
    - `deleteAccount()` - Request account deletion (30-day grace period)
    - `exportMyData()` - Download all authentication data (JSON/CSV)
    - `withdrawPhoneConsent()` - Remove phone number and consent
    - `optOutOfIPTracking()` - Disable IP address collection

- [ ] **3.3** Create authentication pages
  - **[GDPR] GAP-01, GAP-03:** `/auth/register` with GDPR compliance:
    - Real-time password validation and pattern detection
    - Phone consent checkbox (optional, required if phone provided)
    - Privacy policy acceptance checkbox (required)
    - Terms acceptance checkbox (required)
    - Links to privacy policy and terms
  - `/auth/login` **[IMPROVED]** with passkey button, recovery key option
  - `/auth/verify-email`
  - `/auth/verify-phone`
  - `/auth/setup-mfa` **[IMPROVED]** with backup code expiry, recovery key expiry
  - `/auth/recovery` **[IMPROVED]** with multiple format downloads (PDF, text, JSON)
  - **[NEW]** `/auth/setup-passkey` - Passkey registration wizard with compatibility check
  - **[NEW]** `/auth/manage-passkeys` - List and manage registered passkeys
  - **[NEW]** `/auth/sessions` - Session security dashboard
  - **[NEW]** `/auth/security` - Security settings (MFA, passkeys, sessions, device management)
  - **[GDPR] GAP-04, GAP-05:** `/account/profile` - Update email, phone, username
  - **[GDPR] GAP-15:** `/account/export-data` - Download authentication data (DSAR)
  - **[GDPR] GAP-07:** `/account/delete` - Request account deletion with 30-day grace
  - **[GDPR] GAP-13, GAP-16:** `/account/privacy` - Manage consents (phone, IP tracking)

- [ ] **3.4** Implement state management
  - Auth context provider
  - Token storage (httpOnly cookies)
  - Session persistence

- [ ] **3.5** Add CAPTCHA integration
  - reCAPTCHA v2/v3 wrapper component
  - hCaptcha support

- [ ] **3.6** Database Optimizations - Medium Priority (P2)
  - **[DB-P2] Database Monitoring:**
    - Enable `pg_stat_statements` PostgreSQL extension
    - Create monitoring dashboard (Grafana/custom)
    - Set up slow query alerts (queries > 100ms)
    - Weekly slow query review process
    - Query performance tracking over time
  - **[DB-P2] Read Replica Configuration:**
    - Set up PostgreSQL read replica for analytics queries
    - Configure Django database routing (write to primary, read analytics from replica)
    - Offload GDPR data exports to replica
    - Offload IP tracking history queries to replica
    - Monitor replication lag (alert if > 5 seconds)
  - **[DB-P2] Schema Version Validation:**
    - Create Django management command: `python manage.py validate_schema`
    - Check for missing indexes (compare expected vs actual)
    - Verify all foreign key constraints exist
    - Check table partitions are created correctly
    - Run in CI/CD pipeline before deployment
    - Alert on schema drift between environments

- [ ] **3.7** Rust Security Optimizations - Performance (P2)
  - **[RS-P2-1] Batch Encryption Utilization** (4 hours):
    - Implement batch encryption for user registration (email + phone + location encrypted together)
    - Create `encrypt_batch(fields: Vec<&str>, key: &[u8]) -> Result<Vec<Vec<u8>>>`
    - Use during IP tracking (encrypt IP + location in single call)
    - Reduce PyO3 FFI overhead (one FFI call instead of 3-4)
    - Add benchmarks: single vs batch encryption performance
  - **[RS-P2-2] PyO3 Overhead Benchmarking** (6 hours):
    - Add Criterion benchmarks for all PyO3 bindings
    - Measure FFI overhead vs pure Rust performance
    - Benchmark `hash_password_py()` vs native `hash_password()` (target: <10µs overhead)
    - Benchmark `encrypt_field_py()` vs native `encrypt_field()` (target: <5µs overhead)
    - Profile with `flamegraph` to identify bottlenecks
    - Document acceptable overhead thresholds
  - **[RS-P2-3] Argon2 Auto-Tuning** (8 hours):
    - Add runtime parameter tuning to adjust for server hardware
    - Implement `auto_tune_argon2() -> Params` function
    - Measure hash time with default params (19 MiB, 2 iterations)
    - Adjust memory/iterations to target 200ms on current hardware
    - Save tuned parameters to config file
    - Add Django management command: `python manage.py tune_argon2`
    - Re-tune on deployment to new hardware

- [ ] **3.8** Module-scoped penetration testing - GDPR & Session Security
  - **[PENTEST-GDPR]** Create GDPR compliance test suite (`pentests/test_gdpr_compliance.py`):
    - Test data export (DSAR) completeness (all user PII included)
    - Test data export format (JSON/CSV/PDF generation)
    - Test data export delivery (automated email with download link)
    - Test right to erasure (30-day grace period, hard deletion after 30 days)
    - Test consent tracking (phone consent audit trail)
    - Test PII access logging (admin access to encrypted data logged)
  - **[PENTEST-SESSION]** Create session security test suite (`pentests/test_session_security.py`):
    - Test session fixation prevention (session ID changes after login)
    - Test session hijacking detection (IP change, user agent change detection)
    - Test concurrent session limits (max 3 concurrent sessions per user)
    - Test session timeout (idle timeout, absolute timeout)
    - Test device fingerprinting (detect device changes)
  - **[PENTEST-TIMING]** Create timing attack test suite (`pentests/test_timing_attacks.py`):
    - Test email lookup timing (HMAC constant-time, variance < 500µs)
    - Test phone lookup timing (HMAC constant-time, variance < 500µs)
    - Test password verification timing (constant-time, variance < 1ms)
    - Test TOTP verification timing (constant-time, variance < 500µs)
  - **Effort:** 10-14 hours
  - **Note:** Side-channel scanners (crypto_side_channel) located in syntek-infrastructure for advanced testing

- [ ] **3.9** Implement Social Authentication UI (Web) (`web/packages/ui-auth/`)
  - **Module Location:** Components in `web/packages/ui-auth/src/components/social/`, Hooks in `web/packages/ui-auth/src/hooks/`
  - **[SOCIAL-AUTH-WEB] Components:**
    - `SocialLoginButtons` - Display OAuth provider buttons (Google, GitHub, Microsoft)
    - `SocialAccountCard` - Display linked social account with unlink button
    - `SocialAccountsList` - List all linked social accounts
    - `SocialAuthCallback` - Handle OAuth callback redirect
    - `EmailConflictModal` - Display email conflict error with resolution steps
  - **[SOCIAL-AUTH-WEB] Pages:**
    - `/auth/callback/[provider]` - OAuth callback handler
    - `/profile/social-accounts` - Manage linked social accounts
  - **[SOCIAL-AUTH-WEB] Hooks:**
    - `useSocialAuth` - OAuth flow management
    - `useSocialAccounts` - List/link/unlink social accounts
  - **[SOCIAL-AUTH-WEB] Branding:**
    - Add provider logos (Google, GitHub, Microsoft, Apple, Facebook, LinkedIn, X)
    - Follow each provider's brand guidelines
  - **Effort:** 16-20 hours

- [ ] **3.10** Implement Enhanced Auto-Logout UI (Web) (`web/packages/ui-auth/`)
  - **Module Location:** Components in `web/packages/ui-auth/src/components/session/`, Hooks in `web/packages/ui-auth/src/hooks/`
  - **[AUTO-LOGOUT-WEB] Components:**
    - `AutoLogoutWarning` - Warning modal before timeout
    - `SessionActivityTracker` - Track user activity events
    - `RememberMeCheckbox` - "Keep me logged in" option on login page
  - **[AUTO-LOGOUT-WEB] Hooks:**
    - `useAutoLogout` - Auto-logout timer and warning logic
    - `useSessionStatus` - Check session timeout status
    - `useRememberMe` - Enable/disable remember me
  - **[AUTO-LOGOUT-WEB] UI:**
    - Countdown timer in warning modal (5:00, 4:59, 4:58...)
    - "Stay logged in" button to extend session
    - Toast notification on auto-logout
  - **Effort:** 12-14 hours

**Deliverable:** Fully functional web authentication UI with advanced security features. Users can register (with pattern detection), verify email/phone, set up TOTP, register passkeys, view session security, manage backup codes, and login (with constant-time responses), **login with social providers (Google/GitHub/Microsoft), manage linked social accounts, receive auto-logout warnings with countdown timers**. **GDPR compliance and session security validated through pentests.**

**Testing Criteria:**

```bash
# Component tests
pnpm test packages/ui-auth

# E2E tests
pnpm test:e2e --spec auth/registration.spec.ts
pnpm test:e2e --spec auth/phone-verification.spec.ts
```

#### Phase 4: Mobile Frontend (React Native) (Week 4-5)

**Tasks:**

- [ ] **4.1** Create mobile UI components (`mobile/packages/mobile-auth/`)
  - **Module Location:** All components in `mobile/packages/mobile-auth/src/components/`, Screens in `mobile/packages/mobile-auth/src/screens/`
  - **[GDPR] GAP-01, GAP-03:** Registration screen with legal compliance:
    - Real-time password validation
    - Phone consent checkbox (required if phone provided - GDPR data consent)
    - **Privacy Policy acceptance checkbox (required - GDPR/CCPA legal requirement)**
    - **Terms of Service acceptance checkbox (required - contractual agreement)**
    - Tappable links to open regional documents in modal/browser
    - Auto-detect user region and show appropriate documents
    - NO pre-checked boxes (GAP-12 - GDPR requires explicit consent)
    - Note: Both documents required for legal compliance and business protection
  - Login screen **[IMPROVED]** with biometric option, passkey support
  - Phone verification screen
  - TOTP setup screen
  - **[IMPROVEMENT]** Recovery key storage screen:
    - Save to secure device storage
    - Export options (share, print)
    - Expiry date display
  - **[NEW]** Passkey management screen:
    - Register passkey (platform authenticator)
    - List registered passkeys
    - Delete passkeys
    - Device-specific naming
    - **[SECURITY] M-3:** Platform authenticator attestation validation:
      - Verify device attestation during passkey registration
      - Support iOS/Android platform attestation formats
      - Document attestation validation for compliance
      - Log attestation results for security monitoring
  - **[NEW]** Session security screen:
    - Active sessions with device info
    - Current device fingerprint
    - "Terminate suspicious sessions"
  - **[NEW]** Backup code management screen:
    - View codes (with blur/reveal)
    - Expiry warning
    - Regenerate codes
  - **[GDPR] GAP-04, GAP-05:** Profile update screen:
    - Update email with verification
    - Update phone with verification
    - Update username
  - **[GDPR] GAP-15:** Export data screen:
    - Download authentication data (JSON/CSV)
    - View data summary before export
  - **[GDPR] GAP-07:** Account deletion screen:
    - Request deletion with 30-day grace period
    - Confirmation dialog with consequences
  - **[GDPR] GAP-13, GAP-16:** Privacy settings screen:
    - Withdraw phone consent
    - Opt-out of IP tracking
    - View consent history

- [ ] **4.2** Implement biometric authentication (`mobile/packages/security-auth/`)
  - **Module Location:** Biometric services in `mobile/packages/security-auth/src/biometric/`
  - Face ID/Touch ID integration (iOS)
  - Fingerprint/Face unlock (Android)
  - Fallback to password

- [ ] **4.3** Implement secure storage (`mobile/packages/security-auth/`)
  - **Module Location:** Storage services in `mobile/packages/security-auth/src/storage/`
  - Keychain (iOS) integration
  - KeyStore (Android) integration
  - Encrypted token storage

- [ ] **4.4** Add security features (`mobile/packages/security-core/`)
  - **Module Location:** Security utilities in `mobile/packages/security-core/src/utils/`
  - Root/jailbreak detection
  - Certificate pinning
  - Screen capture prevention (sensitive screens)

- [ ] **4.5** Module-scoped penetration testing - IP Security & Mobile
  - **[PENTEST-IP]** Create IP security test suite (`pentests/test_ip_security.py`):
    - Test IP blacklist blocking (blacklisted IPs receive 403)
    - Test IP whitelist bypass (whitelisted IPs bypass rate limiting)
    - Test IP spoofing prevention (X-Forwarded-For validation)
    - Test VPN/proxy detection (flag suspicious IPs)
    - Test geolocation accuracy (city/country detection)
  - **[PENTEST-MOBILE]** Create mobile security test suite (`pentests/test_mobile_security.py`):
    - Test biometric authentication fallback (password required if biometric fails)
    - Test secure storage (tokens encrypted at rest)
    - Test certificate pinning (reject invalid certificates)
    - Test root/jailbreak detection (warn user on compromised devices)
    - Test screen capture prevention (sensitive screens not capturable)
  - **[PENTEST-CROSS-PLATFORM]** Create cross-platform test suite (`pentests/test_cross_platform.py`):
    - Test session sync across web/mobile (logout on one device logs out on all)
    - Test device management (view active sessions on all devices)
    - Test device change notifications (email/SMS alerts for new devices)
  - **Effort:** 8-10 hours
  - **Note:** Mobile-specific scanners located in syntek-infrastructure for advanced device testing

- [ ] **4.6** Implement Social Authentication (Mobile) (`mobile/packages/mobile-auth/`)
  - **Module Location:** Components in `mobile/packages/mobile-auth/src/components/social/`, Services in `mobile/packages/security-auth/src/oauth/`
  - **[SOCIAL-AUTH-MOBILE] Components:**
    - `SocialLoginButtons` - OAuth provider buttons
    - `SocialAccountCard` - Linked social account display
    - `SocialAuthWebView` - In-app browser for OAuth flow
  - **[SOCIAL-AUTH-MOBILE] Screens:**
    - `SocialAuthCallback` - Handle OAuth callback with deep link
    - `SocialAccountsManagement` - List/link/unlink social accounts
  - **[SOCIAL-AUTH-MOBILE] Deep Linking:**
    - Configure deep link: `yourapp://auth/callback/[provider]`
    - Handle OAuth callback redirect from in-app browser
  - **[SOCIAL-AUTH-MOBILE] PKCE:**
    - Implement PKCE flow for all mobile OAuth requests
    - Generate code_verifier and code_challenge
  - **[SOCIAL-AUTH-MOBILE] Platform-Specific:**
    - iOS: Apple Sign In (native SDK)
    - Android: Google Sign In (native SDK)
  - **Effort:** 20-24 hours

- [ ] **4.7** Implement Enhanced Auto-Logout (Mobile) (`mobile/packages/mobile-auth/`)
  - **Module Location:** Components in `mobile/packages/mobile-auth/src/components/session/`, Hooks in `mobile/packages/mobile-auth/src/hooks/`
  - **[AUTO-LOGOUT-MOBILE] Components:**
    - `AutoLogoutWarning` - Native alert/modal before timeout
    - `SessionActivityTracker` - Track app foreground/background
  - **[AUTO-LOGOUT-MOBILE] Background Handling:**
    - Detect app backgrounding and calculate idle time
    - Auto-logout if backgrounded > idle timeout
    - Update activity when app foregrounded
  - **[AUTO-LOGOUT-MOBILE] Hooks:**
    - `useAutoLogout` - Auto-logout with AppState tracking
    - `useSessionStatus` - Session timeout status
  - **Effort:** 8-10 hours

**Deliverable:** Mobile authentication flow complete with biometric support and secure storage, **social provider login (Google/GitHub/Microsoft), native Apple/Google Sign In, PKCE-secured OAuth flows, background auto-logout detection**. **IP security and mobile-specific security validated through pentests.**

**Testing Criteria:**

```bash
# Unit tests
pnpm test packages/mobile-auth

# iOS simulator test
pnpm test:ios

# Android emulator test
pnpm test:android
```

#### Phase 5: CLI Installation Tool (Week 5)

**Tasks:**

- [ ] **5.1** Implement CLI commands
  - `syntek install auth --full`
  - `syntek install auth --minimal`
  - `syntek install auth --web-only`
  - `syntek install auth --mobile-only`

- [ ] **5.2** Create installation workflow
  - Dependency resolution
  - Package installation across layers
  - Database migration execution **[CRITICAL]** Include new tables and composite indexes
  - **[CRITICAL]** Configuration file generation:
    - Email encryption keys (OpenBao integration)
    - Granular rate limiting per endpoint
    - Constant-time response settings
    - Session fingerprinting config
    - Key rotation schedule
    - Backup code expiry settings
    - Geolocation encryption toggle
    - Advanced password pattern detection rules
    - Argon2id auto-tuning parameters
    - **[SECURITY] M-2:** Global SMS cost attack prevention config:
      - Global SMS rate limit (default: 1000/hour)
      - Daily SMS budget limit (default: $500/day)
      - Cost per SMS by provider (Twilio: $0.0075, AWS SNS: $0.00645, etc.)
      - Budget alert thresholds (80%, 90%, 100%)
      - Alert destinations (email, Slack webhook, PagerDuty)
      - CAPTCHA escalation threshold (default: 100 SMS/hour)
      - Automatic blocking configuration
      - Cost analytics integration (Grafana, Datadog)
    - **[SECURITY] M-1:** Constant-time response configuration:
      - Target response time (default: 250ms minimum)
      - Apply to endpoints: register, login, passwordReset, verifyEmail
      - Timing variance logging (alert if >5ms variance detected)
    - **[SECURITY] L-2:** Session fingerprinting level config:
      - Fingerprint level: minimal, balanced (default), aggressive
      - GDPR consent requirement toggle
      - Privacy transparency toggle
    - **[GDPR] GAP-03, GAP-06, GAP-09, GAP-12:** GDPR compliance configuration:
      - Legal document configuration (regional variants):
        - `LEGAL_REGION` - Auto-detect or manual (EU, USA, CA, AU, GLOBAL)
        - `PRIVACY_POLICY_VERSION` - Current version (e.g., "1.2")
        - `TERMS_VERSION` - Current version (e.g., "2.1")
        - `LEGAL_DOCS_PATH` - Path to legal documents (default: `/legal/`)
        - Regional document mapping: `{region: {privacy: 'path', terms: 'path'}}`
      - Data retention periods (authentication data: 30 days post-deletion, IP logs: 90 days)
      - Account deletion grace period (default: 30 days)
      - Consent audit trail toggle (enabled by default)
      - PII access logging toggle (enabled for admins)
      - Encryption key rotation schedule (default: 90 days)
      - Ensure NO pre-checked consent boxes in UI
      - Note: Both Privacy Policy AND Terms of Service paths must be configured

- [ ] **5.3** Add Social Auth Configuration to CLI
  - **[CLI-SOCIAL-AUTH] Installation:**
    - Add `--social-auth` flag to installation command
    - Prompt for enabled providers (Google, GitHub, Microsoft, etc.)
    - Generate OAuth client ID/secret placeholders in `.env`
  - **[CLI-SOCIAL-AUTH] Configuration:**
    - Generate `SYNTEK_SOCIAL_AUTH` configuration template
    - Add provider-specific settings (redirect URIs, scopes, button text)
    - Generate callback URL routes
  - **[CLI-SOCIAL-AUTH] Documentation:**
    - Generate provider setup guides (Google Console, GitHub Apps, etc.)
    - Document OAuth app registration steps
  - **Effort:** 6-8 hours

- [ ] **5.4** Add verification step
  - Check installation success
  - Validate configuration
  - Run smoke tests

- [ ] **5.5** Generate documentation
  - Installation guide
  - Configuration reference
  - Migration guide from existing auth
  - Social auth setup guides for each provider

**Deliverable:** One-command installation of complete auth stack **including social authentication configuration for 7 OAuth providers**.

**Testing Criteria:**

```bash
# Test installation
syntek install auth --full --dry-run
syntek install auth --full

# Verify installation
syntek verify auth
```

#### Phase 6: Integration Testing & Documentation (Week 6)

**Tasks:**

- [ ] **6.1** End-to-end integration tests
  - Complete registration flow (web) **[IMPROVED]** with pattern detection, constant-time responses
  - Complete registration flow (mobile)
  - Login with TOTP (web)
  - Login with biometric (mobile)
  - **[NEW]** Login with passkey (web + mobile)
  - Password reset flow
  - Account recovery with recovery keys **[IMPROVED]** with versioning
  - **[NEW]** Session security testing (fingerprinting, device change detection, suspicious activity)
  - **[NEW]** Backup code expiry and regeneration flow
  - **[NEW]** Key rotation testing (re-encryption of existing data)
  - **[GDPR]** Test all authentication-specific GDPR features:
    - Registration with phone consent and privacy policy acceptance
    - Email/phone/username update with verification
    - Account deletion (soft delete → 30-day grace → hard delete)
    - Data export (DSAR) - verify all authentication data included
    - Phone consent withdrawal
    - IP tracking opt-out
    - Verify NO pre-checked consent boxes

- [ ] **6.2** Performance testing
  - Login endpoint load testing (1000 req/s)
  - Encryption/decryption benchmarks
  - GraphQL query complexity analysis
  - **[DB] Database Performance Testing:**
    - Login query performance (<5ms target with email_hash index)
    - IP blacklist check performance (<2ms with Redis cache)
    - GDPR data export query optimization (select_related/prefetch_related, <500ms for 1M users)
    - Rate limiting query performance (composite indexes, <3ms)
    - Partition query performance (verify monthly partitions work)
    - Index usage analysis (identify unused indexes, verify critical indexes used)
    - Query plan analysis (EXPLAIN ANALYZE for all critical queries)
    - Load test with 1M users, 10M IP tracking records, 100K login attempts
    - Verify no N+1 queries in GDPR export (django-debug-toolbar)
    - Test soft delete performance (query exclusion overhead)
    - Bloom filter effectiveness (measure hit rate, false positive rate)

- [ ] **6.3** Security audit
  - **[CRITICAL]** Test all 6 critical security fixes:
    - **#1 Email Encryption:** Verify emails encrypted at rest, decrypted on read, never exposed in plain
    - **#2 Algorithm Versioning:** Test recovery key upgrades, no downgrade attacks possible
    - **#3 Rate Limiting:** Test all endpoints, verify SMS cost attack prevention, no bypass possible
    - **#4 Timing Attacks:** Measure response times, verify constant-time responses (±5ms variance max)
    - **#5 Geolocation Privacy:** Verify city/country encrypted if stored, consent mechanism works
    - **#6 Key Rotation:** Test re-encryption job, zero-downtime rotation, key versioning
  - **[SECURITY]** Test security review findings (M-1, M-2, M-3, L-1, L-2):
    - **[SECURITY] M-1:** Account enumeration via timing attacks:
      - Test password reset endpoint timing (valid vs invalid emails)
      - Verify constant-time responses (250ms ±5ms for all outcomes)
      - Test registration endpoint (no "email exists" leaks)
      - Test login endpoint (generic "invalid credentials")
      - Measure timing variance across 1000 requests
    - **[SECURITY] M-2:** SMS cost attack protection (HIGH PRIORITY):
      - Simulate distributed attack from 1000 IPs
      - Verify global SMS rate limit enforcement (1000/hour)
      - Test daily budget blocking ($500/day default)
      - Verify CAPTCHA escalation after threshold
      - Test cost monitoring and alerting
      - Verify no bypass via IP rotation or header manipulation
      - Test provider-level failover under budget constraints
    - **[SECURITY] M-3:** WebAuthn attestation validation:
      - Test attestation verification during passkey registration
      - Verify attestation formats (packed, fido-u2f, android-key)
      - Test with hardware keys (YubiKey, Titan Security Key)
      - Test with platform authenticators (Touch ID, Windows Hello)
      - Verify attestation logging for audit
      - Document attestation validation for NIST AAL3 compliance
    - **[SECURITY] L-1:** Recovery key race condition:
      - Test 100 concurrent recovery key usage attempts
      - Verify only ONE request succeeds (database locking)
      - Test across multiple application instances (Redis lock)
      - Verify no double-use possible
    - **[SECURITY] L-2:** Enhanced session fingerprinting:
      - Test fingerprint entropy with additional sources
      - Verify WebGL, audio, font detection
      - Test fingerprint levels (minimal, balanced, aggressive)
      - Verify GDPR consent mechanism
      - Test privacy transparency
  - **[SECURITY]** Username/email enumeration testing:
    - Test registration endpoint (no "email exists" leaks)
    - Test login endpoint (generic "invalid credentials")
    - Test password reset (no user existence confirmation)
    - Timing attack resistance (constant-time)
  - **[SECURITY]** Password pattern detection testing:
    - Keyboard patterns (qwerty, asdf)
    - Sequences (123456, abcdef)
    - Common substitutions (P@ssw0rd)
    - Date patterns (DDMMYYYY)
  - **[SECURITY]** Session security testing:
    - Session hijacking detection
    - Device fingerprint changes
    - Impossible travel detection
    - Suspicious activity flagging
  - OWASP Top 10 compliance verification
  - NIST 800-63B alignment check (AAL1, AAL2, AAL3)
  - Penetration testing (authentication bypass attempts)
  - Dependency vulnerability scan (Rust, Python, Node.js)
  - **[RUST-SECURITY] Comprehensive Rust Security Testing:**
    - **Fuzzing Tests:** Use AFL.rs or cargo-fuzz for encryption/decryption (find edge cases)
    - **Timing Attack Tests:** Measure constant-time HMAC comparison (variance < 1µs across 10,000 calls)
    - **Memory Leak Tests:** Run valgrind or AddressSanitizer on Rust modules
    - **Side-Channel Tests:** Cache-timing analysis for cryptographic operations
    - **Key Rotation Tests:** Zero-downtime re-encryption with versioned keys
    - **PyO3 Integration Tests:** Test all Python bindings from Django (encrypt/decrypt cycle)
    - **Error Handling Tests:** Verify FFI boundary error propagation (Rust → Python)
    - **Concurrent Encryption Tests:** Thread safety verification (1000 parallel encryptions)
    - **Zeroization Tests:** Verify plaintext zeroized after encryption (memory dumps)
    - **Input Validation Tests:** Test email/phone/IP validators with malformed inputs
    - **Argon2 Parameter Tests:** Verify OWASP 2025 params (19456 KiB, 2 iterations, 1 parallelism)
    - **HMAC Correctness Tests:** Verify hash-for-lookup produces consistent results
    - **Token Randomness Tests:** Statistical tests for uniform distribution (chi-squared test)

- [ ] **6.4** Documentation
  - Architecture overview
  - API reference (GraphQL schema docs)
  - Configuration guide
  - Deployment guide
  - Security best practices
  - Troubleshooting guide
  - **[GDPR] GAP-03:** Legal document templates (regional variants):
    - **Privacy Policy Templates (REQUIRED - GDPR/CCPA legal requirement):**
      - `docs/legal-templates/PRIVACY-POLICY-EU.md` - GDPR-compliant (EU/UK)
      - `docs/legal-templates/PRIVACY-POLICY-USA.md` - CCPA-compliant (California/USA)
      - `docs/legal-templates/PRIVACY-POLICY-CA.md` - PIPEDA-compliant (Canada)
      - `docs/legal-templates/PRIVACY-POLICY-AU.md` - Privacy Act-compliant (Australia)
      - `docs/legal-templates/PRIVACY-POLICY-GLOBAL.md` - Default fallback
    - **Terms of Service Templates (REQUIRED - Business protection):**
      - `docs/legal-templates/TERMS-OF-SERVICE-EU.md` - EU jurisdiction
      - `docs/legal-templates/TERMS-OF-SERVICE-USA.md` - USA jurisdiction
      - `docs/legal-templates/TERMS-OF-SERVICE-CA.md` - Canada jurisdiction
      - `docs/legal-templates/TERMS-OF-SERVICE-AU.md` - Australia jurisdiction
      - `docs/legal-templates/TERMS-OF-SERVICE-GLOBAL.md` - Default fallback
    - Note: Templates include placeholders for company name, DPO contact, jurisdiction
    - **IMPORTANT:** Must be reviewed by lawyer before production deployment
    - Both Privacy Policy AND Terms of Service are required:
      - Privacy Policy: Legal mandate (GDPR Art. 13/14, CCPA Sec. 1798.100)
      - Terms of Service: Contractual protection (liability, disputes, service rules)
  - **[GDPR] GAP-06, GAP-11, GAP-19, GAP-21, GAP-22:** GDPR compliance documentation:
    - `backend/security-auth/authentication/DATA_RETENTION_POLICY.md` - Global retention schedule
    - `backend/security-auth/authentication/DATA_RETENTION_POLICY_EU.md` - GDPR-specific retention
    - `backend/security-auth/authentication/DATA_RETENTION_POLICY_USA.md` - CCPA-specific retention
    - `docs/gdpr/LEGITIMATE-INTEREST-ASSESSMENT-IP-TRACKING.md` - LIA for IP tracking
    - `docs/gdpr/DPIA-BIOMETRIC-AUTHENTICATION.md` - DPIA for Face ID/Touch ID
    - `docs/gdpr/DPIA-IP-TRACKING.md` - DPIA for IP address collection
    - `docs/security/DATABASE-BACKUP-RESTORE-AUTH.md` - Backup procedure for encrypted PII
    - `docs/security/ENCRYPTION-KEY-ROTATION-AUTH.md` - Key rotation for auth encryption keys

- [ ] **6.5** Module-scoped penetration testing - Full Suite & Documentation
  - **[PENTEST-FULL-SUITE]** Execute complete module pentest suite:
    - Run all pentest suites: `pytest backend/security-auth/pentests/`
    - Generate coverage report (target: > 90% security test coverage)
    - Verify all attack vectors tested (OWASP Top 10, authentication-specific)
    - Document test results in `pentests/PENTEST-RESULTS.md`
  - **[PENTEST-OWASP]** OWASP Top 10 2025 verification:
    - A01 (Broken Access Control): Session hijacking, authorization bypass
    - A02 (Cryptographic Failures): Encryption strength, key management, timing attacks
    - A03 (Injection): SQL injection, GraphQL injection, XSS
    - A04 (Insecure Design): Rate limiting, MFA bypass, weak recovery
    - A05 (Security Misconfiguration): Default credentials, verbose errors, CORS
    - A06 (Vulnerable Components): Dependency scanning (cargo audit, pip-audit, npm audit)
    - A07 (Authentication Failures): Brute force, credential stuffing, session fixation
    - A08 (Software/Data Integrity): JWT security, session integrity
    - A09 (Logging Failures): Log analysis, PII leak detection
    - A10 (SSRF): URL validation, webhook security
  - **[PENTEST-DOC]** Create pentest documentation:
    - `pentests/README.md`: How to run module pentests locally
    - `pentests/ATTACK-VECTORS.md`: List of tested attack vectors
    - `pentests/COVERAGE.md`: Test coverage report and gaps
    - `pentests/INTEGRATION-SYNTEK-INFRASTRUCTURE.md`: How to use heavy scanners from syntek-infrastructure
  - **[PENTEST-CI-FINAL]** Final CI/CD integration:
    - Add pentest badge to README (pass/fail status)
    - Add security coverage badge (> 90%)
    - Document pentest schedule (PR checks, nightly, weekly)
    - Note: Heavy automated scans (nightly/weekly) run in syntek-infrastructure
  - **Effort:** 12-16 hours
  - **Note:** This completes module-scoped pentests. For infrastructure-wide pentests, CI/CD automation, and heavy Rust scanners, see syntek-infrastructure/security/pentest/

- [ ] **6.6** Social Authentication Testing
  - **[SOCIAL-AUTH-TEST] Integration Tests:**
    - Test Google OAuth flow (authorization, callback, token exchange)
    - Test GitHub OAuth flow
    - Test Microsoft OAuth flow
    - Test email conflict scenarios
    - Test account linking/unlinking
    - Test PKCE flows (mobile)
  - **[SOCIAL-AUTH-TEST] Security Tests:**
    - Test CSRF state validation
    - Test state token expiration
    - Test OAuth token encryption/decryption
    - Test rate limiting on OAuth callbacks
  - **[SOCIAL-AUTH-TEST] GDPR Tests:**
    - Test DSAR export includes social accounts
    - Test social account deletion
    - Test OAuth token revocation
  - **Effort:** 12-16 hours

- [ ] **6.7** Auto-Logout Testing
  - **[AUTO-LOGOUT-TEST] Integration Tests:**
    - Test idle timeout calculation
    - Test absolute timeout
    - Test session activity updates
    - Test remember me functionality
    - Test auto-logout warnings
  - **[AUTO-LOGOUT-TEST] UI Tests:**
    - Test warning modal display
    - Test countdown timer
    - Test "Stay logged in" button
    - Test mobile background/foreground detection
  - **Effort:** 8-10 hours

- [ ] **6.8** Social Auth Documentation
  - **[SOCIAL-AUTH-DOC] Setup Guides:**
    - Google OAuth setup (Google Console)
    - GitHub OAuth setup (GitHub Apps)
    - Microsoft OAuth setup (Azure App Registration)
    - Apple Sign In setup (Apple Developer Portal)
  - **[SOCIAL-AUTH-DOC] Configuration Reference:**
    - Provider-specific settings
    - Scope explanations
    - Email conflict resolution
  - **[SOCIAL-AUTH-DOC] User Guides:**
    - How to link social accounts
    - How to unlink social accounts
    - How to set primary social login
  - **Effort:** 6-8 hours

**Deliverable:** Production-ready authentication system with complete documentation. All 6 critical security issues resolved, 9 high-priority improvements implemented, 16 authentication-specific GDPR gaps addressed, **comprehensive module-scoped security testing passed (> 90% coverage), social authentication with 7 OAuth providers, enhanced auto-logout with activity tracking**. Heavy penetration testing infrastructure available in syntek-infrastructure.

**Testing Criteria:**

```bash
# E2E tests
pnpm test:e2e --spec auth/complete-flow.spec.ts
pnpm test:e2e --spec auth/passkey-flow.spec.ts
pnpm test:e2e --spec auth/session-security.spec.ts

# Performance tests
k6 run tests/load/auth-endpoints.js
k6 run tests/load/argon2-performance.js

# Security scan
npm audit
pip-audit
cargo audit

# Security-specific tests
pytest tests/security/test_timing_attacks.py
pytest tests/security/test_email_encryption.py
pytest tests/security/test_key_rotation.py
pytest tests/security/test_rate_limiting.py
pytest tests/security/test_constant_time.py

# Social auth tests
pytest backend/security-auth/pentests/test_social_auth_flows.py
pytest backend/security-auth/pentests/test_oauth_security.py
pnpm test packages/ui-auth/social-auth.test.tsx
pnpm test packages/mobile-auth/social-auth.test.tsx

# Auto-logout tests
pytest backend/security-auth/pentests/test_auto_logout.py
pnpm test packages/ui-auth/auto-logout.test.tsx
pnpm test packages/mobile-auth/auto-logout.test.tsx
```

---

### 🔒 Code Review Implementation Summary

**All implementation phases have been updated to include:**

#### Phase 1 (Backend Foundation) - Added

- **[CRITICAL]** Email encryption/decryption (Critical Issue #1)
- **[CRITICAL]** Algorithm versioning for recovery keys (Critical Issue #2)
- **[CRITICAL]** Geolocation data encryption (Critical Issue #5)
- **[CRITICAL]** Key rotation implementation (Critical Issue #6)
- **[IMPROVEMENT]** Advanced password pattern detection (Improvement #7)
- **[IMPROVEMENT]** Argon2id auto-tuning (Improvement #12)
- **[IMPROVEMENT]** Session security service with fingerprinting (Improvement #8)
- **[IMPROVEMENT]** Backup code expiry management (Improvement #9)
- **[PERFORMANCE]** Composite database indexes (Improvement #11)
- **[ARCHITECTURE]** Standardized service layer pattern (Improvement #14)
- **[NEW]** `auth_session_security` table for tracking device fingerprints
- **[NEW]** Social authentication backend (OAuth 2.0 for 7 providers)
- **[NEW]** Enhanced auto-logout with activity tracking and warnings

#### Phase 2 (GraphQL API Layer) - Added

- **[CRITICAL]** Granular rate limiting per endpoint (Critical Issue #3)
- **[CRITICAL]** Constant-time response middleware (Critical Issue #4)
- **[IMPROVEMENT]** Enhanced MFA types with expiry tracking
- **[NEW]** Session security queries and mutations
- **[NEW]** Passkey-specific error handling
- **[NEW]** Suspicious activity detection middleware
- **[NEW]** Social authentication GraphQL API (7 mutations, 3 queries)
- **[NEW]** Auto-logout GraphQL API (session status, remember me)

#### Phase 3 (Web Frontend) - Added

- **[IMPROVEMENT]** WebAuthn/Passkey components (Improvement #10)
  - Passkey registration wizard
  - Passkey authentication button
  - Passkey management UI
- **[IMPROVEMENT]** Enhanced password validation with real-time pattern detection
- **[IMPROVEMENT]** Recovery key multi-format downloads (PDF, text, JSON)
- **[NEW]** Session security dashboard
- **[NEW]** Backup code status indicator with expiry warnings
- **[NEW]** Pages: `/auth/setup-passkey`, `/auth/manage-passkeys`, `/auth/sessions`, `/auth/security`
- **[NEW]** Social login UI (Google, GitHub, Microsoft provider buttons)
- **[NEW]** Auto-logout warning modal with countdown timer

#### Phase 4 (Mobile Frontend) - Added

- **[IMPROVEMENT]** Passkey management for mobile (platform authenticators)
- **[IMPROVEMENT]** Enhanced recovery key storage (secure device storage, export)
- **[NEW]** Session security screen for mobile
- **[NEW]** Backup code management with blur/reveal
- **[NEW]** Social authentication (PKCE flows, native Apple/Google Sign In)
- **[NEW]** Auto-logout with background/foreground detection

#### Phase 5 (CLI Installation) - Added

- **[CRITICAL]** Configuration generation for:
  - Email encryption keys (OpenBao)
  - Granular rate limiting
  - Constant-time response settings
  - Session fingerprinting
  - Key rotation schedule
  - Backup code expiry
  - Advanced password patterns
  - Argon2id auto-tuning
- **[NEW]** Social authentication configuration (7 OAuth providers)

#### Phase 6 (Testing & Documentation) - Added

- **[CRITICAL]** Security testing for all 6 critical issues:
  1. Email encryption testing
  2. Algorithm versioning testing
  3. Rate limiting testing (prevent SMS cost attacks)
  4. Timing attack resistance testing (±5ms variance max)
  5. Geolocation privacy testing
  6. Key rotation testing (zero-downtime)
- **[SECURITY]** Username/email enumeration testing
- **[SECURITY]** Password pattern detection testing
- **[SECURITY]** Session security testing (hijacking, fingerprinting)
- **[NEW]** Passkey flow testing (web + mobile)
- **[NEW]** Backup code expiry testing
- **[NEW]** Social authentication testing (OAuth flows, PKCE, email conflicts)
- **[NEW]** Auto-logout testing (idle timeout, warnings, remember me)
- **[NEW]** Social auth documentation (7 provider setup guides)

#### Summary of Code Review Implementation

- ✅ **6 Critical Issues** - All incorporated into phases
- ✅ **9 High-Priority Improvements** - All incorporated into phases
- ✅ **5 Performance Optimizations** - All incorporated into phases
- ✅ **2 Architectural Improvements** - All incorporated into phases
- ✅ **15 Total Enhancements** - Distributed across all phases

#### Testing Requirements Added

- Timing attack resistance tests (constant-time verification)
- Email encryption cycle tests
- Recovery key versioning upgrade scenarios
- Session fingerprinting and device change detection
- Backup code expiry and notification triggers
- Key rotation background job testing
- Security testing for all OWASP Top 10 vulnerabilities

---

### 🛡️ Security Review Implementation Summary

**All implementation phases have been updated to include security review findings:**

#### Phase 1 (Backend Foundation) - Added

- **[SECURITY] M-2:** Global SMS rate limiting service (prevent $1000s/day cost attacks)
  - Global SMS counter (Redis-based, shared across instances)
  - Daily budget monitoring and automatic blocking
  - Alert system for approaching limits
  - CAPTCHA escalation logic
- **[SECURITY] L-1:** Recovery key database locking (prevent race conditions)
  - PostgreSQL `SELECT FOR UPDATE` for atomic operations
  - Redis distributed locking for multi-instance deployments
  - Concurrency protection (100 simultaneous requests → 1 success)

#### Phase 2 (GraphQL API Layer) - Added

- **[SECURITY] M-1:** Constant-time delays for password reset endpoint
  - Fixed 250ms minimum response time (prevent account enumeration)
  - Generic success messages ("If account exists, reset email sent")
  - Timing variance logging (alert if >5ms deviation)
- **[SECURITY] M-2:** Enhanced SMS verification with global rate limiting
  - Per-IP limit: 3/hour (existing)
  - Global limit: 1000/hour across all IPs
  - Daily budget enforcement: $500/day (configurable)
  - CAPTCHA escalation after 100 SMS/hour globally
  - Cost analytics dashboard integration

#### Phase 3 (Web Frontend) - Added

- **[SECURITY] M-3:** WebAuthn attestation validation
  - Verify authenticator attestation during registration
  - Document attestation formats (packed, fido-u2f, android-key, etc.)
  - NIST AAL3 compliance implementation
  - Attestation logging for security audit
- **[SECURITY] L-2:** Enhanced session fingerprinting entropy
  - WebGL vendor/renderer detection
  - Audio context fingerprinting
  - Font detection (installed fonts)
  - Hardware concurrency and device memory
  - Configurable levels: minimal, balanced (default), aggressive
  - GDPR consent mechanism for enhanced fingerprinting

#### Phase 4 (Mobile Frontend) - Added

- **[SECURITY] M-3:** Platform authenticator attestation validation
  - iOS/Android platform attestation format support
  - Device attestation verification during passkey registration
  - Attestation logging for compliance documentation

#### Phase 5 (CLI Installation) - Added

- **[SECURITY] M-2:** Global SMS cost attack prevention configuration
  - Global SMS rate limit (default: 1000/hour)
  - Daily budget limit (default: $500/day)
  - Cost per SMS by provider (Twilio, AWS SNS, etc.)
  - Budget alert thresholds (80%, 90%, 100%)
  - Alert destinations (email, Slack, PagerDuty)
  - CAPTCHA escalation threshold configuration
  - Cost analytics integration
- **[SECURITY] M-1:** Constant-time response configuration
  - Target response time (default: 250ms minimum)
  - Apply to endpoints: register, login, passwordReset
  - Timing variance logging and alerting
- **[SECURITY] L-2:** Session fingerprinting level configuration
  - Fingerprint level: minimal, balanced (default), aggressive
  - GDPR consent requirement toggle
  - Privacy transparency settings

#### Phase 6 (Testing & Documentation) - Added

- **[SECURITY] M-1:** Account enumeration timing attack testing
  - Test password reset, registration, login endpoints
  - Verify constant-time responses (250ms ±5ms)
  - Measure timing variance across 1000 requests
- **[SECURITY] M-2:** SMS cost attack protection testing (HIGH PRIORITY)
  - Simulate distributed attack from 1000 IPs
  - Verify global rate limit enforcement
  - Test daily budget blocking
  - Verify CAPTCHA escalation
  - Test cost monitoring and alerting
  - Verify no bypass methods
- **[SECURITY] M-3:** WebAuthn attestation validation testing
  - Test with hardware keys (YubiKey, Titan)
  - Test with platform authenticators (Touch ID, Windows Hello)
  - Verify attestation formats and logging
  - Document for NIST AAL3 compliance
- **[SECURITY] L-1:** Recovery key race condition testing
  - Test 100 concurrent usage attempts
  - Verify database locking (only 1 success)
  - Test across multiple instances
- **[SECURITY] L-2:** Enhanced fingerprinting testing
  - Test fingerprint entropy with additional sources
  - Test fingerprint levels and GDPR consent

#### Summary of Security Review Implementation

- ✅ **3 Medium-Priority Findings** - All incorporated into phases
  - M-1: Account Enumeration via Timing (Phases 2, 5, 6)
  - M-2: SMS Cost Attack Protection (Phases 1, 2, 5, 6) - **HIGH PRIORITY**
  - M-3: WebAuthn Attestation Validation (Phases 3, 4, 6)
- ✅ **2 Low-Priority Findings** - All incorporated into phases
  - L-1: Recovery Key Race Condition (Phases 1, 6)
  - L-2: Session Fingerprint Evasion (Phases 3, 5, 6)
- ✅ **5 Total Security Findings** - Distributed across all 6 phases

#### Security Testing Requirements Added

- Account enumeration timing attack tests (±5ms variance max)
- SMS cost attack simulation (distributed, 1000 IPs)
- WebAuthn attestation verification tests
- Recovery key concurrency tests (100 simultaneous requests)
- Enhanced fingerprinting entropy tests
- NIST AAL3 compliance verification
- Financial risk mitigation testing (budget limits, alerts)

#### Priority for Implementation

1. **CRITICAL:** M-2 (SMS Cost Attack) - Implement before production (financial risk)
2. **HIGH:** M-1 (Account Enumeration) - Implement during Phase 2
3. **MEDIUM:** M-3 (Passkey Attestation) - Implement for NIST AAL3 compliance
4. **LOW:** L-1 (Recovery Key Race) - Implement during Phase 1 (low effort)
5. **LOW:** L-2 (Fingerprint Evasion) - Implement for enhanced security

**Security Rating:** 4.5/5 (STRONG) → With all findings implemented: 5/5 (EXCELLENT)

---

### Integration Points Between Layers

#### Backend ↔ Rust

**Encryption/Decryption:**

```python
# Django service calls Rust via PyO3
from syntek_security import encrypt_phone_number, decrypt_phone_number

# Encrypt before database write
encrypted_phone = encrypt_phone_number(phone_number, settings.ENCRYPTION_KEY)
user.phone_number = encrypted_phone
user.save()

# Decrypt after database read
decrypted_phone = decrypt_phone_number(user.phone_number, settings.ENCRYPTION_KEY)
```

**Password Hashing:**

```python
from syntek_security import hash_password, verify_password

# Hash password on registration
hashed = hash_password(password)
user.password = hashed

# Verify password on login
is_valid = verify_password(password, user.password)
```

#### GraphQL ↔ Backend

**Service Layer Pattern:**

```python
# GraphQL mutation calls Django service
@strawberry.mutation
def register(self, info, email: str, password: str, ...) -> RegisterPayload:
    # GraphQL layer handles API contract
    # Service layer handles business logic
    result = AuthService.register_user(
        email=email,
        password=password,
        phone_number=phone_number,
    )
    return RegisterPayload.from_service_result(result)
```

#### Frontend ↔ GraphQL

**Apollo Client Integration:**

```typescript
// React hook calls GraphQL mutation
const [register] = useMutation(REGISTER_MUTATION);

const handleRegister = async (formData) => {
  const { data } = await register({
    variables: {
      email: formData.email,
      password: formData.password,
      phoneNumber: formData.phoneNumber,
    },
  });

  if (data.register.success) {
    // Handle success (redirect to verification)
  }
};
```

#### Mobile ↔ Backend

**Secure API Communication:**

```typescript
// Mobile uses same GraphQL endpoint with certificate pinning
const client = new ApolloClient({
  link: createHttpLink({
    uri: config.apiBaseUrl + "/graphql/",
    fetch: customFetch, // Custom fetch with cert pinning
  }),
  cache: new InMemoryCache(),
});
```

**Biometric ↔ Token Storage:**

```typescript
// After successful biometric auth, retrieve token from secure storage
const storedToken = await SecureStore.getItemAsync("access_token");

// Use token for GraphQL requests
const client = new ApolloClient({
  link: new HttpLink({
    headers: {
      authorization: storedToken ? `Bearer ${storedToken}` : "",
    },
  }),
});
```

---

### Risks & Mitigations

| Risk                                                                            | Likelihood | Impact   | Mitigation                                                                                                               |
| ------------------------------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| **SMS delivery failures** (provider outage)                                     | Medium     | High     | Implement fallback to email-based verification; support multiple SMS providers; add retry logic with exponential backoff |
| **TOTP time sync issues** (client/server clock drift)                           | Medium     | Medium   | Allow ±1 time window (90 seconds total); provide clear error messaging; implement time sync check endpoint               |
| **Passkey browser compatibility** (Safari, older browsers)                      | High       | Medium   | Feature detection; graceful fallback to TOTP; progressive enhancement approach                                           |
| **Encryption key rotation** (key compromise scenario)                           | Low        | Critical | Implement key versioning in database schema; background job for re-encryption; store key ID with encrypted data          |
| **Phone number format variations** (international formats)                      | High       | Low      | Use libphonenumber for validation; store E.164 format only; provide country selector in UI                               |
| **Recovery key storage** (user loses keys)                                      | High       | Medium   | Encourage printing/downloading; provide secure cloud backup option (encrypted); email recovery as ultimate fallback      |
| **Concurrent session conflicts** (user logs in multiple devices simultaneously) | Medium     | Low      | Implement session priority (newer session bumps older); configurable max sessions; clear UI for session management       |
| **CAPTCHA accessibility** (visually impaired users)                             | Low        | Medium   | Provide audio alternative; allow bypass for verified users; implement honeypot as alternative                            |
| **Mobile biometric spoofing** (fingerprint/face ID bypass)                      | Low        | High     | Require password for sensitive operations; implement device binding; monitor for suspicious patterns                     |
| **GraphQL query complexity attacks** (nested queries)                           | Medium     | High     | Already mitigated by syntek-graphql-core (query depth/complexity limits); rate limiting per user/IP                      |
| **Username enumeration** (attacker checks if username exists)                   | High       | Low      | Generic error messages ("Invalid credentials"); rate limiting on registration endpoint; CAPTCHA after multiple attempts  |
| **Argon2 performance** (slow hashing impacts login speed)                       | Low        | Medium   | Tune Argon2 parameters (m=19456, t=2, p=1); horizontal scaling; consider caching for frequent re-auths                   |
| **Rust-Python boundary overhead** (FFI performance)                             | Low        | Low      | Batch operations where possible; benchmark critical paths; optimise PyO3 bindings                                        |
| **IP encryption key compromise** (attacker decrypts stored IPs)                 | Low        | High     | Store encryption keys in OpenBao; implement key rotation; use HMAC-SHA256 hashing for lookups (one-way)                  |
| **VPN/proxy IP tracking** (user IP changes frequently)                          | High       | Low      | Track device fingerprint alongside IP; allow multiple IPs per session; configurable IP change tolerance                  |
| **IPv6 address privacy** (temporary IPv6 addresses)                             | Medium     | Low      | Support both IPv4 and IPv6; normalize IPv6 format; consider /64 subnet tracking for IPv6                                 |
| **False positive IP blocks** (shared IPs, NAT)                                  | Medium     | Medium   | Implement graduated blocking (warning → temporary → permanent); allow manual unblock by admin; whitelist trusted IPs     |
| **IP geolocation accuracy** (VPN, proxy, mobile)                                | High       | Low      | Mark geolocation as "estimated"; don't rely solely on location for security decisions; optional feature                  |
| **Logging performance impact** (high-traffic sites)                             | Medium     | Medium   | Use async logging; batch log writes; implement sampling for high-volume events; use Redis queue for log buffering        |
| **Log storage costs** (large log volumes)                                       | Medium     | Medium   | Implement log rotation; configurable retention periods; compress old logs; use tiered storage (hot/cold)                 |
| **Sensitive data in logs** (accidental PII leakage)                             | Medium     | Critical | Mandatory log sanitization; never log passwords/tokens; automated PII detection; regular log audits                      |
| **GDPR compliance** (IP addresses = personal data)                              | High       | High     | Encrypt IPs at rest; configurable retention; support data deletion requests; document legal basis for IP tracking        |
| **Log provider outage** (GlitchTip, Grafana down)                               | Low        | Low      | Fallback to local file logging; buffer logs during outage; retry with exponential backoff; monitor log delivery rate     |

---

### Design Decisions & Recommendations (Updated)

**Technical Decisions (All Modular):**

- ✅ **SMS Provider**: Twilio (recommended) - see Section 1 for details
- ✅ **CAPTCHA**: All versions supported (v2, v3, hCaptcha) - see Section 2 for setup
- ✅ **Passkey Priority**: MVP - WebAuthn implementation included
- ✅ **Username**: Modular (unique identifier OR display name) - default unique
- ✅ **Organisation Assignment**: Modular (self-select, invite, admin) - see Section 4
- ✅ **Recovery Key Format**: All formats (printable, download, display) - see Section 5
- ✅ **Phone Number**: Modular (required OR optional) - default optional
- ✅ **Cryptography**: Argon2id, AES-256-GCM, ChaCha20-Poly1305, HMAC-SHA256 - see Modern Cryptography Standards section

**Infrastructure Requirements:**

- ✅ **Encryption Key Management**: OpenBao (confirmed from CLAUDE.md)
  - Master encryption key stored in OpenBao secrets engine
  - HMAC key for token hashing stored in OpenBao
  - Key rotation policy: 90 days (configurable)
- ⚠️ **SMS Credentials**: Need Twilio account credentials
  - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
  - Or alternative provider credentials
- ⚠️ **CAPTCHA Keys**: Need to generate from Google reCAPTCHA admin console
  - `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY`
  - Instructions provided in Section 2
- ⚠️ **Email Provider**: Choose based on scale
  - **Recommended**: Postmark and Mailgun
  - Need credentials: API keys, sender verification
- ⚠️ **Redis**: Required for rate limiting and session management
  - Need Redis connection URL
  - Recommended: Redis 7.x with persistence enabled
- ⚠️ **PostgreSQL**: Required version 18.1+
  - Need database connection details
  - Encryption at rest recommended
- ⚠️ **GlitchTip** (recommended) or alternative logging provider
  - **GlitchTip**: Self-hosted or cloud, Sentry-compatible
  - **Grafana**: Loki URL, Prometheus metrics port, optional auth credentials
  - **Sentry**: DSN (alternative to GlitchTip)
  - **Datadog**: API key and application key
  - **Splunk**: HEC token and Splunk URL
  - **ELK Stack**: Elasticsearch URL and credentials
  - **Standard**: File-based logging (no external service required)

**Compliance Considerations:**

- 🔒 **Data Residency**: Phone numbers encrypted at rest, region configurable per deployment
  - **GDPR**: EU/UK deployments should use EU-region database
  - **Recommendation**: Use database geo-replication for multi-region compliance
- 🔒 **SMS Logging**: Twilio provides audit logs (30-day retention by default)
  - **Recommendation**: Configure extended retention for compliance (configurable in Twilio)
  - Do NOT log SMS content (only metadata: to, from, timestamp, status)
- 🔒 **Biometric Data**: NEVER stored server-side (iOS/Android platform keychain only)
  - Biometric templates remain on device (Face ID, Touch ID, Android Biometric)
  - Server only stores: device ID, last used timestamp, enabled status
  - **GDPR compliant**: No biometric data leaves device
- 🔒 **IP Address Tracking**: Encrypted at rest, GDPR compliant
  - **Legal Basis**: Legitimate interest for security and fraud prevention (GDPR Article 6(1)(f))
  - **Encryption**: AES-256-GCM encryption via Rust, stored as binary
  - **Hashing**: HMAC-SHA256 for lookups (one-way, cannot reverse to original IP)
  - **Retention**: Configurable (default 90 days), automatically purged
  - **User Rights**: Support data access, rectification, erasure requests (GDPR Articles 15-17)
  - **Transparency**: Document IP tracking in privacy policy
  - **Recommendation**: Shorter retention for EU/UK users (30-90 days), exclude from analytics
- 🔒 **Authentication Logs**: Sensitive data sanitized, compliant retention
  - **Sanitization**: Passwords, tokens, API keys never logged (automatic redaction)
  - **Retention**: Configurable (default 90 days), supports GDPR deletion requests
  - **Access Control**: Admin-only access to logs, audit trail for log access
  - **PII Handling**: Email, user ID logged for security; can be pseudonymized if required
  - **Log Deletion**: Support bulk deletion on user account deletion (GDPR "right to erasure")
  - **Provider Selection**: Choose GDPR-compliant provider (GlitchTip EU, Grafana Cloud EU, etc.)

---

## Next Steps

### Immediate Actions Required

1. **Gather Infrastructure Credentials:**
   - [ ] Twilio account credentials (or alternative SMS provider)
   - [ ] Generate reCAPTCHA site keys from Google admin console
   - [ ] Email provider credentials (Postmark, Mailgun, SendGrid, or AWS SES)
   - [ ] Logging provider credentials (GlitchTip DSN, Grafana Loki URL, or Sentry DSN)
   - [ ] Redis connection URL (for rate limiting/sessions)
   - [ ] PostgreSQL connection details (version 18.1+)
   - [ ] Configure OpenBao for encryption key storage

2. **Environment Configuration:**
   - [ ] Create `.env` file with all credentials (never commit to repo)
   - [ ] Configure OpenBao secrets for encryption keys and HMAC keys
   - [ ] Set up Redis instance (local or cloud-hosted)
   - [ ] Configure email sender verification (SPF, DKIM, DMARC)

3. **Begin Implementation:**
   - [ ] **Phase 1**: Run `/syntek-dev-suite:backend` to implement backend services (Week 1-2)
   - [ ] **Phase 2**: Implement GraphQL API layer (Week 2-3)
   - [ ] **Phase 3**: Run `/syntek-dev-suite:frontend` to implement web UI (Week 3-4)
   - [ ] **Phase 4**: Implement mobile frontend (Week 4-5)
   - [ ] **Phase 5**: Implement CLI installation tool (Week 5)
   - [ ] **Phase 6**: Run `/syntek-dev-suite:test-writer` for comprehensive tests (Week 6)

### Configuration Templates Generated

All modules include configuration templates that developers can customize per deployment:

- Django settings (all authentication options modular)
- Web configuration (UI customization, theme, branding)
- Mobile configuration (biometric settings, security options)
- SMS/email provider settings (swappable providers)
- IP tracking configuration (whitelist/blacklist, geolocation)
- Logging configuration (GlitchTip, Grafana, Sentry, standard)

### Architecture Highlights

✅ **All sensitive data encrypted at API layer via Rust**
✅ **Nothing stored in plaintext** (passwords, IPs, phone numbers, tokens)
✅ **Memory-safe with zeroisation** (no data leaks in Rust layer)
✅ **Modern cryptography**: Argon2id, AES-256-GCM, ChaCha20-Poly1305, HMAC-SHA256
✅ **IP tracking fully encrypted** (AES-256-GCM + HMAC-SHA256 hashing)
✅ **Modular authentication logging** (GlitchTip, Grafana, Sentry, Datadog, Splunk, ELK, standard)
✅ **IP whitelist/blacklist** (organisation-level restrictions, auto-blocking)
✅ **Suspicious activity detection** (pattern-based, configurable thresholds)
✅ **Modular configuration** (every feature can be enabled/disabled)
✅ **One-command CLI installation** across all layers
✅ **Full compliance**: OWASP, NIST, NCSC, GDPR, CIS, SOC 2

---

**Document Version:** 3.7
**Last Updated:** 12.02.2026
**Author:** System Architect
**Status:** ✅ **Ready for Implementation**

**Version History:**

**v3.8 (Current)** - Comprehensive Modularity & Configuration Requirements Added

- ✅ **Added Section 10: Modularity & Configuration Requirements** (comprehensive configuration documentation)
- ✅ **Configuration architecture:** Backend (Django), Frontend (Web/Mobile), Provider-specific settings
- ✅ **Feature toggles:** Every authentication feature can be enabled/disabled via configuration
- ✅ **Provider abstraction:** SMS, CAPTCHA, logging, OAuth providers are modular and swappable
- ✅ **Installation-time configuration:** CLI generates project-specific configuration files
- ✅ **Runtime configuration:** Admin interface for dynamic settings changes
- ✅ **Styling & theming:** Complete UI customization via themes and CSS variables
- ✅ **Headless hooks:** Bring-your-own-UI support with authentication logic separation
- ✅ **Database customization:** Extend authentication models for project-specific needs
- ✅ **Configuration validation:** CLI validates and tests all settings before deployment
- ✅ **Use case examples:** Configuration templates for SaaS, Enterprise B2B, Mobile Apps, Healthcare/HIPAA
- ✅ **Documentation generation:** Auto-generated project-specific setup and configuration guides
- 📊 **SUCCESS CRITERIA:** Zero source code modifications required - configuration-only installation

**v3.7** - Social Media Authentication and Enhanced Auto-Logout Integrated into Phases

- ✅ **Integrated comprehensive social media authentication into all phases:**
  - Phase 1: Backend OAuth services for 7 providers (Google, GitHub, Microsoft, Apple, Facebook, LinkedIn, Twitter/X)
  - Phase 2: GraphQL API with 7 social auth mutations and 3 queries
  - Phase 3: Web UI with social login buttons and account management
  - Phase 4: Mobile OAuth with PKCE flows and native Apple/Google Sign In
  - Phase 5: CLI configuration for social auth providers
  - Phase 6: Social auth testing (OAuth flows, CSRF, GDPR compliance)
- ✅ **Integrated enhanced auto-logout functionality into all phases:**
  - Phase 1: Backend session activity tracking and timeout services
  - Phase 2: GraphQL API for session status and "Remember me"
  - Phase 3: Web auto-logout warning modal with countdown timer
  - Phase 4: Mobile background/foreground detection and auto-logout
  - Phase 6: Auto-logout testing (idle timeout, warnings, remember me)
- ✅ **Database schema extended:**
  - `auth_social_account`, `auth_oauth_state`, `auth_social_login_attempt` tables added
  - `auth_session` table extended with activity tracking and remember me fields
- ✅ **Security features:**
  - OAuth token encryption via Rust (AES-256-GCM)
  - CSRF protection via state tokens
  - PKCE support for mobile OAuth flows
  - Email conflict resolution for social accounts
  - Session hijacking prevention with activity tracking
- ✅ **Total effort added:** 140-176 hours across all phases (MVP: 100-120 hours)
- 📊 **Implementation:** All social auth and auto-logout features integrated into existing phased plan (not separate section)

**v3.6** - Legal Document Requirements Clarified with Regional Variants

- ✅ **Clarified BOTH Privacy Policy AND Terms of Service are required:**
  - Privacy Policy: Legal requirement (GDPR Art. 13/14, CCPA) - explains data processing
  - Terms of Service: Business requirement - defines service rules, liability, disputes
- ✅ **Added regional variant support for legal documents:**
  - EU (GDPR), USA (CCPA), Canada (PIPEDA), Australia (Privacy Act), Global fallback
  - Regional file naming: `PRIVACY-POLICY-{REGION}.md`, `TERMS-OF-SERVICE-{REGION}.md`
- ✅ **Updated User model** to track document versions AND regions for each acceptance
- ✅ **Updated Phase 1:** Legal acceptance tracking with regional variants
- ✅ **Updated Phase 2 (GAP-03):** Register mutation requires BOTH acceptPrivacyPolicy AND acceptTerms
- ✅ **Updated Phase 3 & 4:** Registration forms require BOTH checkboxes with regional document links
- ✅ **Updated Phase 5:** Configuration for regional legal documents and version tracking
- ✅ **Updated Phase 6:** Added legal document templates (10 files: 5 Privacy Policies + 5 Terms of Service)
- ✅ **Added data retention policies** with regional variants (EU, USA, Global)
- 📊 **Legal Compliance:** Both documents required for full legal compliance and business protection

**v3.5** - GDPR Implementation Integrated into Phases + Future Modules Documented

- ✅ **16 authentication-specific GDPR gaps integrated** into implementation phases
- ✅ **Phase 1:** Added GAP-06, 07, 08, 14 (data retention, deletion, audit logging, consent trail)
- ✅ **Phase 2:** Added GAP-03, 04, 05, 13, 15, 16 (privacy acceptance, profile updates, DSAR, opt-outs)
- ✅ **Phase 3:** Added GAP-01, 03 (consent checkboxes, GDPR pages)
- ✅ **Phase 4:** Added mobile GDPR screens (consent, profile updates, data export, deletion, privacy)
- ✅ **Phase 5:** Added GDPR configuration (retention, grace period, key rotation)
- ✅ **Phase 6:** Added GDPR testing and documentation (DPIAs, LIA, retention policy, backup procedures)
- ✅ **Detailed GDPR review removed** (2,621 lines removed)
- ✅ **Future Required Modules section added:** Documents 8 organization-wide GDPR gaps for future `syntek-gdpr` module
- 📊 **GDPR Status:** 16/24 gaps in this module (67%), 8/24 gaps deferred to future module (33%)

**v3.4** - GDPR Review Added with Gap Categorization

- ✅ **GDPR compliance review completed** by GDPR Compliance Specialist
- ✅ **24 GDPR gaps identified** with detailed analysis and solutions
- ✅ **Gap categorization added:** 16 authentication-specific vs. 8 general compliance gaps
- ✅ **Overall GDPR Rating:** 4.5/5 (STRONG) → 5/5 (EXCELLENT after gaps fixed)
- ✅ **Recommendation:** Implement 16 auth-specific gaps in this module, defer 8 general gaps to `syntek-gdpr`
- ✅ **GDPR review appended** to bottom of file (2,533 lines added)

**v3.3** - Implementation Plan Updated with Security Review Recommendations

- ✅ **Security review findings incorporated** into all 6 implementation phases
- ✅ **Medium-priority findings (M-1, M-2, M-3):** All incorporated
  - M-1: Account Enumeration via Timing (Phases 2, 5, 6)
  - M-2: SMS Cost Attack Protection (Phases 1, 2, 5, 6) - **HIGH PRIORITY for production**
  - M-3: WebAuthn Attestation Validation (Phases 3, 4, 6)
- ✅ **Low-priority findings (L-1, L-2):** All incorporated
  - L-1: Recovery Key Race Condition (Phases 1, 6)
  - L-2: Session Fingerprint Evasion (Phases 3, 5, 6)
- ✅ **Security testing requirements added** to Phase 6
- ✅ **Security Review Implementation Summary** section added
- ✅ **Detailed security review removed** (findings now in phases, reducing document by 1,096 lines)
- 📊 **Overall Security Rating:** 4.5/5 (STRONG) → 5/5 (EXCELLENT with all findings implemented)

**v3.2** - Implementation Plan Updated with Code Review Recommendations

- ✅ **All 6 phases updated** with code review recommendations
- ✅ **Phase 1:** Added 11 critical fixes and improvements (email encryption, key rotation, session security, etc.)
- ✅ **Phase 2:** Added 6 security enhancements (rate limiting, constant-time responses, session queries)
- ✅ **Phase 3:** Added 7 new features (passkeys, session security dashboard, backup code management)
- ✅ **Phase 4:** Added mobile passkey and session security features
- ✅ **Phase 5:** Added configuration generation for all critical security fixes
- ✅ **Phase 6:** Added comprehensive security testing for all critical issues
- ✅ **Total:** 15 enhancements distributed across all implementation phases
- ✅ **Critical Issues:** All 6 critical security issues incorporated into phases
- ✅ **Improvements:** All 9 high-priority improvements incorporated into phases

**v3.1** - Code Review Completed

- Identified 6 critical security issues (email encryption, algorithm versioning, rate limiting, timing attacks, geolocation privacy, key rotation)
- Identified 9 high-priority improvements (password patterns, session security, backup codes, passkeys, indexes, Argon2id tuning, batch operations, service layer, IP hashing)
- Documented 5 performance optimizations and 2 architectural improvements

**v3.0** - IP Tracking and Logging Added

- Added encrypted IP tracking (whitelist/blacklist, security monitoring)
- Added modular authentication logging (GlitchTip, Grafana, Sentry, etc.)
- Added 4 new database tables for IP tracking and login attempts
- Added IP encryption/hashing functions to Rust security modules
- Added GraphQL mutations/queries for IP management
- Added GDPR compliance section for IP tracking and logging

**v2.0** - Initial Architecture with Recommendations

- Complete technical architecture (database, GraphQL, Rust, CLI)
- 6-week implementation timeline
- Modern cryptography standards (Argon2id, AES-256-GCM, ChaCha20-Poly1305, HMAC-SHA256)
- Configuration architecture for modular deployment

---

## Future Required Modules for Full GDPR Compliance

**Note:** This authentication module implements **16 authentication-specific GDPR gaps** (67% of total gaps). For full GDPR compliance in EU/UK deployments, the following **8 general GDPR/compliance gaps** (33% of total) will require separate modules:

---

### 🔴 REQUIRED: `syntek-gdpr` or `syntek-compliance` Module

**Purpose:** Provide organization-wide GDPR compliance features that apply across ALL Syntek modules, not just authentication.

#### Phase 0: Pre-Production (P0 - Critical) - 4 gaps

**GAP-02: Cookie Consent Banner**

- **Scope:** Organization-wide (applies to ALL modules)
- **What it does:** Implements cookie consent management for analytics, marketing, and functional cookies
- **Why not in auth module:** Authentication only needs "necessary" cookies (session, CSRF). Cookie consent applies to analytics tracking, marketing pixels, and functional cookies across all modules
- **Recommended Package:** `@syntek/ui-gdpr` (cookie consent banner component)
- **Implementation:**
  - Cookie consent banner UI component (web/mobile)
  - Cookie preference storage and management
  - Integration with analytics modules (Google Analytics, Matomo, etc.)
  - Automatic cookie blocking based on consent
  - Consent audit trail
- **Effort:** Medium (8-12 hours)

**GAP-17: Data Processing Agreements (DPAs)**

- **Scope:** Organization-wide (legal agreements)
- **What it does:** Manages DPAs with ALL third-party processors (SMS, email, logging, analytics, payment, etc.)
- **Why not in auth module:** DPAs are organization-level legal agreements, not module-specific. Every module that uses a processor needs a DPA
- **Recommended Package:** `syntek-compliance` (DPA management)
- **Implementation:**
  - DPA templates for common processors (Twilio, SendGrid, AWS, Stripe, etc.)
  - DPA tracking system (signed, renewal dates, responsible party)
  - Automated DPA renewal reminders
  - Storage of signed DPAs (`docs/legal/dpas/`)
- **Effort:** High (20-30 hours for templates + tracking system)

**GAP-20: Breach Detection and Notification Procedure**

- **Scope:** Organization-wide (covers ALL data types)
- **What it does:** 72-hour breach notification workflow for GDPR Article 33/34 compliance
- **Why not in auth module:** Breaches can occur in ANY module (auth, payments, profiles, analytics). Need centralized breach response
- **Recommended Package:** `syntek-compliance` (breach response)
- **Implementation:**
  - Breach detection alerts (automated monitoring)
  - 72-hour notification workflow (supervisory authority + affected users)
  - Breach severity classification (Article 33 vs. Article 34 threshold)
  - Incident response plan documentation
  - Breach notification templates (email, SMS, web banner)
  - Post-breach audit report generation
- **Effort:** High (30-40 hours for workflow + templates)

**GAP-24: Standard Contractual Clauses (SCCs) for USA Transfers**

- **Scope:** Organization-wide (legal mechanism for data transfers)
- **What it does:** Implements SCCs for all data transfers to USA/non-EU countries
- **Why not in auth module:** SCCs are organization-level legal mechanisms. Every module that transfers data internationally needs SCCs
- **Recommended Package:** `syntek-compliance` (SCCs management)
- **Implementation:**
  - SCC templates (EU Commission approved)
  - Transfer Impact Assessment (TIA) documentation
  - SCC signing workflow with processors
  - Storage of signed SCCs (`docs/legal/sccs/`)
  - Automatic detection of international transfers
- **Effort:** High (25-35 hours for templates + TIA + workflow)

#### Phase 1: High Priority (P1) - 1 gap

**GAP-10: Records of Processing Activities (RoPA)**

- **Scope:** Organization-wide (covers ALL modules)
- **What it does:** Creates and maintains RoPA per GDPR Article 30
- **Why not in auth module:** RoPA must document ALL processing activities across all modules. It's a central register
- **Recommended Package:** `syntek-compliance` (RoPA management)
- **Implementation:**
  - RoPA document template (Markdown or structured database)
  - Automatic RoPA generation from module metadata
  - Each module contributes its processing activities
  - DPO review and approval workflow
  - Annual RoPA review reminders
- **Effort:** Medium (15-20 hours for system + template)

#### Phase 2: Medium Priority (P2) - 3 gaps

**GAP-18: Sub-Processor List**

- **Scope:** Organization-wide (lists ALL processors)
- **What it does:** Maintains centralized list of all sub-processors per GDPR Article 28
- **Why not in auth module:** Sub-processor list covers processors from all modules (SMS, email, analytics, payments, CRM, etc.)
- **Recommended Package:** `syntek-compliance` (sub-processor management)
- **Implementation:**
  - Sub-processor registry (database or Markdown)
  - Automatic detection of processors from configuration
  - Each module declares its processors
  - Public sub-processor list page (`/legal/sub-processors`)
  - Update notifications to users when processors change
- **Effort:** Low (6-8 hours)

**GAP-23: DPO Contact Details**

- **Scope:** Organization-wide (DPO is org-level role)
- **What it does:** Publishes DPO contact details per GDPR Article 37
- **Why not in auth module:** DPO is organization-wide role, not module-specific
- **Recommended Package:** `@syntek/ui-gdpr` (DPO contact component)
- **Implementation:**
  - Global DPO configuration: `SYNTEK_GDPR = { 'DPO_EMAIL': '...', 'DPO_NAME': '...', 'DPO_PHONE': '...' }`
  - DPO contact page component (`/legal/dpo-contact`)
  - DPO contact in footer (all pages)
  - Automatic DPO email forwarding for DSAR requests
- **Effort:** Low (3-4 hours)

**GAP-15 (Extended): Full DSAR Orchestration Across All Modules**

- **Scope:** Organization-wide (combines data from ALL modules)
- **What it does:** Orchestrates DSAR (Data Subject Access Request) across all installed modules
- **Why not in auth module:** Full DSAR must include data from auth, profiles, payments, orders, analytics, CRM, etc. Need central orchestrator
- **Recommended Package:** `syntek-dsar` (DSAR orchestration)
- **Implementation:**
  - DSAR orchestrator service that calls each module's `exportMyData` endpoint
  - Each module implements `IExportable` interface
  - Combined export in JSON/CSV/PDF format
  - DSAR request tracking (received, processing, completed)
  - 30-day fulfillment deadline tracking
  - Automated email delivery of export
- **Effort:** Medium (12-16 hours for orchestration)
- **Note:** Authentication module implements `exportMyData` for authentication data only. This gap is for the central orchestrator.

---

### 📦 Recommended Module Structure

```
syntek-modules/
├── backend/
│   ├── security-auth/              # This module (authentication-specific GDPR)
│   └── gdpr-compliance/            # NEW: Organization-wide GDPR module
│       ├── cookie-consent/         # GAP-02: Cookie management
│       ├── dpa-management/         # GAP-17: DPA templates and tracking
│       ├── breach-response/        # GAP-20: 72-hour notification workflow
│       ├── sccs-management/        # GAP-24: SCCs for data transfers
│       ├── ropa/                   # GAP-10: Records of Processing Activities
│       ├── sub-processors/         # GAP-18: Sub-processor list
│       ├── dpo-config/             # GAP-23: DPO contact configuration
│       └── dsar-orchestrator/      # GAP-15: Full DSAR across all modules
│
├── web/packages/
│   ├── ui-auth/                    # This module (authentication UI)
│   └── ui-gdpr/                    # NEW: GDPR UI components
│       ├── CookieConsentBanner/    # GAP-02
│       ├── DPOContact/             # GAP-23
│       ├── DSARRequest/            # GAP-15
│       └── PrivacySettings/        # Cross-module privacy controls
│
└── mobile/packages/
    ├── mobile-auth/                # This module (authentication mobile)
    └── mobile-gdpr/                # NEW: GDPR mobile components
        ├── CookieConsentModal/     # GAP-02
        ├── DPOContact/             # GAP-23
        └── DSARRequest/            # GAP-15
```

---

### ⚠️ IMPORTANT: Deployment Considerations

#### EU/UK Deployments

**BOTH modules required for full GDPR compliance:**

1. `syntek-security-auth` (authentication + 16 auth-specific GDPR gaps)
2. `syntek-gdpr` or `syntek-compliance` (8 organization-wide GDPR gaps)

**Installation:**

```bash
# Install authentication module
syntek install auth --full

# Install GDPR compliance module (when available)
syntek install gdpr --full
```

#### USA/Non-EU Deployments

**Authentication module may be sufficient:**

- `syntek-security-auth` provides core authentication + authentication-specific GDPR features
- GDPR compliance module is optional (but recommended for privacy-conscious deployments)

**Note:** Even USA deployments benefit from GDPR compliance (CCPA, user trust, data minimization)

---

### 📊 Summary

| Category                            | Gaps          | Priority | Recommended Module                        |
| ----------------------------------- | ------------- | -------- | ----------------------------------------- |
| **Authentication Module (This)**    | 16 gaps (67%) | P0-P2    | `syntek-security-auth`                    |
| **GDPR Compliance Module (Future)** | 8 gaps (33%)  | P0-P2    | `syntek-gdpr` or `syntek-compliance`      |
| **Total GDPR Gaps**                 | 24 gaps       | P0-P2    | Both modules required for full compliance |

**Effort Estimates for GDPR Compliance Module:**

- **P0 (Critical):** 90-120 hours (GAP-02, 17, 20, 24)
- **P1 (High):** 15-20 hours (GAP-10)
- **P2 (Medium):** 20-30 hours (GAP-18, 23, 15)
- **Total:** 125-170 hours (~3-4 weeks of development)

---

### ✅ Next Steps

1. **Complete authentication module** with 16 authentication-specific GDPR gaps (this plan)
2. **Create `syntek-gdpr` module** to handle 8 organization-wide GDPR gaps
3. **Integrate both modules** via `IExportable` interface and RoPA registration
4. **Test full GDPR compliance** with both modules installed
5. **Document deployment requirements** (EU/UK must install both modules)

**This authentication module is GDPR-compliant for authentication-specific features. For full organization-wide GDPR compliance, the `syntek-gdpr` module will be required.**

---

# Penetration Testing Strategy for Authentication System

## Executive Summary

This section provides **detailed attack vectors, test methodologies, and security scanner implementations** for the authentication module. It serves as a reference guide for the **module-scoped penetration tests integrated into Phases 1-6** above.

**Scope of This Document:**

- ✅ Attack surface analysis and threat modeling
- ✅ Detailed test implementations (Python test suites)
- ✅ Security scanner architectures (reference implementations)
- ✅ OWASP Top 10 mapping and coverage
- ✅ Test coverage matrices and metrics

**Implementation Locations:**

- **Module-scoped pentests**: Integrated into **Phases 1.6, 2.7, 3.8, 4.5, 6.5** (lightweight Python tests)
- **Heavy Rust scanners**: Located in **syntek-infrastructure/security/pentest/scanners/** (auth_brute_force, mfa_bypass, crypto_side_channel, etc.)
- **CI/CD automation**: Managed by **syntek-infrastructure** for scheduled testing across all environments

**Key Objectives:**

- Validate security controls across all authentication flows
- Test Rust cryptographic implementations for side-channel vulnerabilities
- Verify GDPR compliance and data protection measures
- Automate regression testing for security vulnerabilities
- Establish continuous security monitoring

**Note:** The test implementations below provide **reference architectures** and **detailed specifications**. The actual module-scoped tests in Phases 1-6 are **lightweight Python integration tests** suitable for PR checks and module testing. Heavy automated scanners and infrastructure-wide pentests are managed in **syntek-infrastructure**.

---

## 1. Attack Surface Analysis

### 1.1 Authentication Components

| Component               | Attack Vectors                                                                              | Critical Assets                                      | Test Priority |
| ----------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------- |
| **Registration Flow**   | Email enumeration, phone enumeration, CAPTCHA bypass, automated registration, fake accounts | User credentials, PII (email, phone)                 | P0            |
| **Login Flow**          | Brute force, credential stuffing, timing attacks, session hijacking, MFA bypass             | Session tokens, password hashes, TOTP secrets        | P0            |
| **MFA/TOTP**            | TOTP brute force, backup code enumeration, QR code interception, time drift attacks         | TOTP secrets, backup codes, recovery keys            | P0            |
| **Password Recovery**   | Account takeover, email interception, token prediction, recovery key brute force            | Recovery tokens, recovery keys, password reset links | P0            |
| **Passkeys (WebAuthn)** | Relying party spoofing, credential ID enumeration, authenticator cloning                    | Passkey credentials, challenge-response              | P1            |
| **IP Tracking**         | IP spoofing, VPN/proxy abuse, geolocation bypass, X-Forwarded-For manipulation              | IP addresses, location data                          | P1            |
| **Session Management**  | Session fixation, session hijacking, concurrent session abuse, cookie theft                 | Session cookies, JWT tokens, refresh tokens          | P0            |
| **GraphQL API**         | Introspection abuse, query complexity attacks, batch attack abuse, mutation abuse           | All authentication data                              | P0            |
| **Rust Crypto Layer**   | Timing attacks, side-channel attacks, memory leaks, FFI boundary exploits                   | Encryption keys, plaintext data, password hashes     | P0            |

### 1.2 OWASP Top 10 2025 Mapping

| OWASP Risk                         | Authentication Manifestation                                                  | Test Coverage                                                 |
| ---------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **A01: Broken Access Control**     | Unauthorized access to user accounts, privilege escalation, session hijacking | Session security tests, authorization bypass tests            |
| **A02: Cryptographic Failures**    | Weak encryption, exposed secrets, plaintext storage, timing attacks           | Crypto tests, side-channel tests, key rotation tests          |
| **A03: Injection**                 | SQL injection in email/phone lookups, GraphQL injection, LDAP injection       | Input validation tests, parameterized query tests             |
| **A04: Insecure Design**           | Missing rate limiting, weak MFA, insecure recovery, predictable tokens        | Rate limiting tests, MFA bypass tests, token randomness tests |
| **A05: Security Misconfiguration** | Default credentials, verbose errors, exposed admin panels, open CORS          | Configuration scanning, error message analysis                |
| **A06: Vulnerable Components**     | Outdated Django, Strawberry, PyO3, React, vulnerable dependencies             | Dependency scanning, CVE monitoring                           |
| **A07: Authentication Failures**   | Weak passwords, credential stuffing, session fixation, MFA bypass             | Password policy tests, brute force tests, session tests       |
| **A08: Software/Data Integrity**   | Tampered session cookies, JWT signature bypass, code injection                | JWT security tests, integrity validation tests                |
| **A09: Logging Failures**          | Missing audit logs, sensitive data in logs, log injection                     | Log analysis, PII leak detection, log injection tests         |
| **A10: SSRF**                      | SSRF via email verification, webhook abuse, URL parameter injection           | URL validation tests, SSRF payload testing                    |

---

## 2. Penetration Testing Tools & Harnesses

### 2.1 Custom Rust-Based Security Scanners

**Location:** `pentest/scanners/`

#### Scanner 1: Authentication Brute Force Tester

```rust
// pentest/scanners/auth_brute_force.rs
use tokio;
use reqwest::Client;
use std::time::Duration;

pub struct AuthBruteForceTester {
    target: String,
    rate_limit_threshold: u32,
    concurrent_requests: u32,
}

impl AuthBruteForceTester {
    pub async fn test_login_rate_limiting(&self) -> TestResult {
        let client = Client::new();
        let mut success_count = 0;
        let mut blocked_count = 0;

        // Test 1: Sequential requests (should trigger rate limiting)
        for i in 0..self.rate_limit_threshold + 10 {
            let response = client.post(&format!("{}/graphql", self.target))
                .json(&serde_json::json!({
                    "query": "mutation { login(email: \"test@example.com\", password: \"wrong\") { success } }"
                }))
                .send()
                .await?;

            if response.status().is_success() {
                success_count += 1;
            } else if response.status() == 429 {
                blocked_count += 1;
            }
        }

        // Test 2: Concurrent requests (should trigger IP-based rate limiting)
        let mut handles = vec![];
        for _ in 0..self.concurrent_requests {
            let client = client.clone();
            let target = self.target.clone();
            handles.push(tokio::spawn(async move {
                client.post(&format!("{}/graphql", target))
                    .json(&serde_json::json!({
                        "query": "mutation { login(email: \"test@example.com\", password: \"wrong\") { success } }"
                    }))
                    .send()
                    .await
            }));
        }

        let concurrent_results = futures::future::join_all(handles).await;
        let concurrent_blocked = concurrent_results.iter()
            .filter(|r| r.as_ref().ok().and_then(|resp| Some(resp.status() == 429)).unwrap_or(false))
            .count();

        TestResult {
            passed: blocked_count > 0 && concurrent_blocked > 0,
            details: format!(
                "Sequential: {}/{} blocked, Concurrent: {}/{} blocked",
                blocked_count, self.rate_limit_threshold + 10,
                concurrent_blocked, self.concurrent_requests
            ),
        }
    }

    pub async fn test_account_enumeration(&self) -> TestResult {
        // Test if different response times reveal account existence
        let client = Client::new();

        let existing_email_times = self.measure_login_times(
            &client, "existing@example.com", 100
        ).await?;

        let nonexistent_email_times = self.measure_login_times(
            &client, "nonexistent@example.com", 100
        ).await?;

        // Check for timing attack vulnerability
        let time_difference = (existing_email_times.mean() - nonexistent_email_times.mean()).abs();

        TestResult {
            passed: time_difference < Duration::from_micros(500), // < 500µs difference
            details: format!("Time difference: {:?}", time_difference),
        }
    }
}
```

#### Scanner 2: TOTP/MFA Bypass Tester

```rust
// pentest/scanners/mfa_bypass.rs
pub struct MfaBypasser {
    target: String,
}

impl MfaBypasser {
    pub async fn test_totp_brute_force(&self) -> TestResult {
        // Test 1: Rate limiting on TOTP verification
        let client = Client::new();
        let mut attempts = 0;
        let mut blocked = false;

        for code in 0..1000000 {
            let response = client.post(&format!("{}/graphql", self.target))
                .json(&serde_json::json!({
                    "query": format!(
                        "mutation {{ verifyTotp(userId: \"test-user\", code: \"{:06}\") {{ success }} }}",
                        code
                    )
                }))
                .send()
                .await?;

            attempts += 1;

            if response.status() == 429 {
                blocked = true;
                break;
            }
        }

        TestResult {
            passed: blocked && attempts < 10, // Should block after < 10 attempts
            details: format!("Blocked after {} attempts", attempts),
        }
    }

    pub async fn test_backup_code_enumeration(&self) -> TestResult {
        // Test if backup code verification leaks information
        let client = Client::new();

        let timing_results = vec![
            self.test_backup_code(&client, "VALID-CODE-1").await?,
            self.test_backup_code(&client, "INVALID-CODE").await?,
        ];

        // Verify constant-time behavior
        let variance = calculate_variance(&timing_results);

        TestResult {
            passed: variance < Duration::from_micros(100), // < 100µs variance
            details: format!("Timing variance: {:?}", variance),
        }
    }

    pub async fn test_recovery_key_brute_force(&self) -> TestResult {
        // Test recovery key rate limiting
        let client = Client::new();
        let mut attempts = 0;
        let mut blocked = false;

        for _ in 0..50 {
            let fake_key = generate_random_recovery_key();
            let response = client.post(&format!("{}/graphql", self.target))
                .json(&serde_json::json!({
                    "query": format!(
                        "mutation {{ useRecoveryKey(userId: \"test-user\", key: \"{}\") {{ success }} }}",
                        fake_key
                    )
                }))
                .send()
                .await?;

            attempts += 1;

            if response.status() == 429 {
                blocked = true;
                break;
            }
        }

        TestResult {
            passed: blocked && attempts < 5, // Should block after < 5 attempts
            details: format!("Blocked after {} attempts", attempts),
        }
    }
}
```

#### Scanner 3: GraphQL Security Tester

```rust
// pentest/scanners/graphql_security.rs
pub struct GraphQLSecurityTester {
    target: String,
}

impl GraphQLSecurityTester {
    pub async fn test_introspection_disabled(&self) -> TestResult {
        let client = Client::new();

        let response = client.post(&format!("{}/graphql", self.target))
            .json(&serde_json::json!({
                "query": "{ __schema { types { name } } }"
            }))
            .send()
            .await?;

        TestResult {
            passed: !response.status().is_success(),
            details: format!("Introspection status: {}", response.status()),
        }
    }

    pub async fn test_query_depth_limiting(&self) -> TestResult {
        let client = Client::new();

        // Generate deeply nested query (depth > 10)
        let deep_query = generate_deeply_nested_query(15);

        let response = client.post(&format!("{}/graphql", self.target))
            .json(&serde_json::json!({
                "query": deep_query
            }))
            .send()
            .await?;

        TestResult {
            passed: response.status() == 400, // Should reject deep queries
            details: format!("Deep query response: {}", response.status()),
        }
    }

    pub async fn test_batch_attack_mitigation(&self) -> TestResult {
        let client = Client::new();

        // Send 100 mutations in a single batch
        let batch_query = (0..100).map(|i| {
            format!("m{}: login(email: \"user{}@example.com\", password: \"test\") {{ success }}", i, i)
        }).collect::<Vec<_>>().join("\n");

        let response = client.post(&format!("{}/graphql", self.target))
            .json(&serde_json::json!({
                "query": format!("mutation {{ {} }}", batch_query)
            }))
            .send()
            .await?;

        TestResult {
            passed: response.status() == 429 || response.status() == 400,
            details: format!("Batch attack response: {}", response.status()),
        }
    }
}
```

#### Scanner 4: Rust Crypto Side-Channel Tester

```rust
// pentest/scanners/crypto_side_channel.rs
use std::time::Instant;

pub struct CryptoSideChannelTester {
    target: String,
}

impl CryptoSideChannelTester {
    pub async fn test_hmac_constant_time(&self) -> TestResult {
        // Test HMAC email lookup for timing attacks
        let client = Client::new();

        let mut timing_results = Vec::new();

        // Test 1: Existing email (should match HMAC)
        for _ in 0..1000 {
            let start = Instant::now();
            let _ = client.post(&format!("{}/api/check-email", self.target))
                .json(&serde_json::json!({
                    "email": "existing@example.com"
                }))
                .send()
                .await?;
            timing_results.push(start.elapsed());
        }

        let existing_mean = calculate_mean(&timing_results);
        timing_results.clear();

        // Test 2: Non-existing email (should not match HMAC)
        for _ in 0..1000 {
            let start = Instant::now();
            let _ = client.post(&format!("{}/api/check-email", self.target))
                .json(&serde_json::json!({
                    "email": "nonexistent@example.com"
                }))
                .send()
                .await?;
            timing_results.push(start.elapsed());
        }

        let nonexistent_mean = calculate_mean(&timing_results);

        // Calculate statistical difference
        let time_difference = (existing_mean - nonexistent_mean).abs();
        let variance = calculate_variance(&timing_results);

        TestResult {
            passed: time_difference < Duration::from_micros(1), // < 1µs difference
            details: format!(
                "Time difference: {:?}, Variance: {:?}",
                time_difference, variance
            ),
        }
    }

    pub async fn test_encryption_timing_leaks(&self) -> TestResult {
        // Test if encryption time varies based on plaintext content
        let short_plaintext = "a";
        let long_plaintext = "a".repeat(1000);

        let short_times = self.measure_encryption_time(&short_plaintext, 1000).await?;
        let long_times = self.measure_encryption_time(&long_plaintext, 1000).await?;

        let time_difference = (short_times.mean() - long_times.mean()).abs();

        TestResult {
            passed: time_difference < Duration::from_micros(10), // < 10µs difference
            details: format!("Timing difference: {:?}", time_difference),
        }
    }
}
```

#### Scanner 5: Session Security Tester

```rust
// pentest/scanners/session_security.rs
pub struct SessionSecurityTester {
    target: String,
}

impl SessionSecurityTester {
    pub async fn test_session_fixation(&self) -> TestResult {
        let client = Client::new();

        // Step 1: Get unauthenticated session cookie
        let unauthenticated_response = client.get(&format!("{}/", self.target))
            .send()
            .await?;

        let unauthenticated_cookie = unauthenticated_response.cookies()
            .find(|c| c.name() == "sessionid")
            .map(|c| c.value().to_string());

        // Step 2: Authenticate with the same session cookie
        let login_response = client.post(&format!("{}/graphql", self.target))
            .json(&serde_json::json!({
                "query": "mutation { login(email: \"test@example.com\", password: \"password\") { sessionToken } }"
            }))
            .send()
            .await?;

        let authenticated_cookie = login_response.cookies()
            .find(|c| c.name() == "sessionid")
            .map(|c| c.value().to_string());

        TestResult {
            passed: unauthenticated_cookie != authenticated_cookie,
            details: "Session cookie should change after authentication".to_string(),
        }
    }

    pub async fn test_session_hijacking_detection(&self) -> TestResult {
        let client = Client::new();

        // Step 1: Login and get session cookie
        let login_response = client.post(&format!("{}/graphql", self.target))
            .json(&serde_json::json!({
                "query": "mutation { login(email: \"test@example.com\", password: \"password\") { sessionToken } }"
            }))
            .send()
            .await?;

        let session_cookie = login_response.cookies()
            .find(|c| c.name() == "sessionid")
            .unwrap()
            .value()
            .to_string();

        // Step 2: Use session from different IP address
        let hijack_client = Client::builder()
            .default_headers({
                let mut headers = reqwest::header::HeaderMap::new();
                headers.insert("X-Forwarded-For", "1.2.3.4".parse().unwrap());
                headers
            })
            .build()?;

        let hijack_response = hijack_client.get(&format!("{}/api/user/profile", self.target))
            .header("Cookie", format!("sessionid={}", session_cookie))
            .send()
            .await?;

        TestResult {
            passed: hijack_response.status() == 403 || hijack_response.status() == 401,
            details: format!("Hijack attempt status: {}", hijack_response.status()),
        }
    }

    pub async fn test_concurrent_session_limits(&self) -> TestResult {
        // Test if multiple concurrent sessions are allowed
        let client = Client::new();

        // Create 10 concurrent sessions
        let mut handles = vec![];
        for _ in 0..10 {
            let client = client.clone();
            let target = self.target.clone();
            handles.push(tokio::spawn(async move {
                client.post(&format!("{}/graphql", target))
                    .json(&serde_json::json!({
                        "query": "mutation { login(email: \"test@example.com\", password: \"password\") { sessionToken } }"
                    }))
                    .send()
                    .await
            }));
        }

        let results = futures::future::join_all(handles).await;
        let success_count = results.iter()
            .filter(|r| r.as_ref().ok().and_then(|resp| Some(resp.status().is_success())).unwrap_or(false))
            .count();

        TestResult {
            passed: success_count <= 3, // Should limit to max 3 concurrent sessions
            details: format!("Concurrent sessions allowed: {}", success_count),
        }
    }
}
```

### 2.2 Python-Based Integration Tests

**Location:** `tests/security/pentest/`

#### Test Suite 1: Password Security

```python
# tests/security/pentest/test_password_security.py
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor
import time

class TestPasswordSecurity:
    def test_weak_password_rejection(self, graphql_client):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "password",
            "12345678",
            "qwerty123",
            "abc123",
            "Password1",  # Common pattern
            "asdfasdf",   # Keyboard pattern
            "aaaaaaaa",   # Repeated characters
        ]

        for password in weak_passwords:
            response = graphql_client.execute(
                """
                mutation {
                    register(
                        email: "test@example.com",
                        password: "%s",
                        firstName: "Test",
                        lastName: "User"
                    ) {
                        success
                        errors
                    }
                }
                """ % password
            )

            assert not response['data']['register']['success'], \
                f"Weak password '{password}' should be rejected"
            assert 'password' in response['data']['register']['errors']

    def test_password_breach_detection(self, graphql_client):
        """Test integration with Have I Been Pwned API"""
        breached_password = "password123"  # Known breached password

        response = graphql_client.execute(
            """
            mutation {
                register(
                    email: "test@example.com",
                    password: "%s",
                    firstName: "Test",
                    lastName: "User"
                ) {
                    success
                    errors
                }
            }
            """ % breached_password
        )

        assert not response['data']['register']['success']
        assert 'breached' in str(response['data']['register']['errors']).lower()

    def test_password_history(self, graphql_client, test_user):
        """Test that users cannot reuse recent passwords"""
        old_password = "OldPassword123!"
        new_password = "NewPassword123!"

        # Change password 5 times
        for i in range(5):
            response = graphql_client.execute(
                """
                mutation {
                    changePassword(
                        userId: "%s",
                        currentPassword: "%s",
                        newPassword: "%s"
                    ) {
                        success
                    }
                }
                """ % (test_user.id, old_password if i == 0 else f"Password{i}123!",
                       f"Password{i+1}123!")
            )
            assert response['data']['changePassword']['success']

        # Try to reuse old password
        response = graphql_client.execute(
            """
            mutation {
                changePassword(
                    userId: "%s",
                    currentPassword: "Password5123!",
                    newPassword: "%s"
                ) {
                    success
                    errors
                }
            }
            """ % (test_user.id, old_password)
        )

        assert not response['data']['changePassword']['success']
        assert 'history' in str(response['data']['changePassword']['errors']).lower()
```

#### Test Suite 2: GDPR Compliance

```python
# tests/security/pentest/test_gdpr_compliance.py
import pytest
import time

class TestGDPRCompliance:
    def test_data_export(self, graphql_client, test_user):
        """Test GDPR data export (DSAR)"""
        response = graphql_client.execute(
            """
            mutation {
                requestDataExport(userId: "%s") {
                    success
                    exportId
                }
            }
            """ % test_user.id
        )

        assert response['data']['requestDataExport']['success']
        export_id = response['data']['requestDataExport']['exportId']

        # Wait for export to complete (max 30 seconds)
        for _ in range(30):
            status_response = graphql_client.execute(
                """
                query {
                    dataExportStatus(exportId: "%s") {
                        status
                        downloadUrl
                    }
                }
                """ % export_id
            )

            if status_response['data']['dataExportStatus']['status'] == 'completed':
                break
            time.sleep(1)

        assert status_response['data']['dataExportStatus']['status'] == 'completed'
        assert status_response['data']['dataExportStatus']['downloadUrl'] is not None

    def test_right_to_erasure(self, graphql_client, test_user):
        """Test GDPR right to erasure (30-day grace period)"""
        # Request deletion
        response = graphql_client.execute(
            """
            mutation {
                requestAccountDeletion(userId: "%s") {
                    success
                    scheduledDeletionDate
                }
            }
            """ % test_user.id
        )

        assert response['data']['requestAccountDeletion']['success']
        scheduled_date = response['data']['requestAccountDeletion']['scheduledDeletionDate']

        # Verify 30-day grace period
        from datetime import datetime, timedelta
        expected_date = (datetime.now() + timedelta(days=30)).date()
        assert datetime.fromisoformat(scheduled_date).date() == expected_date

    def test_consent_tracking(self, graphql_client, test_user):
        """Test consent audit trail"""
        # Grant phone consent
        response = graphql_client.execute(
            """
            mutation {
                grantPhoneConsent(userId: "%s") {
                    success
                }
            }
            """ % test_user.id
        )

        assert response['data']['grantPhoneConsent']['success']

        # Verify consent log
        log_response = graphql_client.execute(
            """
            query {
                consentHistory(userId: "%s") {
                    consentType
                    granted
                    timestamp
                    version
                }
            }
            """ % test_user.id
        )

        logs = log_response['data']['consentHistory']
        assert len(logs) > 0
        assert logs[0]['consentType'] == 'phone'
        assert logs[0]['granted'] == True
```

#### Test Suite 3: IP Security

```python
# tests/security/pentest/test_ip_security.py
import pytest
import requests

class TestIPSecurity:
    def test_ip_blacklist_blocking(self, graphql_client, blacklisted_ip):
        """Test that blacklisted IPs are blocked"""
        response = requests.post(
            f"{graphql_client.url}/graphql",
            json={
                "query": """
                mutation {
                    login(email: "test@example.com", password: "password") {
                        success
                    }
                }
                """
            },
            headers={"X-Forwarded-For": blacklisted_ip}
        )

        assert response.status_code == 403

    def test_ip_whitelist_bypass(self, graphql_client, whitelisted_ip):
        """Test that whitelisted IPs bypass rate limiting"""
        # Make 100 requests from whitelisted IP (should not be rate limited)
        for _ in range(100):
            response = requests.post(
                f"{graphql_client.url}/graphql",
                json={
                    "query": """
                    mutation {
                        login(email: "test@example.com", password: "wrong") {
                            success
                        }
                    }
                    """
                },
                headers={"X-Forwarded-For": whitelisted_ip}
            )

            assert response.status_code != 429, "Whitelisted IP should not be rate limited"

    def test_ip_spoofing_prevention(self, graphql_client):
        """Test that X-Forwarded-For spoofing is prevented"""
        # Try to bypass IP blacklist by spoofing X-Forwarded-For
        response = requests.post(
            f"{graphql_client.url}/graphql",
            json={
                "query": """
                mutation {
                    login(email: "test@example.com", password: "password") {
                        success
                    }
                }
                """
            },
            headers={
                "X-Forwarded-For": "1.2.3.4",  # Spoofed IP
                "X-Real-IP": "5.6.7.8",  # Different IP
            }
        )

        # Should use trusted proxy headers only
        assert response.status_code in [200, 429]  # Not 403 (not using spoofed IP)
```

---

## 3. Scheduled Penetration Testing Strategy

### 3.1 Environment-Specific Testing

| Environment     | Test Frequency | Test Scope                                                           | Automation                | Manual Review                             |
| --------------- | -------------- | -------------------------------------------------------------------- | ------------------------- | ----------------------------------------- |
| **Development** | On every PR    | Unit security tests, basic auth tests                                | 100% automated            | None                                      |
| **Testing**     | Nightly        | Full pentest suite, regression tests, dependency scans               | 100% automated            | Weekly review                             |
| **Staging**     | Weekly         | Full pentest suite + manual testing, OWASP Top 10, zero-day research | 80% automated, 20% manual | Weekly review                             |
| **Production**  | Monthly        | Non-destructive scans only, external penetration testing (quarterly) | 50% automated, 50% manual | Monthly review + quarterly external audit |

### 3.2 CI/CD Integration

#### GitHub Actions Workflow

```yaml
# .github/workflows/security-pentest.yml
name: Security Penetration Testing

on:
  pull_request:
    branches: [main, staging, testing]
  schedule:
    - cron: "0 2 * * *" # Daily at 2 AM UTC
  workflow_dispatch: # Manual trigger

jobs:
  pentest-dev:
    name: Development Environment Tests
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Build Rust pentest tools
        run: |
          cd pentest
          cargo build --release

      - name: Run authentication brute force tests
        run: ./pentest/target/release/auth_brute_force --target http://localhost:8000 --threshold 10

      - name: Run MFA bypass tests
        run: ./pentest/target/release/mfa_bypass --target http://localhost:8000

      - name: Run GraphQL security tests
        run: ./pentest/target/release/graphql_security --target http://localhost:8000

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: pentest-results-dev
          path: pentest/results/

  pentest-testing:
    name: Testing Environment (Nightly)
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 2 * * *'
    environment: testing
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.14"

      - name: Install dependencies
        run: |
          pip install -r tests/security/requirements.txt

      - name: Run Python security tests
        run: |
          pytest tests/security/pentest/ \
            --target=${{ secrets.TESTING_URL }} \
            --junit-xml=pentest-results.xml

      - name: Run Rust pentest tools
        run: |
          cd pentest
          cargo build --release
          ./scripts/run_full_suite.sh --target ${{ secrets.TESTING_URL }}

      - name: Run OWASP ZAP scan
        uses: zaproxy/action-full-scan@v0.4.0
        with:
          target: ${{ secrets.TESTING_URL }}
          rules_file_name: ".zap/rules.tsv"
          cmd_options: "-a"

      - name: Upload results to DefectDojo
        run: |
          python scripts/upload_to_defectdojo.py \
            --results pentest/results/ \
            --environment testing

      - name: Notify security team
        if: failure()
        uses: slackapi/slack-github-action@v1.24.0
        with:
          payload: |
            {
              "text": "Nightly penetration testing failed on Testing environment",
              "attachments": [{
                "color": "danger",
                "fields": [{
                  "title": "Environment",
                  "value": "Testing",
                  "short": true
                }, {
                  "title": "Workflow",
                  "value": "${{ github.workflow }}",
                  "short": true
                }]
              }]
            }

  pentest-staging:
    name: Staging Environment (Weekly)
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 2 * * 0' # Weekly on Sunday
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Run full pentest suite
        run: |
          cd pentest
          cargo build --release
          ./scripts/run_full_suite.sh --target ${{ secrets.STAGING_URL }} --comprehensive

      - name: Run OWASP Top 10 tests
        run: |
          pytest tests/security/owasp/ \
            --target=${{ secrets.STAGING_URL }} \
            --comprehensive

      - name: Run side-channel tests
        run: |
          ./pentest/target/release/crypto_side_channel \
            --target ${{ secrets.STAGING_URL }} \
            --iterations 10000

      - name: Upload results
        run: |
          python scripts/upload_to_defectdojo.py \
            --results pentest/results/ \
            --environment staging \
            --engagement-id ${{ secrets.DEFECTDOJO_ENGAGEMENT_ID }}

  pentest-production:
    name: Production Environment (Monthly)
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 3 1 * *' # Monthly on 1st at 3 AM
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Run non-destructive scans only
        run: |
          cd pentest
          cargo build --release
          ./scripts/run_production_safe_suite.sh \
            --target ${{ secrets.PRODUCTION_URL }} \
            --read-only

      - name: Run passive vulnerability scanning
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "config"
          scan-ref: "."

      - name: Upload results
        run: |
          python scripts/upload_to_defectdojo.py \
            --results pentest/results/ \
            --environment production \
            --engagement-id ${{ secrets.DEFECTDOJO_PRODUCTION_ENGAGEMENT_ID }}

      - name: Trigger external penetration testing
        if: github.event.schedule == '0 3 1 */3 *' # Quarterly
        run: |
          curl -X POST ${{ secrets.EXTERNAL_PENTEST_WEBHOOK }} \
            -H "Authorization: Bearer ${{ secrets.EXTERNAL_PENTEST_TOKEN }}" \
            -d '{"environment": "production", "scope": "authentication"}'
```

### 3.3 Automated Testing Schedule

```bash
# scripts/schedule_pentests.sh
#!/bin/bash

# Development: On every commit
- Rust unit tests for crypto functions
- Python unit tests for authentication logic
- Basic auth flow tests (registration, login, logout)

# Testing Environment: Nightly at 2 AM UTC
0 2 * * * /usr/local/bin/run_pentest_suite.sh testing

# Staging Environment: Weekly on Sundays at 2 AM UTC
0 2 * * 0 /usr/local/bin/run_pentest_suite.sh staging

# Production: Monthly on 1st at 3 AM UTC
0 3 1 * * /usr/local/bin/run_pentest_suite.sh production --read-only

# External Penetration Testing: Quarterly
0 3 1 */3 * /usr/local/bin/trigger_external_pentest.sh production
```

---

## 4. Rust-Specific Security Testing

### 4.1 Cryptographic Side-Channel Tests

**Test Coverage:**

- HMAC timing attacks (email/phone lookup)
- Encryption timing leaks
- Password verification timing attacks
- TOTP constant-time comparison

**Tools:**

- `pentest/scanners/crypto_side_channel.rs` (custom)
- `cargo-timing` (<https://github.com/RustCrypto/cargo-timing>)
- `criterion` benchmarks with statistical analysis

**Automation:**

```bash
# Run 10,000 iterations to detect timing attacks
cargo bench --bench crypto_timing -- --iterations 10000

# Analyze variance (should be < 1µs for constant-time operations)
./scripts/analyze_timing_variance.py crypto_timing_results.json
```

### 4.2 Memory Safety Tests

**Test Coverage:**

- Memory leaks in PyO3 FFI boundary
- Zeroization verification (plaintext cleared after encryption)
- Use-after-free in Rust crypto functions
- Buffer overflows in unsafe blocks

**Tools:**

- Valgrind: `valgrind --leak-check=full python manage.py test`
- AddressSanitizer: `RUSTFLAGS="-Z sanitizer=address" cargo test`
- Miri: `cargo +nightly miri test`

**Automation:**

```yaml
# .github/workflows/memory-safety.yml
- name: Run Miri tests
  run: |
    rustup +nightly component add miri
    cargo +nightly miri test --package syntek-encryption

- name: Run AddressSanitizer
  run: |
    RUSTFLAGS="-Z sanitizer=address" cargo test --target x86_64-unknown-linux-gnu
```

### 4.3 Fuzzing Tests

**Test Coverage:**

- Encryption/decryption with malformed inputs
- HMAC with invalid keys
- Password hashing with edge cases
- PyO3 bindings with unexpected Python types

**Tools:**

- AFL.rs: `cargo afl build && cargo afl fuzz -i in -o out target/debug/fuzz_target`
- cargo-fuzz: `cargo fuzz run encrypt_field -- -max_total_time=3600`

**Automation:**

```bash
# Run fuzzing for 1 hour daily
0 3 * * * cargo fuzz run encrypt_field -- -max_total_time=3600
```

---

## 5. Test Coverage Matrix

### 5.1 Authentication Flow Coverage

| Flow                   | Attack Vectors                                                                           | Automated Tests | Manual Tests | Coverage |
| ---------------------- | ---------------------------------------------------------------------------------------- | --------------- | ------------ | -------- |
| **Registration**       | Email enumeration, CAPTCHA bypass, automated registration, weak passwords, SQL injection | ✅ Automated    | ✅ Manual    | 95%      |
| **Login**              | Brute force, credential stuffing, timing attacks, session fixation, SQL injection        | ✅ Automated    | ✅ Manual    | 98%      |
| **TOTP Setup**         | QR code interception, secret exposure, backup code enumeration                           | ✅ Automated    | ✅ Manual    | 90%      |
| **TOTP Verification**  | Brute force, time drift attacks, replay attacks                                          | ✅ Automated    | ✅ Manual    | 95%      |
| **Password Reset**     | Account takeover, token prediction, email interception                                   | ✅ Automated    | ✅ Manual    | 92%      |
| **Recovery Keys**      | Brute force, enumeration, race conditions                                                | ✅ Automated    | ✅ Manual    | 88%      |
| **Passkeys**           | Relying party spoofing, credential ID enumeration                                        | ❌ Manual only  | ✅ Manual    | 70%      |
| **Session Management** | Session fixation, hijacking, concurrent sessions                                         | ✅ Automated    | ✅ Manual    | 96%      |
| **IP Tracking**        | IP spoofing, VPN/proxy abuse, geolocation bypass                                         | ✅ Automated    | ✅ Manual    | 85%      |
| **GDPR Export**        | Data leakage, unauthorized access, incomplete export                                     | ✅ Automated    | ✅ Manual    | 80%      |

### 5.2 OWASP Top 10 Coverage

| OWASP Risk                     | Test Suite                                    | Automation | Coverage |
| ------------------------------ | --------------------------------------------- | ---------- | -------- |
| A01: Broken Access Control     | Session security tests, authorization tests   | ✅         | 95%      |
| A02: Cryptographic Failures    | Crypto side-channel tests, key rotation tests | ✅         | 92%      |
| A03: Injection                 | SQL injection tests, GraphQL injection tests  | ✅         | 98%      |
| A04: Insecure Design           | Rate limiting tests, MFA bypass tests         | ✅         | 90%      |
| A05: Security Misconfiguration | Configuration scanning, CORS tests            | ✅         | 85%      |
| A06: Vulnerable Components     | Dependency scanning (Dependabot, Snyk)        | ✅         | 100%     |
| A07: Authentication Failures   | Brute force tests, password security tests    | ✅         | 97%      |
| A08: Software/Data Integrity   | JWT security tests, session integrity tests   | ✅         | 88%      |
| A09: Logging Failures          | Log analysis, PII leak detection              | ✅         | 82%      |
| A10: SSRF                      | URL validation tests, webhook security tests  | ✅         | 75%      |

---

## 6. Metrics & Reporting

### 6.1 Key Performance Indicators (KPIs)

| Metric                             | Target                                    | Measurement                               | Frequency         |
| ---------------------------------- | ----------------------------------------- | ----------------------------------------- | ----------------- |
| **Test Coverage**                  | > 90%                                     | Code coverage + security test coverage    | Weekly            |
| **Vulnerability Discovery Time**   | < 24 hours                                | Time from deployment to discovery         | Continuous        |
| **Vulnerability Remediation Time** | < 7 days for Critical, < 30 days for High | Time from discovery to fix                | Per vulnerability |
| **False Positive Rate**            | < 10%                                     | Manual verification of automated findings | Monthly           |
| **Penetration Test Pass Rate**     | > 95%                                     | Percentage of tests passed                | Per test run      |
| **Mean Time to Detect (MTTD)**     | < 1 hour                                  | Time from exploit to detection            | Continuous        |
| **Mean Time to Respond (MTTR)**    | < 4 hours                                 | Time from detection to mitigation         | Per incident      |

### 6.2 Reporting Dashboard

**Tools:**

- **DefectDojo**: Centralized vulnerability management
- **Grafana**: Real-time security metrics dashboard
- **Slack**: Automated security alerts

**Dashboard Panels:**

1. **Vulnerability Trends**: Critical/High/Medium/Low over time
2. **Test Pass/Fail Rates**: Per environment
3. **Coverage Metrics**: OWASP Top 10, authentication flows
4. **Mean Time to Remediate**: Per severity level
5. **External Penetration Test Results**: Quarterly trends

### 6.3 Incident Response

**Severity Levels:**

| Severity     | Examples                                               | Response Time        | Notification                     |
| ------------ | ------------------------------------------------------ | -------------------- | -------------------------------- |
| **Critical** | Authentication bypass, data breach, encryption failure | Immediate (< 1 hour) | Security team + CISO + CTO       |
| **High**     | MFA bypass, session hijacking, weak crypto             | < 4 hours            | Security team + Engineering lead |
| **Medium**   | Rate limiting bypass, verbose errors, missing logs     | < 24 hours           | Security team                    |
| **Low**      | Minor misconfigurations, informational leaks           | < 7 days             | Security team (weekly review)    |

**Escalation Path:**

1. Automated alert → Security team Slack channel
2. If Critical/High: Page on-call engineer
3. If no response in 30 minutes: Escalate to Engineering Manager
4. If no response in 1 hour: Escalate to CTO/CISO
5. If data breach confirmed: Activate incident response plan + legal team

---

## 7. External Penetration Testing

### 7.1 Quarterly External Audits

**Scope:**

- Full authentication system (backend, API, frontend, mobile)
- OWASP Top 10 verification
- Rust cryptographic implementation review
- Social engineering tests (phishing, pretexting)
- Physical security (if applicable)

**Deliverables:**

- Executive summary report
- Detailed technical findings
- Proof-of-concept exploits
- Remediation recommendations
- Re-test after fixes

**Recommended Vendors:**

- NCC Group (<https://www.nccgroup.com/>)
- Trail of Bits (<https://www.trailofbits.com/>)
- Bishop Fox (<https://bishopfox.com/>)
- Cure53 (<https://cure53.de/>) - Rust/crypto specialists

### 7.2 Bug Bounty Program (Future)

**Platform:** HackerOne or Bugcrowd

**Scope:**

- Authentication system (all environments except production)
- Staging environment only (production excluded initially)
- Web, mobile, API, GraphQL

**Rewards:**

| Severity | Reward           |
| -------- | ---------------- |
| Critical | $5,000 - $10,000 |
| High     | $2,000 - $5,000  |
| Medium   | $500 - $2,000    |
| Low      | $100 - $500      |

**Out of Scope:**

- Social engineering
- Physical attacks
- DoS attacks
- Spam/flooding
- Third-party service vulnerabilities

---

## 8. Implementation Checklist

### Phase 1: Setup (Week 1)

- [ ] Create `pentest/` directory structure
- [ ] Implement Rust pentest scanners (5 scanners)
- [ ] Write Python integration tests (3 test suites)
- [ ] Set up CI/CD workflows (GitHub Actions)
- [ ] Configure DefectDojo for vulnerability tracking

### Phase 2: Development Testing (Week 2)

- [ ] Integrate pentest into PR checks
- [ ] Run initial dev environment tests
- [ ] Fix any discovered vulnerabilities
- [ ] Achieve > 90% test coverage

### Phase 3: Testing Environment (Week 3)

- [ ] Deploy nightly pentest schedule
- [ ] Configure Slack alerts
- [ ] Run first full pentest suite
- [ ] Document findings and remediation

### Phase 4: Staging/Production (Week 4)

- [ ] Deploy weekly staging tests
- [ ] Deploy monthly production scans
- [ ] Configure external pentest trigger
- [ ] Create security dashboard in Grafana

### Phase 5: Continuous Improvement (Ongoing)

- [ ] Review and update test suites monthly
- [ ] Add new attack vectors as discovered
- [ ] Integrate bug bounty findings
- [ ] Annual security audit review

---

## 9. Conclusion

This penetration testing strategy provides comprehensive coverage of the authentication system across all environments. The combination of automated scheduled testing, custom Rust-based security scanners, and manual quarterly audits ensures continuous security validation.

**Key Success Factors:**

1. **Automation-first**: 80%+ of tests automated for continuous feedback
2. **Environment-specific**: Different test intensity for dev/testing/staging/production
3. **Rust-focused**: Custom side-channel and crypto tests for Rust security layer
4. **CI/CD integrated**: Security tests run on every PR and nightly
5. **External validation**: Quarterly professional penetration testing

**Expected Outcomes:**

- **< 24 hours**: Vulnerability discovery time
- **> 95%**: Test pass rate
- **> 90%**: Security test coverage
- **< 7 days**: Critical vulnerability remediation time

This strategy aligns with OWASP Top 10 2025, NIST Cybersecurity Framework, and GDPR compliance requirements, ensuring robust security for the authentication system.

---

## 10. Modularity & Configuration Requirements

### 10.1 Core Modularity Principles

**CRITICAL:** Every component of the authentication system MUST be modular and configurable when installed in other projects. The authentication module is a **library**, not an application - projects must be able to customize all behavior without modifying source code.

**Design Principles:**

1. **Configuration-Driven**: All behavior controlled via Django settings, not hardcoded values
2. **Sensible Defaults**: Works out-of-box with secure defaults, customizable for specific needs
3. **Feature Toggles**: Every feature can be enabled/disabled via configuration
4. **Provider Abstraction**: SMS, CAPTCHA, logging providers are pluggable
5. **Styling Agnostic**: UI components accept custom themes, colors, logos
6. **Multi-Tenant Safe**: Supports organisation-level configuration overrides

### 10.2 Configuration Architecture

#### Backend Configuration Structure

All authentication configuration lives in the Django settings file:

```python
# myproject/settings/auth.py

from syntek_security_auth.defaults import get_default_auth_config

# Option 1: Use all defaults (recommended for MVP)
SYNTEK_AUTHENTICATION = get_default_auth_config()

# Option 2: Override specific settings
SYNTEK_AUTHENTICATION = {
    **get_default_auth_config(),
    'PASSWORD_MIN_LENGTH': 16,  # Custom requirement
    'TOTP_REQUIRED': True,      # Enforce MFA
    'MAX_CONCURRENT_SESSIONS': 3,
}

# Option 3: Full custom configuration
SYNTEK_AUTHENTICATION = {
    # Registration
    'REGISTRATION_ENABLED': True,
    'REQUIRE_EMAIL_VERIFICATION': True,
    'REQUIRE_PHONE_VERIFICATION': False,
    'ALLOW_USERNAME': True,
    'USERNAME_REQUIRED': False,
    'PHONE_NUMBER_REQUIRED': False,

    # Password Requirements
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_NUMBERS': True,
    'PASSWORD_REQUIRE_SPECIAL': True,
    'PASSWORD_HISTORY_COUNT': 5,
    'CHECK_COMMON_PASSWORDS': True,

    # Login Security
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,
    'LOCKOUT_INCREMENT': True,
    'CAPTCHA_ON_REGISTRATION': False,
    'CAPTCHA_ON_LOGIN': False,
    'CAPTCHA_PROVIDER': 'recaptcha_v2',

    # MFA
    'TOTP_REQUIRED': False,
    'TOTP_ISSUER': 'My Company',
    'BACKUP_CODE_COUNT': 10,
    'RECOVERY_KEY_COUNT': 12,

    # Sessions
    'MAX_CONCURRENT_SESSIONS': 5,
    'SESSION_TIMEOUT': 1800,
    'IDLE_TIMEOUT': 1800,
    'ABSOLUTE_TIMEOUT': 43200,
    'REMEMBER_ME_DURATION': 2592000,
    'TERMINATE_OTHER_SESSIONS_ON_PASSWORD_CHANGE': True,

    # Auto-Logout
    'AUTO_LOGOUT_ENABLED': True,
    'AUTO_LOGOUT_WARNING_TIME': 300,
    'AUTO_LOGOUT_COUNTDOWN_SECONDS': 60,

    # IP Tracking
    'ENABLE_IP_TRACKING': True,
    'ENABLE_IP_WHITELIST': False,
    'ENABLE_IP_BLACKLIST': True,
    'AUTO_BLOCK_AFTER_FAILED_ATTEMPTS': 10,
    'AUTO_BLOCK_DURATION': 86400,

    # Social Authentication
    'SOCIAL_AUTH_ENABLED': True,
    'SOCIAL_AUTH_PROVIDERS': ['google', 'github', 'microsoft'],
    'SOCIAL_AUTH_AUTO_CREATE_USER': True,
    'SOCIAL_AUTH_ALLOW_LINKING': True,
    'SOCIAL_AUTH_REQUIRE_VERIFIED_EMAIL': True,
}
```

#### Provider Configuration

```python
# SMS Provider (Modular)
SYNTEK_SMS = {
    'PROVIDER': 'twilio',  # 'twilio', 'aws_sns', 'vonage', None
    'TWILIO_ACCOUNT_SID': env('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': env('TWILIO_AUTH_TOKEN'),
    'TWILIO_FROM_NUMBER': env('TWILIO_FROM_NUMBER'),

    # Rate limiting (cost protection)
    'MAX_SMS_PER_USER_PER_DAY': 10,
    'GLOBAL_DAILY_SMS_BUDGET': 500,
    'ALERT_ON_BUDGET_THRESHOLD': 0.8,
}

# CAPTCHA Provider (Modular)
SYNTEK_CAPTCHA = {
    'PROVIDER': 'recaptcha_v3',  # 'recaptcha_v2', 'recaptcha_v3', 'hcaptcha', None
    'RECAPTCHA_SITE_KEY': env('RECAPTCHA_SITE_KEY'),
    'RECAPTCHA_SECRET_KEY': env('RECAPTCHA_SECRET_KEY'),
    'RECAPTCHA_MIN_SCORE': 0.5,
    'HCAPTCHA_SITE_KEY': env('HCAPTCHA_SITE_KEY', default=None),
    'HCAPTCHA_SECRET_KEY': env('HCAPTCHA_SECRET_KEY', default=None),
}

# Logging Provider (Modular)
SYNTEK_AUTH_LOGGING = {
    'PROVIDER': 'glitchtip',  # 'glitchtip', 'grafana', 'sentry', 'datadog', 'standard', None
    'LOG_LEVEL': 'INFO',
    'LOG_FAILED_LOGINS': True,
    'LOG_SUCCESSFUL_LOGINS': False,  # Reduce noise
    'LOG_PASSWORD_CHANGES': True,
    'SANITIZE_LOGS': True,
}

# Social Authentication Providers (OAuth)
SYNTEK_SOCIAL_AUTH = {
    # Google OAuth
    'GOOGLE_ENABLED': True,
    'GOOGLE_CLIENT_ID': env('GOOGLE_CLIENT_ID'),
    'GOOGLE_CLIENT_SECRET': env('GOOGLE_CLIENT_SECRET'),
    'GOOGLE_SCOPES': ['openid', 'email', 'profile'],

    # GitHub OAuth
    'GITHUB_ENABLED': True,
    'GITHUB_CLIENT_ID': env('GITHUB_CLIENT_ID'),
    'GITHUB_CLIENT_SECRET': env('GITHUB_CLIENT_SECRET'),
    'GITHUB_SCOPES': ['user:email'],

    # Microsoft OAuth
    'MICROSOFT_ENABLED': False,
    'MICROSOFT_CLIENT_ID': env('MICROSOFT_CLIENT_ID', default=None),
    'MICROSOFT_CLIENT_SECRET': env('MICROSOFT_CLIENT_SECRET', default=None),
    'MICROSOFT_TENANT_ID': env('MICROSOFT_TENANT_ID', default='common'),

    # Apple Sign In
    'APPLE_ENABLED': False,
    'APPLE_CLIENT_ID': env('APPLE_CLIENT_ID', default=None),
    'APPLE_TEAM_ID': env('APPLE_TEAM_ID', default=None),
    'APPLE_KEY_ID': env('APPLE_KEY_ID', default=None),
    'APPLE_PRIVATE_KEY': env('APPLE_PRIVATE_KEY', default=None),
}
```

#### Frontend Configuration (Web)

```typescript
// myproject/config/auth.ts

import { AuthConfig } from '@syntek/ui-auth';

export const authConfig: AuthConfig = {
  // Registration
  enableRegistration: true,
  requireEmailVerification: true,
  requirePhoneVerification: false,
  enableUsername: true,
  usernameRequired: false,
  phoneNumberRequired: false,

  // Password
  passwordMinLength: 12,
  showPasswordStrengthIndicator: true,

  // CAPTCHA
  enableCaptcha: false,
  captchaProvider: 'recaptcha_v3',
  captchaSiteKey: process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY,

  // MFA
  enableTOTP: true,
  enablePasskeys: false,

  // Social Authentication
  enableSocialAuth: true,
  socialProviders: ['google', 'github'],
  socialButtonStyle: 'outline', // 'outline', 'filled', 'icon-only'

  // Auto-Logout
  enableAutoLogout: true,
  autoLogoutWarningTime: 300,
  autoLogoutCountdownSeconds: 60,
  showActivityIndicator: true,

  // UI Customization
  theme: 'system',
  logo: '/logo.png',
  brandColor: '#0066FF',
  customCSS: '/auth-custom.css',

  // Forms
  showLabels: true,
  showPlaceholders: true,
  showHelpText: true,
  inlineValidation: true,
};

// Pass to AuthProvider
import { AuthProvider } from '@syntek/ui-auth';

<AuthProvider config={authConfig}>
  {children}
</AuthProvider>
```

#### Mobile Configuration (React Native)

```typescript
// myapp/config/auth.ts

import { MobileAuthConfig } from "@syntek/mobile-auth";

export const mobileAuthConfig: MobileAuthConfig = {
  // API
  apiBaseUrl: process.env.API_BASE_URL,
  apiTimeout: 30000,

  // Biometric
  enableBiometric: true,
  biometricPrompt: "Authenticate to access your account",
  fallbackToPassword: true,
  biometricStorageKey: "syntek_biometric_key",

  // Security
  enableRootDetection: true,
  enableCertificatePinning: true,
  certificateHashes: [
    // SHA256 hashes of your SSL certificates
    "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
  ],

  // Social Authentication
  enableSocialAuth: true,
  socialProviders: ["google", "apple"], // Platform-specific
  usePKCE: true, // Always true for mobile

  // Auto-Logout
  enableAutoLogout: true,
  autoLogoutIdleTime: 1800,
  showAutoLogoutWarning: true,

  // Storage
  secureStorageKey: "com.myapp.auth",

  // UI
  theme: {
    primaryColor: "#0066FF",
    errorColor: "#EF4444",
    successColor: "#10B981",
  },
};
```

### 10.3 Feature Toggle Configuration

Every authentication feature can be disabled:

```python
SYNTEK_AUTHENTICATION = {
    # Core Features (can disable individually)
    'REGISTRATION_ENABLED': True,           # ❌ Disable if invite-only
    'PASSWORD_LOGIN_ENABLED': True,         # ❌ Disable if SSO-only
    'SOCIAL_AUTH_ENABLED': True,            # ❌ Disable if no OAuth
    'TOTP_ENABLED': True,                   # ❌ Disable if no MFA
    'PASSKEYS_ENABLED': False,              # ❌ Disable if not using WebAuthn
    'RECOVERY_KEYS_ENABLED': True,          # ❌ Disable if no account recovery
    'USERNAME_ENABLED': True,               # ❌ Disable if email-only login
    'PHONE_NUMBER_ENABLED': False,          # ❌ Disable if no phone verification

    # Security Features (can disable individually)
    'IP_TRACKING_ENABLED': True,            # ❌ Disable for privacy
    'IP_WHITELIST_ENABLED': False,          # ❌ Enable for corporate networks
    'IP_BLACKLIST_ENABLED': True,           # ❌ Disable if using WAF
    'SESSION_FINGERPRINTING': 'basic',      # 'none', 'basic', 'strict'
    'AUTO_LOGOUT_ENABLED': True,            # ❌ Disable for kiosk mode

    # Optional Integrations (None = disabled)
    'SMS_PROVIDER': 'twilio',               # None = no SMS
    'CAPTCHA_PROVIDER': None,               # None = no CAPTCHA
    'LOGGING_PROVIDER': 'glitchtip',        # None = standard Django logging
    'GEOLOCATION_PROVIDER': None,           # None = no IP geolocation
}
```

### 10.4 Per-Module Configuration

Each sub-module has its own configuration namespace:

```python
# Authentication Core
SYNTEK_AUTHENTICATION = { ... }

# Social Authentication (can be used independently)
SYNTEK_SOCIAL_AUTH = {
    'GOOGLE_ENABLED': True,
    'GITHUB_ENABLED': False,
    # ... OAuth provider settings
}

# Auto-Logout (can be used independently)
SYNTEK_AUTO_LOGOUT = {
    'ENABLED': True,
    'IDLE_TIMEOUT': 1800,
    'WARNING_TIME': 300,
    # ... auto-logout settings
}

# IP Tracking (can be used independently)
SYNTEK_IP_TRACKING = {
    'ENABLED': True,
    'ENCRYPT_IPS': True,
    'TRACK_GEOLOCATION': False,
    # ... IP tracking settings
}

# GDPR Compliance (can be used independently)
SYNTEK_GDPR = {
    'ENABLED': True,
    'DPO_EMAIL': 'dpo@mycompany.com',
    'PRIVACY_POLICY_URL': '/legal/privacy',
    # ... GDPR settings
}
```

### 10.5 Installation-Time Configuration

The Rust CLI generates configuration files during installation:

```bash
# Install authentication module
syntek install auth

# Interactive prompts:
? Enable email verification? (Y/n) Y
? Enable phone verification? (y/N) N
? Enable MFA (TOTP)? (Y/n) Y
? Enable passkeys? (y/N) N
? SMS provider? (twilio/aws_sns/vonage/none) twilio
? CAPTCHA provider? (recaptcha_v2/recaptcha_v3/hcaptcha/none) recaptcha_v3
? Logging provider? (glitchtip/grafana/sentry/standard) glitchtip
? Enable social authentication? (Y/n) Y
? Select OAuth providers: (google, github, microsoft, apple, facebook, linkedin, twitter)
  [x] Google
  [x] GitHub
  [ ] Microsoft
  [ ] Apple
  [ ] Facebook
  [ ] LinkedIn
  [ ] Twitter

# Generates:
# - myproject/settings/auth.py (with SYNTEK_AUTHENTICATION)
# - .env.example (with required environment variables)
# - docs/AUTH_SETUP.md (setup instructions)
```

**Generated `.env.example`:**

```bash
# Authentication Settings
RECAPTCHA_SITE_KEY=your_recaptcha_site_key_here
RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key_here

# SMS Provider (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Logging (GlitchTip)
GLITCHTIP_DSN=https://your_glitchtip_dsn

# Social Authentication - Google
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Social Authentication - GitHub
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Rust Encryption Keys (generated automatically)
ENCRYPTION_KEY_PATH=/var/keys/encryption.key
HMAC_KEY_PATH=/var/keys/hmac.key
```

### 10.6 Runtime Configuration (Admin Interface)

Some settings can be changed at runtime via Django admin:

```python
# myproject/admin.py

from syntek_security_auth.admin import AuthenticationConfigAdmin

# Register admin interface for runtime config
admin.site.register(AuthenticationConfig, AuthenticationConfigAdmin)

# Allows admins to change:
# - TOTP_REQUIRED (enforce MFA)
# - MAX_LOGIN_ATTEMPTS
# - LOCKOUT_DURATION
# - SESSION_TIMEOUT
# - CAPTCHA thresholds
# - IP whitelist/blacklist entries
# - Social provider enable/disable (without code changes)
```

**Organisation-Level Overrides** (Multi-Tenant):

```python
# Different organisations can have different settings
class Organisation(models.Model):
    name = models.CharField(max_length=255)

    # Override global settings
    require_mfa = models.BooleanField(default=False)
    max_session_timeout = models.IntegerField(default=1800)
    allowed_social_providers = models.JSONField(default=list)
    ip_whitelist_only = models.BooleanField(default=False)

    def get_auth_config(self):
        # Returns organisation-specific config
        return {
            **settings.SYNTEK_AUTHENTICATION,
            'TOTP_REQUIRED': self.require_mfa,
            'SESSION_TIMEOUT': self.max_session_timeout,
        }
```

### 10.7 Styling & Theming (UI Components)

All UI components are fully customizable:

**Web (Next.js/React):**

```typescript
// Custom theme
import { AuthProvider, createAuthTheme } from '@syntek/ui-auth';

const customTheme = createAuthTheme({
  colors: {
    primary: '#0066FF',
    secondary: '#6366F1',
    success: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
    background: '#FFFFFF',
    surface: '#F9FAFB',
    text: '#111827',
    textSecondary: '#6B7280',
    border: '#E5E7EB',
  },
  fonts: {
    body: 'Inter, sans-serif',
    heading: 'Inter, sans-serif',
    mono: 'Fira Code, monospace',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    full: '9999px',
  },
});

<AuthProvider config={authConfig} theme={customTheme}>
  {children}
</AuthProvider>

// Or use CSS variables (recommended)
// All components use CSS custom properties:
:root {
  --auth-color-primary: #0066FF;
  --auth-color-error: #EF4444;
  --auth-border-radius: 0.5rem;
  --auth-font-family: 'Inter', sans-serif;
}

// Override individual components
.syntek-auth-button {
  border-radius: var(--auth-border-radius);
  background: linear-gradient(to right, #0066FF, #6366F1);
}
```

**Mobile (React Native):**

```typescript
import { AuthProvider } from '@syntek/mobile-auth';

const customTheme = {
  colors: {
    primary: '#0066FF',
    error: '#EF4444',
    success: '#10B981',
    background: '#FFFFFF',
    text: '#111827',
  },
  fonts: {
    regular: 'Inter-Regular',
    medium: 'Inter-Medium',
    bold: 'Inter-Bold',
  },
  spacing: (factor: number) => factor * 8,
};

<AuthProvider config={mobileAuthConfig} theme={customTheme}>
  {children}
</AuthProvider>
```

### 10.8 Custom Components (Bring Your Own UI)

Projects can replace default components with custom implementations:

```typescript
// Use default components
import { LoginForm } from '@syntek/ui-auth';
<LoginForm />

// Or bring your own (using headless hooks)
import { useLogin } from '@syntek/ui-auth/hooks';

function CustomLoginForm() {
  const { login, loading, error } = useLogin();

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      login({ email, password });
    }}>
      {/* Your custom UI */}
    </form>
  );
}
```

**Available Headless Hooks:**

- `useLogin()` - Login logic without UI
- `useRegister()` - Registration logic
- `usePasswordReset()` - Password reset flow
- `useTOTP()` - TOTP setup/verify
- `useSocialAuth()` - OAuth flow
- `useAutoLogout()` - Auto-logout state management
- `useSession()` - Session management

### 10.9 Database Customization

Projects can extend authentication models:

```python
# myproject/models.py

from syntek_security_auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Add custom fields
    department = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    manager = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'custom_users'

# settings.py
AUTH_USER_MODEL = 'myproject.CustomUser'
```

**Extend Authentication Models:**

```python
from syntek_security_auth.models import AbstractSession

class CustomSession(AbstractSession):
    # Add custom session data
    device_name = models.CharField(max_length=255)
    browser_version = models.CharField(max_length=100)
```

### 10.10 Validation & Enforcement

The CLI validates configuration on installation:

```bash
syntek install auth --validate

# Checks:
# ✓ All required environment variables present
# ✓ SMS provider credentials valid (test API call)
# ✓ CAPTCHA keys valid (test verification)
# ✓ Database migrations compatible
# ✓ Rust encryption keys generated
# ✓ OAuth redirect URLs configured
# ✗ ERROR: GOOGLE_CLIENT_SECRET missing in .env

# Fix issues:
syntek install auth --fix

# Interactive prompts to fix configuration errors
```

### 10.11 Configuration Examples by Use Case

#### Example 1: Simple SaaS (Email + Password Only)

```python
SYNTEK_AUTHENTICATION = {
    'REGISTRATION_ENABLED': True,
    'REQUIRE_EMAIL_VERIFICATION': True,
    'REQUIRE_PHONE_VERIFICATION': False,
    'TOTP_REQUIRED': False,
    'SOCIAL_AUTH_ENABLED': False,
    'PASSKEYS_ENABLED': False,
    'IP_TRACKING_ENABLED': True,
    'CAPTCHA_PROVIDER': 'recaptcha_v3',
}
```

#### Example 2: Enterprise B2B (Strict Security)

```python
SYNTEK_AUTHENTICATION = {
    'REGISTRATION_ENABLED': False,  # Invite-only
    'REQUIRE_EMAIL_VERIFICATION': True,
    'TOTP_REQUIRED': True,  # Enforce MFA
    'PASSKEYS_ENABLED': True,
    'PASSWORD_MIN_LENGTH': 16,
    'SESSION_TIMEOUT': 900,  # 15 minutes
    'IP_WHITELIST_ENABLED': True,  # Corporate network only
    'SOCIAL_AUTH_ENABLED': True,
    'SOCIAL_AUTH_PROVIDERS': ['microsoft', 'google'],  # SSO
}
```

#### Example 3: Consumer Mobile App (Social + Biometric)

```python
# Backend
SYNTEK_AUTHENTICATION = {
    'REGISTRATION_ENABLED': True,
    'REQUIRE_EMAIL_VERIFICATION': False,  # Email optional
    'SOCIAL_AUTH_ENABLED': True,
    'SOCIAL_AUTH_PROVIDERS': ['google', 'apple', 'facebook'],
    'TOTP_REQUIRED': False,  # Optional MFA
    'CAPTCHA_PROVIDER': None,  # No CAPTCHA for mobile
}

# Mobile
const mobileAuthConfig = {
  enableBiometric: true,
  enableSocialAuth: true,
  socialProviders: ['google', 'apple'],
  enablePasswordLogin: false,  # Social/biometric only
};
```

#### Example 4: Healthcare/HIPAA (Maximum Security)

```python
SYNTEK_AUTHENTICATION = {
    'TOTP_REQUIRED': True,
    'PASSKEYS_ENABLED': True,
    'PASSWORD_MIN_LENGTH': 16,
    'PASSWORD_HISTORY_COUNT': 24,
    'SESSION_TIMEOUT': 600,  # 10 minutes
    'MAX_CONCURRENT_SESSIONS': 1,
    'TERMINATE_OTHER_SESSIONS_ON_PASSWORD_CHANGE': True,
    'IP_TRACKING_ENABLED': True,
    'LOG_ALL_ACCESS': True,
    'ENABLE_AUDIT_TRAIL': True,
    'AUTO_LOGOUT_ENABLED': True,
    'AUTO_LOGOUT_WARNING_TIME': 120,  # 2 minutes warning
}
```

### 10.12 Documentation Generation

The CLI generates project-specific documentation:

```bash
syntek install auth

# Generates:
# docs/authentication/
# ├── SETUP.md              # Installation steps
# ├── CONFIGURATION.md      # All config options
# ├── CUSTOMIZATION.md      # Theming and styling
# ├── API_REFERENCE.md      # GraphQL API docs
# ├── SECURITY.md           # Security best practices
# └── EXAMPLES.md           # Code examples
```

**Generated CONFIGURATION.md** includes:

- All available settings with descriptions
- Default values
- Valid options for enums
- Environment variables required
- Provider-specific setup guides
- Multi-tenant configuration examples
- Performance tuning recommendations

---

## 11. Configuration Compliance Checklist

Before deploying the authentication module, verify:

- [ ] **Backend Configuration**
  - [ ] `SYNTEK_AUTHENTICATION` settings reviewed
  - [ ] SMS provider configured (if enabled)
  - [ ] CAPTCHA provider configured (if enabled)
  - [ ] Logging provider configured
  - [ ] Social OAuth providers configured
  - [ ] Environment variables set in `.env`

- [ ] **Frontend Configuration**
  - [ ] `AuthConfig` matches backend settings
  - [ ] CAPTCHA site key configured
  - [ ] API endpoint URLs correct
  - [ ] Theme/branding customized

- [ ] **Mobile Configuration**
  - [ ] Biometric authentication configured
  - [ ] Certificate pinning hashes set
  - [ ] Secure storage keys generated
  - [ ] OAuth redirect URLs registered

- [ ] **Security Configuration**
  - [ ] Encryption keys generated and stored in OpenBao
  - [ ] Password requirements meet policy
  - [ ] Session timeouts appropriate for use case
  - [ ] IP tracking enabled/disabled per requirements
  - [ ] MFA enforcement configured per user role

- [ ] **Modularity Validation**
  - [ ] All features can be toggled on/off
  - [ ] Default configuration works without customization
  - [ ] Configuration documented in project README
  - [ ] No hardcoded values in implementation
  - [ ] Provider abstractions allow swapping services

**SUCCESS CRITERIA:** The authentication module can be installed and configured in any Django/Next.js/React Native project with ZERO source code modifications, only configuration changes.

---
