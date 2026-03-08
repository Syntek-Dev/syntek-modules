//! US074 — Parser tests
//!
//! Acceptance criterion:
//!   Given a valid `syntek.manifest.toml` file
//!   When the CLI framework parses it
//!   Then all declared fields are validated and any missing required fields
//!   raise a descriptive error.
//!
//! These tests are in the RED phase — they will fail until the implementation
//! stubs in `parser.rs` are replaced with real logic.

use syntek_manifest::error::ManifestError;
use syntek_manifest::manifest::ModuleKind;
use syntek_manifest::parser::ManifestParser;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn valid_backend_toml() -> &'static str {
    r#"
id      = "syntek-auth"
version = "1.0.0"
kind    = "backend"

installed_apps = ["syntek_auth"]

[[options]]
key     = "MFA_REQUIRED"
label   = "Require MFA for all users?"
kind    = "bool"
default = "true"

[[settings]]
key     = "MFA_REQUIRED"
kind    = "bool"
default = "true"

[[post_install_steps]]
label   = "Add URL patterns"
snippet = "path('auth/', include('syntek_auth.urls')),"
lang    = "python"
"#
}

fn valid_frontend_toml() -> &'static str {
    r#"
id          = "syntek-ui-auth"
version     = "1.0.0"
kind        = "frontend"
entry_point = "app/layout.tsx"

[[providers]]
name   = "AuthProvider"
import = "@syntek/ui-auth"

[[options]]
key     = "ENABLE_SOCIAL_LOGIN"
label   = "Enable social login?"
kind    = "bool"
default = "false"
"#
}

// ---------------------------------------------------------------------------
// Happy-path: valid manifest parsing
// ---------------------------------------------------------------------------

#[test]
fn parse_valid_backend_manifest_returns_manifest() {
    // Arrange — a well-formed backend manifest.
    let toml = valid_backend_toml();

    // Act
    let result = ManifestParser::parse(toml);

    // Assert
    assert!(
        result.is_ok(),
        "Expected Ok(manifest) for valid backend TOML, got: {result:?}"
    );
    let manifest = result.unwrap();
    assert_eq!(manifest.id, "syntek-auth");
    assert_eq!(manifest.version, "1.0.0");
    assert_eq!(manifest.kind, ModuleKind::Backend);
}

#[test]
fn parse_valid_frontend_manifest_returns_manifest() {
    let toml = valid_frontend_toml();

    let result = ManifestParser::parse(toml);

    assert!(
        result.is_ok(),
        "Expected Ok(manifest) for valid frontend TOML, got: {result:?}"
    );
    let manifest = result.unwrap();
    assert_eq!(manifest.id, "syntek-ui-auth");
    assert_eq!(manifest.kind, ModuleKind::Frontend);
    assert_eq!(manifest.entry_point.as_deref(), Some("app/layout.tsx"));
}

#[test]
fn parse_backend_manifest_populates_installed_apps() {
    let manifest = ManifestParser::parse(valid_backend_toml()).unwrap();

    assert_eq!(
        manifest.installed_apps,
        vec!["syntek_auth"],
        "installed_apps should contain the declared app label"
    );
}

#[test]
fn parse_manifest_populates_options_list() {
    let manifest = ManifestParser::parse(valid_backend_toml()).unwrap();

    assert_eq!(manifest.options.len(), 1);
    let opt = &manifest.options[0];
    assert_eq!(opt.key, "MFA_REQUIRED");
    assert_eq!(opt.label, "Require MFA for all users?");
    assert_eq!(opt.kind, "bool");
    assert_eq!(opt.default.as_deref(), Some("true"));
}

#[test]
fn parse_manifest_populates_settings_list() {
    let manifest = ManifestParser::parse(valid_backend_toml()).unwrap();

    assert_eq!(manifest.settings.len(), 1);
    let setting = &manifest.settings[0];
    assert_eq!(setting.key, "MFA_REQUIRED");
    assert_eq!(setting.kind, "bool");
}

#[test]
fn parse_frontend_manifest_populates_providers() {
    let manifest = ManifestParser::parse(valid_frontend_toml()).unwrap();

    assert_eq!(manifest.providers.len(), 1);
    let provider = &manifest.providers[0];
    assert_eq!(provider.name, "AuthProvider");
    assert_eq!(provider.import, "@syntek/ui-auth");
}

#[test]
fn parse_manifest_populates_post_install_steps() {
    let manifest = ManifestParser::parse(valid_backend_toml()).unwrap();

    assert_eq!(manifest.post_install_steps.len(), 1);
    let step = &manifest.post_install_steps[0];
    assert_eq!(step.label, "Add URL patterns");
    assert_eq!(step.lang, "python");
    assert!(
        step.snippet.contains("syntek_auth.urls"),
        "snippet should reference the URL module"
    );
}

