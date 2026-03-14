//! US076 — Red phase: key versioning tests for `syntek-crypto`
//!
//! Tests cover:
//! - [`KeyVersion`] byte serialisation round-trip
//! - [`KeyRing`] construction, active key resolution, version lookup
//! - [`encrypt_versioned`] / [`decrypt_versioned`] round-trip
//! - Version prefix present in raw ciphertext blob
//! - Cross-version decryption (ciphertext encrypted under v1 decrypts with a
//!   ring that contains both v1 and v2)
//! - [`reencrypt_to_active`] migrates old ciphertext to current key version
//! - Error cases: empty ring, unknown version, wrong key, tampered ciphertext
//!
//! All tests **fail** during the red phase because the implementation bodies
//! contain `todo!()`.  No test logic is stubbed out — the assertions reflect
//! the real contract that the green-phase implementation must satisfy.
//!
//! Run with: `cargo test -p syntek-crypto`

use syntek_crypto::CryptoError;
use syntek_crypto::key_versioning::{
    KeyRing, KeyVersion, decrypt_fields_batch_versioned, decrypt_versioned,
    encrypt_fields_batch_versioned, encrypt_versioned, reencrypt_to_active,
};

// ---------------------------------------------------------------------------
// Shared fixtures
// ---------------------------------------------------------------------------

const MODEL: &str = "User";
const FIELD: &str = "email";
const PLAINTEXT: &str = "user@example.com";

fn key_v1() -> [u8; 32] {
    [0x01u8; 32]
}

fn key_v2() -> [u8; 32] {
    [0x02u8; 32]
}

fn single_key_ring() -> KeyRing {
    let mut ring = KeyRing::new();
    ring.add(KeyVersion(1), &key_v1())
        .expect("add v1 must succeed");
    ring
}

fn two_key_ring() -> KeyRing {
    let mut ring = KeyRing::new();
    ring.add(KeyVersion(1), &key_v1())
        .expect("add v1 must succeed");
    ring.add(KeyVersion(2), &key_v2())
        .expect("add v2 must succeed");
    ring
}

// ---------------------------------------------------------------------------
// KeyVersion — byte serialisation
// ---------------------------------------------------------------------------

/// KeyVersion(1) must serialise to [0x00, 0x01] (big-endian).
#[test]
fn test_key_version_to_bytes_big_endian() {
    let v = KeyVersion(1);
    assert_eq!(v.to_bytes(), [0x00, 0x01]);
}

/// KeyVersion(256) must serialise to [0x01, 0x00].
#[test]
fn test_key_version_to_bytes_256() {
    let v = KeyVersion(256);
    assert_eq!(v.to_bytes(), [0x01, 0x00]);
}

/// from_bytes round-trip: parsing the bytes produced by to_bytes must return
/// the original version.
#[test]
fn test_key_version_from_bytes_roundtrip() {
    for n in [1u16, 2, 255, 256, 1000, u16::MAX] {
        let v = KeyVersion(n);
        let parsed = KeyVersion::from_bytes(v.to_bytes());
        assert_eq!(
            parsed, v,
            "KeyVersion({n}) round-trip via to_bytes/from_bytes must be lossless"
        );
    }
}

// ---------------------------------------------------------------------------
// KeyRing — construction and active key
// ---------------------------------------------------------------------------

/// A freshly constructed ring is empty.
#[test]
fn test_keyring_new_is_empty() {
    let ring = KeyRing::new();
    assert!(ring.is_empty(), "new KeyRing must be empty");
    assert_eq!(ring.len(), 0, "new KeyRing len must be 0");
}

/// KeyRing::default() must produce an empty ring identical to KeyRing::new().
#[test]
fn test_keyring_default_produces_empty_ring() {
    let ring = KeyRing::default();
    assert!(
        ring.is_empty(),
        "KeyRing::default() must produce an empty ring"
    );
    assert_eq!(ring.len(), 0, "KeyRing::default() len must be 0");
}

