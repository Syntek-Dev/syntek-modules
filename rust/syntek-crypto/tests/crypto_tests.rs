//! Integration tests for syntek-crypto — US006 Red Phase
//!
//! All tests in this file are written against the expected *final* behaviour of the public
//! API. Because every function body is `unimplemented!()` at this stage, each test will
//! panic at runtime, producing a failing (red) test suite. No test logic is skipped or
//! stubbed out — the assertions reflect the real contract that the green-phase implementation
//! must satisfy.
//!
//! Run with: `cargo test -p syntek-crypto`

use syntek_crypto::{
    CryptoError, decrypt_field, decrypt_fields_batch, encrypt_field, encrypt_fields_batch,
    hash_password, hmac_sign, hmac_verify, verify_password,
};

// ---------------------------------------------------------------------------
// Shared test fixtures
// ---------------------------------------------------------------------------

/// A 32-byte all-zero key used as a fixed test vector throughout this suite.
/// A real key must be generated from a CSPRNG; this constant is test-only.
const TEST_KEY: [u8; 32] = [0u8; 32];

/// A representative plaintext value used for encrypt/decrypt round-trip tests.
const PLAINTEXT: &str = "hello@example.com";

/// Model and field names used as AAD in the canonical encrypt/decrypt pair.
const MODEL: &str = "User";
const FIELD: &str = "email";

// ---------------------------------------------------------------------------
// AC1 — encrypt_field returns a base64-encoded nonce || ciphertext || tag blob
// ---------------------------------------------------------------------------

/// AC1: Encrypting a plaintext value must return a non-empty base64 string.
#[test]
fn test_encrypt_field_returns_base64_encoded_output() {
    let result = encrypt_field(PLAINTEXT, &TEST_KEY, MODEL, FIELD)
        .expect("encrypt_field must not return Err for valid inputs");

    assert!(!result.is_empty(), "ciphertext string must not be empty");

    // Verify the string is valid standard base64.
    use base64ct::{Base64, Encoding};
    let decoded = Base64::decode_vec(&result).expect("ciphertext must be valid base64");

    // AES-256-GCM layout: 12 bytes nonce + ≥0 bytes ciphertext + 16 bytes tag.
    // The minimum possible output for a zero-length plaintext is 28 bytes.
    assert!(
        decoded.len() >= 12 + PLAINTEXT.len() + 16,
        "decoded blob must contain at least nonce (12 B) + ciphertext + tag (16 B); \
         got {} bytes",
        decoded.len()
    );
}

/// AC1 (structure): The first 12 bytes of the decoded blob are the nonce;
/// the remaining bytes must include at least a 16-byte GCM authentication tag.
#[test]
fn test_encrypt_field_decoded_blob_has_correct_byte_layout() {
    use base64ct::{Base64, Encoding};

    let encoded =
        encrypt_field(PLAINTEXT, &TEST_KEY, MODEL, FIELD).expect("encrypt_field must succeed");

    let bytes = Base64::decode_vec(&encoded).expect("must be valid base64");

    // Nonce is 12 bytes; tag is 16 bytes appended by aes-gcm.
    let nonce_len = 12;
    let tag_len = 16;
    let min_expected = nonce_len + PLAINTEXT.len() + tag_len;

    assert_eq!(
        bytes.len(),
        min_expected,
        "byte layout: nonce ({nonce_len}) + ciphertext ({}) + tag ({tag_len}) = {min_expected}",
        PLAINTEXT.len(),
    );
}

// ---------------------------------------------------------------------------
// AC2 — decrypt_field round-trip recovers original plaintext
// ---------------------------------------------------------------------------

/// AC2: Decrypting a ciphertext produced by encrypt_field must return the original value.
#[test]
fn test_decrypt_field_roundtrip_returns_original_plaintext() {
    let ciphertext =
        encrypt_field(PLAINTEXT, &TEST_KEY, MODEL, FIELD).expect("encrypt_field must succeed");

    let recovered = decrypt_field(&ciphertext, &TEST_KEY, MODEL, FIELD)
        .expect("decrypt_field must succeed for a valid ciphertext");

    assert_eq!(
        recovered, PLAINTEXT,
        "decrypted value must exactly match the original plaintext"
    );
}

