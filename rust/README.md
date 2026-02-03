# Syntek Rust Security Modules

This directory contains security-critical Rust crates for the Syntek ecosystem.

## Modules

### `encryption/` - Encryption and Decryption
PyO3-based encryption/decryption module for Django integration. Handles:
- Field-level encryption (individual fields like IP addresses)
- Batch encryption (multiple fields together)
- Authenticated encryption using ChaCha20-Poly1305
- Password hashing with Argon2
- Automatic zeroization of sensitive data

### `security/` - Security Primitives
Core security utilities including:
- Zeroize integration
- Secure memory handling
- Secret type wrappers
- Security best practices

## Development

### Prerequisites

- Rust 1.92.0 or later
- Python 3.14+ (for PyO3 bindings)

### Building

```bash
# Build all modules
cargo build --workspace

# Build with release optimizations
cargo build --workspace --release

# Run tests
cargo test --workspace

# Run clippy
cargo clippy --workspace -- -D warnings
```

### Security Checks

```bash
# Install cargo-audit
cargo install cargo-audit

# Check for vulnerabilities
cargo audit

# Install cargo-geiger (detect unsafe code)
cargo install cargo-geiger

# Check unsafe code usage
cargo geiger
```

## Integration with Django

The `encryption` module builds as a Python extension module:

```bash
cd encryption
pip install maturin
maturin develop  # Development build
maturin build --release  # Production build
```

## Security Guidelines

See `.claude/SYNTEK-RUST-SECURITY-GUIDE.md` for comprehensive security guidelines including:

- Memory safety patterns
- Cryptographic best practices
- Unsafe code guidelines
- Dependency security
- Testing strategies

## Key Security Principles

1. **Memory Safety First**: Prefer safe Rust, minimize unsafe code
2. **Zeroize Sensitive Data**: Always use `zeroize` for secrets
3. **Use Established Crypto**: ring, RustCrypto, not custom implementations
4. **Validate All Inputs**: Especially at FFI boundaries
5. **No Debug/Display for Secrets**: Prevent accidental logging
6. **Constant-Time Comparisons**: For all secret comparisons
7. **Overflow Checks Enabled**: Even in release builds
8. **Regular Audits**: Use `cargo audit` and `cargo geiger`

## Testing

```bash
# Unit tests
cargo test

# Property-based tests (if using proptest)
cargo test --features proptest

# Fuzzing (requires nightly)
cargo +nightly fuzz run <target>
```

## Benchmarking

```bash
cargo bench
```

## Documentation

```bash
cargo doc --open --workspace --no-deps
```

## License

MIT OR Apache-2.0
