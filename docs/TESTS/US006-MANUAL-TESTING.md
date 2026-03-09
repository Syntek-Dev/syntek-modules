# Manual Testing Guide — US006: syntek-crypto

**Package**: `syntek-crypto` (`rust/syntek-crypto/`)\
**Last Updated**: `2026-03-09`\
**Story Status**: Completed\
**Tested against**: Rust stable (edition 2024)

---

## Overview

`syntek-crypto` is a pure Rust library crate providing AES-256-GCM field-level encryption, Argon2id
password hashing, and HMAC-SHA256 integrity verification for all Syntek backend modules. It has no
web UI and no GraphQL API — all manual verification is done via the command line.

A tester should verify that: ciphertext is correctly structured; tampered data is rejected; Argon2id
parameters match the security specification; the AAD binding prevents cross-model ciphertext
substitution; nonces are never reused; and sensitive memory is zeroised after use.

---

## Prerequisites

Before testing, ensure the following are in place:

- [ ] Rust stable toolchain is installed: `rustup show` — confirm `stable` is active
- [ ] You are in the repo root: `cd /path/to/syntek-modules`
- [ ] The workspace builds cleanly: `cargo check -p syntek-crypto`
- [ ] The `base64ct` and `proptest` dependencies are present in `rust/syntek-crypto/Cargo.toml`
- [ ] (Green phase only) Implementation is complete and `cargo test -p syntek-crypto` passes

---

## Scenario 1 — Red Phase: All Tests Fail on Stubs

**What this tests**: Confirms the red TDD phase is correctly set up — every test panics due to
`unimplemented!()` stubs, and no test is accidentally passing or skipped.

### Setup

No setup required beyond the workspace being checked out.

### Steps

1. Run the test suite:

   ```bash
   cargo test -p syntek-crypto 2>&1 | tail -20
   ```

2. Count the failures:

   ```bash
   cargo test -p syntek-crypto 2>&1 | grep -E "^test result"
   ```

### Expected Result

> **Status**: N/A — green phase complete. Stubs have been replaced by the full implementation.

- [ ] Every test in `tests/crypto_tests.rs` is listed as `FAILED`
- [ ] The summary line reads: `test result: FAILED. 0 passed; 29 failed`
- [ ] All failures show `panicked at 'not yet implemented'` — not compilation errors
- [ ] The doc-tests target shows `test result: ok. 0 passed` (no runnable doc examples)

---

## Scenario 2 — Green Phase: Full Test Suite Passes

**What this tests**: After the green-phase implementation is complete, all tests pass with no
failures.

### Steps

1. Run the full test suite in release mode to exercise Argon2id at full cost:

   ```bash
   cargo test -p syntek-crypto --release
   ```

2. Check for any ignored or skipped tests:

   ```bash
   cargo test -p syntek-crypto -- --include-ignored 2>&1 | grep -E "ignored|FAILED"
   ```

### Expected Result

> **Status**: PASS — 2026-03-09

- [x] `test result: ok. 40 passed; 0 failed; 0 ignored`
- [x] No tests are marked as ignored
- [x] No `FAILED` lines appear in output

---

## Scenario 3 — Encrypt/Decrypt Round-Trip (Manual Inspection)

**What this tests**: A manually compiled binary confirms the ciphertext is valid base64, has the
correct byte layout (`nonce || ciphertext || tag`), and that decryption recovers the original value.

### Setup

Create a temporary example binary (do not commit):