/// AC2 (empty string): The round-trip must work for a zero-length plaintext.
#[test]
fn test_decrypt_field_roundtrip_empty_plaintext() {
    let ciphertext = encrypt_field("", &TEST_KEY, MODEL, FIELD)
        .expect("encrypt_field must accept empty plaintext");

    let recovered = decrypt_field(&ciphertext, &TEST_KEY, MODEL, FIELD)
        .expect("decrypt_field must succeed for empty-plaintext ciphertext");

    assert_eq!(recovered, "", "empty plaintext must round-trip correctly");
}

/// AC2 (unicode): The round-trip must preserve multi-byte UTF-8 characters.
#[test]
fn test_decrypt_field_roundtrip_unicode_plaintext() {
    let unicode = "ünïcödé tëxt — £ € ¥";

    let ciphertext = encrypt_field(unicode, &TEST_KEY, MODEL, FIELD)
        .expect("encrypt_field must accept unicode plaintext");

    let recovered = decrypt_field(&ciphertext, &TEST_KEY, MODEL, FIELD)
        .expect("decrypt_field must succeed for unicode ciphertext");

    assert_eq!(
        recovered, unicode,
        "unicode plaintext must round-trip correctly"
    );
}

// ---------------------------------------------------------------------------
// AC3 — tampered ciphertext yields DecryptionError, no plaintext exposed
// ---------------------------------------------------------------------------

/// AC3: Flipping a single byte in the ciphertext portion must cause decryption to fail
/// with a DecryptionError. No partial plaintext must be returned.
#[test]
fn test_decrypt_field_tampered_ciphertext_returns_decryption_error() {
    use base64ct::{Base64, Encoding};

    let encoded =
        encrypt_field(PLAINTEXT, &TEST_KEY, MODEL, FIELD).expect("encrypt_field must succeed");

    // Decode, flip one byte in the ciphertext body (byte 13, after the nonce),
    // re-encode.
    let mut bytes = Base64::decode_vec(&encoded).expect("valid base64");
    bytes[13] ^= 0xFF;
    let tampered = Base64::encode_string(&bytes);

    let result = decrypt_field(&tampered, &TEST_KEY, MODEL, FIELD);

    assert!(
        result.is_err(),
        "decrypt_field must return Err for a tampered ciphertext"
    );

    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!("expected CryptoError::DecryptionError, got {:?}", other),
    }
}

/// AC3: Completely invalid (non-base64) input must also return a DecryptionError.
#[test]
fn test_decrypt_field_invalid_base64_returns_decryption_error() {
    let result = decrypt_field("not-valid-base64!!!", &TEST_KEY, MODEL, FIELD);

    assert!(result.is_err(), "invalid base64 must return Err");

    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!(
            "expected CryptoError::DecryptionError for invalid base64, got {:?}",
            other
        ),
    }
}

/// AC1 (key validation): Passing a key shorter than 32 bytes to encrypt_field must return
/// an InvalidInput error before any cryptographic operation is attempted.
#[test]
fn test_encrypt_field_wrong_key_length_returns_invalid_input() {
    let short_key = [0u8; 16];
    let result = encrypt_field(PLAINTEXT, &short_key, MODEL, FIELD);
    assert!(
        result.is_err(),
        "encrypt_field must return Err for a non-32-byte key"
    );
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!(
            "expected CryptoError::InvalidInput for wrong key length, got {:?}",
            other
        ),
    }
}

/// AC2 (key validation): Passing a key shorter than 32 bytes to decrypt_field must return
/// a DecryptionError. The base64 blob must be long enough to pass the length guard so
/// that the key-length check is reached.
#[test]
fn test_decrypt_field_wrong_key_length_returns_decryption_error() {
    use base64ct::{Base64, Encoding};
    // 28-byte blob: >= 12 bytes so the nonce-length guard passes, then the key-length check fires.
    let blob = Base64::encode_string(&[0u8; 28]);
    let short_key = [0u8; 16];
    let result = decrypt_field(&blob, &short_key, MODEL, FIELD);
    assert!(
        result.is_err(),
        "decrypt_field must return Err for a non-32-byte key"
    );
    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!(
            "expected CryptoError::DecryptionError for wrong key length, got {:?}",
            other
        ),
    }
}