/// After adding one key the ring has len 1 and is not empty.
#[test]
fn test_keyring_add_single_key_len_is_one() {
    let ring = single_key_ring();
    assert_eq!(ring.len(), 1, "KeyRing with one entry must have len 1");
    assert!(!ring.is_empty(), "KeyRing with one entry must not be empty");
}

/// The active key of a single-entry ring is that entry.
#[test]
fn test_keyring_active_returns_only_entry() {
    let ring = single_key_ring();
    let (version, key_bytes) = ring
        .active()
        .expect("active must succeed on non-empty ring");
    assert_eq!(version, KeyVersion(1), "active version must be 1");
    assert_eq!(key_bytes, &key_v1(), "active key bytes must match v1");
}

/// The active key of a two-entry ring is the highest version.
#[test]
fn test_keyring_active_returns_highest_version() {
    let ring = two_key_ring();
    let (version, key_bytes) = ring.active().expect("active must succeed");
    assert_eq!(
        version,
        KeyVersion(2),
        "active version must be 2 (highest in ring)"
    );
    assert_eq!(key_bytes, &key_v2(), "active key bytes must match v2");
}

/// active() on an empty ring returns an error.
#[test]
fn test_keyring_active_empty_ring_returns_error() {
    let ring = KeyRing::new();
    let result = ring.active();
    assert!(result.is_err(), "active on empty ring must return Err");
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!("expected CryptoError::InvalidInput, got {:?}", other),
    }
}

/// get() returns the correct key bytes for a known version.
#[test]
fn test_keyring_get_known_version_returns_key_bytes() {
    let ring = two_key_ring();
    let k1 = ring.get(KeyVersion(1)).expect("get v1 must succeed");
    let k2 = ring.get(KeyVersion(2)).expect("get v2 must succeed");
    assert_eq!(k1, &key_v1());
    assert_eq!(k2, &key_v2());
}

/// get() for an unknown version returns an error.
#[test]
fn test_keyring_get_unknown_version_returns_error() {
    let ring = single_key_ring();
    let result = ring.get(KeyVersion(99));
    assert!(
        result.is_err(),
        "get for an unknown version must return Err"
    );
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!("expected CryptoError::InvalidInput, got {:?}", other),
    }
}

/// add() rejects KeyVersion(0) which is reserved.
#[test]
fn test_keyring_add_version_zero_returns_error() {
    let mut ring = KeyRing::new();
    let result = ring.add(KeyVersion(0), &[0xAAu8; 32]);
    assert!(result.is_err(), "KeyVersion(0) must be rejected");
    match result.unwrap_err() {
        CryptoError::InvalidInput(msg) => {
            assert!(
                msg.contains("reserved"),
                "error must mention reserved: {msg}"
            );
        }
        other => panic!("expected CryptoError::InvalidInput, got {:?}", other),
    }
}

/// add() rejects a duplicate version.
#[test]
fn test_keyring_add_duplicate_version_returns_error() {
    let mut ring = KeyRing::new();
    ring.add(KeyVersion(1), &key_v1())
        .expect("first add must succeed");
    let result = ring.add(KeyVersion(1), &[0xBBu8; 32]);
    assert!(result.is_err(), "duplicate version must be rejected");
    match result.unwrap_err() {
        CryptoError::InvalidInput(msg) => {
            assert!(
                msg.contains("already exists"),
                "error must mention already exists: {msg}"
            );
        }
        other => panic!("expected CryptoError::InvalidInput, got {:?}", other),
    }
}

/// add() rejects a key that is not exactly 32 bytes.
#[test]
fn test_keyring_add_wrong_key_length_returns_error() {
    let mut ring = KeyRing::new();
    let short_key = [0u8; 16];
    let result = ring.add(KeyVersion(1), &short_key);
    assert!(result.is_err(), "add with 16-byte key must return Err");
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!("expected CryptoError::InvalidInput, got {:?}", other),
    }
}

