# Syntek Security Module

Core security utilities and primitives for safe handling of sensitive data in Rust.

## Features

- **Zeroize Integration**: Automatic secure memory clearing
- **Secret Types**: Wrapper types for sensitive data
- **Memory Safety**: Utilities for secure memory handling
- **Security Auditing**: Tools for code analysis

## Installation

### As Rust Dependency

```toml
[dependencies]
syntek-security = { path = "../path/to/rust/security" }
```

## Usage

### Secret Wrapper Types

```rust
use syntek_security::Secret;
use zeroize::Zeroize;

// Create a secret value
let password = Secret::new("user-password".to_string());

// Access the secret (via closure to ensure zeroization)
password.expose_secret(|secret_value| {
    // Use secret_value here
    println!("Password length: {}", secret_value.len());
});

// Secret is automatically zeroized when dropped
drop(password);
```

### Secure Memory Handling

```rust
use syntek_security::{SecureVec, SecureString};

// SecureVec automatically zeroizes on drop
let mut secure_data = SecureVec::new(vec![1, 2, 3, 4]);
secure_data.push(5);

// SecureString for text data
let secure_text = SecureString::from("sensitive info");

// Both are automatically zeroized when dropped
```

### Constant-Time Comparison

```rust
use syntek_security::constant_time_compare;

let token1 = b"secret-token-123";
let token2 = b"secret-token-123";

// Constant-time comparison (prevents timing attacks)
if constant_time_compare(token1, token2) {
    println!("Tokens match");
}
```

### Security Auditing

```rust
use syntek_security::audit;

// Log security-relevant events
audit::log_access("user_123", "resource_456");
audit::log_authentication_attempt("user_123", true);
audit::log_sensitive_operation("decrypt_field", "user_123");
```

## API Reference

### `Secret<T>`

Wrapper type for sensitive data that ensures:
- No accidental logging (no Debug/Display implementation)
- Explicit access via closure
- Automatic zeroization on drop

```rust
impl<T> Secret<T>
where
    T: Zeroize,
{
    pub fn new(value: T) -> Self;
    pub fn expose_secret<F, R>(&self, f: F) -> R
    where
        F: FnOnce(&T) -> R;
}
```

### `SecureVec<T>`

Vector that automatically zeroizes its contents on drop:

```rust
impl<T> SecureVec<T>
where
    T: Zeroize,
{
    pub fn new(vec: Vec<T>) -> Self;
    pub fn push(&mut self, value: T);
    pub fn pop(&mut self) -> Option<T>;
    pub fn as_slice(&self) -> &[T];
}
```

### `SecureString`

String that automatically zeroizes on drop:

```rust
impl SecureString {
    pub fn from(s: &str) -> Self;
    pub fn as_str(&self) -> &str;
    pub fn into_string(self) -> String;
}
```

### `constant_time_compare`

Compare byte slices in constant time:

```rust
pub fn constant_time_compare(a: &[u8], b: &[u8]) -> bool
```

## Examples

### API Token Storage

```rust
use syntek_security::{Secret, SecureString};

struct ApiClient {
    token: Secret<SecureString>,
}

impl ApiClient {
    pub fn new(token: String) -> Self {
        Self {
            token: Secret::new(SecureString::from(&token)),
        }
    }

    pub fn make_request(&self, url: &str) -> Result<Response, Error> {
        self.token.expose_secret(|token| {
            // Use token here
            let auth_header = format!("Bearer {}", token.as_str());
            // Make HTTP request with auth_header
        })
    }
}

// Token is automatically zeroized when ApiClient is dropped
```

### Session Key Management

```rust
use syntek_security::SecureVec;

struct Session {
    session_key: SecureVec<u8>,
}

impl Session {
    pub fn new() -> Self {
        let key = generate_random_key();
        Self {
            session_key: SecureVec::new(key),
        }
    }

    pub fn encrypt(&self, data: &[u8]) -> Vec<u8> {
        // Use session_key for encryption
        let key_slice = self.session_key.as_slice();
        encrypt_data(data, key_slice)
    }
}

// session_key is automatically zeroized when Session is dropped
```

### Secure Password Comparison

```rust
use syntek_security::constant_time_compare;

fn verify_password(provided: &[u8], stored_hash: &[u8]) -> bool {
    let computed_hash = hash_password(provided);
    constant_time_compare(&computed_hash, stored_hash)
}
```

## Configuration Options

| Feature Flag | Description |
|--------------|-------------|
| `audit-logging` | Enable security audit logging |
| `paranoid` | Extra security checks (performance impact) |

```toml
[dependencies]
syntek-security = { path = "../syntek-security", features = ["audit-logging"] }
```

## Security Considerations

### Memory Zeroization

All sensitive data types automatically zeroize memory:

```rust
{
    let password = Secret::new("sensitive".to_string());
    // Use password
} // Memory containing "sensitive" is now zeroed
```

### No Debug Output

Secret types cannot be debug-printed:

```rust
let secret = Secret::new("sensitive");
// println!("{:?}", secret); // Compile error!
```

### Explicit Access

Access to secret values requires explicit exposure:

```rust
let secret = Secret::new("value");

// Wrong - no direct access
// let value = secret.value; // Doesn't exist

// Right - explicit exposure
secret.expose_secret(|value| {
    // Use value here
});
```

## Testing

```bash
# Run tests
cargo test

# Run with security features
cargo test --all-features

# Check for memory leaks
valgrind --leak-check=full cargo test
```

## Performance

Zeroization has minimal performance impact:
- SecureVec operations: ~1% overhead vs Vec
- Zeroization on drop: ~100ns for typical data sizes

## Dependencies

- `zeroize` - Secure memory clearing
- `secrecy` - Secret type wrappers
- `subtle` - Constant-time operations

## Best Practices

1. **Use Secret<T> for all sensitive data**
   ```rust
   // Bad
   let api_key: String = "...";

   // Good
   let api_key: Secret<String> = Secret::new("...".to_string());
   ```

2. **Minimize exposure scope**
   ```rust
   secret.expose_secret(|value| {
       // Use value only within this closure
       process(value)
   }); // value is no longer accessible
   ```

3. **Use constant-time comparisons for secrets**
   ```rust
   // Bad - timing leak
   if token1 == token2 { ... }

   // Good - constant time
   if constant_time_compare(token1, token2) { ... }
   ```

4. **Avoid cloning secrets unnecessarily**
   ```rust
   // Prefer references
   fn process(secret: &Secret<String>) { ... }

   // Instead of cloning
   fn process(secret: Secret<String>) { ... }
   ```

## Compliance

This module helps meet:
- **GDPR Article 32**: Secure processing of personal data
- **GDPR Article 17**: Right to erasure (secure deletion)
- **PCI DSS Requirement 3**: Protect stored cardholder data

## License

MIT OR Apache-2.0