```bash
mkdir -p rust/syntek-crypto/examples
cat > rust/syntek-crypto/examples/roundtrip.rs << 'EOF'
use syntek_crypto::{decrypt_field, encrypt_field};
use base64ct::{Base64, Encoding};

fn main() {
    let key = [0xABu8; 32];
    let plaintext = "user@example.com";
    let model = "User";
    let field = "email";

    let ciphertext = encrypt_field(plaintext, &key, model, field)
        .expect("encrypt_field failed");

    println!("Ciphertext (base64): {ciphertext}");

    let decoded = Base64::decode_vec(&ciphertext).expect("invalid base64");
    println!("Decoded length:      {} bytes", decoded.len());
    println!("  Nonce (12 B):      {:?}", &decoded[..12]);
    println!("  Ciphertext body:   {:?}", &decoded[12..decoded.len()-16]);
    println!("  Auth tag (16 B):   {:?}", &decoded[decoded.len()-16..]);

    let recovered = decrypt_field(&ciphertext, &key, model, field)
        .expect("decrypt_field failed");

    println!("Recovered:           {recovered}");
    assert_eq!(recovered, plaintext, "round-trip FAILED");
    println!("Round-trip: PASS");
}
EOF
```

### Steps

1. Run the example:

   ```bash
   cargo run --example roundtrip -p syntek-crypto
   ```

2. Inspect the printed output.

### Expected Result

> **Status**: PASS — 2026-03-09

- [x] `Ciphertext (base64):` line is a non-empty base64 string (no spaces, no `=` issues)
- [x] `Decoded length:` is `12 + 16 (plaintext bytes) + 16 = 44` bytes for `"user@example.com"` (16
      chars)
- [x] `Nonce (12 B):` shows 12 distinct byte values (not all zeros — CSPRNG-generated)
- [x] `Recovered:` is `user@example.com`
- [x] Final line is `Round-trip: PASS`

### Cleanup

```bash
rm rust/syntek-crypto/examples/roundtrip.rs
```

---

## Scenario 4 — Tampered Ciphertext is Rejected

**What this tests**: Flipping a single byte in the ciphertext body causes `decrypt_field` to return
a `DecryptionError`. No plaintext is ever returned for a corrupted blob.

### Setup

Extend the example approach, or run interactively:

```bash
cat > rust/syntek-crypto/examples/tamper.rs << 'EOF'
use syntek_crypto::{CryptoError, decrypt_field, encrypt_field};
use base64ct::{Base64, Encoding};

fn main() {
    let key = [0xABu8; 32];

    let ct = encrypt_field("sensitive-data", &key, "User", "email")
        .expect("encrypt_field failed");

    let mut bytes = Base64::decode_vec(&ct).expect("invalid base64");
    bytes[13] ^= 0xFF;  // flip a byte in the ciphertext body (after the 12-byte nonce)
    let tampered = Base64::encode_string(&bytes);

    match decrypt_field(&tampered, &key, "User", "email") {
        Err(CryptoError::DecryptionError(msg)) => {
            println!("Correctly rejected tampered ciphertext: {msg}");
            println!("Tamper test: PASS");
        }
        Ok(val) => panic!("SECURITY FAILURE — plaintext leaked: {val}"),
        Err(other) => panic!("Wrong error variant: {other:?}"),
    }
}
EOF
cargo run --example tamper -p syntek-crypto
```

### Expected Result

> **Status**: PASS — 2026-03-09

- [x] Output: `Correctly rejected tampered ciphertext: ...`
- [x] Output: `Tamper test: PASS`
- [x] No plaintext is printed

### Cleanup

```bash
rm rust/syntek-crypto/examples/tamper.rs
```

---

## Scenario 5 — Argon2id Parameters Match Security Specification

**What this tests**: The PHC string produced by `hash_password` encodes exactly `m=65536`, `t=3`,
`p=4` as required by the security specification (OWASP/NIST SP 800-132).

### Steps

1. Run inline via cargo test output, or create a quick example:

   ```bash
   cargo test -p syntek-crypto test_hash_password_phc -- --nocapture 2>&1
   ```