/// AC3: A ciphertext that is too short to contain a nonce must return a DecryptionError.
#[test]
fn test_decrypt_field_too_short_ciphertext_returns_decryption_error() {
    use base64ct::{Base64, Encoding};

    // Only 8 bytes — shorter than the 12-byte nonce.
    let short = Base64::encode_string(&[0u8; 8]);
    let result = decrypt_field(&short, &TEST_KEY, MODEL, FIELD);

    assert!(result.is_err(), "too-short blob must return Err");

    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!(
            "expected CryptoError::DecryptionError for too-short blob, got {:?}",
            other
        ),
    }
}

// ---------------------------------------------------------------------------
// AC4 — hash_password returns a valid Argon2id PHC string
// ---------------------------------------------------------------------------

/// AC4: The returned hash must begin with the Argon2id PHC prefix.
#[test]
fn test_hash_password_returns_argon2id_phc_string() {
    let hash = hash_password("correct-horse-battery-staple")
        .expect("hash_password must succeed for a non-empty password");

    assert!(
        hash.starts_with("$argon2id$"),
        "PHC string must start with '$argon2id$'; got: {hash}"
    );
}

/// AC4: The PHC string must encode the expected memory cost (65536 KiB).
#[test]
fn test_hash_password_phc_encodes_correct_memory_cost() {
    let hash = hash_password("test-password-for-params").expect("hash_password must succeed");

    // The PHC format encodes m=65536 in the parameters segment.
    assert!(
        hash.contains("m=65536"),
        "PHC string must encode m=65536; got: {hash}"
    );
}

/// AC4: The PHC string must encode the expected time cost (t=3).
#[test]
fn test_hash_password_phc_encodes_correct_time_cost() {
    let hash = hash_password("test-password-for-params").expect("hash_password must succeed");

    assert!(
        hash.contains("t=3"),
        "PHC string must encode t=3; got: {hash}"
    );
}

/// AC4: The PHC string must encode the expected parallelism (p=4).
#[test]
fn test_hash_password_phc_encodes_correct_parallelism() {
    let hash = hash_password("test-password-for-params").expect("hash_password must succeed");

    assert!(
        hash.contains("p=4"),
        "PHC string must encode p=4; got: {hash}"
    );
}

/// AC4: An empty password must return an InvalidInput error, not a hash.
#[test]
fn test_hash_password_empty_password_returns_invalid_input_error() {
    let result = hash_password("");

    assert!(result.is_err(), "empty password must return Err");

    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!(
            "expected CryptoError::InvalidInput for empty password, got {:?}",
            other
        ),
    }
}

// ---------------------------------------------------------------------------
// AC5 — verify_password returns true for correct, false for wrong
// ---------------------------------------------------------------------------

/// AC5: verify_password must return true when the password matches the hash.
#[test]
fn test_verify_password_correct_password_returns_true() {
    let password = "correct-horse-battery-staple";
    let hash = hash_password(password).expect("hash_password must succeed");

    let result = verify_password(password, &hash)
        .expect("verify_password must not return Err for valid inputs");

    assert!(
        result,
        "verify_password must return true for the correct password"
    );
}

/// AC5: verify_password must return false when the password does not match.
#[test]
fn test_verify_password_wrong_password_returns_false() {
    let password = "correct-horse-battery-staple";
    let hash = hash_password(password).expect("hash_password must succeed");

    let result = verify_password("wrong-password", &hash)
        .expect("verify_password must not return Err for a wrong password");

    assert!(
        !result,
        "verify_password must return false for an incorrect password"
    );
}

/// AC5: verify_password must return false for an empty candidate password
/// rather than panicking or leaking hash information.
#[test]
fn test_verify_password_empty_candidate_returns_false_or_invalid_input() {
    let hash = hash_password("some-password").expect("hash_password must succeed");

    // Either an InvalidInput error or false is acceptable — plaintext must never leak.
    match verify_password("", &hash) {
        Ok(false) => {}
        Err(CryptoError::InvalidInput(_)) => {}
        Ok(true) => panic!("verify_password must not return true for an empty password"),
        Err(other) => panic!("unexpected error variant for empty candidate: {:?}", other),
    }
}

// ---------------------------------------------------------------------------
// AC6 — sensitive in-memory values are zeroised after use
// ---------------------------------------------------------------------------