// ---------------------------------------------------------------------------
// encrypt_versioned / decrypt_versioned — basic round-trip
// ---------------------------------------------------------------------------

/// Encrypting with a single-key ring and decrypting with the same ring must
/// recover the original plaintext.
#[test]
fn test_encrypt_decrypt_versioned_roundtrip_single_key() {
    let ring = single_key_ring();

    let ct =
        encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD).expect("encrypt_versioned must succeed");

    let recovered = decrypt_versioned(&ct, &ring, MODEL, FIELD)
        .expect("decrypt_versioned must succeed for a freshly encrypted ciphertext");

    assert_eq!(
        recovered, PLAINTEXT,
        "decrypted value must match the original plaintext"
    );
}

/// Round-trip with a two-key ring; the active key (v2) must be used for new
/// encryptions.
#[test]
fn test_encrypt_decrypt_versioned_roundtrip_two_key_ring_uses_active() {
    let ring = two_key_ring();

    let ct =
        encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD).expect("encrypt_versioned must succeed");

    let recovered =
        decrypt_versioned(&ct, &ring, MODEL, FIELD).expect("decrypt_versioned must succeed");

    assert_eq!(recovered, PLAINTEXT);
}

// ---------------------------------------------------------------------------
// Version prefix is present in the raw ciphertext blob
// ---------------------------------------------------------------------------

/// The first 2 decoded bytes of a versioned ciphertext must equal the active
/// version serialised as big-endian u16.
#[test]
fn test_encrypt_versioned_blob_starts_with_version_prefix() {
    use base64ct::{Base64, Encoding};

    let ring = single_key_ring();
    let ct =
        encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD).expect("encrypt_versioned must succeed");

    let blob = Base64::decode_vec(&ct).expect("ciphertext must be valid base64");

    assert!(
        blob.len() >= 2,
        "ciphertext blob must be at least 2 bytes (version prefix)"
    );

    let version_bytes: [u8; 2] = [blob[0], blob[1]];
    let version = KeyVersion::from_bytes(version_bytes);

    assert_eq!(
        version,
        KeyVersion(1),
        "version prefix in blob must match the active key version (1); got {:?}",
        version
    );
}

/// When the active version is 2, the blob prefix must be [0x00, 0x02].
#[test]
fn test_encrypt_versioned_blob_prefix_reflects_active_version_2() {
    use base64ct::{Base64, Encoding};

    let ring = two_key_ring();
    let ct =
        encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD).expect("encrypt_versioned must succeed");

    let blob = Base64::decode_vec(&ct).expect("must be valid base64");
    let version = KeyVersion::from_bytes([blob[0], blob[1]]);

    assert_eq!(
        version,
        KeyVersion(2),
        "active version is 2; blob prefix must be KeyVersion(2)"
    );
}

/// The total decoded blob length must be 2 (version) + 12 (nonce) + plaintext
/// + 16 (GCM tag) bytes.
#[test]
fn test_encrypt_versioned_blob_has_correct_byte_layout() {
    use base64ct::{Base64, Encoding};

    let ring = single_key_ring();
    let ct =
        encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD).expect("encrypt_versioned must succeed");

    let blob = Base64::decode_vec(&ct).expect("must be valid base64");

    let expected = 2 + 12 + PLAINTEXT.len() + 16;
    assert_eq!(
        blob.len(),
        expected,
        "blob layout: 2 version + 12 nonce + {} plaintext + 16 tag = {} expected, got {}",
        PLAINTEXT.len(),
        expected,
        blob.len()
    );
}

// ---------------------------------------------------------------------------
// Cross-version decryption
// ---------------------------------------------------------------------------

