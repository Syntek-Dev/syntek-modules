# Syntek Encryption Module

PyO3-based encryption/decryption module for Django integration with field-level and batch encryption support.

## Features

- **Authenticated Encryption**: ChaCha20-Poly1305 (AEAD)
- **Password Hashing**: Argon2id
- **Field-Level Encryption**: Encrypt individual database fields
- **Batch Encryption**: Encrypt multiple fields together for efficiency
- **Memory Safety**: Automatic zeroization of plaintext data
- **Python Integration**: Seamless Django integration via PyO3

## Installation

### As Python Package

```bash
pip install maturin
cd rust/encryption
maturin develop  # Development
maturin build --release  # Production
```

### As Rust Dependency

```toml
[dependencies]
syntek-encryption = { path = "../path/to/rust/encryption" }
```

## Usage

### From Python/Django

```python
import syntek_encryption as enc

# Initialize encryptor with key
key = b"32-byte-key-here" * 32
encryptor = enc.Encryptor(key)

# Encrypt single field
plaintext = b"192.168.1.1"
ciphertext = encryptor.encrypt_field(plaintext)

# Decrypt single field
decrypted = encryptor.decrypt_field(ciphertext)
assert decrypted == plaintext

# Batch encrypt multiple fields
fields = [b"John", b"Doe", b"john@example.com", b"+1234567890"]
batch_ciphertext = encryptor.encrypt_batch(fields)

# Batch decrypt
decrypted_fields = encryptor.decrypt_batch(batch_ciphertext)
assert decrypted_fields == fields

# Password hashing
password = b"user-password"
password_hash = enc.hash_password(password)

# Password verification
is_valid = enc.verify_password(password, password_hash)
assert is_valid
```

### From Rust

```rust
use syntek_encryption::{Encryptor, hash_password, verify_password};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let key = [0u8; 32];
    let encryptor = Encryptor::new(&key);

    // Encrypt data
    let plaintext = b"sensitive data";
    let ciphertext = encryptor.encrypt(plaintext)?;

    // Decrypt data
    let decrypted = encryptor.decrypt(&ciphertext)?;
    assert_eq!(&*decrypted, plaintext);

    // Password hashing
    let password = b"user-password";
    let hash = hash_password(password)?;
    assert!(verify_password(password, &hash)?);

    Ok(())
}
```

## Django Integration

### Settings Configuration

```python
# settings/base.py
SYNTEK_ENCRYPTION = {
    'KEY_PATH': env('ENCRYPTION_KEY_PATH'),  # Path to 32-byte key file
    'KEY_ROTATION_ENABLED': True,
    'ZEROIZE_ON_DELETE': True,  # Zeroize memory on object deletion
}
```

### Model Usage

```python
from django.db import models
from syntek_encryption.fields import EncryptedCharField, EncryptedTextField

class User(models.Model):
    # Encrypted fields
    ip_address = EncryptedCharField(max_length=45)
    email = EncryptedCharField(max_length=255)
    phone = EncryptedCharField(max_length=20)
    notes = EncryptedTextField()

    # Regular fields
    username = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
```

### GraphQL Layer Encryption

```python
import strawberry
from syntek_encryption import get_encryptor

@strawberry.type
class UserType:
    id: int
    username: str

    @strawberry.field
    def email(self) -> str:
        # Decrypt on read
        encryptor = get_encryptor()
        return encryptor.decrypt_field(self._email).decode('utf-8')

@strawberry.mutation
def create_user(username: str, email: str) -> UserType:
    # Encrypt on write
    encryptor = get_encryptor()
    encrypted_email = encryptor.encrypt_field(email.encode('utf-8'))

    user = User.objects.create(
        username=username,
        _email=encrypted_email
    )
    return UserType.from_model(user)
```

## Configuration Options

| Setting                | Type | Default    | Description                    |
| ---------------------- | ---- | ---------- | ------------------------------ |
| `KEY_PATH`             | str  | Required   | Path to 32-byte encryption key |
| `KEY_ROTATION_ENABLED` | bool | `False`    | Enable key rotation support    |
| `ZEROIZE_ON_DELETE`    | bool | `True`     | Zeroize memory on deletion     |
| `MAX_FIELD_SIZE`       | int  | `10485760` | Max field size (10MB)          |
| `BATCH_SIZE_LIMIT`     | int  | `100`      | Max fields in batch operation  |

## Security Considerations

### Key Management

**Never commit encryption keys to version control:**

```bash
# Generate new key
python -c "import os; print(os.urandom(32).hex())" > encryption.key
chmod 600 encryption.key

# Add to .gitignore
echo "*.key" >> .gitignore
```

**Use environment variables or secret management:**

```python
# settings/production.py
import os
from pathlib import Path

SYNTEK_ENCRYPTION = {
    'KEY_PATH': os.getenv('ENCRYPTION_KEY_PATH', '/run/secrets/encryption_key'),
}
```

### Memory Safety

All plaintext data is automatically zeroized after use:

```python
# Plaintext is zeroized immediately after encryption
ciphertext = encryptor.encrypt_field(plaintext)
# plaintext memory is now zeroed in Rust

# Decrypted data is zeroized when variable goes out of scope
decrypted = encryptor.decrypt_field(ciphertext)
# Use decrypted data
# Memory is automatically zeroized when decrypted is garbage collected
```

### Performance Considerations

**Use batch operations for multiple fields:**

```python
# Bad - multiple individual encryptions
encrypted_fields = [
    encryptor.encrypt_field(f.encode()) for f in fields
]

# Good - single batch operation
encrypted_batch = encryptor.encrypt_batch(
    [f.encode() for f in fields]
)
```

## Testing

```bash
# Rust tests
cargo test

# Python tests
cd python-tests
pytest test_encryption.py

# Property-based tests
cargo test --features proptest
```

## Benchmarks

```bash
cargo bench
```

Example results:

- Single field encryption: ~10 μs
- Batch encryption (10 fields): ~50 μs
- Password hashing: ~100 ms (intentionally slow)

## Error Handling

```python
from syntek_encryption import EncryptionError

try:
    decrypted = encryptor.decrypt_field(invalid_ciphertext)
except EncryptionError as e:
    print(f"Decryption failed: {e}")
```

## Compliance

This module helps meet:

**GDPR:**

- **Article 32**: Security of processing (encryption at rest)
- **Article 17**: Right to erasure (zeroization)
- **Article 5(1)(f)**: Integrity and confidentiality

**NIST:**

- **NIST 800-53 SC-28**: Protection of information at rest
- **NIST 800-63B**: Cryptographic key management
- **NIST 800-175B**: Guideline for using cryptographic standards

**OWASP:**

- **OWASP A02:2021**: Cryptographic Failures prevention
- **OWASP ASVS V6**: Stored Cryptography Verification

**CIS Benchmarks:**

- **CIS Control 3.11**: Encrypt sensitive data at rest
- **CIS Control 3.10**: Encrypt sensitive data in transit

**SOC 2:**

- **CC6.1**: Logical and physical access controls
- **CC6.7**: Information asset protection through encryption

**Additional:**

- **PCI DSS Requirement 3**: Protect stored cardholder data
- **NCSC Guidance**: Cryptography for secure communications

## Dependencies

- `ring` - Cryptographic primitives
- `chacha20poly1305` - Authenticated encryption
- `argon2` - Password hashing
- `zeroize` - Secure memory clearing
- `pyo3` - Python bindings

## License

MIT OR Apache-2.0