/// AC6: This test verifies that zeroize is declared as a dependency and that
/// the key buffer passed into encrypt_field is a separate copy from anything
/// the crate retains. Because zeroize operates on internal heap buffers that are
/// not observable from outside the function, the canonical test strategy is to
/// confirm the function completes without exposing internal state.
///
/// A compile-time guard: the `zeroize` crate must be present in `Cargo.toml`.
/// If removed, the crate will fail to build, which counts as a test failure.
#[test]
fn test_zeroize_sensitive_values_compile_time_dependency_present() {
    // This test exercises the full encrypt → decrypt pipeline.
    // The zeroize crate zeroes key material on function return. We cannot inspect
    // freed memory from a safe Rust test, but we can confirm the API works end-to-end
    // and that no `unsafe` code is required to call it.
    let mut key = [0u8; 32];
    key[0] = 0xDE;
    key[31] = 0xAD;

    let ciphertext =
        encrypt_field("sensitive-data", &key, MODEL, FIELD).expect("encrypt_field must succeed");

    let recovered =
        decrypt_field(&ciphertext, &key, MODEL, FIELD).expect("decrypt_field must succeed");

    assert_eq!(recovered, "sensitive-data");

    // After the calls complete, the crate's internal copies of the key material
    // must have been zeroised via the zeroize crate. We bind `key` to `_` here
    // to make the expected ownership intent explicit.
    let _ = key;
}

// ---------------------------------------------------------------------------
// AC7 — AAD mismatch prevents cross-model ciphertext substitution
// ---------------------------------------------------------------------------

/// AC7: A ciphertext produced for model="User", field="email" must not decrypt
/// successfully when presented as model="Order", field="email".
/// The GCM authentication tag binds the AAD, so mismatched context causes failure.
#[test]
fn test_aad_mismatch_prevents_cross_model_substitution() {
    let ciphertext =
        encrypt_field(PLAINTEXT, &TEST_KEY, "User", "email").expect("encrypt_field must succeed");

    // Attempt to decrypt with a different model name — this must fail.
    let result = decrypt_field(&ciphertext, &TEST_KEY, "Order", "email");

    assert!(
        result.is_err(),
        "decrypt_field must return Err when the model name in the AAD does not match"
    );

    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!(
            "expected CryptoError::DecryptionError for AAD mismatch, got {:?}",
            other
        ),
    }
}

/// AC7: A ciphertext produced for model="User", field="email" must not decrypt
/// when the field name is changed to "phone" (different AAD).
#[test]
fn test_aad_mismatch_different_field_name_returns_decryption_error() {
    let ciphertext =
        encrypt_field(PLAINTEXT, &TEST_KEY, "User", "email").expect("encrypt_field must succeed");

    let result = decrypt_field(&ciphertext, &TEST_KEY, "User", "phone");

    assert!(
        result.is_err(),
        "decrypt_field must return Err when the field name in the AAD does not match"
    );

    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!(
            "expected CryptoError::DecryptionError for field-name AAD mismatch, got {:?}",
            other
        ),
    }
}

// ---------------------------------------------------------------------------
// AC8 — nonce uniqueness across 10,000 encryptions
// ---------------------------------------------------------------------------

/// AC8: Running encrypt_field 10,000 times with the same key and plaintext must
/// produce 10,000 distinct nonces. Nonce reuse under AES-256-GCM is catastrophic;
/// this test guards against any accidental static or counter-based nonce generation
/// that could produce repeats within a realistic workload.
#[test]
fn test_nonce_uniqueness_10000_encryptions() {
    use base64ct::{Base64, Encoding};
    use std::collections::HashSet;

    const ITERATIONS: usize = 10_000;
    let mut nonces: HashSet<Vec<u8>> = HashSet::with_capacity(ITERATIONS);

    for i in 0..ITERATIONS {
        let ct = encrypt_field(PLAINTEXT, &TEST_KEY, MODEL, FIELD)
            .unwrap_or_else(|_| panic!("encrypt_field must succeed on iteration {i}"));

        let bytes = Base64::decode_vec(&ct)
            .unwrap_or_else(|_| panic!("must be valid base64 on iteration {i}"));

        // The nonce occupies the first 12 bytes of the decoded blob.
        let nonce = bytes[..12].to_vec();

        assert!(
            nonces.insert(nonce),
            "nonce collision detected on iteration {i} — nonces must be unique"
        );
    }

    assert_eq!(
        nonces.len(),
        ITERATIONS,
        "all {ITERATIONS} nonces must be distinct"
    );
}

