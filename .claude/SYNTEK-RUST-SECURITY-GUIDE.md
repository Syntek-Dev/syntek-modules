# Syntek Rust Security Guide

This guide provides security guidelines and best practices for developing Rust security modules in the Syntek ecosystem.

## Overview

The `rust/` directory contains security-critical Rust crates that provide:
- **encryption/** - Encryption/decryption with PyO3 bindings for Django
- **security/** - Zeroize, memory safety, and secure primitives

All Rust modules handle sensitive data and must follow strict security guidelines.

## Compliance Requirements

**All Rust code must comply with:**
- **OWASP ASVS** - Application Security Verification Standard
- **NIST 800-53** - Security and Privacy Controls
- **NIST 800-63B** - Digital Identity Guidelines
- **GDPR Article 32** - Security of processing
- **CIS Benchmarks** - Secure coding practices
- **SOC 2** - Security controls and monitoring

**See `.claude/SECURITY-COMPLIANCE.md` for comprehensive compliance requirements.**

---

## Memory Safety

### Safe Rust First
Always prefer safe Rust patterns. Only use `unsafe` when absolutely necessary.

```rust
// Good - Safe Rust
fn process_data(data: &[u8]) -> Vec<u8> {
    data.iter().map(|&b| b ^ 0xFF).collect()
}

// Avoid unless necessary
fn process_data_unsafe(data: &[u8]) -> Vec<u8> {
    unsafe {
        // Only if performance-critical and proven safe
    }
}
```

### Unsafe Code Requirements
When `unsafe` is unavoidable:

1. **Document the safety invariants**
   ```rust
   /// SAFETY: `ptr` must be valid for reads of `len` bytes
   unsafe fn read_bytes(ptr: *const u8, len: usize) -> &[u8] {
       std::slice::from_raw_parts(ptr, len)
   }
   ```

2. **Keep unsafe blocks minimal**
   ```rust
   // Good - minimal unsafe scope
   fn example(data: &[u8]) -> Result<String, Error> {
       let processed = process_safely(data)?;
       let result = unsafe {
           // Only the unsafe operation
           std::str::from_utf8_unchecked(&processed)
       };
       Ok(result.to_string())
   }
   ```

3. **Add safety tests**
   ```rust
   #[test]
   fn test_unsafe_boundary() {
       // Test edge cases
       assert!(unsafe_function(&[]).is_ok());
       assert!(unsafe_function(&[1, 2, 3]).is_ok());
   }
   ```

### Sensitive Data Handling

**Always use `zeroize` for sensitive data:**

```rust
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Zeroize, ZeroizeOnDrop)]
struct EncryptionKey {
    key: [u8; 32],
}

impl EncryptionKey {
    fn from_slice(slice: &[u8]) -> Result<Self, Error> {
        let mut key = [0u8; 32];
        key.copy_from_slice(slice);
        Ok(Self { key })
    }

    // Key is automatically zeroized when dropped
}

// For Vec<u8> and other heap data
fn process_secret(mut secret: Vec<u8>) -> Result<(), Error> {
    // ... use secret ...

    // Explicit zeroize before dropping
    secret.zeroize();
    Ok(())
}
```

**Never log or debug-print sensitive data:**

```rust
use std::fmt;

struct Secret(Vec<u8>);

impl fmt::Debug for Secret {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Secret([REDACTED])")
    }
}
```

---

## Cryptography

### Use Established Libraries

**Prefer:**
- `ring` - Fast, audited cryptographic primitives
- `RustCrypto` - Pure Rust implementations
- `chacha20poly1305` - Authenticated encryption
- `argon2` - Password hashing

**Avoid:**
- Custom crypto implementations
- Outdated algorithms (MD5, SHA1 for security)
- Unauthenticated encryption modes

### Example: Authenticated Encryption

```rust
use chacha20poly1305::{
    aead::{Aead, KeyInit, OsRng},
    ChaCha20Poly1305, Nonce,
};
use zeroize::Zeroizing;

pub struct Encryptor {
    cipher: ChaCha20Poly1305,
}

impl Encryptor {
    pub fn new(key: &[u8; 32]) -> Self {
        let cipher = ChaCha20Poly1305::new(key.into());
        Self { cipher }
    }

    pub fn encrypt(&self, plaintext: &[u8]) -> Result<Vec<u8>, Error> {
        let nonce = ChaCha20Poly1305::generate_nonce(&mut OsRng);
        let ciphertext = self.cipher
            .encrypt(&nonce, plaintext)
            .map_err(|_| Error::EncryptionFailed)?;

        // Prepend nonce to ciphertext
        let mut result = nonce.to_vec();
        result.extend_from_slice(&ciphertext);
        Ok(result)
    }

    pub fn decrypt(&self, data: &[u8]) -> Result<Zeroizing<Vec<u8>>, Error> {
        if data.len() < 12 {
            return Err(Error::InvalidData);
        }

        let (nonce, ciphertext) = data.split_at(12);
        let nonce = Nonce::from_slice(nonce);

        let plaintext = self.cipher
            .decrypt(nonce, ciphertext)
            .map_err(|_| Error::DecryptionFailed)?;

        Ok(Zeroizing::new(plaintext))
    }
}
```

### Password Hashing

```rust
use argon2::{
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};

pub fn hash_password(password: &[u8]) -> Result<String, Error> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();

    let password_hash = argon2
        .hash_password(password, &salt)
        .map_err(|_| Error::HashingFailed)?
        .to_string();

    Ok(password_hash)
}

pub fn verify_password(password: &[u8], hash: &str) -> Result<bool, Error> {
    let parsed_hash = PasswordHash::new(hash)
        .map_err(|_| Error::InvalidHash)?;

    let argon2 = Argon2::default();
    Ok(argon2.verify_password(password, &parsed_hash).is_ok())
}
```

---

## PyO3 FFI Safety

### Input Validation

**Always validate Python inputs:**

```rust
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

#[pyfunction]
fn encrypt_field(py: Python, plaintext: &[u8], key: &[u8]) -> PyResult<Vec<u8>> {
    // Validate inputs before processing
    if key.len() != 32 {
        return Err(PyValueError::new_err("Key must be 32 bytes"));
    }

    if plaintext.is_empty() {
        return Err(PyValueError::new_err("Plaintext cannot be empty"));
    }

    if plaintext.len() > 10_000_000 {
        return Err(PyValueError::new_err("Plaintext too large (max 10MB)"));
    }

    // Safe to process
    encrypt_internal(plaintext, key)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}
```

### Error Handling

**Never expose internal error details to Python:**

```rust
use pyo3::exceptions::{PyRuntimeError, PyValueError};

#[derive(Debug)]
enum InternalError {
    CryptoError(String),
    IoError(std::io::Error),
}

impl std::fmt::Display for InternalError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::CryptoError(_) => write!(f, "Cryptographic operation failed"),
            Self::IoError(_) => write!(f, "I/O operation failed"),
        }
    }
}

impl From<InternalError> for PyErr {
    fn from(err: InternalError) -> PyErr {
        // Generic error message, log details internally
        PyRuntimeError::new_err(err.to_string())
    }
}
```

### Memory Safety with Python

```rust
use pyo3::types::PyBytes;

#[pyfunction]
fn process_sensitive_data<'py>(
    py: Python<'py>,
    data: &[u8],
) -> PyResult<&'py PyBytes> {
    // Process data in Rust
    let mut result = process_internal(data)?;

    // Copy to Python bytes object
    let py_bytes = PyBytes::new(py, &result);

    // Zeroize the Rust copy
    result.zeroize();

    Ok(py_bytes)
}
```

---

## Dependency Security

### RustSec Auditing

**Always run cargo-audit before releases:**

```bash
cargo install cargo-audit
cargo audit
```

Add to CI/CD:

```yaml
# .github/workflows/security.yml
name: Security Audit
on: [push, pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo install cargo-audit
      - run: cargo audit
```

### Dependency Pinning

**Use Cargo.lock in version control:**

```toml
# Cargo.toml
[dependencies]
ring = "0.17"           # Specify minimum version
zeroize = { version = "1.7", features = ["derive"] }

[dev-dependencies]
proptest = "1.4"        # Fuzzing and property testing
```

### Supply Chain Security

```bash
# Verify dependency sources
cargo tree

# Check for known vulnerabilities
cargo audit

# Review dependencies
cargo geiger  # Detects unsafe code in dependencies
```

---

## Testing

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encrypt_decrypt_round_trip() {
        let key = [0u8; 32];
        let encryptor = Encryptor::new(&key);

        let plaintext = b"sensitive data";
        let ciphertext = encryptor.encrypt(plaintext).unwrap();
        let decrypted = encryptor.decrypt(&ciphertext).unwrap();

        assert_eq!(&*decrypted, plaintext);
    }

    #[test]
    fn test_wrong_key_fails() {
        let key1 = [0u8; 32];
        let key2 = [1u8; 32];

        let enc1 = Encryptor::new(&key1);
        let enc2 = Encryptor::new(&key2);

        let ciphertext = enc1.encrypt(b"data").unwrap();
        assert!(enc2.decrypt(&ciphertext).is_err());
    }
}
```

### Property-Based Testing

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_encrypt_decrypt_any_data(data in any::<Vec<u8>>()) {
        let key = [0u8; 32];
        let encryptor = Encryptor::new(&key);

        let ciphertext = encryptor.encrypt(&data)?;
        let decrypted = encryptor.decrypt(&ciphertext)?;

        prop_assert_eq!(&*decrypted, &data);
    }
}
```

### Fuzzing

```rust
// fuzz/fuzz_targets/decrypt.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let key = [0u8; 32];
    let encryptor = Encryptor::new(&key);

    // Should never panic, only return error
    let _ = encryptor.decrypt(data);
});
```

---

## Common Vulnerabilities

### Timing Attacks

**Use constant-time comparisons:**

```rust
use subtle::ConstantTimeEq;

// Bad - timing leak
fn verify_token_insecure(token: &[u8], expected: &[u8]) -> bool {
    token == expected  // Short-circuits on first difference
}

// Good - constant time
fn verify_token_secure(token: &[u8], expected: &[u8]) -> bool {
    if token.len() != expected.len() {
        return false;
    }
    token.ct_eq(expected).into()
}
```

### Integer Overflow

```rust
// Enable overflow checks in release mode
// Cargo.toml:
// [profile.release]
// overflow-checks = true

// Or use checked arithmetic
fn safe_allocation(count: usize, size: usize) -> Result<Vec<u8>, Error> {
    let total_size = count.checked_mul(size)
        .ok_or(Error::IntegerOverflow)?;

    if total_size > MAX_ALLOCATION {
        return Err(Error::AllocationTooLarge);
    }

    Ok(vec![0u8; total_size])
}
```

### Panic Safety

```rust
// Bad - panics expose internal state
fn parse_data(data: &[u8]) -> Vec<u8> {
    let len = data[0] as usize;  // Panics if empty
    data[1..len + 1].to_vec()    // Panics if out of bounds
}

// Good - returns errors
fn parse_data_safe(data: &[u8]) -> Result<Vec<u8>, Error> {
    let len = *data.first().ok_or(Error::EmptyData)? as usize;

    let end = len.checked_add(1).ok_or(Error::InvalidLength)?;
    if end > data.len() {
        return Err(Error::InsufficientData);
    }

    Ok(data[1..end].to_vec())
}
```

---

## Compliance Requirements

### GDPR & Data Protection

```rust
/// GDPR-compliant user data storage
#[derive(Zeroize, ZeroizeOnDrop)]
pub struct PersonalData {
    #[zeroize(skip)]  // Don't zeroize ID
    user_id: i64,

    // Encrypted PII
    encrypted_name: Vec<u8>,
    encrypted_email: Vec<u8>,
    encrypted_phone: Vec<u8>,
}

impl PersonalData {
    /// Encrypt PII before storage (GDPR Art. 32)
    pub fn new(user_id: i64, name: &str, email: &str, phone: &str) -> Result<Self, Error> {
        let encryptor = get_encryptor()?;

        Ok(Self {
            user_id,
            encrypted_name: encryptor.encrypt(name.as_bytes())?,
            encrypted_email: encryptor.encrypt(email.as_bytes())?,
            encrypted_phone: encryptor.encrypt(phone.as_bytes())?,
        })
    }

    /// Right to erasure (GDPR Art. 17)
    pub fn erase(&mut self) {
        self.encrypted_name.zeroize();
        self.encrypted_email.zeroize();
        self.encrypted_phone.zeroize();
    }
}
```

### Audit Logging

```rust
use tracing::{info, warn};

pub fn log_security_event(event: SecurityEvent) {
    match event {
        SecurityEvent::LoginSuccess { user_id, ip } => {
            info!(
                user_id = user_id,
                ip = %ip,
                "User login successful"
            );
        }
        SecurityEvent::LoginFailure { username, ip, reason } => {
            warn!(
                username = username,
                ip = %ip,
                reason = reason,
                "Login attempt failed"
            );
        }
        SecurityEvent::DataAccess { user_id, resource } => {
            info!(
                user_id = user_id,
                resource = resource,
                "User accessed protected resource"
            );
        }
    }
}
```

---

## Code Review Checklist

Before committing Rust security code, verify:

### Memory Safety
- [ ] No unnecessary `unsafe` blocks
- [ ] All `unsafe` blocks have SAFETY comments
- [ ] Sensitive data uses `Zeroize` / `ZeroizeOnDrop`
- [ ] No `Debug` impl for sensitive types
- [ ] No panics in production code paths

### Cryptography
- [ ] Using established libraries (ring, RustCrypto)
- [ ] Authenticated encryption (not raw encryption)
- [ ] Proper key derivation (not raw passwords as keys)
- [ ] Constant-time comparisons for secrets
- [ ] Random nonces/IVs generated securely

### FFI/PyO3
- [ ] Input validation on all Python inputs
- [ ] Size limits on heap allocations
- [ ] Generic error messages (no internal details)
- [ ] Memory properly zeroized before return

### Dependencies
- [ ] `cargo audit` passes
- [ ] No known vulnerable versions
- [ ] Minimal dependency tree
- [ ] Dependencies actively maintained

### Testing
- [ ] Unit tests for all public functions
- [ ] Negative tests (wrong keys, invalid input)
- [ ] Fuzzing for parsing/decryption
- [ ] Property tests where applicable

---

## Security Commands

Use these commands for security analysis:

```bash
# Vulnerability scanning
/vuln-scan

# Cryptographic review
/crypto-review

# Memory safety audit
/memory-audit

# Threat modeling
/threat-model

# Set up fuzzing
/fuzz-setup

# Generate compliance report
/compliance-report
```

---

## Resources

- [Rust Security Working Group](https://github.com/rust-secure-code/wg)
- [RustSec Advisory Database](https://rustsec.org/)
- [Rust Crypto Book](https://cryptography.rs/)
- [PyO3 User Guide](https://pyo3.rs/)
- [Zeroize Documentation](https://docs.rs/zeroize/)
- [Ring Documentation](https://briansmith.org/rustdoc/ring/)

---

## Getting Help

For security concerns:
1. Check this guide first
2. Review module-specific READMEs
3. Consult the Rust security agents:
   - `/crypto-review` for cryptographic questions
   - `/memory-audit` for memory safety
   - `/threat-model` for threat analysis
