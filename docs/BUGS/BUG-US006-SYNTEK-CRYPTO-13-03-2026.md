# BUG-US006 — `syntek-crypto` QA Findings

**Date**: 13/03/2026 **Source**: `docs/QA/QA-US006-SYNTEK-CRYPTO-11-03-2026.md` **Total Findings**:
17 **Fixed**: 15 **No Fix Required**: 2 **Deferred**: 0

---

## Summary

| ID  | Severity | Title                                               | Status                         |
| --- | -------- | --------------------------------------------------- | ------------------------------ |
| 001 | Critical | `decrypt_fields_batch` missing key-length guard     | Fixed                          |
| 002 | Critical | `KeyRing::add` permits duplicate version insertion  | Fixed                          |
| 003 | High     | `reencrypt_to_active` plaintext not zeroised        | Fixed                          |
| 004 | High     | `hmac_sign`/`hmac_verify` accept empty key          | Fixed                          |
| 005 | High     | `syntek.manifest.toml` absent from repository       | Fixed                          |
| 006 | High     | `verify_password` uses `Argon2::default()`          | Fixed                          |
| 007 | Medium   | `KeyRing` O(n) lookup undocumented                  | Fixed (doc)                    |
| 008 | Medium   | `hmac_verify` rejects uppercase hex signatures      | Fixed                          |
| 009 | Medium   | `encrypt_versioned`/`decrypt_versioned` duplication | Fixed                          |
| 010 | Medium   | Test count discrepancy US006 vs US076               | Investigated — No Fix Required |
| 011 | Medium   | `deny.toml` strict `unmaintained` policy            | Fixed                          |
| 012 | Medium   | Empty `examples/` directory                         | Fixed                          |
| 013 | Low      | `CryptoError` lacks `PartialEq`                     | Fixed                          |
| 014 | Low      | `KeyVersion(0)` reserved but not enforced           | Fixed                          |
| 015 | Low      | `hmac_sign`/`hmac_verify` missing key length docs   | Fixed                          |
| 016 | Low      | Property test excludes large payloads               | Fixed                          |
| 017 | Low      | All-zero test key not guarded                       | Investigated — No Fix Required |

**Verification**: `cargo clippy -p syntek-crypto -- -D warnings` — clean ·
`cargo test -p syntek-crypto` — 80/80 pass

---

## Critical

---

### BUG-US006-001 — `decrypt_fields_batch` missing upfront key-length validation

**Severity**: Critical **Status**: Fixed **QA Finding**: C1 **File(s)**:
`rust/syntek-crypto/src/lib.rs`

#### Root Cause

`encrypt_fields_batch` validates `key.len() == 32` at the top of the function and returns
`CryptoError::InvalidInput` before touching any field. `decrypt_fields_batch` had no such upfront
guard. It delegated directly to `decrypt_field`, which checks key length only after base64 decoding,
meaning N base64 decode allocations were made before the first error was returned. The error variant
was also inconsistent: `BatchError` (wrapping `DecryptionError`) instead of `InvalidInput`.

#### Fix Applied

Added the same upfront key-length guard to `decrypt_fields_batch` that exists in
`encrypt_fields_batch`. The function now returns `CryptoError::InvalidInput` immediately if the key
is not exactly 32 bytes, matching the encrypt path's error semantics exactly.

```rust
// Added at the top of decrypt_fields_batch, before the iterator:
if key.len() != 32 {
    return Err(CryptoError::InvalidInput(format!(
        "key must be 32 bytes, got {}",
        key.len()
    )));
}
```

#### Verification

Call `decrypt_fields_batch(&[("email", ct)], &[0u8; 16], "User")` and observe
`CryptoError::InvalidInput`, matching the encrypt path.

---

### BUG-US006-002 — `KeyRing::add` permits silent duplicate version insertion

**Severity**: Critical **Status**: Fixed **QA Finding**: C2 **File(s)**:
`rust/syntek-crypto/src/key_versioning.rs`

#### Root Cause