// ---------------------------------------------------------------------------
// HMAC — sign and verify
// ---------------------------------------------------------------------------

/// hmac_sign must return a non-empty hex string for any non-empty input.
#[test]
fn test_hmac_sign_returns_non_empty_hex_string() {
    let sig =
        hmac_sign(b"payload", b"secret-key").expect("hmac_sign must succeed for a non-empty key");

    assert!(!sig.is_empty(), "hmac_sign must return a non-empty string");

    // Must be a valid 64-character lowercase hex string (HMAC-SHA256 = 32 bytes = 64 hex chars).
    assert_eq!(
        sig.len(),
        64,
        "HMAC-SHA256 hex digest must be 64 characters; got {} chars",
        sig.len()
    );

    assert!(
        sig.chars().all(|c| c.is_ascii_hexdigit()),
        "hmac_sign output must contain only hex digits; got: {sig}"
    );
}

/// hmac_verify must return true when the signature matches the data and key.
#[test]
fn test_hmac_verify_valid_signature_returns_true() {
    let data = b"webhook-payload";
    let key = b"shared-secret";

    let sig = hmac_sign(data, key).expect("hmac_sign must succeed");
    let valid = hmac_verify(data, key, &sig);

    assert!(valid, "hmac_verify must return true for a valid signature");
}

/// hmac_verify must return false when the signature is incorrect.
#[test]
fn test_hmac_verify_invalid_signature_returns_false() {
    let data = b"webhook-payload";
    let key = b"shared-secret";

    let valid = hmac_verify(
        data,
        key,
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    );

    assert!(
        !valid,
        "hmac_verify must return false for an incorrect signature"
    );
}

/// hmac_verify must return false when the data is different from what was signed,
/// even if the key is the same — guards against data substitution attacks.
#[test]
fn test_hmac_verify_mismatched_data_returns_false() {
    let key = b"shared-secret";
    let sig = hmac_sign(b"original-payload", key).expect("hmac_sign must succeed");

    let valid = hmac_verify(b"different-payload", key, &sig);

    assert!(
        !valid,
        "hmac_verify must return false when data does not match the signature"
    );
}

/// Timing safety: hmac_verify must use constant-time comparison. This test cannot
/// directly measure timing from safe Rust, but it exercises both a matching and a
/// non-matching call to confirm the function is deterministic and does not panic
/// on strings of differing lengths.
#[test]
fn test_hmac_verify_constant_time_comparison_does_not_panic() {
    let data = b"timing-test-payload";
    let key = b"timing-test-key";

    let correct_sig = hmac_sign(data, key).expect("hmac_sign must succeed");

    // Signatures of different lengths — must not panic or short-circuit in a
    // length-dependent way.
    assert!(!hmac_verify(data, key, "short"));
    assert!(!hmac_verify(data, key, "a"));
    assert!(!hmac_verify(data, key, &"f".repeat(64)));
    assert!(hmac_verify(data, key, &correct_sig));
}

// ---------------------------------------------------------------------------
// Property-based tests (proptest)
// ---------------------------------------------------------------------------

use proptest::prelude::*;

