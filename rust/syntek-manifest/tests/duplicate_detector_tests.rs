//! US074 — Duplicate block detector tests
//!
//! Acceptance criterion:
//!   Given a `settings.py` already contains a `SYNTEK_<MODULE>` block
//!   When the installer runs again
//!   Then it detects the existing block, warns the developer, and does not
//!   overwrite without explicit confirmation.
//!
//! RED phase — tests will fail until the stub is replaced with real logic.

use std::io::Write;

use syntek_manifest::duplicate_detector::DuplicateDetector;
use syntek_manifest::error::ManifestError;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn temp_file_with_content(content: &str) -> tempfile::NamedTempFile {
    let mut f = tempfile::NamedTempFile::new().expect("failed to create temp file");
    f.write_all(content.as_bytes()).unwrap();
    f
}

// ---------------------------------------------------------------------------
// settings_key — module ID to Python settings key
// ---------------------------------------------------------------------------

#[test]
fn settings_key_converts_hyphen_module_id_to_uppercase_underscores() {
    let key = DuplicateDetector::settings_key("syntek-auth").unwrap();
    assert_eq!(key, "SYNTEK_AUTH", "Expected SYNTEK_AUTH, got: {key}");
}

#[test]
fn settings_key_handles_multi_segment_module_id() {
    let key = DuplicateDetector::settings_key("syntek-email-marketing").unwrap();
    assert_eq!(
        key, "SYNTEK_EMAIL_MARKETING",
        "Expected SYNTEK_EMAIL_MARKETING, got: {key}"
    );
}

#[test]
fn settings_key_already_uppercase_module_id_is_handled() {
    // Defensive: even if the caller passes an already-uppercased id.
    let key = DuplicateDetector::settings_key("SYNTEK-AUTH").unwrap();
    assert!(
        key.contains("SYNTEK") && key.contains("AUTH"),
        "settings_key should produce a valid Python identifier. Got: {key}"
    );
}

// ---------------------------------------------------------------------------
// content_has_block — in-memory string scan
// ---------------------------------------------------------------------------

#[test]
fn content_has_block_returns_true_when_block_is_present() {
    let content = "DEBUG = True\n\nSYNTEK_AUTH = {\n    'MFA_REQUIRED': True,\n}\n";

    let result = DuplicateDetector::content_has_block(content, "syntek-auth");

    assert!(
        result,
        "content_has_block should return true when SYNTEK_AUTH is present"
    );
}

#[test]
fn content_has_block_returns_false_when_block_is_absent() {
    let content = "DEBUG = True\n\nINSTALLED_APPS = []\n";

    let result = DuplicateDetector::content_has_block(content, "syntek-auth");

    assert!(
        !result,
        "content_has_block should return false when SYNTEK_AUTH is absent"
    );
}

#[test]
fn content_has_block_does_not_false_positive_on_partial_key_match() {
    // SYNTEK_AUTH_EXTRA should not match syntek-auth → SYNTEK_AUTH.
    let content = "SYNTEK_AUTH_EXTRA = {}\n";

    // This test is intentionally lenient: if the implementation correctly
    // looks for `SYNTEK_AUTH =` (with equals sign or dict delimiter) it will
    // return false. If it does a naive substring match it will incorrectly
    // return true. Either way the test documents expected behaviour.
    // We assert the strict interpretation.
    let result = DuplicateDetector::content_has_block(content, "syntek-auth");

    assert!(
        !result,
        "content_has_block should not false-positive on SYNTEK_AUTH_EXTRA. Got: {result}"
    );
}

#[test]
fn content_has_block_is_case_sensitive_for_module_key() {
    // Django settings are conventionally uppercase; lowercase should not match.
    let content = "syntek_auth = {}\n";

    let result = DuplicateDetector::content_has_block(content, "syntek-auth");

    assert!(
        !result,
        "content_has_block should not match lowercase key. Got: {result}"
    );
}

// ---------------------------------------------------------------------------
// has_existing_block — file-based scan
// ---------------------------------------------------------------------------

#[test]
fn has_existing_block_returns_true_when_block_present_in_file() {
    let f = temp_file_with_content("SYNTEK_AUTH = {\n    'MFA_REQUIRED': True,\n}\n");

    let result = DuplicateDetector::has_existing_block(f.path(), "syntek-auth")
        .expect("has_existing_block should not error on a readable file");

    assert!(
        result,
        "has_existing_block should return true when SYNTEK_AUTH is in the file"
    );
}