// ---------------------------------------------------------------------------
// Missing required fields — descriptive errors
// ---------------------------------------------------------------------------

#[test]
fn parse_missing_id_returns_descriptive_error() {
    let toml = r#"
version = "1.0.0"
kind    = "backend"
"#;

    let err = ManifestParser::parse(toml).unwrap_err();

    match &err {
        ManifestError::MissingField { field } => {
            assert_eq!(field, "id", "Error should name the missing field `id`");
        }
        other => panic!("Expected MissingField(id), got: {other:?}"),
    }
}

#[test]
fn parse_missing_version_returns_descriptive_error() {
    let toml = r#"
id   = "syntek-auth"
kind = "backend"
"#;

    let err = ManifestParser::parse(toml).unwrap_err();

    match &err {
        ManifestError::MissingField { field } => {
            assert_eq!(field, "version");
        }
        other => panic!("Expected MissingField(version), got: {other:?}"),
    }
}

#[test]
fn parse_missing_kind_returns_descriptive_error() {
    let toml = r#"
id      = "syntek-auth"
version = "1.0.0"
"#;

    let err = ManifestParser::parse(toml).unwrap_err();

    match &err {
        ManifestError::MissingField { field } => {
            assert_eq!(field, "kind");
        }
        other => panic!("Expected MissingField(kind), got: {other:?}"),
    }
}

// ---------------------------------------------------------------------------
// Invalid field values
// ---------------------------------------------------------------------------

#[test]
fn parse_unknown_kind_returns_descriptive_error() {
    let toml = r#"
id      = "syntek-auth"
version = "1.0.0"
kind    = "plugin"
"#;

    let err = ManifestParser::parse(toml).unwrap_err();

    match &err {
        ManifestError::UnknownKind { kind } => {
            assert_eq!(kind, "plugin");
        }
        other => panic!("Expected UnknownKind(plugin), got: {other:?}"),
    }
}

#[test]
fn parse_malformed_toml_returns_toml_parse_error() {
    let toml = "id = [this is not valid toml";

    let err = ManifestParser::parse(toml).unwrap_err();

    assert!(
        matches!(err, ManifestError::TomlParse(_)),
        "Expected TomlParse error, got: {err:?}"
    );
}

// ---------------------------------------------------------------------------
// All four kinds are accepted
// ---------------------------------------------------------------------------

#[test]
fn parse_rust_crate_kind_is_accepted() {
    let toml = r#"id = "syntek-crypto" version = "1.0.0" kind = "rust-crate""#;
    // Note: The stub returns Err, so this test will fail until implemented.
    // The assertion is on the kind — not that it's Ok — so we check the parsed value.
    let result = ManifestParser::parse(toml);
    if let Ok(m) = result {
        assert_eq!(m.kind, ModuleKind::RustCrate);
    } else {
        // Still red: if parse fails, force-fail to keep test red.
        panic!("parse returned Err for a valid rust-crate manifest: {result:?}");
    }
}

#[test]
fn parse_mobile_kind_is_accepted() {
    let toml = r#"
id      = "syntek-mobile-auth"
version = "1.0.0"
kind    = "mobile"
"#;
    let result = ManifestParser::parse(toml);
    if let Ok(m) = result {
        assert_eq!(m.kind, ModuleKind::Mobile);
    } else {
        panic!("parse returned Err for a valid mobile manifest: {result:?}");
    }
}

// ---------------------------------------------------------------------------
// H2 — normaliser must not corrupt TOML string values
// ---------------------------------------------------------------------------

#[test]
fn parse_string_value_containing_equals_sign_is_not_corrupted() {
    // A string value like "kind = optional" must not be split by the normaliser.
    let toml = r#"
id      = "syntek-flags"
version = "1.0.0"
kind    = "backend"

[[options]]
key     = "FEATURE_X"
label   = "kind = optional"
kind    = "str"
"#;

    let result = ManifestParser::parse(toml);
    assert!(
        result.is_ok(),
        "String value containing '=' should not cause a parse error. Got: {result:?}"
    );
    let manifest = result.unwrap();
    assert_eq!(
        manifest.options[0].label, "kind = optional",
        "String value should be preserved intact"
    );
}

// ---------------------------------------------------------------------------
// Optional fields default to empty collections
// ---------------------------------------------------------------------------

#[test]
fn parse_minimal_manifest_options_default_to_empty() {
    let toml = r#"
id      = "syntek-geo"
version = "1.0.0"
kind    = "backend"
"#;
    let result = ManifestParser::parse(toml);
    if let Ok(m) = result {
        assert!(m.options.is_empty(), "options should default to []");
        assert!(m.settings.is_empty(), "settings should default to []");
        assert!(
            m.installed_apps.is_empty(),
            "installed_apps should default to []"
        );
        assert!(m.providers.is_empty(), "providers should default to []");
        assert!(
            m.post_install_steps.is_empty(),
            "post_install_steps should default to []"
        );
        assert!(
            m.entry_point.is_none(),
            "entry_point should default to None"
        );
    } else {
        panic!("parse returned Err for a minimal valid manifest: {result:?}");
    }
}