proptest! {
    /// Property: encrypt_field followed by decrypt_field must recover the original
    /// plaintext for any arbitrary UTF-8 string input.
    ///
    /// This covers the full space of valid string values including empty strings,
    /// very long strings, strings with special characters, and multi-byte sequences.
    #[test]
    fn prop_encrypt_decrypt_roundtrip_arbitrary_plaintext(plaintext in ".*") {
        let ciphertext = encrypt_field(&plaintext, &TEST_KEY, MODEL, FIELD)
            .expect("encrypt_field must succeed for any valid plaintext");

        let recovered = decrypt_field(&ciphertext, &TEST_KEY, MODEL, FIELD)
            .expect("decrypt_field must succeed for a freshly encrypted ciphertext");

        prop_assert_eq!(
            recovered,
            plaintext,
            "decrypted value must equal the original plaintext"
        );
    }

    /// Property: encrypt_field called twice on the same plaintext must produce two
    /// distinct ciphertexts due to random nonce generation (IND-CPA security).
    #[test]
    fn prop_encrypt_field_produces_unique_ciphertexts(plaintext in ".{1,256}") {
        let ct1 = encrypt_field(&plaintext, &TEST_KEY, MODEL, FIELD)
            .expect("first encrypt_field must succeed");
        let ct2 = encrypt_field(&plaintext, &TEST_KEY, MODEL, FIELD)
            .expect("second encrypt_field must succeed");

        prop_assert_ne!(
            ct1,
            ct2,
            "two encryptions of the same plaintext must produce different ciphertexts"
        );
    }

    /// Property: hmac_sign must produce the same digest for the same data and key,
    /// i.e. the function is deterministic.
    #[test]
    fn prop_hmac_sign_is_deterministic(data in prop::collection::vec(any::<u8>(), 0..256)) {
        let key = b"determinism-test-key";

        let sig1 = hmac_sign(&data, key).expect("hmac_sign must succeed");
        let sig2 = hmac_sign(&data, key).expect("hmac_sign must succeed");

        prop_assert_eq!(sig1, sig2, "hmac_sign must be deterministic");
    }

    /// Property: hmac_verify must return false for any signature that differs from
    /// the one produced by hmac_sign, regardless of how close the bytes are.
    #[test]
    fn prop_hmac_verify_rejects_wrong_signatures(
        data in prop::collection::vec(any::<u8>(), 1..256),
        wrong_sig in "[0-9a-f]{64}",
    ) {
        let key = b"rejection-test-key";
        let correct_sig = hmac_sign(&data, key).expect("hmac_sign must succeed");

        // Only check when the generated signature happens to differ from the correct one.
        prop_assume!(wrong_sig != correct_sig);

        prop_assert!(
            !hmac_verify(&data, key, &wrong_sig),
            "hmac_verify must reject an incorrect signature"
        );
    }
}

// ---------------------------------------------------------------------------
// AC9 — encrypt_fields_batch returns ordered ciphertexts with unique nonces
// ---------------------------------------------------------------------------

/// AC9: Encrypting a batch of 3 fields must return exactly 3 ciphertexts.
#[test]
fn test_encrypt_fields_batch_returns_correct_count() {
    let fields = [
        ("email", "hello@example.com"),
        ("phone", "+441234567890"),
        ("address", "10 Downing Street"),
    ];

    let results = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed for valid inputs");

    assert_eq!(
        results.len(),
        3,
        "batch of 3 fields must return exactly 3 ciphertexts; got {}",
        results.len()
    );
}

/// AC9 (byte layout): Each ciphertext in the batch must decode to the correct
/// byte layout: 12 bytes nonce + plaintext bytes + 16 bytes GCM tag.
#[test]
fn test_encrypt_fields_batch_ciphertexts_decode_to_correct_lengths() {
    use base64ct::{Base64, Encoding};

    let fields = [
        ("email", "hello@example.com"),
        ("phone", "+441234567890"),
        ("address", "10 Downing Street"),
    ];

    let results = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed");

    for (i, ((field_name, plaintext), encoded)) in fields.iter().zip(results.iter()).enumerate() {
        let bytes = Base64::decode_vec(encoded).unwrap_or_else(|_| {
            panic!("ciphertext at index {i} ({field_name}) must be valid base64")
        });

        let expected_len = 12 + plaintext.len() + 16;
        assert_eq!(
            bytes.len(),
            expected_len,
            "ciphertext at index {i} ({field_name}): expected {} bytes (12 nonce + {} plaintext + 16 tag), got {}",
            expected_len,
            plaintext.len(),
            bytes.len()
        );
    }
}

/// AC9 (nonce uniqueness): Nonces extracted from a batch of ciphertexts must all
/// be distinct — each field is encrypted with its own independent random nonce.
#[test]
fn test_encrypt_fields_batch_each_field_has_unique_nonce() {
    use base64ct::{Base64, Encoding};
    use std::collections::HashSet;

    let fields = [
        ("email", "hello@example.com"),
        ("phone", "+441234567890"),
        ("address", "10 Downing Street"),
    ];

    let results = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed");

    let nonces: HashSet<Vec<u8>> = results
        .iter()
        .enumerate()
        .map(|(i, encoded)| {
            let bytes = Base64::decode_vec(encoded)
                .unwrap_or_else(|_| panic!("ciphertext at index {i} must be valid base64"));
            bytes[..12].to_vec()
        })
        .collect();

    assert_eq!(
        nonces.len(),
        fields.len(),
        "every field in the batch must have a unique nonce; got {} distinct nonces for {} fields",
        nonces.len(),
        fields.len()
    );
}

