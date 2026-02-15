# FFI Security Considerations

## Overview

This document describes security considerations when using Rust encryption functions from Python via PyO3 Foreign Function Interface (FFI). Understanding these limitations is critical for implementing secure systems.

## Table of Contents

- [Memory Security Limitations](#memory-security-limitations)
- [Zeroization Strategy](#zeroization-strategy)
- [Secure Python Patterns](#secure-python-patterns)
- [High-Security Operations](#high-security-operations)
- [Common Pitfalls](#common-pitfalls)
- [Best Practices Checklist](#best-practices-checklist)

---

## Memory Security Limitations

### The FFI Boundary Problem

**CRITICAL:** Rust cannot zeroize Python's heap memory. When data crosses the FFI boundary from Rust to Python, Rust loses control over that memory.

```
┌─────────────────────────────────────────────────────────┐
│                  FFI Boundary                           │
├─────────────────────┬───────────────────────────────────┤
│   Rust Side         │   Python Side                     │
├─────────────────────┼───────────────────────────────────┤
│ ✅ Can zeroize      │ ❌ Rust cannot zeroize            │
│ ✅ Memory control   │ ❌ Python GC controls memory      │
│ ✅ Explicit drop    │ ❌ Non-deterministic cleanup      │
└─────────────────────┴───────────────────────────────────┘
```

### What Rust DOES Zeroize

Rust zeroizes:

- ✅ Owned data within Rust functions (before returning)
- ✅ Intermediate buffers used during encryption/decryption
- ✅ Keys loaded from environment or passed as byte arrays
- ✅ Plaintext bytes after conversion to string (inside Rust)

### What Rust CANNOT Zeroize

Rust cannot zeroize:

- ❌ Python strings returned from Rust functions
- ❌ Python bytes objects containing decrypted data
- ❌ Python variables holding sensitive data
- ❌ Data copied by Python's memory management

**Example of the Problem:**

```python
# ❌ INSECURE: Decrypted value lingers in Python memory
from syntek_rust import decrypt_field

ciphertext = get_encrypted_password()
key = get_encryption_key()

# Rust decrypts, zeroizes its copy, returns Python string
password = decrypt_field(ciphertext, key)  # ❌ Python string not zeroized

# Use password
authenticate(password)

# Even if you delete it, Python may not immediately free memory
del password  # ❌ Memory may linger until GC runs

# The decrypted password may remain in memory for an indefinite time
# and could be exposed in memory dumps, swap files, or core dumps
```

---

## Zeroization Strategy

### Rust Responsibilities

**Rust Side (Inside `syntek-encryption`):**

1. **Zeroize intermediate buffers:**

   ```rust
   pub fn decrypt_field(ciphertext: &[u8], key: &[u8]) -> Result<String> {
       // Decrypt into byte vector
       let mut plaintext_bytes = cipher.decrypt(nonce, encrypted_data)?;

       // Convert to String
       let result = String::from_utf8(plaintext_bytes.clone())?;

       // ✅ RUST ZEROIZES: Clear the byte vector before dropping
       plaintext_bytes.zeroize();

       Ok(result)  // ❌ PYTHON OWNS: Rust cannot zeroize this String
   }
   ```

2. **Use `SecretString` for sensitive return values:**

   ```rust
   pub fn decrypt_field_secure(ciphertext: &[u8], key: &[u8]) -> Result<SecretString> {
       let mut plaintext_bytes = cipher.decrypt(nonce, encrypted_data)?;
       let plaintext = String::from_utf8(plaintext_bytes.clone())?;

       // ✅ Zeroize intermediate bytes
       plaintext_bytes.zeroize();

       // ✅ SecretString will zeroize when dropped (in Rust)
       Ok(SecretString::new(plaintext.into_boxed_str()))
   }
   ```

### Python Responsibilities

**Python Side (Application Code):**

Python must implement its own secure memory handling:

1. **Use `SecureString` or similar libraries:**

   ```python
   # ✅ SECURE: Use secure string library
   from secure_string import SecureString

   # Decrypt into SecureString
   password = SecureString(decrypt_field(ciphertext, key))

   # Use password (via .expose() or similar)
   authenticate(password.expose())

   # Explicit cleanup
   password.zero()  # ✅ Zeroizes Python memory
   del password
   ```

2. **Minimize sensitive data lifetime:**

   ```python
   # ✅ BETTER: Use context manager for automatic cleanup
   with SecureString(decrypt_field(ciphertext, key)) as password:
       authenticate(password.expose())
   # ✅ Automatically zeroized when exiting context
   ```

3. **Avoid string operations that copy data:**

   ```python
   # ❌ INSECURE: String operations create copies
   password = decrypt_field(ciphertext, key)
   password_upper = password.upper()  # Creates copy
   password_stripped = password.strip()  # Creates copy
   # Now you have 3 copies in memory!

   # ✅ SECURE: Minimize copies
   password = decrypt_field(ciphertext, key)
   # Use directly without creating copies
   authenticate(password)
   # Explicit cleanup
   del password
   ```

---

## Secure Python Patterns

### Pattern 1: Use Secure String Libraries

**Recommended Libraries:**

- **`secure_string`** - Provides SecureString with zeroization
- **`memset_zero`** - Overwrites memory with zeros
- **`ctypes`** - Access raw memory for manual zeroization

**Example with `secure_string`:**

```python
from secure_string import SecureString
from syntek_rust import decrypt_field

def login(email_encrypted: bytes, password_encrypted: bytes, key: bytes) -> bool:
    """Authenticate user with encrypted credentials."""

    # Decrypt email (less sensitive, can use regular string)
    email = decrypt_field(email_encrypted, key)

    # Decrypt password into SecureString
    password = SecureString(decrypt_field(password_encrypted, key))

    try:
        # Authenticate (expose password only for authentication)
        result = authenticate(email, password.expose())
        return result
    finally:
        # ✅ CRITICAL: Zeroize password before returning
        password.zero()
        del password
```

### Pattern 2: Context Managers for Automatic Cleanup

```python
from contextlib import contextmanager
from secure_string import SecureString
from syntek_rust import decrypt_field

@contextmanager
def decrypt_secure(ciphertext: bytes, key: bytes):
    """Context manager for secure decryption."""
    secure_value = SecureString(decrypt_field(ciphertext, key))
    try:
        yield secure_value
    finally:
        secure_value.zero()
        del secure_value

# Usage
with decrypt_secure(encrypted_password, key) as password:
    authenticate(user, password.expose())
# ✅ Automatically zeroized when exiting context
```

### Pattern 3: Manual Memory Zeroization with ctypes

```python
import ctypes
from syntek_rust import decrypt_field

def secure_decrypt(ciphertext: bytes, key: bytes) -> str:
    """Decrypt with manual memory zeroization."""
    plaintext = decrypt_field(ciphertext, key)

    try:
        # Use the plaintext
        result = process(plaintext)
        return result
    finally:
        # ✅ Manually zeroize Python string
        # Get string buffer address
        buffer = (ctypes.c_char * len(plaintext)).from_buffer_copy(
            plaintext.encode('utf-8')
        )
        # Overwrite with zeros
        ctypes.memset(ctypes.addressof(buffer), 0, len(plaintext))
        del plaintext
```

---

## High-Security Operations

### Using `decrypt_field_secure()` (Rust SecretString)

For highly sensitive data (passwords, API keys, encryption keys), use `decrypt_field_secure()`:

**Rust Function:**

```rust
/// Decrypt into SecretString (maximum security)
pub fn decrypt_field_secure(ciphertext: &[u8], key: &[u8]) -> Result<SecretString>
```

**Python Usage:**

```python
from syntek_rust import decrypt_field_secure

# Decrypt API key (high security)
# ✅ Returns Rust SecretString (zeroized on Rust side when dropped)
api_key_secret = decrypt_field_secure(encrypted_api_key, key)

# ⚠️ WARNING: Exposing SecretString still creates Python string
# Python must handle that string securely
api_key_value = api_key_secret.expose_secret()  # ⚠️ Now in Python memory

# Use immediately and cleanup
try:
    make_api_call(api_key_value)
finally:
    del api_key_value  # Best effort cleanup
```

**Note:** Even with `decrypt_field_secure()`, once data crosses to Python, Python must handle it securely. The Rust `SecretString` provides protection on the Rust side only.

---

## Common Pitfalls

### Pitfall 1: Relying on `del` for Security

```python
# ❌ INSECURE: `del` doesn't guarantee memory is cleared
password = decrypt_field(ciphertext, key)
authenticate(password)
del password  # ❌ Python may not immediately free memory

# ✅ SECURE: Explicit zeroization before del
password = SecureString(decrypt_field(ciphertext, key))
authenticate(password.expose())
password.zero()  # ✅ Explicitly clear memory
del password
```

### Pitfall 2: String Concatenation Creates Copies

```python
# ❌ INSECURE: Each operation creates a copy in memory
password = decrypt_field(ciphertext, key)
message = "Password is: " + password  # Copy 1
log_message = message + " (authenticated)"  # Copy 2
# Now there are 3+ copies of the password in memory!

# ✅ SECURE: Minimize operations on sensitive data
password = decrypt_field(ciphertext, key)
# Use directly without concatenation
authenticate(password)
del password
```

### Pitfall 3: Passing Sensitive Data to Logging

```python
# ❌ CRITICAL VULNERABILITY: Password leaked to logs
password = decrypt_field(ciphertext, key)
logger.info(f"User logged in with password: {password}")  # ❌ NEVER DO THIS

# ✅ SECURE: Never log sensitive data
password = decrypt_field(ciphertext, key)
authenticate(password)
logger.info("User logged in successfully")  # ✅ No sensitive data
del password
```

### Pitfall 4: Storing Decrypted Data Long-Term

```python
# ❌ INSECURE: Storing decrypted data in class attributes
class User:
    def __init__(self, encrypted_api_key: bytes, key: bytes):
        self.api_key = decrypt_field(encrypted_api_key, key)  # ❌ Stays in memory

    def make_request(self):
        api_call(self.api_key)  # Exposed for entire object lifetime

# ✅ SECURE: Decrypt on-demand, cleanup immediately
class User:
    def __init__(self, encrypted_api_key: bytes, key: bytes):
        self.encrypted_api_key = encrypted_api_key
        self.key = key

    def make_request(self):
        api_key = decrypt_field(self.encrypted_api_key, self.key)
        try:
            api_call(api_key)
        finally:
            del api_key  # ✅ Cleanup after use
```

### Pitfall 5: Exception Handling Without Cleanup

```python
# ❌ INSECURE: Exception leaves password in memory
password = decrypt_field(ciphertext, key)
authenticate(password)  # If this raises, password leaks
del password  # Never reached if exception occurs

# ✅ SECURE: Use try/finally for guaranteed cleanup
password = decrypt_field(ciphertext, key)
try:
    authenticate(password)
finally:
    del password  # ✅ Always executed, even on exception
```

---

## Best Practices Checklist

### Application-Level Security

- [ ] **Use secure string libraries** (`secure_string`, `memset_zero`)
- [ ] **Implement context managers** for automatic cleanup
- [ ] **Minimize sensitive data lifetime** - decrypt on-demand, cleanup immediately
- [ ] **Use try/finally blocks** to guarantee cleanup even on exceptions
- [ ] **Never log sensitive data** (passwords, API keys, tokens)
- [ ] **Avoid string operations** that create copies (concatenation, formatting, slicing)
- [ ] **Don't store decrypted data** in long-lived objects or global variables
- [ ] **Implement zeroization** before deleting sensitive variables

### Code Review Checklist

When reviewing code that uses decryption:

1. ✅ **Is sensitive data cleaned up in all code paths?** (including exceptions)
2. ✅ **Is cleanup guaranteed by try/finally or context managers?**
3. ✅ **Are string operations minimized on sensitive data?**
4. ✅ **Is logging free of sensitive data?**
5. ✅ **Is sensitive data stored only as long as necessary?**
6. ✅ **Are error messages sanitized** (no sensitive data in exceptions)?

### System-Level Security

- [ ] **Disable swap for sensitive processes** (prevents sensitive data in swap files)
- [ ] **Disable core dumps** (prevents sensitive data in crash dumps)
- [ ] **Use memory encryption** (e.g., Intel SGX) for maximum protection
- [ ] **Implement memory forensics protection** (overwrite freed memory)
- [ ] **Use encrypted RAM** on systems handling highly sensitive data

---

## Security Levels

### Level 1: Basic Security (Most Applications)

**Suitable for:** Web applications, APIs, general authentication

```python
# Decrypt, use immediately, cleanup
from syntek_rust import decrypt_field

password = decrypt_field(ciphertext, key)
try:
    authenticate(password)
finally:
    del password
```

**Limitations:**

- ⚠️ Python string remains in memory until GC
- ⚠️ Vulnerable to memory dumps if process crashes
- ⚠️ Vulnerable to swap file exposure

### Level 2: Enhanced Security (Sensitive Applications)

**Suitable for:** Financial systems, healthcare, PII processing

```python
# Use secure string library with explicit zeroization
from secure_string import SecureString
from syntek_rust import decrypt_field

password = SecureString(decrypt_field(ciphertext, key))
try:
    authenticate(password.expose())
finally:
    password.zero()  # Explicit zeroization
    del password
```

**Improvements:**

- ✅ Memory explicitly zeroed before deallocation
- ✅ Reduced window of vulnerability
- ⚠️ Still vulnerable to core dumps before cleanup

### Level 3: Maximum Security (Critical Systems)

**Suitable for:** Cryptographic keys, national security, critical infrastructure

```python
# Use secure string + memory forensics protection
from secure_string import SecureString
from syntek_rust import decrypt_field_secure
import os

# Disable core dumps for this process
import resource
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

# Use SecretString on Rust side + SecureString on Python side
secret = decrypt_field_secure(ciphertext, key)
password = SecureString(secret.expose_secret())
try:
    authenticate(password.expose())
finally:
    password.zero()
    del password
    del secret
```

**Maximum Protection:**

- ✅ Rust SecretString zeroizes on Rust side
- ✅ Python SecureString zeroizes on Python side
- ✅ Core dumps disabled
- ✅ Minimal exposure window

---

## Summary

### Key Takeaways

1. **FFI Boundary Limitation:** Rust cannot zeroize Python memory
2. **Shared Responsibility:** Both Rust (intermediate buffers) and Python (returned values) must implement zeroization
3. **Use Secure Libraries:** `secure_string`, `memset_zero` for Python-side protection
4. **Minimize Lifetime:** Decrypt on-demand, cleanup immediately
5. **Defense in Depth:** Combine multiple techniques for maximum security

### The Security Contract

```
┌─────────────────────────────────────────────────────────┐
│             Rust Guarantees                             │
├─────────────────────────────────────────────────────────┤
│ ✅ Intermediate buffers zeroized                        │
│ ✅ Keys zeroized after use                              │
│ ✅ Plaintext bytes zeroized before return               │
│ ✅ SecretString zeroized when dropped (Rust side)       │
└─────────────────────────────────────────────────────────┘
                            ↓
                    FFI Boundary
                            ↓
┌─────────────────────────────────────────────────────────┐
│          Python Responsibilities                        │
├─────────────────────────────────────────────────────────┤
│ ⚠️ Returned strings/bytes NOT automatically zeroized    │
│ ✅ Use SecureString or similar for sensitive data       │
│ ✅ Implement context managers for automatic cleanup     │
│ ✅ Minimize sensitive data lifetime                     │
│ ✅ Use try/finally for guaranteed cleanup               │
└─────────────────────────────────────────────────────────┘
```

### When in Doubt

**Default to paranoia:** If data is sensitive enough to encrypt, it's sensitive enough to handle carefully when decrypted. Always prefer explicit zeroization, minimal lifetime, and secure libraries.

---

## Further Reading

- [OWASP Memory Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Memory_Management_Cheat_Sheet.html)
- [Python `secure_string` Library](https://github.com/dnet/secure-string)
- [Rust `secrecy` Crate Documentation](https://docs.rs/secrecy/)
- [PyO3 Security Considerations](https://pyo3.rs/latest/safety.html)