/// A ciphertext produced when only v1 was in the ring must still decrypt
/// correctly when the ring is later expanded to include v2 (v2 becomes active).
#[test]
fn test_decrypt_versioned_old_ciphertext_with_expanded_ring() {
    // Encrypt under v1-only ring.
    let ring_v1_only = single_key_ring();
    let ct_v1 = encrypt_versioned(PLAINTEXT, &ring_v1_only, MODEL, FIELD)
        .expect("encrypt_versioned must succeed under v1-only ring");

    // Expand the ring to add v2 (v2 is now the active key).
    let ring_v1_and_v2 = two_key_ring();

    // The v1 ciphertext must still decrypt with the expanded ring.
    let recovered = decrypt_versioned(&ct_v1, &ring_v1_and_v2, MODEL, FIELD)
        .expect("ciphertext produced under v1 must decrypt with a ring that still holds v1");

    assert_eq!(
        recovered, PLAINTEXT,
        "cross-version decryption must recover the original plaintext"
    );
}

/// A ciphertext produced under v2 must not decrypt when only v1 is in the ring
/// (the v2 key is unavailable).
#[test]
fn test_decrypt_versioned_unknown_version_returns_error() {
    let ring_both = two_key_ring();
    let ct_v2 = encrypt_versioned(PLAINTEXT, &ring_both, MODEL, FIELD)
        .expect("encrypt_versioned must succeed under two-key ring (active = v2)");

    // Ring with v1 only — v2 is absent.
    let ring_v1_only = single_key_ring();
    let result = decrypt_versioned(&ct_v2, &ring_v1_only, MODEL, FIELD);

    assert!(
        result.is_err(),
        "decrypt_versioned must return Err when the key version is not in the ring"
    );
    match result.unwrap_err() {
        CryptoError::DecryptionError(_) | CryptoError::InvalidInput(_) => {}
        other => panic!(
            "expected DecryptionError or InvalidInput for unknown version, got {:?}",
            other
        ),
    }
}

// ---------------------------------------------------------------------------
// Error cases
// ---------------------------------------------------------------------------

/// encrypt_versioned on an empty ring must return an error.
#[test]
fn test_encrypt_versioned_empty_ring_returns_error() {
    let ring = KeyRing::new();
    let result = encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD);
    assert!(
        result.is_err(),
        "encrypt_versioned on an empty ring must return Err"
    );
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!("expected CryptoError::InvalidInput, got {:?}", other),
    }
}

/// decrypt_versioned with a tampered ciphertext must return a DecryptionError.
#[test]
fn test_decrypt_versioned_tampered_ciphertext_returns_decryption_error() {
    use base64ct::{Base64, Encoding};

    let ring = single_key_ring();
    let ct =
        encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD).expect("encrypt_versioned must succeed");

    // Flip a byte in the ciphertext body (byte 15: past the 2-byte version +
    // 12-byte nonce, i.e. within the ciphertext/tag region).
    let mut blob = Base64::decode_vec(&ct).expect("must be valid base64");
    blob[15] ^= 0xFF;
    let tampered = Base64::encode_string(&blob);

    let result = decrypt_versioned(&tampered, &ring, MODEL, FIELD);
    assert!(
        result.is_err(),
        "decrypt_versioned must return Err for a tampered ciphertext"
    );
    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!("expected CryptoError::DecryptionError, got {:?}", other),
    }
}

/// decrypt_versioned with invalid base64 must return a DecryptionError.
#[test]
fn test_decrypt_versioned_invalid_base64_returns_error() {
    let ring = single_key_ring();
    let result = decrypt_versioned("not-valid-base64!!!", &ring, MODEL, FIELD);
    assert!(result.is_err(), "invalid base64 must return Err");
    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!("expected CryptoError::DecryptionError, got {:?}", other),
    }
}

/// decrypt_versioned with a blob shorter than 2 bytes must return an error.
#[test]
fn test_decrypt_versioned_blob_too_short_returns_error() {
    use base64ct::{Base64, Encoding};

    let short = Base64::encode_string(&[0u8; 1]);
    let ring = single_key_ring();
    let result = decrypt_versioned(&short, &ring, MODEL, FIELD);
    assert!(result.is_err(), "blob shorter than 2 bytes must return Err");
}