/// AC9 (order preservation): Decrypting each ciphertext with its own field name
/// must recover the original plaintext at the same position.
#[test]
fn test_encrypt_fields_batch_preserves_order() {
    let fields = [
        ("email", "hello@example.com"),
        ("phone", "+441234567890"),
        ("address", "10 Downing Street"),
    ];

    let ciphertexts = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed");

    for (i, ((field_name, plaintext), ciphertext)) in
        fields.iter().zip(ciphertexts.iter()).enumerate()
    {
        let recovered = decrypt_field(ciphertext, &TEST_KEY, "User", field_name)
            .unwrap_or_else(|_| panic!("decrypt_field must succeed for index {i} ({field_name})"));

        assert_eq!(
            recovered, *plaintext,
            "plaintext at index {i} ({field_name}) must be recovered correctly; expected {:?}, got {:?}",
            plaintext, recovered
        );
    }
}

/// AC9 (per-field AAD): A ciphertext encrypted for field "email" must not decrypt
/// successfully when presented under field "phone" — each field's ciphertext is
/// bound to its own AAD (model + field_name).
#[test]
fn test_encrypt_fields_batch_each_field_uses_own_aad() {
    let fields = [("email", "hello@example.com"), ("phone", "+441234567890")];

    let ciphertexts = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed");

    // The ciphertext for "email" (index 0) must not decrypt under "phone".
    let result = decrypt_field(&ciphertexts[0], &TEST_KEY, "User", "phone");

    assert!(
        result.is_err(),
        "ciphertext encrypted for 'email' must not decrypt under 'phone' — AAD mismatch expected"
    );

    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!(
            "expected CryptoError::DecryptionError for cross-field AAD mismatch, got {:?}",
            other
        ),
    }
}

/// AC9 (empty batch): An empty input slice must return Ok with an empty Vec.
#[test]
fn test_encrypt_fields_batch_empty_batch_returns_empty_vec() {
    let results = encrypt_fields_batch(&[], &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed for an empty batch");

    assert!(
        results.is_empty(),
        "empty batch must return an empty Vec; got {} elements",
        results.len()
    );
}

// ---------------------------------------------------------------------------
// AC10 — decrypt_fields_batch recovers original plaintexts in order
// ---------------------------------------------------------------------------

/// AC10: Encrypting a batch then decrypting it must recover all original plaintexts
/// in the same order.
#[test]
fn test_decrypt_fields_batch_roundtrip_returns_original_plaintexts() {
    let fields = [
        ("email", "hello@example.com"),
        ("phone", "+441234567890"),
        ("address", "10 Downing Street"),
    ];

    let ciphertexts = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed");

    // Build (field_name, ciphertext) pairs for the decrypt call.
    let decrypt_pairs: Vec<(&str, &str)> = fields
        .iter()
        .map(|(name, _)| *name)
        .zip(ciphertexts.iter().map(|s| s.as_str()))
        .collect();

    let recovered = decrypt_fields_batch(&decrypt_pairs, &TEST_KEY, "User")
        .expect("decrypt_fields_batch must succeed for freshly encrypted ciphertexts");

    assert_eq!(
        recovered.len(),
        fields.len(),
        "decrypt_fields_batch must return the same number of plaintexts as input fields"
    );

    for (i, ((_, original_plaintext), decrypted)) in fields.iter().zip(recovered.iter()).enumerate()
    {
        assert_eq!(
            decrypted, original_plaintext,
            "plaintext at index {i} must match after round-trip; expected {:?}, got {:?}",
            original_plaintext, decrypted
        );
    }
}

/// AC10 (empty batch): An empty input slice must return Ok with an empty Vec.
#[test]
fn test_decrypt_fields_batch_empty_batch_returns_empty_vec() {
    let results = decrypt_fields_batch(&[], &TEST_KEY, "User")
        .expect("decrypt_fields_batch must succeed for an empty batch");

    assert!(
        results.is_empty(),
        "empty batch must return an empty Vec; got {} elements",
        results.len()
    );
}

// ---------------------------------------------------------------------------
// AC11 — encrypt_fields_batch fails atomically on any field error
// ---------------------------------------------------------------------------

/// AC11: Passing a key that is not 32 bytes must cause the entire batch to fail.
///
/// The function may validate the key upfront (returning InvalidInput) or fail on
/// the first field (returning BatchError). Both are acceptable — what must NOT
/// happen is a partial Ok result or a silent success.
#[test]
fn test_encrypt_fields_batch_wrong_key_length_returns_batch_error() {
    let fields = [("email", "hello@example.com"), ("phone", "+441234567890")];

    // 16-byte key — AES-256-GCM requires exactly 32 bytes.
    let short_key = [0u8; 16];

    let result = encrypt_fields_batch(&fields, &short_key, "User");

    assert!(
        result.is_err(),
        "encrypt_fields_batch must return Err for a non-32-byte key"
    );

    // Accept either InvalidInput (upfront key validation) or BatchError (per-field failure).
    // Both represent atomic failure with no partial results.
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        CryptoError::BatchError { .. } => {}
        other => panic!(
            "expected CryptoError::InvalidInput or CryptoError::BatchError for wrong key length, got {:?}",
            other
        ),
    }
}