// ---------------------------------------------------------------------------
// M1 — parser rejects id with non-ASCII characters
// ---------------------------------------------------------------------------

#[test]
fn parse_rejects_id_with_non_ascii_hyphen() {
    // U+2011 NON-BREAKING HYPHEN — would survive `replace('-', "_")` unchanged
    // and produce a syntactically invalid Python identifier.
    let toml = "id = \"syntek\u{2011}auth\"\nversion = \"1.0.0\"\nkind = \"backend\"\n";
    let err = ManifestParser::parse(toml).unwrap_err();
    assert!(
        matches!(err, ManifestError::InvalidId { .. }),
        "Expected InvalidId for non-ASCII hyphen in id. Got: {err:?}"
    );
}

#[test]
fn parse_rejects_id_with_unicode_letters() {
    let toml = "id = \"syntek-aüth\"\nversion = \"1.0.0\"\nkind = \"backend\"\n";
    let err = ManifestParser::parse(toml).unwrap_err();
    assert!(
        matches!(err, ManifestError::InvalidId { .. }),
        "Expected InvalidId for Unicode letter in id. Got: {err:?}"
    );
}

// ---------------------------------------------------------------------------
// L3 — parser rejects empty id or version
// ---------------------------------------------------------------------------

#[test]
fn parse_rejects_empty_id() {
    let toml = r#"
id      = ""
version = "1.0.0"
kind    = "backend"
"#;
    let err = ManifestParser::parse(toml).unwrap_err();
    assert!(
        matches!(err, ManifestError::MissingField { .. }),
        "Expected MissingField for empty id. Got: {err:?}"
    );
}

#[test]
fn parse_rejects_empty_version() {
    let toml = r#"
id      = "syntek-auth"
version = ""
kind    = "backend"
"#;
    let err = ManifestParser::parse(toml).unwrap_err();
    assert!(
        matches!(err, ManifestError::MissingField { .. }),
        "Expected MissingField for empty version. Got: {err:?}"
    );
}

// ---------------------------------------------------------------------------
// L5 — SemVer validation on version field
// ---------------------------------------------------------------------------

#[test]
fn parse_rejects_non_semver_version() {
    let toml = r#"
id      = "syntek-auth"
version = "potato"
kind    = "backend"
"#;
    let err = ManifestParser::parse(toml).unwrap_err();
    assert!(
        matches!(err, ManifestError::InvalidVersion { .. }),
        "Expected InvalidVersion for non-SemVer string. Got: {err:?}"
    );
}

#[test]
fn parse_rejects_version_with_only_major_minor() {
    let toml = r#"
id      = "syntek-auth"
version = "1.0"
kind    = "backend"
"#;
    let err = ManifestParser::parse(toml).unwrap_err();
    assert!(
        matches!(err, ManifestError::InvalidVersion { .. }),
        "Expected InvalidVersion for a version missing the patch component. Got: {err:?}"
    );
}

#[test]
fn parse_accepts_valid_semver() {
    let toml = r#"
id      = "syntek-auth"
version = "2.14.3"
kind    = "backend"
"#;
    let result = ManifestParser::parse(toml);
    assert!(
        result.is_ok(),
        "Expected Ok for a valid SemVer version. Got: {result:?}"
    );
    assert_eq!(result.unwrap().version, "2.14.3");
}

#[test]
fn parse_accepts_semver_with_prerelease_suffix() {
    let toml = r#"
id      = "syntek-auth"
version = "1.0.0-alpha.1"
kind    = "backend"
"#;
    let result = ManifestParser::parse(toml);
    assert!(
        result.is_ok(),
        "Expected Ok for a SemVer with pre-release suffix. Got: {result:?}"
    );
}

// ---------------------------------------------------------------------------
// L6 — oversized manifest is rejected before normalisation
// ---------------------------------------------------------------------------

#[test]
fn parse_rejects_oversized_manifest() {
    // Build a string exceeding 64 KiB (65_536 bytes).
    // Use a comment padded to exceed the limit — still technically valid TOML
    // structure, but the size guard fires before parsing.
    let padding = "# ".repeat(40_000); // ~80 000 bytes
    let toml =
        format!("{padding}\nid = \"syntek-auth\"\nversion = \"1.0.0\"\nkind = \"backend\"\n");
    assert!(
        toml.len() > 65_536,
        "Test pre-condition: padded TOML should exceed 64 KiB"
    );

    let err = ManifestParser::parse(&toml).unwrap_err();
    assert!(
        matches!(err, ManifestError::TomlParse(_)),
        "Expected TomlParse error for oversized manifest. Got: {err:?}"
    );
}