`KeyRing::add` did not check whether `version` already existed in `entries` before pushing. Calling
`add(KeyVersion(1), &key_a)` followed by `add(KeyVersion(1), &key_b)` silently created two entries
for version 1. `KeyRing::get` used `Iterator::find` (returns first match), while `KeyRing::active`
used `Iterator::max_by_key` (returns last match on ties). This created non-deterministic key
resolution depending on insertion order, leading to potential silent data corruption where
ciphertexts encrypted under one duplicate could not be decrypted.

#### Fix Applied

Added a duplicate-version check in `KeyRing::add` that scans `entries` for an existing entry with
the same version. If found, `CryptoError::InvalidInput` is returned with a descriptive message. This
makes misconfigured key rotation fail loudly at ring construction time rather than silently
corrupting data at runtime.

```rust
// Added in KeyRing::add, after the key-length check:
if self.entries.iter().any(|(v, _)| *v == version) {
    return Err(CryptoError::InvalidInput(format!(
        "key version {:?} already exists in ring",
        version
    )));
}
```

#### Verification

Calling `ring.add(KeyVersion(1), &key_a)` then `ring.add(KeyVersion(1), &key_b)` now returns
`Err(CryptoError::InvalidInput("key version KeyVersion(1) already exists in ring"))`.

---

## High

---

### BUG-US006-003 — `reencrypt_to_active` holds plaintext without zeroise guarantee

**Severity**: High **Status**: Fixed **QA Finding**: H1 **File(s)**:
`rust/syntek-crypto/src/key_versioning.rs`

#### Root Cause

The `reencrypt_to_active` function decrypted old ciphertext into a plain `String` binding. Rust's
`String` type does not implement `ZeroizeOnDrop` — when the binding goes out of scope, the heap
bytes are reclaimed by the allocator without being overwritten. This violated the crate's AC6
security contract that "all sensitive in-memory values are zeroised via the `zeroize` crate". The
window between decrypt and re-encrypt left plaintext data resident in heap memory where a
use-after-free or heap dump could expose sensitive field values.

#### Fix Applied

Wrapped the intermediate plaintext in `zeroize::Zeroizing<String>`, which implements `Drop` by
overwriting the heap buffer with zeroes before deallocation. `Zeroizing<T>` implements
`Deref<Target = T>`, so the `&plaintext` dereference to `&str` in the `encrypt_versioned` call works
transparently.

```rust
// Before:
let plaintext = decrypt_versioned(ciphertext, ring, model, field)?;
encrypt_versioned(&plaintext, ring, model, field)

// After:
let plaintext = zeroize::Zeroizing::new(decrypt_versioned(ciphertext, ring, model, field)?);
encrypt_versioned(&plaintext, ring, model, field)
```

#### Verification

The `zeroize` crate is already a declared dependency in `Cargo.toml`. `Zeroizing<String>` guarantees
the heap buffer is overwritten on drop.

---

### BUG-US006-004 — `hmac_sign` and `hmac_verify` accept empty key without error

**Severity**: High **Status**: Fixed **QA Finding**: H2 **File(s)**:
`rust/syntek-crypto/src/lib.rs`, `rust/syntek-crypto/tests/crypto_tests.rs`

#### Root Cause

HMAC with a zero-length key is technically valid per RFC 2104 but cryptographically useless — it
provides no authentication. The `hmac` crate's `new_from_slice` accepts keys of any length including
empty. A consumer with a misconfigured environment variable loading an empty string would silently
produce valid-looking HMAC signatures that any other empty-key holder could reproduce, defeating the
authentication purpose entirely.

#### Fix Applied

1. **`hmac_sign`**: Changed return type from `String` to `Result<String, CryptoError>`. Added an
   upfront guard that returns `CryptoError::InvalidInput` if `key` is empty.
2. **`hmac_verify`**: Added an upfront guard that returns `false` immediately if `key` is empty.
3. **Test file**: Updated all 8 call sites in `crypto_tests.rs` to use `.expect()` / `.unwrap()` on
   the new `Result` return type from `hmac_sign`.