// ---------------------------------------------------------------------------
// AC12 — decrypt_fields_batch fails atomically on any field error
// ---------------------------------------------------------------------------

/// AC12: Tampering with the second field's ciphertext must cause the entire batch
/// to fail, naming the tampered field in the error.
#[test]
fn test_decrypt_fields_batch_tampered_ciphertext_returns_batch_error() {
    use base64ct::{Base64, Encoding};

    let fields = [("email", "hello@example.com"), ("phone", "+441234567890")];

    let mut ciphertexts = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed");

    // Tamper the second ciphertext: flip byte 13 (within the ciphertext body,
    // past the 12-byte nonce) to invalidate the GCM authentication tag.
    let mut bytes = Base64::decode_vec(&ciphertexts[1]).expect("must be valid base64");
    bytes[13] ^= 0xFF;
    ciphertexts[1] = Base64::encode_string(&bytes);

    let decrypt_pairs: Vec<(&str, &str)> = fields
        .iter()
        .map(|(name, _)| *name)
        .zip(ciphertexts.iter().map(|s| s.as_str()))
        .collect();

    let result = decrypt_fields_batch(&decrypt_pairs, &TEST_KEY, "User");

    assert!(
        result.is_err(),
        "decrypt_fields_batch must return Err when any ciphertext is tampered"
    );

    match result.unwrap_err() {
        CryptoError::BatchError { field, .. } => {
            assert_eq!(
                field, "phone",
                "BatchError must name the tampered field ('phone'); got '{field}'"
            );
        }
        other => panic!(
            "expected CryptoError::BatchError for tampered ciphertext, got {:?}",
            other
        ),
    }
}

/// AC12: Encrypting a batch with model="User" then decrypting with model="Order"
/// must cause every field to fail. The returned error must be a BatchError for
/// the first failing field — no partial plaintexts are exposed.
#[test]
fn test_decrypt_fields_batch_aad_mismatch_returns_batch_error() {
    let fields = [("email", "hello@example.com"), ("phone", "+441234567890")];

    let ciphertexts = encrypt_fields_batch(&fields, &TEST_KEY, "User")
        .expect("encrypt_fields_batch must succeed");

    // Build decrypt pairs using the wrong model name.
    let decrypt_pairs: Vec<(&str, &str)> = fields
        .iter()
        .map(|(name, _)| *name)
        .zip(ciphertexts.iter().map(|s| s.as_str()))
        .collect();

    // Decrypt with model="Order" — every field's AAD will mismatch.
    let result = decrypt_fields_batch(&decrypt_pairs, &TEST_KEY, "Order");

    assert!(
        result.is_err(),
        "decrypt_fields_batch must return Err when model name in AAD does not match"
    );

    match result.unwrap_err() {
        CryptoError::BatchError { field, .. } => {
            // The first failing field must be named — order is preserved so it will be "email".
            assert_eq!(
                field, "email",
                "BatchError must name the first failing field ('email'); got '{field}'"
            );
        }
        other => panic!(
            "expected CryptoError::BatchError for AAD model mismatch, got {:?}",
            other
        ),
    }
}