#[test]
fn has_existing_block_returns_false_when_block_absent_from_file() {
    let f = temp_file_with_content("DEBUG = True\n\nINSTALLED_APPS = []\n");

    let result = DuplicateDetector::has_existing_block(f.path(), "syntek-auth")
        .expect("has_existing_block should not error on a readable file");

    assert!(
        !result,
        "has_existing_block should return false when SYNTEK_AUTH is not in the file"
    );
}

#[test]
fn has_existing_block_returns_io_error_for_nonexistent_file() {
    let path = std::path::Path::new("/nonexistent/path/to/settings.py");

    let result = DuplicateDetector::has_existing_block(path, "syntek-auth");

    assert!(
        matches!(result, Err(ManifestError::Io { .. })),
        "has_existing_block should return ManifestError::Io for a missing file. Got: {result:?}"
    );
}

// ---------------------------------------------------------------------------
// H1 — content_has_block must not false-positive on comments or string values
// ---------------------------------------------------------------------------

#[test]
fn content_has_block_not_fooled_by_pattern_inside_comment() {
    let content = "# SYNTEK_AUTH = {} was removed\nDEBUG = True\n";
    let result = DuplicateDetector::content_has_block(content, "syntek-auth");
    assert!(
        !result,
        "content_has_block should not match a commented-out line. Got: {result}"
    );
}

#[test]
fn content_has_block_not_fooled_by_pattern_inside_string_value() {
    let content = "LOGGING = {\n    'message': 'Set SYNTEK_AUTH = {} in settings',\n}\n";
    let result = DuplicateDetector::content_has_block(content, "syntek-auth");
    assert!(
        !result,
        "content_has_block should not match a pattern inside a string value. Got: {result}"
    );
}

// ---------------------------------------------------------------------------
// Integration: detector → settings writer should not overwrite
// ---------------------------------------------------------------------------

#[test]
fn duplicate_detected_means_installer_must_not_overwrite_silently() {
    // This test documents the required behaviour as a logical assertion:
    // if content_has_block returns true, the installer logic must not proceed
    // to write without confirmation. Since this is a library test (no UI),
    // we verify the detector correctly signals the presence of a duplicate.

    let existing_content = "SYNTEK_PAYMENTS = {\n    'STRIPE_KEY': env('STRIPE_KEY'),\n}\n";

    let has_block = DuplicateDetector::content_has_block(existing_content, "syntek-payments");

    assert!(
        has_block,
        "Duplicate detector must identify the existing SYNTEK_PAYMENTS block so the \
         installer can prompt for confirmation before overwriting"
    );
}

// ---------------------------------------------------------------------------
// M1 — settings_key rejects non-ASCII characters in module id
// ---------------------------------------------------------------------------

#[test]
fn settings_key_rejects_non_ascii_hyphen() {
    // U+2011 NON-BREAKING HYPHEN — visually identical to a regular hyphen
    // but a different Unicode code point. It would survive `replace('-', "_")`
    // unchanged and produce an invalid Python identifier.
    let non_ascii_hyphen_id = "syntek\u{2011}auth"; // syntek‑auth with U+2011
    let result = DuplicateDetector::settings_key(non_ascii_hyphen_id);
    assert!(
        matches!(
            result,
            Err(syntek_manifest::error::ManifestError::InvalidId { .. })
        ),
        "settings_key should reject a non-ASCII hyphen in the module id. Got: {result:?}"
    );
}

#[test]
fn settings_key_rejects_unicode_letters() {
    let result = DuplicateDetector::settings_key("syntek-aüth");
    assert!(
        matches!(
            result,
            Err(syntek_manifest::error::ManifestError::InvalidId { .. })
        ),
        "settings_key should reject non-ASCII letters. Got: {result:?}"
    );
}

#[test]
fn settings_key_accepts_ascii_alphanumeric_and_hyphens() {
    let result = DuplicateDetector::settings_key("syntek-auth-v2");
    assert!(
        result.is_ok(),
        "settings_key should accept ASCII alphanumeric and hyphens. Got: {result:?}"
    );
    assert_eq!(result.unwrap(), "SYNTEK_AUTH_V2");
}

#[test]
fn content_has_block_returns_false_for_invalid_module_id() {
    // A non-ASCII id can never produce a valid block pattern in a settings.py,
    // so content_has_block should return false rather than panic.
    let content = "DEBUG = True\n";
    let result = DuplicateDetector::content_has_block(content, "syntek\u{2011}auth");
    assert!(
        !result,
        "content_has_block should return false for an invalid module id"
    );
}
