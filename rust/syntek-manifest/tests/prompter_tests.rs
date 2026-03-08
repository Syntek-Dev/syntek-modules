//! US074 — Option prompter tests
//!
//! Acceptance criterion:
//!   Given a developer runs a module's installer binary with no arguments
//!   When the binary starts
//!   Then it presents an interactive prompt for each install option declared
//!   in the manifest.
//!
//! RED phase — tests will fail until the stub is replaced with real logic.

use std::sync::Mutex;

use syntek_manifest::manifest::ManifestOption;
use syntek_manifest::prompter::{OptionPrompter, is_ci_environment};

/// Serialises all tests that mutate process-wide environment variables.
/// `std::env::set/remove_var` is not thread-safe across concurrent tests.
static ENV_MUTEX: Mutex<()> = Mutex::new(());

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn make_option(key: &str, label: &str, kind: &str, default: Option<&str>) -> ManifestOption {
    ManifestOption {
        key: key.to_string(),
        label: label.to_string(),
        kind: kind.to_string(),
        default: default.map(str::to_string),
    }
}

// ---------------------------------------------------------------------------
// prompt_labels — one label per option
// ---------------------------------------------------------------------------

#[test]
fn prompt_labels_returns_one_label_per_option() {
    let options = vec![
        make_option(
            "MFA_REQUIRED",
            "Require MFA for all users?",
            "bool",
            Some("true"),
        ),
        make_option(
            "SESSION_TIMEOUT",
            "Session timeout (seconds)",
            "int",
            Some("1800"),
        ),
    ];

    let labels = OptionPrompter::prompt_labels(&options);

    assert_eq!(
        labels.len(),
        2,
        "Expected one label per option, got {}: {labels:?}",
        labels.len()
    );
}

#[test]
fn prompt_labels_contains_option_label_text() {
    let options = vec![make_option(
        "MFA_REQUIRED",
        "Require MFA for all users?",
        "bool",
        Some("true"),
    )];

    let labels = OptionPrompter::prompt_labels(&options);

    assert!(
        labels
            .first()
            .map(|l| l.contains("Require MFA"))
            .unwrap_or(false),
        "Label should contain the option label text. Got: {labels:?}"
    );
}

#[test]
fn prompt_labels_for_empty_options_returns_empty_vec() {
    let labels = OptionPrompter::prompt_labels(&[]);
    assert!(labels.is_empty());
}

// ---------------------------------------------------------------------------
// prompt_count — correct count
// ---------------------------------------------------------------------------

#[test]
fn prompt_count_equals_number_of_options() {
    let options = vec![
        make_option("A", "Option A", "bool", None),
        make_option("B", "Option B", "str", None),
        make_option("C", "Option C", "int", None),
    ];

    let count = OptionPrompter::prompt_count(&options);

    assert_eq!(count, 3, "prompt_count should equal the number of options");
}

#[test]
fn prompt_count_is_zero_for_no_options() {
    assert_eq!(OptionPrompter::prompt_count(&[]), 0);
}

// ---------------------------------------------------------------------------
// apply_defaults — headless / CI mode
// ---------------------------------------------------------------------------

#[test]
fn apply_defaults_returns_one_entry_per_option_with_default() {
    let options = vec![
        make_option("MFA_REQUIRED", "Require MFA?", "bool", Some("true")),
        make_option("SESSION_TIMEOUT", "Session timeout", "int", Some("1800")),
    ];

    let values = OptionPrompter::apply_defaults(&options);

    assert_eq!(
        values.len(),
        2,
        "apply_defaults should return one entry per option that has a default"
    );
    assert_eq!(values.get("MFA_REQUIRED").map(String::as_str), Some("true"));
    assert_eq!(
        values.get("SESSION_TIMEOUT").map(String::as_str),
        Some("1800")
    );
}

#[test]
fn apply_defaults_skips_options_without_defaults() {
    let options = vec![make_option("CUSTOM_KEY", "Enter custom key", "str", None)];

    let values = OptionPrompter::apply_defaults(&options);

    assert!(
        !values.contains_key("CUSTOM_KEY"),
        "Options without defaults should not appear in the map"
    );
}