4. **Doc comments**: Added key length guidance (recommended minimum 32 bytes / 256 bits) to both
   functions. This also resolves BUG-US006-015 (L3).

```rust
// hmac_sign — changed signature and added guard:
pub fn hmac_sign(data: &[u8], key: &[u8]) -> Result<String, CryptoError> {
    if key.is_empty() {
        return Err(CryptoError::InvalidInput(
            "HMAC key must not be empty".to_string(),
        ));
    }
    // ... existing logic wrapped in Ok(...)
}

// hmac_verify — added guard:
pub fn hmac_verify(data: &[u8], key: &[u8], sig: &str) -> bool {
    if key.is_empty() {
        return false;
    }
    // ... existing logic
}
```

> **Breaking change**: `hmac_sign` now returns `Result<String, CryptoError>`. The `syntek-pyo3`
> crate does not call `hmac_sign`, so there is no downstream impact within this repository.

#### Verification

- `hmac_sign(b"data", b"")` returns `Err(CryptoError::InvalidInput(...))`
- `hmac_verify(b"data", b"", &sig)` returns `false`

---

### BUG-US006-005 — `syntek.manifest.toml` absent from repository

**Severity**: High **Status**: Fixed **QA Finding**: H3 **File(s)**:
`rust/syntek-crypto/syntek.manifest.toml` (created)

#### Root Cause

The US006 completion checklist marked the `syntek.manifest.toml` creation task as done, but the file
was never committed to the repository. The `syntek add` CLI install flow depends on this manifest to
locate and pin the crate version from the Forgejo Cargo registry. Without it, the published install
path (`syntek add syntek-crypto`) would fail for downstream consumers.

#### Fix Applied

Created `rust/syntek-crypto/syntek.manifest.toml` with the crate ID and Forgejo Cargo registry
coordinates. Contains only identity and registry metadata — no configurable options, per the
security policy that the Rust layer is not configurable by consumers.

```toml
[crate]
id = "syntek-crypto"
description = "AES-256-GCM encryption, Argon2id hashing, and HMAC-SHA256 for Syntek modules"

[registry]
type = "cargo"
url = "https://git.syntek-studio.com/syntek/_cargo-registry"
index = "https://git.syntek-studio.com/syntek/_cargo-registry.git"
```

---

### BUG-US006-006 — `verify_password` uses `Argon2::default()` instead of explicit parameters

**Severity**: High **Status**: Fixed **QA Finding**: H4 **File(s)**: `rust/syntek-crypto/src/lib.rs`

#### Root Cause

`hash_password` correctly constructs an `Argon2` instance with the Syntek-standard parameters
(`m=65536, t=3, p=4`). `verify_password` used `Argon2::default()`, which uses the `argon2` crate's
compile-time defaults (`m=65536, t=2, p=1` as of argon2 0.5). Verification still succeeded because
the PHC string carries the original parameters, but the asymmetry created:

1. A correctness trap — if the `argon2` crate changes its defaults in a future version, behaviour
   could silently change.
2. A maintenance risk — developers reading `verify_password` would assume the code uses project
   defaults and could copy the pattern into parameter-dependent operations.
3. A violation of the explicit parameter control stated in the security specification.

#### Fix Applied

Replaced `Argon2::default()` in `verify_password` with the same explicitly parameterised
`Argon2::new(Algorithm::Argon2id, Version::V0x13, params)` construction used in `hash_password`.

```rust
// Before:
match Argon2::default().verify_password(password.as_bytes(), &parsed_hash) {

// After:
let params =
    Params::new(65536, 3, 4, None).map_err(|e| CryptoError::HashError(e.to_string()))?;
let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);

match argon2.verify_password(password.as_bytes(), &parsed_hash) {
```

#### Verification

Both `hash_password` and `verify_password` now use identical parameter construction.
`test_verify_password_correct_password_returns_true` confirms verification still succeeds.

---

## Medium

---

### BUG-US006-007 — `KeyRing` backing store O(n) lookup not documented

