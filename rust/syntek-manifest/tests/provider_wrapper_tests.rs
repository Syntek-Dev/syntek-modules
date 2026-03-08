//! US074 — Provider wrapper tests
//!
//! Acceptance criterion:
//!   Given a frontend module installer runs and the developer selects options
//!   When the installer completes
//!   Then the project's app root is wrapped with required providers and a
//!   minimal usage stub is written to the declared entry file.
//!
//! RED phase — tests will fail until the stub is replaced with real logic.

use syntek_manifest::error::ManifestError;
use syntek_manifest::manifest::ManifestProvider;
use syntek_manifest::provider_wrapper::ProviderWrapper;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn make_provider(name: &str, import: &str) -> ManifestProvider {
    ManifestProvider {
        name: name.to_string(),
        import: import.to_string(),
    }
}

fn temp_empty_file() -> tempfile::NamedTempFile {
    tempfile::NamedTempFile::new().expect("failed to create temp file")
}

// ---------------------------------------------------------------------------
// build_imports — one import statement per provider
// ---------------------------------------------------------------------------

#[test]
fn build_imports_returns_one_import_per_provider() {
    let providers = vec![
        make_provider("AuthProvider", "@syntek/ui-auth"),
        make_provider("SessionProvider", "@syntek/session"),
    ];

    let imports = ProviderWrapper::build_imports(&providers).unwrap();

    assert_eq!(
        imports.len(),
        2,
        "Expected one import line per provider. Got: {imports:?}"
    );
}

#[test]
fn build_imports_contains_import_path_for_each_provider() {
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let imports = ProviderWrapper::build_imports(&providers).unwrap();

    assert!(
        imports
            .first()
            .map(|i| i.contains("@syntek/ui-auth"))
            .unwrap_or(false),
        "Import line should contain the provider import path. Got: {imports:?}"
    );
}

#[test]
fn build_imports_contains_named_export_for_each_provider() {
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let imports = ProviderWrapper::build_imports(&providers).unwrap();

    assert!(
        imports
            .first()
            .map(|i| i.contains("AuthProvider"))
            .unwrap_or(false),
        "Import line should contain the provider component name. Got: {imports:?}"
    );
}

#[test]
fn build_imports_empty_providers_returns_empty_vec() {
    assert!(ProviderWrapper::build_imports(&[]).unwrap().is_empty());
}

// ---------------------------------------------------------------------------
// build_jsx_wrapper — nested JSX expression
// ---------------------------------------------------------------------------

#[test]
fn build_jsx_wrapper_wraps_single_provider() {
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let jsx = ProviderWrapper::build_jsx_wrapper(&providers).unwrap();

    assert!(
        jsx.contains("<AuthProvider>"),
        "JSX wrapper should open AuthProvider. Got:\n{jsx}"
    );
    assert!(
        jsx.contains("</AuthProvider>"),
        "JSX wrapper should close AuthProvider. Got:\n{jsx}"
    );
}

#[test]
fn build_jsx_wrapper_nests_multiple_providers_in_order() {
    let providers = vec![
        make_provider("AuthProvider", "@syntek/ui-auth"),
        make_provider("SessionProvider", "@syntek/session"),
    ];

    let jsx = ProviderWrapper::build_jsx_wrapper(&providers).unwrap();

    let auth_open = jsx.find("<AuthProvider>").unwrap_or(usize::MAX);
    let session_open = jsx.find("<SessionProvider>").unwrap_or(usize::MAX);

    assert!(
        auth_open < session_open,
        "AuthProvider should be the outer wrapper (declared first). Got:\n{jsx}"
    );
}

#[test]
fn build_jsx_wrapper_contains_children_placeholder() {
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let jsx = ProviderWrapper::build_jsx_wrapper(&providers).unwrap();

    assert!(
        jsx.contains("{children}") || jsx.contains("children"),
        "JSX wrapper should include a children slot. Got:\n{jsx}"
    );
}

// ---------------------------------------------------------------------------
// build_usage_stub — generated entry file content
// ---------------------------------------------------------------------------

#[test]
fn build_usage_stub_contains_import_statements() {
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let stub = ProviderWrapper::build_usage_stub("app/layout.tsx", &providers).unwrap();

    assert!(
        stub.contains("import") || stub.contains("from"),
        "Usage stub should contain import statements. Got:\n{stub}"
    );
}

#[test]
fn build_usage_stub_contains_provider_wrapper() {
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let stub = ProviderWrapper::build_usage_stub("app/layout.tsx", &providers).unwrap();

    assert!(
        stub.contains("AuthProvider"),
        "Usage stub should reference the declared provider. Got:\n{stub}"
    );
}

// ---------------------------------------------------------------------------
// wrap_entry_point — writes to disk
// ---------------------------------------------------------------------------

