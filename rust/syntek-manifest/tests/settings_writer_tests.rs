//! US074 — Settings writer tests
//!
//! Acceptance criteria:
//!   Given a backend module installer runs and the developer selects options
//!   When the installer completes
//!   Then the correct `SYNTEK_<MODULE>` config block is written to `settings.py`
//!   and the app is added to `INSTALLED_APPS` with no duplicate entries.
//!
//! RED phase — tests will fail until the stub is replaced with real logic.

use std::collections::HashMap;
use std::io::Write;

use syntek_manifest::error::ManifestError;
use syntek_manifest::manifest::ManifestSetting;
use syntek_manifest::settings_writer::SettingsWriter;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn make_setting(key: &str, kind: &str, default: Option<&str>) -> ManifestSetting {
    ManifestSetting {
        key: key.to_string(),
        kind: kind.to_string(),
        default: default.map(str::to_string),
    }
}

fn values(pairs: &[(&str, &str)]) -> HashMap<String, String> {
    pairs
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
}

fn temp_settings_file(content: &str) -> tempfile::NamedTempFile {
    let mut f = tempfile::NamedTempFile::new().expect("failed to create temp file");
    f.write_all(content.as_bytes())
        .expect("failed to write temp file");
    f
}

// ---------------------------------------------------------------------------
// build_config_block — rendered text assertions
// ---------------------------------------------------------------------------

#[test]
fn build_config_block_starts_with_syntek_module_key() {
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    let block = SettingsWriter::build_config_block("syntek-auth", &settings, &vals).unwrap();

    assert!(
        block.contains("SYNTEK_AUTH"),
        "Config block should start with SYNTEK_AUTH. Got:\n{block}"
    );
}

#[test]
fn build_config_block_is_a_python_dict_literal() {
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    let block = SettingsWriter::build_config_block("syntek-auth", &settings, &vals).unwrap();

    assert!(block.contains('{'), "Block should open a dict with '{{'");
    assert!(block.contains('}'), "Block should close a dict with '}}'");
}

#[test]
fn build_config_block_contains_resolved_setting_key_and_value() {
    let settings = vec![make_setting("SESSION_TIMEOUT", "int", Some("1800"))];
    let vals = values(&[("SESSION_TIMEOUT", "900")]);

    let block = SettingsWriter::build_config_block("syntek-auth", &settings, &vals).unwrap();

    assert!(
        block.contains("SESSION_TIMEOUT"),
        "Block should contain the setting key. Got:\n{block}"
    );
    assert!(
        block.contains("900"),
        "Block should contain the resolved value, not the default. Got:\n{block}"
    );
}

#[test]
fn build_config_block_renders_bool_true_as_python_true() {
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("false"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    let block = SettingsWriter::build_config_block("syntek-auth", &settings, &vals).unwrap();

    // Python uses `True` (capital T), not `true`.
    assert!(
        block.contains("True"),
        "bool true should render as Python `True`. Got:\n{block}"
    );
}

#[test]
fn build_config_block_renders_bool_false_as_python_false() {
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "false")]);

    let block = SettingsWriter::build_config_block("syntek-auth", &settings, &vals).unwrap();

    assert!(
        block.contains("False"),
        "bool false should render as Python `False`. Got:\n{block}"
    );
}

#[test]
fn build_config_block_renders_str_value_with_quotes() {
    let settings = vec![make_setting("API_KEY", "str", None)];
    let vals = values(&[("API_KEY", "env('SYNTEK_API_KEY')")]);

    let block = SettingsWriter::build_config_block("syntek-auth", &settings, &vals).unwrap();

    assert!(
        block.contains("'API_KEY'") || block.contains('"'),
        "String values should be quoted in the rendered block. Got:\n{block}"
    );
}

// ---------------------------------------------------------------------------
// render_value — per-field rendering
// ---------------------------------------------------------------------------

#[test]
fn render_value_bool_true_produces_python_true() {
    let rendered = SettingsWriter::render_value("MFA_REQUIRED", "bool", "true").unwrap();
    assert!(
        rendered.contains("True"),
        "Expected Python `True`, got: {rendered}"
    );
}

#[test]
fn render_value_bool_false_produces_python_false() {
    let rendered = SettingsWriter::render_value("MFA_REQUIRED", "bool", "false").unwrap();
    assert!(
        rendered.contains("False"),
        "Expected Python `False`, got: {rendered}"
    );
}