**Severity**: Medium **Status**: Fixed (documentation) **QA Finding**: M1 **File(s)**:
`rust/syntek-crypto/src/key_versioning.rs`

#### Root Cause

Both `KeyRing::get` and `KeyRing::active` perform linear scans over `self.entries` on every
invocation. In the expected deployment scenario (2–5 keys) this is inconsequential. However, the
`entries` field had no documented capacity bound, meaning a misconfigured ring with many entries
would degrade throughput linearly without any indication this was unintended.

#### Fix Applied

Added a `# Capacity` section to the `KeyRing` doc comment documenting that the ring is designed for
small key sets (typically 2–4 entries) and that lookups are O(n). A full replacement with `BTreeMap`
was considered but deferred — the duplicate-version guard (BUG-US006-002) already prevents unbounded
growth from misconfiguration.

```rust
/// # Capacity
///
/// The ring is designed for small key sets (typically 2-4 entries during a
/// rotation cycle). Lookups are O(n) linear scans over the backing `Vec`.
/// Do not populate the ring with a large number of entries; if more than
/// ~10 versions are needed simultaneously, the backing store should be
/// replaced with an indexed map.
```

---

### BUG-US006-008 — `hmac_verify` silently rejects uppercase hex signatures

**Severity**: Medium **Status**: Fixed **QA Finding**: M2 **File(s)**:
`rust/syntek-crypto/src/lib.rs`

#### Root Cause

`hmac_sign` always produces lowercase hex output. `hmac_verify` passed the signature directly to
`decode_hex_32` without case normalisation. Consumers who uppercase signatures before storage
(common in HTTP header normalisation) had no guidance that the verifier was case-sensitive. To
eliminate the ambiguity and make the API robust against HTTP header normalisation, the fix
normalises input to lowercase before processing.

#### Fix Applied

Added `sig.to_ascii_lowercase()` in `hmac_verify` before passing to `decode_hex_32`. Updated the doc
comment to explicitly state that both lowercase and uppercase hex are accepted.

```rust
// Added in hmac_verify:
let sig_lower = sig.to_ascii_lowercase();
let Some(expected) = decode_hex_32(&sig_lower) else {
    return false;
};
```

---

### BUG-US006-009 — `encrypt_versioned`/`decrypt_versioned` duplicate AES-GCM logic

**Severity**: Medium **Status**: Fixed **QA Finding**: M3 **File(s)**:
`rust/syntek-crypto/src/aes_gcm.rs` (new), `rust/syntek-crypto/src/key_versioning.rs`,
`rust/syntek-crypto/src/lib.rs`

#### Root Cause

`encrypt_versioned` and `decrypt_versioned` re-imported `aes_gcm`, `base64ct`, and `rand` and
duplicated the AES-256-GCM encrypt/decrypt logic that already existed in `lib.rs`. The AAD
construction `format!("{}:{}", model, field)` appeared in four locations. Any change to the
encryption routine had to be applied in two places.

#### Fix Applied

Extracted two `pub(crate)` helpers into a new file `rust/syntek-crypto/src/aes_gcm.rs`:

- `aes_gcm_encrypt(plaintext: &str, key: &[u8], aad: &[u8]) -> Result<String, CryptoError>`
- `aes_gcm_decrypt(ciphertext: &str, key: &[u8], aad: &[u8]) -> Result<String, CryptoError>`

These hold the single canonical AES-256-GCM implementation (nonce generation, encryption, base64
encoding/decoding). AAD is passed in as a parameter — callers construct
`format!("{}:{}", model, field).into_bytes()` as before, keeping the calling convention unchanged.

`lib.rs` — `encrypt_field` and `decrypt_field` now delegate to the helpers. `key_versioning.rs` —
`encrypt_versioned` and `decrypt_versioned` now delegate to the helpers; inline `use` blocks inside
function bodies removed.

#### Verification

All 80 tests pass. `cargo clippy -p syntek-crypto -- -D warnings` — clean. No behaviour change.

---

### BUG-US006-010 — Test count discrepancy between US006 completion and test status