#[test]
fn wrap_entry_point_writes_provider_to_empty_entry_file() {
    let f = temp_empty_file();
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    ProviderWrapper::wrap_entry_point(f.path(), &providers, false)
        .expect("wrap_entry_point should not fail on empty file");

    let content = std::fs::read_to_string(f.path()).unwrap();
    assert!(
        content.contains("AuthProvider"),
        "Entry file should contain the provider after wrapping. Got:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// wrap_entry_point — H6 refuses to overwrite existing content
// ---------------------------------------------------------------------------

#[test]
fn wrap_entry_point_refuses_to_overwrite_existing_content() {
    use std::io::Write;
    let mut f = tempfile::NamedTempFile::new().unwrap();
    f.write_all(b"export default function RootLayout({ children }) {\n  return children;\n}\n")
        .unwrap();
    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let result = ProviderWrapper::wrap_entry_point(f.path(), &providers, false);

    assert!(
        matches!(result, Err(ManifestError::Io { .. })),
        "wrap_entry_point should refuse to overwrite a file with existing content. Got: {result:?}"
    );
}

// ---------------------------------------------------------------------------
// H3 — Provider name validation
// ---------------------------------------------------------------------------

#[test]
fn build_imports_rejects_provider_name_with_space() {
    let providers = vec![make_provider("Auth Provider", "@syntek/ui-auth")];
    let result = ProviderWrapper::build_imports(&providers);
    assert!(
        matches!(result, Err(ManifestError::InvalidProviderName { .. })),
        "Expected InvalidProviderName for name with space. Got: {result:?}"
    );
}

#[test]
fn build_jsx_wrapper_rejects_provider_name_with_angle_bracket() {
    let providers = vec![make_provider("<script>", "@syntek/ui-auth")];
    let result = ProviderWrapper::build_jsx_wrapper(&providers);
    assert!(
        matches!(result, Err(ManifestError::InvalidProviderName { .. })),
        "Expected InvalidProviderName for name with angle bracket. Got: {result:?}"
    );
}

#[test]
fn build_imports_rejects_empty_provider_name() {
    let providers = vec![make_provider("", "@syntek/ui-auth")];
    let result = ProviderWrapper::build_imports(&providers);
    assert!(
        matches!(result, Err(ManifestError::InvalidProviderName { .. })),
        "Expected InvalidProviderName for empty name. Got: {result:?}"
    );
}

#[test]
fn build_imports_accepts_valid_alphanumeric_name() {
    let providers = vec![make_provider("AuthProvider2", "@syntek/ui-auth")];
    let result = ProviderWrapper::build_imports(&providers);
    assert!(
        result.is_ok(),
        "Valid alphanumeric name should be accepted. Got: {result:?}"
    );
}

// ---------------------------------------------------------------------------
// L2 — build_jsx_wrapper with empty providers returns {children} not "{children}"
// ---------------------------------------------------------------------------

#[test]
fn build_jsx_wrapper_with_empty_providers_returns_children_expression() {
    let jsx = ProviderWrapper::build_jsx_wrapper(&[]).unwrap();

    // The returned string must be the JSX expression {children}, not the string
    // literal "{children}" (which would render the literal text "{children}"
    // rather than the children prop).
    assert_eq!(
        jsx, "{children}",
        "Empty providers should return the JSX expression {{children}} without outer quotes. Got: {jsx}"
    );

    // Confirm it does NOT include surrounding double-quotes.
    assert!(
        !jsx.starts_with('"') && !jsx.ends_with('"'),
        "Return value must not be wrapped in double-quote string delimiters. Got: {jsx}"
    );
}

#[test]
fn build_usage_stub_with_no_providers_returns_children_not_string_literal() {
    let stub = ProviderWrapper::build_usage_stub("app/layout.tsx", &[]).unwrap();

    // The generated component must use {children} as the JSX return value,
    // not the string literal "{children}".
    assert!(
        stub.contains("return {children}"),
        "Generated stub should use JSX children expression, not a string literal. Got:\n{stub}"
    );
    assert!(
        !stub.contains("return \"{children}\""),
        "Generated stub must not return a string literal \"\\'{{children}}'\". Got:\n{stub}"
    );
}

// ---------------------------------------------------------------------------
// MC4 — wrap_entry_point with force=true preserves existing content
// ---------------------------------------------------------------------------

#[test]
fn wrap_entry_point_with_force_preserves_existing_content() {
    use std::io::Write;

    let existing_content =
        "export default function RootLayout({ children }) {\n  return children;\n}\n";
    let mut f = tempfile::NamedTempFile::new().unwrap();
    f.write_all(existing_content.as_bytes()).unwrap();

    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let result = ProviderWrapper::wrap_entry_point(f.path(), &providers, true);

    assert!(
        result.is_ok(),
        "wrap_entry_point with force=true should succeed even when file has content. Got: {result:?}"
    );

    let content = std::fs::read_to_string(f.path()).unwrap();

    // The existing content should be preserved.
    assert!(
        content.contains("export default function RootLayout"),
        "Existing default export should be preserved. Got:\n{content}"
    );

    // The import for the provider should be prepended.
    assert!(
        content.contains("import { AuthProvider }"),
        "Provider import should be prepended. Got:\n{content}"
    );

    // The import must appear before the existing export.
    let import_pos = content.find("import { AuthProvider }").unwrap();
    let export_pos = content.find("export default").unwrap();
    assert!(
        import_pos < export_pos,
        "Import should precede existing export. import_pos={import_pos}, export_pos={export_pos}"
    );
}

#[test]
fn wrap_entry_point_with_force_false_still_blocks_on_existing_content() {
    use std::io::Write;

    let mut f = tempfile::NamedTempFile::new().unwrap();
    f.write_all(b"export default function Layout() { return null; }\n")
        .unwrap();

    let providers = vec![make_provider("AuthProvider", "@syntek/ui-auth")];

    let result = ProviderWrapper::wrap_entry_point(f.path(), &providers, false);

    assert!(
        matches!(result, Err(ManifestError::Io { .. })),
        "force=false should still block on existing content. Got: {result:?}"
    );
}