/// AAD mismatch: encrypting under model="User" then decrypting as model="Order"
/// must fail.
#[test]
fn test_decrypt_versioned_aad_mismatch_returns_error() {
    let ring = single_key_ring();
    let ct = encrypt_versioned(PLAINTEXT, &ring, "User", "email")
        .expect("encrypt_versioned must succeed");

    let result = decrypt_versioned(&ct, &ring, "Order", "email");
    assert!(
        result.is_err(),
        "AAD model mismatch must cause decryption to fail"
    );
    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!("expected CryptoError::DecryptionError, got {:?}", other),
    }
}

// ---------------------------------------------------------------------------
// reencrypt_to_active — lazy migration primitive
// ---------------------------------------------------------------------------

/// A ciphertext already at the active version must be returned unchanged.
#[test]
fn test_reencrypt_to_active_already_current_returns_unchanged() {
    let ring = two_key_ring(); // active = v2

    // Encrypt under active (v2).
    let ct_v2 =
        encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD).expect("encrypt_versioned must succeed");

    let result = reencrypt_to_active(&ct_v2, &ring, MODEL, FIELD)
        .expect("reencrypt_to_active must succeed when ciphertext is already at active version");

    assert_eq!(
        result, ct_v2,
        "re-encrypting an already-current ciphertext must return the original unchanged"
    );
}

/// A ciphertext at an older version must be re-encrypted under the active key.
/// After re-encryption the version prefix must equal the active version.
#[test]
fn test_reencrypt_to_active_migrates_old_version_to_current() {
    use base64ct::{Base64, Encoding};

    // Encrypt under v1-only ring.
    let ring_v1 = single_key_ring();
    let ct_v1 = encrypt_versioned(PLAINTEXT, &ring_v1, MODEL, FIELD)
        .expect("encrypt_versioned must succeed under v1");

    // Expand ring to v2 (active = v2).
    let ring_both = two_key_ring();

    let migrated = reencrypt_to_active(&ct_v1, &ring_both, MODEL, FIELD)
        .expect("reencrypt_to_active must succeed when ring holds both v1 and v2");

    // The migrated ciphertext blob must have a v2 prefix.
    let blob = Base64::decode_vec(&migrated).expect("migrated ciphertext must be valid base64");
    let version = KeyVersion::from_bytes([blob[0], blob[1]]);

    assert_eq!(
        version,
        KeyVersion(2),
        "migrated ciphertext must have version 2 prefix; got {:?}",
        version
    );

    // The migrated ciphertext must still decrypt to the original plaintext.
    let recovered = decrypt_versioned(&migrated, &ring_both, MODEL, FIELD)
        .expect("migrated ciphertext must decrypt correctly");

    assert_eq!(
        recovered, PLAINTEXT,
        "plaintext must be preserved after migration to active key"
    );
}

/// reencrypt_to_active must return a DecryptionError when the base64-decoded
/// blob is shorter than 2 bytes and cannot contain a version prefix.
#[test]
fn test_reencrypt_to_active_blob_too_short_returns_error() {
    use base64ct::{Base64, Encoding};
    // A 1-byte blob — too short to contain the 2-byte version prefix.
    let too_short = Base64::encode_string(&[0u8; 1]);
    let ring = single_key_ring();
    let result = reencrypt_to_active(&too_short, &ring, MODEL, FIELD);
    assert!(
        result.is_err(),
        "reencrypt_to_active with a 1-byte blob must return Err"
    );
    match result.unwrap_err() {
        CryptoError::DecryptionError(_) => {}
        other => panic!(
            "expected CryptoError::DecryptionError for too-short blob, got {:?}",
            other
        ),
    }
}