**Severity**: Medium **Status**: Investigated — No Fix Required **QA Finding**: M4 **File(s)**:
`docs/STORIES/US006.md`, `docs/TESTS/US006-TEST-STATUS.md`

#### Root Cause

The US006 completion notes state "49/49 passing — 36 unit, 4 property-based (proptest), 9 doctests".
The `key_versioning_tests.rs` file's own module docstring explicitly attributes it to "US076 — Red
phase: key versioning tests". The 29 key versioning tests were added as part of US076's scope but
exist in the same crate. Both test files run under `cargo test -p syntek-crypto`. The current total
is 80 tests, but US006 owns 51 (42 + 9) and US076 owns 29.

#### Fix Applied

No code fix required. This is a documentation traceability issue. The test status document correctly
scopes US006's tests. When US076 story documentation is created, it should explicitly list
`key_versioning_tests.rs` as its test file.

---

### BUG-US006-011 — `deny.toml` strict `unmaintained` policy risks CI instability

**Severity**: Medium **Status**: Fixed **QA Finding**: M5 **File(s)**: `deny.toml`

#### Root Cause

The `deny.toml` advisory policy set `unmaintained = "all"`, meaning any transitive dependency
flagged as unmaintained by the RustSec advisory database would fail `cargo deny check`. Several
dependencies in the crypto chain have a history of being flagged as superseded, which can block CI
when an upstream crate is marked unmaintained for reasons unrelated to security.

#### Fix Applied

Changed `unmaintained` from `"all"` (deny) to `"warn"`. `yanked = "deny"` remains strict to protect
against known-bad versions.

```toml
# Before:
unmaintained = "all"

# After:
unmaintained = "warn"
```

---

### BUG-US006-012 — Empty `examples/` directory committed without context

**Severity**: Medium **Status**: Fixed **QA Finding**: M6 **File(s)**:
`rust/syntek-crypto/examples/.gitkeep` (created)

#### Root Cause

The manual testing guide instructs testers to create temporary example binaries in
`rust/syntek-crypto/examples/` and then delete them. The directory was committed empty, providing no
context about its purpose and potentially confusing contributors who look for runnable examples.

#### Fix Applied

Added `rust/syntek-crypto/examples/.gitkeep` with a comment explaining the directory is for
temporary manual-testing example binaries and that they should not be committed.

---

## Low

---

### BUG-US006-013 — `CryptoError` lacks `PartialEq` derivation

**Severity**: Low **Status**: Fixed **QA Finding**: L1 **File(s)**: `rust/syntek-crypto/src/lib.rs`

#### Root Cause

The `CryptoError` enum derived `Debug` and used `thiserror::Error` but did not derive `PartialEq`.
Tests were forced to use `match result.unwrap_err()` blocks instead of the more ergonomic
`assert_eq!(err, CryptoError::InvalidInput("..."))`.

#### Fix Applied

Added `PartialEq` to the derive list on `CryptoError`. All variants contain only `String` fields,
which implement `PartialEq`, so the derivation is straightforward.

```rust
// Before:
#[derive(Debug, thiserror::Error)]

// After:
#[derive(Debug, PartialEq, thiserror::Error)]
```

---

### BUG-US006-014 — `KeyVersion(0)` documented as reserved but not enforced

**Severity**: Low **Status**: Fixed **QA Finding**: L2 **File(s)**:
`rust/syntek-crypto/src/key_versioning.rs`

#### Root Cause

The `KeyVersion` doc comment stated "Version 0 is reserved; valid versioned keys start at 1."
However, `KeyRing::add` accepted `KeyVersion(0)` without error. A consumer who accidentally inserted
a version-0 key would produce ciphertexts with a `0x00 0x00` prefix that could conflict with any
future use of version 0 as a sentinel or format discriminator.

#### Fix Applied

Added a guard in `KeyRing::add` that rejects `KeyVersion(0)` with `CryptoError::InvalidInput`. The
guard is checked before the key-length and duplicate-version checks.