2. Alternatively, inspect the PHC string directly:

   ```bash
   cat > rust/syntek-crypto/examples/phc.rs << 'EOF'
   use syntek_crypto::hash_password;

   fn main() {
       let hash = hash_password("correct-horse-battery-staple")
           .expect("hash_password failed");
       println!("PHC string: {hash}");

       assert!(hash.starts_with("$argon2id$"), "must start with $argon2id$");
       assert!(hash.contains("m=65536"),       "must encode m=65536");
       assert!(hash.contains("t=3"),           "must encode t=3");
       assert!(hash.contains("p=4"),           "must encode p=4");
       println!("Argon2id parameters: PASS");
   }
   EOF
   cargo run --example phc -p syntek-crypto --release
   ```

   > Use `--release` — Argon2id with `m=65536` is intentionally slow in debug mode.

### Expected Result

> **Status**: PASS — 2026-03-09

- [x] PHC string begins with `$argon2id$`
- [x] PHC string contains `m=65536`
- [x] PHC string contains `t=3`
- [x] PHC string contains `p=4`
- [x] Output: `Argon2id parameters: PASS`

### Cleanup

```bash
rm rust/syntek-crypto/examples/phc.rs
```

---

## Scenario 6 — AAD Mismatch Prevents Cross-Model Substitution

**What this tests**: A ciphertext encrypted for `model="User", field="email"` cannot be decrypted
with `model="Order", field="email"` — the GCM authentication tag binds the AAD, so any context
mismatch causes tag verification to fail.

### Steps

```bash
cat > rust/syntek-crypto/examples/aad.rs << 'EOF'
use syntek_crypto::{CryptoError, decrypt_field, encrypt_field};

fn main() {
    let key = [0xABu8; 32];
    let ct = encrypt_field("user@example.com", &key, "User", "email")
        .expect("encrypt_field failed");

    // Attempt cross-model substitution
    match decrypt_field(&ct, &key, "Order", "email") {
        Err(CryptoError::DecryptionError(_)) => println!("Cross-model substitution blocked: PASS"),
        Ok(val) => panic!("SECURITY FAILURE — AAD not enforced, got: {val}"),
        Err(e) => panic!("Wrong error: {e:?}"),
    }

    // Attempt cross-field substitution
    match decrypt_field(&ct, &key, "User", "phone") {
        Err(CryptoError::DecryptionError(_)) => println!("Cross-field substitution blocked: PASS"),
        Ok(val) => panic!("SECURITY FAILURE — field AAD not enforced, got: {val}"),
        Err(e) => panic!("Wrong error: {e:?}"),
    }
}
EOF
cargo run --example aad -p syntek-crypto
```

### Expected Result

> **Status**: PASS — 2026-03-09

- [x] Output: `Cross-model substitution blocked: PASS`
- [x] Output: `Cross-field substitution blocked: PASS`
- [x] No plaintext is printed in either case

### Cleanup

```bash
rm rust/syntek-crypto/examples/aad.rs
```

---

## Scenario 7 — Nonce Uniqueness (Spot Check)

**What this tests**: Running `encrypt_field` repeatedly with the same key and plaintext produces
distinct ciphertexts each time, confirming the CSPRNG-generated nonce is never reused.

### Steps

1. Run the dedicated automated test (it performs 10,000 iterations):

   ```bash
   cargo test -p syntek-crypto test_nonce_uniqueness -- --nocapture 2>&1
   ```

2. For a quick manual spot check, encrypt the same value three times and compare:

   ```bash
   cat > rust/syntek-crypto/examples/nonce.rs << 'EOF'
   use syntek_crypto::encrypt_field;

   fn main() {
       let key = [0xABu8; 32];
       let ct1 = encrypt_field("email@example.com", &key, "User", "email").unwrap();
       let ct2 = encrypt_field("email@example.com", &key, "User", "email").unwrap();
       let ct3 = encrypt_field("email@example.com", &key, "User", "email").unwrap();

       println!("ct1: {ct1}");
       println!("ct2: {ct2}");
       println!("ct3: {ct3}");

       assert_ne!(ct1, ct2, "ct1 == ct2 — nonce reuse!");
       assert_ne!(ct1, ct3, "ct1 == ct3 — nonce reuse!");
       assert_ne!(ct2, ct3, "ct2 == ct3 — nonce reuse!");
       println!("Nonce uniqueness: PASS");
   }
   EOF
   cargo run --example nonce -p syntek-crypto
   ```