#[test]
fn render_value_int_produces_unquoted_number() {
    let rendered = SettingsWriter::render_value("SESSION_TIMEOUT", "int", "1800").unwrap();
    assert!(
        rendered.contains("1800"),
        "Expected unquoted int, got: {rendered}"
    );
    // int values should not be wrapped in quotes
    assert!(
        !rendered.contains("'1800'") && !rendered.contains("\"1800\""),
        "int value should not be quoted, got: {rendered}"
    );
}

// ---------------------------------------------------------------------------
// render_value — H4 bool validation
// ---------------------------------------------------------------------------

#[test]
fn render_value_bool_rejects_arbitrary_string() {
    let result = SettingsWriter::render_value("ENABLED", "bool", "yes");
    assert!(
        matches!(result, Err(ManifestError::InvalidBoolValue { .. })),
        "Expected InvalidBoolValue error for 'yes', got: {result:?}"
    );
}

#[test]
fn render_value_bool_accepts_case_insensitive_true() {
    let rendered = SettingsWriter::render_value("ENABLED", "bool", "True").unwrap();
    assert!(
        rendered.contains("True"),
        "Expected Python True, got: {rendered}"
    );
}

#[test]
fn render_value_bool_accepts_case_insensitive_false() {
    let rendered = SettingsWriter::render_value("ENABLED", "bool", "FALSE").unwrap();
    assert!(
        rendered.contains("False"),
        "Expected Python False, got: {rendered}"
    );
}

#[test]
fn render_value_bool_rejects_numeric_one() {
    let result = SettingsWriter::render_value("FLAG", "bool", "1");
    assert!(
        matches!(result, Err(ManifestError::InvalidBoolValue { .. })),
        "Expected InvalidBoolValue error for '1', got: {result:?}"
    );
}

// ---------------------------------------------------------------------------
// write_config_block — writes to disk
// ---------------------------------------------------------------------------