```rust
// Added at the top of KeyRing::add:
if version.0 == 0 {
    return Err(CryptoError::InvalidInput(
        "KeyVersion(0) is reserved; valid versions start at 1".to_string(),
    ));
}
```

#### Verification

`ring.add(KeyVersion(0), &[0u8; 32])` now returns `Err(CryptoError::InvalidInput(...))`.

---

### BUG-US006-015 — `hmac_sign`/`hmac_verify` missing key length guidance

**Severity**: Low **Status**: Fixed **QA Finding**: L3 **File(s)**: `rust/syntek-crypto/src/lib.rs`

#### Root Cause

The public API docs for `hmac_sign` and `hmac_verify` did not document the expected key length or
the implications of short keys. Consumers integrating webhook verification may use keys of varying
lengths without understanding that keys shorter than 32 bytes reduce the effective security level
below 256 bits.

#### Fix Applied

Applied as part of BUG-US006-004 — `# Key length` sections were added to both doc comments when the
empty-key guards were implemented. Documents the recommended minimum (32 bytes / 256 bits), RFC 2104
behaviour for short/long keys, and that empty keys are rejected.

---

### BUG-US006-016 — Property test does not cover large payloads

**Severity**: Low **Status**: Fixed **QA Finding**: L4 **File(s)**:
`rust/syntek-crypto/tests/crypto_tests.rs`

#### Root Cause

The proptest strategy `".*"` generates arbitrary Rust `String` values within proptest's default size
limit (~256 bytes). It did not test very large plaintexts (e.g. multi-megabyte strings) that could
expose performance issues or memory allocation failures in the AES-GCM path.

#### Fix Applied

Added a new `mod large_payload` block at the bottom of `crypto_tests.rs` with four property tests,
each using `ProptestConfig { cases: 10, timeout: 10_000, ..default() }` to keep the suite fast in
both local dev and CI/CD.

| Test                                                       | Strategy                            | Property verified                                              |
| ---------------------------------------------------------- | ----------------------------------- | -------------------------------------------------------------- |
| `prop_encrypt_decrypt_roundtrip_large_plaintext`           | `vec(any::<u8>(), 0..=2_000_000)`   | Full round-trip correctness at up to 2 MiB                     |
| `prop_encrypt_output_larger_than_input_large_payload`      | same                                | Ciphertext always larger than plaintext — no silent truncation |
| `prop_versioned_encrypt_decrypt_roundtrip_large_plaintext` | same                                | Versioned API round-trip correctness at up to 2 MiB            |
| `prop_large_payload_wrong_key_always_fails_decryption`     | `vec(any::<u8>(), 1_000..=100_000)` | Wrong-key decrypt always returns `Err`                         |

Note: proptest 1.5 silently ignores the `timeout` field in closure-style `proptest!` invocations.
The `cases: 10` cap is the primary speed-control mechanism. The `timeout` field is retained for
documentation intent and forward compatibility.

#### Verification

- `cargo test -p syntek-crypto large_payload` — 4/4 pass, ~22 s in debug mode (budget: 60 s)
- `cargo test -p syntek-crypto` — 84/84 pass (80 existing + 4 new)

---

### BUG-US006-017 — All-zero test key used throughout test suite

**Severity**: Low **Status**: Investigated — No Fix Required **QA Finding**: L5 **File(s)**:
`rust/syntek-crypto/tests/crypto_tests.rs`

#### Root Cause

The all-zero 32-byte test key is a well-known weak test vector. The constant is adequately commented
("A real key must be generated from a CSPRNG; this constant is test-only"). The library itself
cannot distinguish a CSPRNG key from a zero key because any 32-byte value is a valid AES-256 key.

#### Fix Applied

No action required within this crate. The test file is in the `tests/` directory and is not compiled
into the library. The risk exists only at the consumer level.

**Recommendation**: Document in `syntek-pyo3` and the Django binding layer that encryption keys must
be validated as non-zero and generated from a CSPRNG before use.

---

## All findings resolved

All 17 QA findings have been addressed. 15 fixed in code, 2 investigated with no fix required.