#[test]
fn apply_defaults_for_empty_options_returns_empty_map() {
    let values = OptionPrompter::apply_defaults(&[]);
    assert!(values.is_empty());
}

// ---------------------------------------------------------------------------
// Label ordering is preserved
// ---------------------------------------------------------------------------

#[test]
fn prompt_labels_preserves_declaration_order() {
    let options = vec![
        make_option("FIRST", "First option", "bool", None),
        make_option("SECOND", "Second option", "bool", None),
        make_option("THIRD", "Third option", "bool", None),
    ];

    let labels = OptionPrompter::prompt_labels(&options);

    assert_eq!(labels.len(), 3);
    assert!(
        labels[0].contains("First"),
        "First label should reference first option"
    );
    assert!(
        labels[1].contains("Second"),
        "Second label should reference second option"
    );
    assert!(
        labels[2].contains("Third"),
        "Third label should reference third option"
    );
}

// ---------------------------------------------------------------------------
// MC1 — is_ci_environment detects CI and non-interactive environments
// ---------------------------------------------------------------------------

#[test]
fn is_ci_environment_returns_true_when_ci_env_set() {
    let _guard = ENV_MUTEX.lock().unwrap();
    let original = std::env::var("CI").ok();

    unsafe {
        std::env::set_var("CI", "true");
    }

    let result = is_ci_environment();

    unsafe {
        match original {
            Some(val) => std::env::set_var("CI", val),
            None => std::env::remove_var("CI"),
        }
    }

    assert!(
        result,
        "is_ci_environment should return true when CI env var is set"
    );
}

#[test]
fn is_ci_environment_returns_true_when_github_actions_set() {
    let _guard = ENV_MUTEX.lock().unwrap();
    let original = std::env::var("GITHUB_ACTIONS").ok();

    unsafe {
        std::env::set_var("GITHUB_ACTIONS", "true");
    }

    let result = is_ci_environment();

    unsafe {
        match original {
            Some(val) => std::env::set_var("GITHUB_ACTIONS", val),
            None => std::env::remove_var("GITHUB_ACTIONS"),
        }
    }

    assert!(
        result,
        "is_ci_environment should return true when GITHUB_ACTIONS is set"
    );
}

#[test]
fn is_ci_environment_returns_false_when_no_env_set() {
    let _guard = ENV_MUTEX.lock().unwrap();
    let ci = std::env::var("CI").ok();
    let ga = std::env::var("GITHUB_ACTIONS").ok();
    let nc = std::env::var("NO_COLOR").ok();

    unsafe {
        std::env::remove_var("CI");
        std::env::remove_var("GITHUB_ACTIONS");
        std::env::remove_var("NO_COLOR");
    }

    let result = is_ci_environment();

    unsafe {
        if let Some(v) = ci {
            std::env::set_var("CI", v);
        }
        if let Some(v) = ga {
            std::env::set_var("GITHUB_ACTIONS", v);
        }
        if let Some(v) = nc {
            std::env::set_var("NO_COLOR", v);
        }
    }

    assert!(
        !result,
        "is_ci_environment should return false when no CI env vars are set"
    );
}

#[test]
fn apply_defaults_provides_ci_fallback_values() {
    // MC1: when is_ci_environment() returns true, the caller should use
    // apply_defaults() rather than prompting. This test verifies that
    // apply_defaults produces a complete map for options with defaults —
    // the pattern used by installer binaries in CI mode.
    let options = vec![
        make_option("MFA_REQUIRED", "Require MFA?", "bool", Some("true")),
        make_option("SESSION_TIMEOUT", "Session timeout", "int", Some("1800")),
    ];

    let defaults = OptionPrompter::apply_defaults(&options);

    assert_eq!(
        defaults.len(),
        2,
        "CI fallback should populate all options that have defaults"
    );
    assert_eq!(
        defaults.get("MFA_REQUIRED").map(String::as_str),
        Some("true")
    );
    assert_eq!(
        defaults.get("SESSION_TIMEOUT").map(String::as_str),
        Some("1800")
    );
}
