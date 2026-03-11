//! US008 — Red phase: Rust-level unit tests for `syntek-graphql-crypto`.
//!
//! These tests verify that the core middleware types exist and satisfy the
//! contracts required by the acceptance criteria.  All tests in this file
//! FAIL during the red phase because the types they reference
//! (`MiddlewareError`, `EncryptedFieldSpec`) do not yet exist in
//! `syntek_graphql_crypto`.
//!
//! Run with: `cargo test -p syntek-graphql-crypto`

// ---------------------------------------------------------------------------
// AC7 / AC8 / AC9 / AC10: MiddlewareError — four distinct variants
//
// The implementation must export a `MiddlewareError` enum with at minimum:
//   - `EncryptFailed`      — wraps the field name and upstream cause
//   - `DecryptFailed`      — wraps the field name and upstream cause
//   - `KeyResolutionFailed`— wraps model name + field name
//   - `UnauthenticatedAccess` — no inner data beyond a non-empty message
//
// `MiddlewareError` must implement `std::error::Error` (via `thiserror`).
// ---------------------------------------------------------------------------

use syntek_graphql_crypto::{EncryptedFieldSpec, MiddlewareError};

// ---------------------------------------------------------------------------
// MiddlewareError — trait implementation tests
// ---------------------------------------------------------------------------

/// AC7 / AC8 / AC9 / AC10: `MiddlewareError` must implement `std::error::Error`
/// so callers can use it with `Box<dyn std::error::Error>` and `?` propagation.
#[test]
fn test_middleware_error_implements_error_trait() {
    let e: Box<dyn std::error::Error> = Box::new(MiddlewareError::DecryptFailed {
        field: "email".to_string(),
    });
    assert!(!e.to_string().is_empty());
}

/// AC7: `DecryptFailed` carries the field name so structured GraphQL errors
/// can include `field_path` in their JSON payload.
#[test]
fn test_decrypt_failed_carries_field_name_in_message() {
    let e = MiddlewareError::DecryptFailed {
        field: "first_name".to_string(),
    };
    let msg = e.to_string();
    assert!(
        msg.contains("first_name"),
        "field name missing from DecryptFailed message: {msg}"
    );
}

/// AC9: `EncryptFailed` carries the field name so the middleware can reject
/// an entire mutation with a structured error referencing the offending field.
#[test]
fn test_encrypt_failed_carries_field_name_in_message() {
    let e = MiddlewareError::EncryptFailed {
        field: "email".to_string(),
    };
    let msg = e.to_string();
    assert!(
        msg.contains("email"),
        "field name missing from EncryptFailed message: {msg}"
    );
}

/// AC7 / AC9: `KeyResolutionFailed` must embed both the model name and the
/// field name so operators can identify the missing `SYNTEK_FIELD_KEY_*`
/// environment variable from the error message alone.
#[test]
fn test_key_resolution_failed_carries_model_and_field_name() {
    let e = MiddlewareError::KeyResolutionFailed {
        model: "User".to_string(),
        field: "phone".to_string(),
    };
    let msg = e.to_string();
    assert!(
        msg.contains("User"),
        "model name missing from KeyResolutionFailed message: {msg}"
    );
    assert!(
        msg.contains("phone"),
        "field name missing from KeyResolutionFailed message: {msg}"
    );
}

/// AC10: `UnauthenticatedAccess` must produce a non-empty human-readable
/// message so the structured GraphQL error payload is never blank.
#[test]
fn test_unauthenticated_access_message_is_non_empty() {
    let e = MiddlewareError::UnauthenticatedAccess;
    assert!(!e.to_string().is_empty());
}

/// Confirm all four variants are distinct types at runtime (Display differs).
#[test]
fn test_middleware_error_variants_produce_distinct_messages() {
    let messages = [
        MiddlewareError::EncryptFailed {
            field: "email".to_string(),
        }
        .to_string(),
        MiddlewareError::DecryptFailed {
            field: "email".to_string(),
        }
        .to_string(),
        MiddlewareError::KeyResolutionFailed {
            model: "User".to_string(),
            field: "email".to_string(),
        }
        .to_string(),
        MiddlewareError::UnauthenticatedAccess.to_string(),
    ];
    // Each message must be unique — variants must not share identical Display output.
    let unique: std::collections::HashSet<&str> = messages.iter().map(String::as_str).collect();
    assert_eq!(
        unique.len(),
        messages.len(),
        "MiddlewareError variants must have distinct Display"
    );
}