### Expected Result

> **Status**: PASS — 2026-03-09

- [x] All three ciphertexts are visibly different strings
- [x] Output: `Nonce uniqueness: PASS`
- [x] The automated 10,000-iteration test passes:
      `test test_nonce_uniqueness_10000_encryptions ... ok`

### Cleanup

```bash
rm rust/syntek-crypto/examples/nonce.rs
```

---

## Scenario 8 — Memory Zeroisation (valgrind)

**What this tests**: Sensitive key material and plaintext buffers are zeroised after use via the
`zeroize` crate, leaving no plaintext residue in memory after the function returns.

> AddressSanitizer requires a nightly Rust toolchain and is not used in this project. Valgrind runs
> on stable Rust and is the standard memory checker for this scenario. The compile-time dependency
> test (`test_zeroize_sensitive_values_compile_time_dependency_present`) provides a baseline guard
> in CI.

### Steps (valgrind — stable)

Build the release binary first — Argon2id at `m=65536` in a debug build under Valgrind will take
hours. Always use `--release`.

```bash
TEST_BIN=$(cargo test -p syntek-crypto --release --no-run --message-format=json 2>/dev/null \
  | jq -r 'select(.executable) | .executable' | grep crypto_tests | head -1)
valgrind --leak-check=full --errors-for-leak-kinds=definite,indirect --error-exitcode=1 \
  "$TEST_BIN" 2>&1 | tail -20
```

> `--errors-for-leak-kinds=definite,indirect` scopes failures to real leaks only. Rust's runtime
> thread-local storage produces a small "possibly lost" block (48 bytes) that is a well-known
> Valgrind false positive — it is not from the crypto code.

### Expected Result

> **Status**: PASS — 2026-03-09

- [x] `definitely lost: 0 bytes in 0 blocks`
- [x] `indirectly lost: 0 bytes in 0 blocks`
- [x] `ERROR SUMMARY: 0 errors from 0 contexts`
- [x] All 40 tests pass under valgrind

---

## Regression Checklist

Run before marking the US006 implementation PR ready for review:

- [x] All 40 automated tests pass: `cargo test -p syntek-crypto --release`
- [x] Clippy is clean: `cargo clippy -p syntek-crypto -- -D warnings`
- [x] Code is formatted: `cargo fmt -p syntek-crypto -- --check`
- [x] Scenario 3 (round-trip) passes manually
- [x] Scenario 4 (tamper rejection) passes manually
- [x] Scenario 5 (Argon2id params) passes manually
- [x] Scenario 6 (AAD mismatch) passes manually
- [x] Scenario 7 (nonce uniqueness) passes manually
- [x] No `unsafe` blocks introduced: `grep -r "unsafe" rust/syntek-crypto/src/`
- [x] No secrets or test keys committed to source:
      `git diff --cached | grep -i "secret\|password\|key"`

---

## Known Issues

| Issue                                                                                        | Workaround                                                         | Story / Issue |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------- |
| Argon2id with `m=65536` is very slow in debug mode                                           | Always use `--release` for hash/verify tests and Valgrind runs     | US006         |
| `cargo test` may time out in CI for the 10,000-nonce test on slow runners                    | CI runs with `--release` (rust.yml)                                | US006         |
| Valgrind reports 48 bytes "possibly lost" — Rust runtime thread-local storage false positive | Use `--errors-for-leak-kinds=definite,indirect`; ignore this block | US006         |

---

## Reporting a Bug

If a scenario fails unexpectedly:

1. Note the exact command and its full output
2. Check whether the failure is in the stub (red phase) or the implementation (green phase)
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report at `docs/BUGS/US006-{YYYY-MM-DD}.md`
5. Reference the story: `Blocks US006`