#[test]
fn write_config_block_appends_syntek_block_to_settings_file() {
    let f = temp_settings_file("# Django settings\n\nINSTALLED_APPS = []\n");
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    SettingsWriter::write_config_block(f.path(), "syntek-auth", &settings, &vals, false)
        .expect("write_config_block should not fail");

    let content = std::fs::read_to_string(f.path()).unwrap();
    assert!(
        content.contains("SYNTEK_AUTH"),
        "settings.py should contain SYNTEK_AUTH after write. Got:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// write_config_block — H5 duplicate detection
// ---------------------------------------------------------------------------

#[test]
fn write_config_block_returns_existing_block_error_when_block_already_present() {
    let f = temp_settings_file("SYNTEK_AUTH = {\n    'MFA_REQUIRED': True,\n}\n");
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    let result =
        SettingsWriter::write_config_block(f.path(), "syntek-auth", &settings, &vals, false);

    assert!(
        matches!(result, Err(ManifestError::ExistingBlock { .. })),
        "Expected ExistingBlock error when block already present. Got: {result:?}"
    );
}

// ---------------------------------------------------------------------------
// write_config_block — C1 atomic write (verify file not corrupted on success)
// ---------------------------------------------------------------------------

#[test]
fn write_config_block_produces_valid_file_content() {
    let original = "# Django settings\nDEBUG = True\n";
    let f = temp_settings_file(original);
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    SettingsWriter::write_config_block(f.path(), "syntek-auth", &settings, &vals, false).unwrap();

    let content = std::fs::read_to_string(f.path()).unwrap();
    // Original content is preserved.
    assert!(
        content.contains("DEBUG = True"),
        "Original content should be preserved"
    );
    // New block is present.
    assert!(
        content.contains("SYNTEK_AUTH = {"),
        "New block should be present"
    );
    // No .tmp file left behind.
    let tmp = f.path().with_extension("py.tmp");
    assert!(
        !tmp.exists(),
        "Temporary file should be cleaned up after atomic write"
    );
}

// ---------------------------------------------------------------------------
// append_installed_app — no-duplicate guarantee
// ---------------------------------------------------------------------------

#[test]
fn append_installed_app_adds_app_when_not_present() {
    let f = temp_settings_file("INSTALLED_APPS = [\n    'django.contrib.admin',\n]\n");

    SettingsWriter::append_installed_app(f.path(), "syntek_auth")
        .expect("append_installed_app should not fail");

    let content = std::fs::read_to_string(f.path()).unwrap();
    assert!(
        content.contains("syntek_auth"),
        "INSTALLED_APPS should contain syntek_auth. Got:\n{content}"
    );
}

#[test]
fn append_installed_app_does_not_duplicate_existing_entry() {
    let f = temp_settings_file("INSTALLED_APPS = [\n    'syntek_auth',\n]\n");

    SettingsWriter::append_installed_app(f.path(), "syntek_auth")
        .expect("append_installed_app should not fail");

    let content = std::fs::read_to_string(f.path()).unwrap();
    let occurrences = content.matches("syntek_auth").count();
    assert_eq!(
        occurrences, 1,
        "syntek_auth should appear exactly once in INSTALLED_APPS, found {occurrences}. Got:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// append_installed_app — C2 false positive prevention
// ---------------------------------------------------------------------------

#[test]
fn append_installed_app_not_fooled_by_comment_containing_label() {
    let f = temp_settings_file(
        "# syntek_auth is required\nINSTALLED_APPS = [\n    'django.contrib.admin',\n]\n",
    );

    SettingsWriter::append_installed_app(f.path(), "syntek_auth").unwrap();

    let content = std::fs::read_to_string(f.path()).unwrap();
    assert!(
        content.contains("'syntek_auth'"),
        "App should be added even when a comment mentions it. Got:\n{content}"
    );
}

#[test]
fn append_installed_app_not_fooled_by_substring_match() {
    // "auth" is a substring of "django.contrib.auth" — must not false-positive.
    let f = temp_settings_file("INSTALLED_APPS = [\n    'django.contrib.auth',\n]\n");

    SettingsWriter::append_installed_app(f.path(), "auth").unwrap();

    let content = std::fs::read_to_string(f.path()).unwrap();
    assert!(
        content.contains("'auth'"),
        "Short label 'auth' should be added since it is not a quoted item. Got:\n{content}"
    );
}

#[test]
fn append_installed_app_empty_label_is_skipped() {
    let original = "INSTALLED_APPS = [\n    'django.contrib.admin',\n]\n";
    let f = temp_settings_file(original);

    // Empty label should not match "" and should not add an empty entry.
    // The function should silently return Ok without modifying the file.
    SettingsWriter::append_installed_app(f.path(), "").unwrap();

    let content = std::fs::read_to_string(f.path()).unwrap();
    // The empty label is detected as "already present" (since empty string would
    // match anything), so the file should be unchanged — but actually our fix
    // explicitly returns Ok for empty label without modifying.
    assert!(
        !content.contains("# Added by syntek-manifest"),
        "Empty label should not cause a write. Got:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// append_installed_app — M6 insertion inside the list
// ---------------------------------------------------------------------------

#[test]
fn append_installed_app_inserts_inside_installed_apps_list() {
    let f =
        temp_settings_file("INSTALLED_APPS = [\n    'django.contrib.admin',\n]\n\nDEBUG = True\n");

    SettingsWriter::append_installed_app(f.path(), "syntek_auth").unwrap();

    let content = std::fs::read_to_string(f.path()).unwrap();
    // The label must appear inside the list (before the `]`), not at end of file.
    let bracket_close = content.find(']').expect("closing ] should exist");
    let label_pos = content.find("'syntek_auth'").expect("label should exist");
    assert!(
        label_pos < bracket_close,
        "App label should be inserted inside INSTALLED_APPS list (before `]`). Got:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// M3 — build_config_block errors when a required setting has no value and no default
// ---------------------------------------------------------------------------

#[test]
fn build_config_block_errors_when_required_setting_has_no_value_and_no_default() {
    // Setting declared with no default; values map is empty.
    let settings = vec![make_setting("STRIPE_SECRET_KEY", "str", None)];
    let vals = values(&[]);

    let result = SettingsWriter::build_config_block("syntek-payments", &settings, &vals);

    assert!(
        matches!(result, Err(ManifestError::MissingField { .. })),
        "Expected MissingField when a required setting has no value and no default. Got: {result:?}"
    );
}

#[test]
fn build_config_block_succeeds_when_setting_has_default_but_no_value() {
    // Setting has a default; no value provided by user — should succeed.
    let settings = vec![make_setting("SESSION_TIMEOUT", "int", Some("1800"))];
    let vals = values(&[]);

    let result = SettingsWriter::build_config_block("syntek-auth", &settings, &vals);

    assert!(
        result.is_ok(),
        "Should succeed when setting has a default even if no explicit value. Got: {result:?}"
    );
    let block = result.unwrap();
    assert!(
        block.contains("1800"),
        "Default value should appear in block"
    );
}

// ---------------------------------------------------------------------------
// M4 — render_value for kind = "int" validates numeric input
// ---------------------------------------------------------------------------

#[test]
fn render_value_int_rejects_non_numeric_string() {
    let result = SettingsWriter::render_value("SESSION_TIMEOUT", "int", "thirty");
    assert!(
        matches!(result, Err(ManifestError::InvalidIntValue { .. })),
        "Expected InvalidIntValue for non-numeric string. Got: {result:?}"
    );
}

#[test]
fn render_value_int_rejects_value_with_suffix() {
    // "1800s" looks like a number but is not parseable as i64.
    let result = SettingsWriter::render_value("SESSION_TIMEOUT", "int", "1800s");
    assert!(
        matches!(result, Err(ManifestError::InvalidIntValue { .. })),
        "Expected InvalidIntValue for value with unit suffix. Got: {result:?}"
    );
}

#[test]
fn render_value_int_accepts_valid_integer() {
    let result = SettingsWriter::render_value("SESSION_TIMEOUT", "int", "3600");
    assert!(
        result.is_ok(),
        "Expected Ok for a valid integer string. Got: {result:?}"
    );
    let rendered = result.unwrap();
    assert!(
        rendered.contains("3600") && !rendered.contains("'3600'"),
        "Integer should be unquoted. Got: {rendered}"
    );
}

#[test]
fn render_value_int_accepts_negative_integer() {
    let result = SettingsWriter::render_value("OFFSET", "int", "-42");
    assert!(
        result.is_ok(),
        "Expected Ok for a negative integer. Got: {result:?}"
    );
}

// ---------------------------------------------------------------------------
// M5 — render_value for kind = "str" escapes single quotes
// ---------------------------------------------------------------------------

#[test]
fn render_value_str_escapes_single_quotes() {
    // A value like "O'Brien" should not produce: 'O'Brien' (syntax error in Python).
    let result = SettingsWriter::render_value("API_OWNER", "str", "O'Brien");
    assert!(
        result.is_ok(),
        "Expected Ok for string with single quote. Got: {result:?}"
    );
    let rendered = result.unwrap();
    // The output should contain an escaped single quote, not a bare unescaped one
    // that would break Python string syntax.
    assert!(
        rendered.contains("\\'"),
        "Single quote in string value should be escaped. Got: {rendered}"
    );
}

#[test]
fn render_value_str_handles_env_call_with_quotes() {
    // env('SYNTEK_API_KEY') contains single quotes — common Django settings pattern.
    let result = SettingsWriter::render_value("API_KEY", "str", "env('SYNTEK_API_KEY')");
    assert!(
        result.is_ok(),
        "Expected Ok for env() call with single quotes. Got: {result:?}"
    );
    let rendered = result.unwrap();
    // Must not produce a bare unescaped inner quote that breaks the outer string delimiter.
    assert!(
        rendered.contains("\\'"),
        "Single quotes inside env() call should be escaped. Got: {rendered}"
    );
}

#[test]
fn render_value_str_plain_string_has_no_unnecessary_escapes() {
    // A plain value with no special characters should not gain backslashes.
    let result = SettingsWriter::render_value("HOST", "str", "localhost");
    let rendered = result.unwrap();
    assert_eq!(
        rendered, "    'HOST': 'localhost',",
        "Plain string should be wrapped in single quotes unchanged. Got: {rendered}"
    );
}

// ---------------------------------------------------------------------------
// MC2 — write_config_block force flag bypasses duplicate check
// ---------------------------------------------------------------------------

#[test]
fn write_config_block_with_force_false_blocks_on_existing_block() {
    let f = temp_settings_file("SYNTEK_AUTH = {\n    'MFA_REQUIRED': True,\n}\n");
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    let result =
        SettingsWriter::write_config_block(f.path(), "syntek-auth", &settings, &vals, false);

    assert!(
        matches!(result, Err(ManifestError::ExistingBlock { .. })),
        "force=false should block write when block already exists. Got: {result:?}"
    );
}

#[test]
fn write_config_block_with_force_true_overwrites_existing_block() {
    let f = temp_settings_file("SYNTEK_AUTH = {\n    'MFA_REQUIRED': True,\n}\n");
    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("false"))];
    let vals = values(&[("MFA_REQUIRED", "false")]);

    let result =
        SettingsWriter::write_config_block(f.path(), "syntek-auth", &settings, &vals, true);

    assert!(
        result.is_ok(),
        "force=true should allow writing even when block already exists. Got: {result:?}"
    );
    let content = std::fs::read_to_string(f.path()).unwrap();
    assert!(
        content.contains("SYNTEK_AUTH"),
        "Block should be present in file after force write. Got:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// MC5 — INSTALLED_APPS label is between list brackets, not after the closing ]
// ---------------------------------------------------------------------------

#[test]
fn append_installed_app_label_is_between_list_brackets() {
    let f = temp_settings_file(
        "INSTALLED_APPS = [\n    'django.contrib.admin',\n    'django.contrib.auth',\n]\n\nDEBUG = True\n",
    );

    SettingsWriter::append_installed_app(f.path(), "syntek_auth").unwrap();

    let content = std::fs::read_to_string(f.path()).unwrap();

    // Locate the INSTALLED_APPS list boundaries.
    let list_open = content
        .find("INSTALLED_APPS")
        .and_then(|pos| content[pos..].find('[').map(|off| pos + off))
        .expect("INSTALLED_APPS opening '[' should exist");
    let list_close = content[list_open..]
        .find(']')
        .map(|off| list_open + off)
        .expect("INSTALLED_APPS closing ']' should exist");

    let label_pos = content
        .find("'syntek_auth'")
        .expect("syntek_auth label should be present");

    assert!(
        label_pos > list_open && label_pos < list_close,
        "App label must appear between '[' and ']' of INSTALLED_APPS, not after the list. \
         list_open={list_open}, label_pos={label_pos}, list_close={list_close}.\nContent:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// MC6 — write_config_block produces syntactically valid Python dict block
// ---------------------------------------------------------------------------

#[test]
fn write_config_block_produces_syntactically_valid_python_block() {
    // End-to-end test: mix of bool, int, and str settings.
    // Validates structural correctness of the generated Python dict.
    let f = temp_settings_file("# Django settings\n");
    let settings = vec![
        make_setting("MFA_REQUIRED", "bool", Some("true")),
        make_setting("SESSION_TIMEOUT", "int", Some("1800")),
        make_setting("HOST", "str", Some("localhost")),
    ];
    let vals = values(&[
        ("MFA_REQUIRED", "false"),
        ("SESSION_TIMEOUT", "900"),
        ("HOST", "example.com"),
    ]);

    SettingsWriter::write_config_block(f.path(), "syntek-auth", &settings, &vals, false).unwrap();

    let content = std::fs::read_to_string(f.path()).unwrap();

    // Structural checks — balanced braces, no bare unquoted words where Python
    // expects True/False for bools.
    assert!(content.contains("SYNTEK_AUTH = {"), "Block header present");
    assert!(content.contains('}'), "Block footer present");

    // Bool rendered as Python boolean literal.
    assert!(content.contains("False"), "bool false → Python False");
    assert!(
        !content.contains(": false,"),
        "bool should not be lowercase"
    );

    // Int rendered without quotes.
    assert!(content.contains("900"), "int value present");
    assert!(!content.contains("'900'"), "int should not be quoted");

    // String rendered with quotes.
    assert!(
        content.contains("'example.com'"),
        "str value should be single-quoted"
    );

    // Brace count balanced — count open and close braces in the block region.
    let block_start = content.find("SYNTEK_AUTH").unwrap();
    let block_content = &content[block_start..];
    let open_braces = block_content.chars().filter(|&c| c == '{').count();
    let close_braces = block_content.chars().filter(|&c| c == '}').count();
    assert_eq!(
        open_braces, close_braces,
        "Python dict braces must be balanced. Open: {open_braces}, Close: {close_braces}"
    );
}

// ---------------------------------------------------------------------------
// MC7 — write_config_block creates file if it does not exist
// ---------------------------------------------------------------------------

#[test]
fn write_config_block_creates_file_if_not_exists() {
    let dir = tempfile::tempdir().expect("failed to create temp dir");
    let path = dir.path().join("new_settings.py");

    // File does not exist yet.
    assert!(!path.exists());

    let settings = vec![make_setting("MFA_REQUIRED", "bool", Some("true"))];
    let vals = values(&[("MFA_REQUIRED", "true")]);

    SettingsWriter::write_config_block(&path, "syntek-auth", &settings, &vals, false)
        .expect("write_config_block should create the file if it does not exist");

    assert!(path.exists(), "File should have been created");
    let content = std::fs::read_to_string(&path).unwrap();
    assert!(
        content.contains("SYNTEK_AUTH"),
        "Created file should contain the config block. Got:\n{content}"
    );
}

// ---------------------------------------------------------------------------
// MC7 — append_installed_app errors on missing file
// ---------------------------------------------------------------------------

#[test]
fn append_installed_app_errors_on_missing_file() {
    let path = std::path::Path::new("/nonexistent/dir/settings.py");

    let result = SettingsWriter::append_installed_app(path, "syntek_auth");

    assert!(
        matches!(result, Err(ManifestError::Io { .. })),
        "append_installed_app should return Io error for a non-existent file. Got: {result:?}"
    );
}