// ---------------------------------------------------------------------------
// EncryptedFieldSpec — struct shape and serde tests
//
// The implementation must export `EncryptedFieldSpec` with:
//   - `field_name: String`
//   - `model_name: String`
//   - `batch_group: Option<String>`
//
// It must derive `serde::Serialize` and `serde::Deserialize` so that field
// specs can be serialised for transport between the Rust layer and Python.
// ---------------------------------------------------------------------------

/// AC1 / AC4: An individual (non-batch) field spec must have
/// `batch_group == None`.
#[test]
fn test_individual_field_spec_has_no_batch_group() {
    let spec = EncryptedFieldSpec {
        field_name: "email".to_string(),
        model_name: "User".to_string(),
        batch_group: None,
    };
    assert!(spec.batch_group.is_none());
}

/// AC2 / AC5: A batch field spec must have `batch_group == Some(name)`.
#[test]
fn test_batch_field_spec_has_batch_group() {
    let spec = EncryptedFieldSpec {
        field_name: "first_name".to_string(),
        model_name: "User".to_string(),
        batch_group: Some("profile".to_string()),
    };
    assert_eq!(spec.batch_group.as_deref(), Some("profile"));
}

/// AC3: Individual and batch specs must be distinguishable solely via
/// `batch_group.is_none()` / `batch_group.is_some()`.
#[test]
fn test_individual_and_batch_specs_are_distinguishable() {
    let individual = EncryptedFieldSpec {
        field_name: "email".to_string(),
        model_name: "User".to_string(),
        batch_group: None,
    };
    let batch = EncryptedFieldSpec {
        field_name: "first_name".to_string(),
        model_name: "User".to_string(),
        batch_group: Some("profile".to_string()),
    };
    assert!(individual.batch_group.is_none());
    assert!(batch.batch_group.is_some());
}

/// Serde roundtrip for an individual `EncryptedFieldSpec` — required so the
/// spec can be serialised for diagnostic output and transport layers.
#[test]
fn test_encrypted_field_spec_individual_serde_roundtrip() {
    let original = EncryptedFieldSpec {
        field_name: "email".to_string(),
        model_name: "User".to_string(),
        batch_group: None,
    };
    let json = serde_json::to_string(&original).expect("serialisation must succeed");
    let recovered: EncryptedFieldSpec =
        serde_json::from_str(&json).expect("deserialisation must succeed");
    assert_eq!(recovered.field_name, original.field_name);
    assert_eq!(recovered.model_name, original.model_name);
    assert_eq!(recovered.batch_group, original.batch_group);
}

/// Serde roundtrip for a batch `EncryptedFieldSpec`.
#[test]
fn test_encrypted_field_spec_batch_serde_roundtrip() {
    let original = EncryptedFieldSpec {
        field_name: "last_name".to_string(),
        model_name: "User".to_string(),
        batch_group: Some("profile".to_string()),
    };
    let json = serde_json::to_string(&original).expect("serialisation must succeed");
    let recovered: EncryptedFieldSpec =
        serde_json::from_str(&json).expect("deserialisation must succeed");
    assert_eq!(recovered.field_name, original.field_name);
    assert_eq!(recovered.model_name, original.model_name);
    assert_eq!(recovered.batch_group, original.batch_group);
}

/// Two field specs in the same batch group must share the same `batch_group`
/// value — this is the grouping key the middleware uses at runtime.
#[test]
fn test_two_specs_in_same_batch_group_share_group_key() {
    let first_name = EncryptedFieldSpec {
        field_name: "first_name".to_string(),
        model_name: "User".to_string(),
        batch_group: Some("profile".to_string()),
    };
    let last_name = EncryptedFieldSpec {
        field_name: "last_name".to_string(),
        model_name: "User".to_string(),
        batch_group: Some("profile".to_string()),
    };
    assert_eq!(first_name.batch_group, last_name.batch_group);
}

/// Two field specs in different batch groups must have distinct group keys —
/// the middleware must never combine them into a single batch call (AC3).
#[test]
fn test_specs_in_different_batch_groups_have_different_keys() {
    let first_name = EncryptedFieldSpec {
        field_name: "first_name".to_string(),
        model_name: "User".to_string(),
        batch_group: Some("profile".to_string()),
    };
    let address_line_1 = EncryptedFieldSpec {
        field_name: "address_line_1".to_string(),
        model_name: "User".to_string(),
        batch_group: Some("address".to_string()),
    };
    assert_ne!(first_name.batch_group, address_line_1.batch_group);
}
