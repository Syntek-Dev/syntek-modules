# QA Report: US006 — `syntek-crypto` Core Cryptographic Primitives

**Date:** 11/03/2026 **Analyst:** QA Agent (The Breaker) **Story:** US006 — `syntek-crypto`: Core
Cryptographic Primitives **Package:** `rust/syntek-crypto` **Branch reviewed:**
`us006/syntek-crypto` (merged via PR #14) **Status:** ISSUES FOUND

---

## Summary

The `syntek-crypto` crate implements AES-256-GCM field-level encryption, Argon2id password hashing,
and HMAC-SHA256 integrity verification. The core cryptographic logic is sound and the test suite is
comprehensive. However, several meaningful gaps were found: the `key_versioning` module was
implemented but is entirely absent from US006's scope and test coverage accounting, the `KeyRing`
has a silent duplicate-version insertion defect, the `hmac_sign` function accepts a zero-length key
without any guard, the `decrypt_fields_batch` function silently ignores the key-length check that
its encrypt counterpart enforces, the `reencrypt_to_active` function exposes plaintext in memory
between decrypt and re-encrypt without a zeroize guard on the intermediate, and the
`syntek.manifest.toml` file required by the story tasks is absent from the repository. Additionally,
the `KeyRing` is backed by an unsorted `Vec` that performs O(n) linear scans on every `get()` and
`active()` call, which will degrade at scale.

---

## 1. CRITICAL (Blocks deployment)

### C1 — `decrypt_fields_batch` does not validate key length before processing

**File:** `rust/syntek-crypto/src/lib.rs:385–399`

`encrypt_fields_batch` validates that `key.len() == 32` at the top of the function and returns
`CryptoError::InvalidInput` before touching any field. `decrypt_fields_batch` contains no such
upfront guard. It delegates directly to `decrypt_field`, which does check the key length, but only
after successfully decoding the base64 blob and reaching the key-length check at line 159. For a
batch of N fields this means N base64 decode allocations are made before the first `DecryptionError`
is returned.

More critically, the error variant returned is asymmetric with the encrypt path: a consumer who
passes a wrong-length key to `decrypt_fields_batch` receives a `BatchError` (wrapping a
`DecryptionError`), whereas the same mistake on `encrypt_fields_batch` returns `InvalidInput`. The
public API contract is inconsistent, and callers who type-match on error variants (as the tests do)
will handle the two paths differently despite the root cause being identical.

**Impact:** Inconsistent error semantics between the encrypt and decrypt batch paths. A defensive
consumer checking for `InvalidInput` on key-length errors from the decrypt batch will silently miss
the error. Partial allocations are performed before failure is signalled.

**Reproduce:** Call `decrypt_fields_batch(&[("email", some_valid_ciphertext)], &[0u8; 16], "User")`
and observe the returned error is `BatchError`, not `InvalidInput`.

**Recommended fix direction:** Add the same upfront key-length guard to `decrypt_fields_batch` that
exists in `encrypt_fields_batch`, returning `CryptoError::InvalidInput` immediately.

---

### C2 — `KeyRing::add` permits silent duplicate version insertion

**File:** `rust/syntek-crypto/src/key_versioning.rs:73–84`

`KeyRing::add` does not check whether `version` already exists in `entries` before pushing. Calling
`add(KeyVersion(1), &key_a)` followed by `add(KeyVersion(1), &key_b)` silently creates two entries
for version 1. `KeyRing::get` uses `Iterator::find`, which returns the first match — `key_a`.
`KeyRing::active` uses `Iterator::max_by_key`, which scans all entries and returns the last maximum
found when there are ties — meaning the active key resolution is non-deterministic across different
insertion orders for the same version number.

A consumer who calls `add` twice for the same version — for example during a misconfigured key
rotation — will receive no error, and subsequent `get` and `active` calls will silently use
whichever duplicate the iterator happens to land on first. This could cause decryption to fail for
ciphertexts that were encrypted under the second duplicate key.

**Impact:** Silent data corruption. Key rotation operations that accidentally repeat a version
number will create a split-brain ring where some ciphertexts cannot be decrypted.

**Reproduce:** Create a `KeyRing`, call `add(KeyVersion(1), &[0x01u8; 32])`, then
`add(KeyVersion(1), &[0x02u8; 32])`. Call `ring.len()` — it returns 2. Call
`ring.get(KeyVersion(1))` — it returns `[0x01; 32]`, silently hiding the second entry.

**Recommended fix direction:** Check for an existing entry with the same version in `add` and return
`CryptoError::InvalidInput` if a duplicate is detected.

---

## 2. HIGH (Must fix before sign-off)

### H1 — `reencrypt_to_active` holds plaintext in a `String` between decrypt and re-encrypt with no zeroize guarantee

**File:** `rust/syntek-crypto/src/key_versioning.rs:279–281`

The `reencrypt_to_active` function decrypts the old ciphertext to a `String` (line 280) and
immediately passes it to `encrypt_versioned` (line 281). The intermediate `plaintext` binding is a
heap-allocated `String`. Rust will drop it when it goes out of scope at the function return, but
`String` does not implement `ZeroizeOnDrop` — the heap bytes are not overwritten before the
allocator reclaims them.

The rest of the crate enforces a zero-plaintext-in-memory guarantee through the `zeroize` crate.
`reencrypt_to_active` breaks that guarantee for the window between decrypt and re-encrypt. For a
crate whose stated security contract includes AC6 ("all sensitive in-memory values are zeroised via
the `zeroize` crate"), this is a material gap.

**Impact:** Plaintext data is briefly resident in heap memory without being zeroised. A
use-after-free or heap dump during a re-encryption operation could expose sensitive field values.

**Reproduce:** Review `key_versioning.rs:280` — the return value of `decrypt_versioned` is bound to
a plain `String`, not a `zeroize::Zeroizing<String>`.

**Recommended fix direction:** Wrap the intermediate plaintext in `Zeroizing<String>` so that the
heap buffer is overwritten when the binding is dropped. The `zeroize` crate provides `Zeroizing<T>`
for exactly this pattern.

---

### H2 — `hmac_sign` accepts a zero-length key without error

**File:** `rust/syntek-crypto/src/lib.rs:270–282`

`hmac_sign` calls `<HmacSha256 as Mac>::new_from_slice(key)` and panics (via `.expect(...)`) if the
slice is rejected. The `hmac` crate's `new_from_slice` accepts keys of any length for HMAC,
including zero-length slices, so the `.expect` path is never triggered. Passing an empty `key` (a
programming error that could result from a misconfigured environment variable loading an empty
string) produces a valid-looking 64-character hex digest without any error or warning.

HMAC with a zero-length key is technically valid per RFC 2104 but is cryptographically useless — it
provides no authentication. Any consumer relying on `hmac_sign` for webhook signature verification
(the stated use case in the docs) would silently accept any payload signed with an empty key if
their key derivation produced an empty slice.

**Impact:** Silent security failure. A misconfigured consumer passes `b""` as the HMAC key; all
signatures verify as correct because both the signer and verifier produce the same deterministic
HMAC-over-empty-key output.

**Reproduce:** Call `hmac_sign(b"any-payload", b"")` — it returns a valid-looking 64-char hex string
without error. Call `hmac_verify(b"any-payload", b"", &that_sig)` — it returns `true`.

**Recommended fix direction:** Add an explicit guard in `hmac_sign` and `hmac_verify` that returns
an error (or `false` for verify) when `key` is empty, matching the pattern used in `hash_password`
and `verify_password`.

---

### H3 — `syntek.manifest.toml` is absent from the repository

**Story task:** "Create `syntek.manifest.toml` — crate ID and Forgejo registry coordinates only"
(checked as complete in US006 task list)

**File:** `rust/syntek-crypto/` — no `syntek.manifest.toml` present

The US006 completion checklist marks this task as done, but the file does not exist anywhere under
`rust/syntek-crypto/`. The `syntek add` CLI install flow documented in CLAUDE.md depends on this
manifest to locate and pin the crate version from the Forgejo Cargo registry. Without it, the
published install path is broken. The completion status in the story is incorrect.

**Impact:** The `syntek add syntek-crypto` install command cannot function. Downstream consumers
using the CLI installer will fail to add the crate to their workspace.

**Reproduce:** `ls /mnt/archive/OldRepos/syntek/syntek-modules/rust/syntek-crypto/` —
`syntek.manifest.toml` is not present.

**Recommended fix direction:** Create `syntek.manifest.toml` with the crate ID and Forgejo registry
coordinates. Update the completion checklist to reflect its actual state.

---

### H4 — `verify_password` uses `Argon2::default()` instead of the Syntek-standard parameters

**File:** `rust/syntek-crypto/src/lib.rs:249`

`hash_password` correctly constructs an `Argon2` instance with the Syntek-standard parameters
(`m=65536, t=3, p=4`) on line 213. `verify_password` uses `Argon2::default()` on line 249, which
uses the argon2 crate's compile-time defaults (`m=65536, t=2, p=1` as of argon2 0.5). Argon2id PHC
strings encode the parameters used during hashing, and the verifier extracts and re-uses those
parameters from the stored PHC string — so verification will still succeed because the PHC string
carries the original parameters.

However, this is a correctness trap and a future maintenance risk. If the `argon2` crate changes its
defaults in a future minor version, or if a developer reads `verify_password` and assumes the code
is using the project-standard parameters, they will be misled. The asymmetry between `hash_password`
and `verify_password` is also a code-quality issue that runs counter to the principle of explicit
parameter control stated in the security specification.

**Impact:** Currently correct due to PHC parameter self-description, but fragile. If
`Argon2::default()` is ever changed upstream or if a developer treats `verify_password` as a
template for future parameter-dependent operations, silent mis-configuration will occur.

**Reproduce:** Read `lib.rs:213` (explicit params) vs `lib.rs:249` (default) — the inconsistency is
structural.

**Recommended fix direction:** Replace `Argon2::default()` in `verify_password` with the same
explicitly parameterised `Argon2::new(Algorithm::Argon2id, Version::V0x13, params)` used in
`hash_password`, making the parameter intent clear and eliminating dependency on crate defaults.

---

## 3. MEDIUM (Fix soon, non-blocking)

### M1 — `KeyRing` backing store is an unsorted `Vec` with O(n) lookup on every call

**File:** `rust/syntek-crypto/src/key_versioning.rs:57–123`

Both `KeyRing::get` and `KeyRing::active` perform linear scans over `self.entries` on every
invocation. In the expected deployment scenario (2–5 keys in the ring) this is inconsequential.
However, the `entries` field is a public-facing `Vec` with no documented capacity bound. If a
misconfigured or adversarially crafted ring is populated with a large number of entries, the O(n)
scan in `active()` is called on every encrypt and decrypt operation, degrading throughput linearly
with ring size.

**Impact:** Performance degradation at scale if the ring is ever unexpectedly large. No security
impact.

**Recommended fix direction:** Document that the ring is designed for small key sets (2–4 entries),
or switch the backing store to a `BTreeMap<KeyVersion, [u8; 32]>` which provides O(log n) lookup and
O(1) max via `.iter().next_back()`.

---

### M2 — `decode_hex_32` rejects uppercase HMAC signatures silently

**File:** `rust/syntek-crypto/src/lib.rs:407–418`

`decode_hex_32` calls `char::to_digit(16)` on each input byte. This accepts both lowercase (`a–f`)
and uppercase (`A–F`) hex characters. However, `hmac_sign` always produces lowercase hex. A consumer
who uppercases the HMAC signature before storage (common in HTTP header normalisation) and then
passes it to `hmac_verify` will receive `false`, appearing as an authentication failure, when the
signature is actually valid.

The doc comment for `hmac_verify` does not state whether the signature must be lowercase, and
`hmac_sign`'s doc comment states "lowercase hex-encoded digest" but does not warn that the verifier
is case-sensitive.

**Impact:** Subtle integration failure when signatures are stored or transmitted via systems that
normalise to uppercase. Difficult to diagnose because no error is returned — just `false`.

**Recommended fix direction:** Document explicitly that `hmac_verify` requires a lowercase hex
signature, and/or normalise the input to lowercase before decoding to remove the silent failure
mode.

---

### M3 — `encrypt_versioned` / `decrypt_versioned` code is duplicated from `lib.rs` without abstraction

**File:** `rust/syntek-crypto/src/key_versioning.rs:144–237`

`encrypt_versioned` re-imports `aes_gcm`, `base64ct`, and `rand` within the function body and
duplicates the AES-256-GCM encrypt/decrypt logic that already exists in `lib.rs:encrypt_field` /
`lib.rs:decrypt_field`. The versioned functions could call `encrypt_field` and `decrypt_field`
internally (passing the raw key bytes extracted from the ring), reducing the duplication surface
from ~90 lines to ~20.

The current duplication means that any future change to the encryption routine (e.g., a different
AAD format, a different base64 encoding) must be applied in two places. The AAD construction
`format!("{}:{}", model, field)` at line 161 and line 221 is identical to the same expression in
`lib.rs` — if the AAD format ever changes, both locations must be updated in sync.

**Impact:** Maintenance risk. Divergent AAD formats between the versioned and unversioned paths
would silently break cross-path interoperability.

**Recommended fix direction:** Extract the AES-256-GCM encrypt/decrypt logic into a private
`aes_encrypt_raw` / `aes_decrypt_raw` helper that both `encrypt_field` and `encrypt_versioned` call.

---

### M4 — Test count discrepancy between the story completion note and the test status document

**Files:** `docs/STORIES/US006.md:133` and `docs/TESTS/US006-TEST-STATUS.md:7`

The story completion notes state "Tests: 49/49 passing — 36 unit, 4 property-based (proptest), 9
doctests" and the completion verification section on line 151 states "40 automated tests passing (36
unit + 4 property-based)". The test status document header also states "Coverage: Full (40/40 unit +
property tests, 9/9 doctests)" matching 49 total.

However, the `key_versioning_tests.rs` file was added under US076 (according to its own module
docstring: "US076 — Red phase: key versioning tests") and is NOT listed in the test status
document's "Test Files" table, which only references `crypto_tests.rs`. The key_versioning tests
currently exist in the repository on the `us009/syntek-auth` branch. If they were also present
during the US006 green phase, the 49-test count is inaccurate (too low or the counts are mixed
across stories). If they were not present, the file has been retroactively included from US076
without updating the US006 test status, creating a false impression of US006 test scope.

**Impact:** Traceability failure. Auditors and reviewers cannot determine whether the key versioning
tests belong to US006 or US076 based on the current documentation. The `key_versioning_tests.rs`
file's own docstring explicitly attributes it to US076, not US006.

**Recommended fix direction:** Confirm which story owns `key_versioning_tests.rs` and
`src/key_versioning.rs`. If US076, remove them from US006's test count and update the story
completion notes accordingly.

---

### M5 — `deny.toml` uses `unmaintained = "all"` which may cause spurious CI failures

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/deny.toml:5`

The `deny.toml` advisory policy sets `unmaintained = "all"`, meaning any transitive dependency
flagged as unmaintained by the RustSec advisory database will fail `cargo deny check`. Several
dependencies in the crypto chain (particularly older HMAC/SHA2 crates) have a history of being
flagged as superseded. This is a strict policy that may block CI when an upstream crate is marked
unmaintained for reasons unrelated to security (e.g., maintenance transferred to a new crate name).

**Impact:** CI instability. A well-intentioned strict policy can prevent legitimate deployments when
the advisory database adds an unmaintained advisory for a transitive dep that has no security
vulnerability.

**Recommended fix direction:** Consider narrowing `unmaintained` to `"workspace"` or adding specific
`[advisories] ignore` entries for known false positives, whilst keeping `yanked = "deny"` strict.

---

### M6 — `examples/` directory is empty — example files from manual testing were cleaned up but the directory was committed

**File:** `rust/syntek-crypto/examples/`

The manual testing guide instructs testers to create temporary example binaries in
`rust/syntek-crypto/examples/` and then delete them. The directory itself was committed to the
repository (it appears in the file tree) but contains no files. An empty committed directory
provides no value and could confuse contributors who look for runnable examples. The story tasks
mention building CLI binaries but no persistent examples exist.

**Impact:** Minor confusion. No security or functional impact.

**Recommended fix direction:** Either add a `.gitkeep` with a comment explaining the directory is
for temporary manual-testing examples (not to be committed), or remove the empty directory entirely.

---

## 4. LOW / Observations

### L1 — `CryptoError` variants do not implement `PartialEq`, preventing pattern-matching in test assertions without `matches!`

**File:** `rust/syntek-crypto/src/lib.rs:44–65`

The `CryptoError` enum derives `Debug` and uses `thiserror::Error` but does not derive `PartialEq`.
Tests are forced to use `match result.unwrap_err()` pattern-matching blocks (which they do
correctly), but the absence of `PartialEq` means
`assert_eq!(err, CryptoError::DecryptionError("..."))` is not possible. This is a minor ergonomics
issue for test authors and for consumers who want to compare errors programmatically.

**Recommended fix direction:** Add `#[derive(PartialEq)]` to `CryptoError` if the string contents of
variants are not required for equality (or implement `PartialEq` manually to compare on variant
discriminant only).

---

### L2 — `KeyVersion(0)` is documented as reserved but is not enforced

**File:** `rust/syntek-crypto/src/key_versioning.rs:29–31`

The doc comment states "Version 0 is reserved; valid versioned keys start at 1." However,
`KeyRing::add` accepts `KeyVersion(0)` without error. A consumer who accidentally inserts a
version-0 key (for example, from a zero-initialised struct) would produce ciphertexts with a
`0x00 0x00` prefix that are indistinguishable from a blob with a zero version, which may conflict
with any future use of version 0 as a sentinel or format discriminator.

**Recommended fix direction:** Add a guard in `KeyRing::add` that rejects `KeyVersion(0)` with
`CryptoError::InvalidInput`.

---

### L3 — `hmac_sign` and `hmac_verify` doc comments do not document the key length expectation

**File:** `rust/syntek-crypto/src/lib.rs:256–313`

HMAC-SHA256 accepts keys of any length (per RFC 2104: keys longer than the block size are hashed,
shorter keys are zero-padded). The public API docs for `hmac_sign` and `hmac_verify` do not document
the expected key length or the implications of short/empty keys. Consumers integrating webhook
verification may use keys of varying lengths without understanding the security implications.

**Recommended fix direction:** Add a note to the doc comments stating the recommended minimum key
length (at least 32 bytes / 256 bits for HMAC-SHA256) and that empty keys are accepted by the
underlying library but provide no security.

---

<!-- markdownlint-disable MD013 -->

### L4 — The `prop_encrypt_decrypt_roundtrip_arbitrary_plaintext` property test uses `".*"` regex which excludes surrogate pairs and some non-UTF-8 boundary cases

<!-- markdownlint-enable MD013 -->

**File:** `rust/syntek-crypto/tests/crypto_tests.rs:583`

The proptest strategy `".*"` generates arbitrary Rust `String` values (which are always valid
UTF-8). This is appropriate for the API. However, it does not test very large plaintexts (e.g.,
multi-megabyte strings) that could expose performance issues or memory allocation failures in the
AES-GCM path. The current strategy defaults to proptest's default string size limit.

**Recommended fix direction:** Add a second property-based test variant with
`prop::string::string_regex("[\\s\\S]{0, 1048576}")` or similar to test large payloads, and verify
that the function returns an error gracefully rather than panicking on allocation failure.

---

<!-- markdownlint-disable MD013 -->

### L5 — Test fixture `TEST_KEY = [0u8; 32]` (all-zero key) is used throughout but never guarded against accidental production use

<!-- markdownlint-enable MD013 -->

**File:** `rust/syntek-crypto/tests/crypto_tests.rs:22`

The all-zero 32-byte test key is a well-known weak test vector. The constant is adequately commented
("A real key must be generated from a CSPRNG; this constant is test-only"). However, if test code is
ever accidentally imported or copied into application code (a common mistake in rapid-development
scenarios), the all-zero key will be silently used. The library itself has no protection against
weak keys — it cannot distinguish a CSPRNG key from a zero key.

**Impact:** No impact within the test file. Risk exists at the consumer level if test vectors are
accidentally copied into application settings.

**Recommended fix direction:** No action required within this crate. Document in `syntek-pyo3` and
the Django binding layer that keys must be validated as non-zero and non-repeating before use.

---

## 5. Missing Test Scenarios

The following scenarios are absent from both the automated test suite and the manual testing guide.
They represent meaningful gaps relative to the AC surface and the deployment threat model.

| #    | Scenario                                                                                                                         | Priority | Rationale                                                                      |
| ---- | -------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------ |
| MT1  | `KeyRing::add` called twice with the same `KeyVersion` — verify the second call returns an error                                 | Critical | Duplicate version insertion is silently accepted (see C2)                      |
| MT2  | `decrypt_fields_batch` called with a 16-byte key — verify `InvalidInput` is returned (not `BatchError`)                          | Critical | Asymmetric error semantics vs. encrypt path (see C1)                           |
| MT3  | `reencrypt_to_active` called during concurrent goroutine-style stress — verify no plaintext residue                              | High     | Intermediate `String` plaintext is not zeroised (see H1)                       |
| MT4  | `hmac_sign` and `hmac_verify` called with `b""` (empty key) — verify an error or `false` is returned                             | High     | Silent success with empty HMAC key (see H2)                                    |
| MT5  | `hmac_verify` called with the correct digest but in uppercase — verify behaviour (should be documented)                          | Medium   | Case sensitivity not documented or tested (see M2)                             |
| MT6  | `KeyRing::add` called with `KeyVersion(0)` — verify `InvalidInput` is returned                                                   | Low      | Reserved version not enforced (see L2)                                         |
| MT7  | `encrypt_versioned` / `decrypt_versioned` called with a very long plaintext (>1 MB) — verify no panic or allocation failure      | Low      | No large-payload tests exist for the versioned path                            |
| MT8  | `reencrypt_to_active` called with a ciphertext whose version prefix decodes to `KeyVersion(0)` — verify it is handled gracefully | Medium   | Zero-version sentinel not guarded in the versioned decrypt path                |
| MT9  | `encrypt_fields_batch` called with 1,000 fields — verify ordering and atomicity are preserved at scale                           | Medium   | No batch scale test exists; ordering and atomicity only tested with 2–3 fields |
| MT10 | `decrypt_versioned` called with a blob exactly 30 bytes (minimum) — verify it succeeds or fails cleanly rather than panicking    | Medium   | Boundary condition at the minimum-length guard `blob.len() < 30`               |
| MT11 | `KeyRing::active()` with multiple entries sharing the same version number (post-duplicate-add) — verify deterministic result     | Critical | Non-deterministic active-key selection when duplicates exist (see C2)          |

---

## Handoff Signals

- Run `/syntek-dev-suite:backend` to address C1 (key-length guard in `decrypt_fields_batch`), C2
  (duplicate-version guard in `KeyRing::add`), H1 (zeroize intermediate in `reencrypt_to_active`),
  H2 (empty-key guard in `hmac_sign`/`hmac_verify`), and H3 (create `syntek.manifest.toml`).
- Run `/syntek-dev-suite:test-writer` to add the missing test scenarios MT1–MT11 listed above.
- Run `/syntek-dev-suite:completion` to correct the US006 completion notes regarding the test count
  discrepancy (M4) and the absent `syntek.manifest.toml` (H3).