/// reencrypt_to_active must return DecryptionError when the old ciphertext
/// cannot be decrypted because its key version is missing from the ring.
#[test]
fn test_reencrypt_to_active_unknown_version_returns_error() {
    let ring_both = two_key_ring();
    let ct_v2 = encrypt_versioned(PLAINTEXT, &ring_both, MODEL, FIELD)
        .expect("encrypt_versioned must succeed under v2");

    // Ring with only v1 — v2 key is missing.
    let ring_v1_only = single_key_ring();
    let result = reencrypt_to_active(&ct_v2, &ring_v1_only, MODEL, FIELD);

    assert!(
        result.is_err(),
        "reencrypt_to_active must return Err when the old ciphertext version is not in the ring"
    );
}

// ---------------------------------------------------------------------------
// Nonce uniqueness — versioned ciphertexts
// ---------------------------------------------------------------------------

/// Encrypting the same plaintext 1 000 times with the versioned API must
/// produce 1 000 distinct nonces (bytes 2..14 of the decoded blob).
#[test]
fn test_encrypt_versioned_nonce_uniqueness_1000_encryptions() {
    use base64ct::{Base64, Encoding};
    use std::collections::HashSet;

    let ring = single_key_ring();
    const ITERATIONS: usize = 1_000;
    let mut nonces: HashSet<Vec<u8>> = HashSet::with_capacity(ITERATIONS);

    for i in 0..ITERATIONS {
        let ct = encrypt_versioned(PLAINTEXT, &ring, MODEL, FIELD)
            .unwrap_or_else(|_| panic!("encrypt_versioned must succeed on iteration {i}"));

        let blob = Base64::decode_vec(&ct)
            .unwrap_or_else(|_| panic!("must be valid base64 on iteration {i}"));

        // version = bytes[0..2]; nonce = bytes[2..14]
        let nonce = blob[2..14].to_vec();

        assert!(
            nonces.insert(nonce),
            "nonce collision on iteration {i} — all nonces must be unique"
        );
    }

    assert_eq!(nonces.len(), ITERATIONS);
}

// ---------------------------------------------------------------------------
// Batch versioned encrypt / decrypt
// ---------------------------------------------------------------------------

/// encrypt_fields_batch_versioned round-trips correctly through
/// decrypt_fields_batch_versioned.
#[test]
fn test_batch_versioned_roundtrip() {
    let ring = single_key_ring();
    let fields = [("email", "user@example.com"), ("phone", "+441234567890")];

    let encrypted =
        encrypt_fields_batch_versioned(&fields, &ring, MODEL).expect("batch encrypt must succeed");
    assert_eq!(encrypted.len(), 2, "must return one ciphertext per field");

    let ct_fields: Vec<(&str, &str)> = fields
        .iter()
        .zip(encrypted.iter())
        .map(|((name, _), ct)| (*name, ct.as_str()))
        .collect();

    let decrypted = decrypt_fields_batch_versioned(&ct_fields, &ring, MODEL)
        .expect("batch decrypt must succeed");

    assert_eq!(decrypted[0], "user@example.com");
    assert_eq!(decrypted[1], "+441234567890");
}

/// encrypt_fields_batch_versioned on an empty ring returns an error.
#[test]
fn test_batch_versioned_encrypt_empty_ring_returns_error() {
    let ring = KeyRing::new();
    let fields = [("email", "user@example.com")];
    let result = encrypt_fields_batch_versioned(&fields, &ring, MODEL);
    assert!(result.is_err(), "empty ring must return Err");
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!("expected InvalidInput, got {:?}", other),
    }
}

/// decrypt_fields_batch_versioned on an empty ring returns an error.
#[test]
fn test_batch_versioned_decrypt_empty_ring_returns_error() {
    let ring = KeyRing::new();
    let fields = [("email", "not-real-ciphertext")];
    let result = decrypt_fields_batch_versioned(&fields, &ring, MODEL);
    assert!(result.is_err(), "empty ring must return Err");
    match result.unwrap_err() {
        CryptoError::InvalidInput(_) => {}
        other => panic!("expected InvalidInput, got {:?}", other),
    }
}
