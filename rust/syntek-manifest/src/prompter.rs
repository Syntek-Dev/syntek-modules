//! Interactive option prompter.
//!
//! Renders each [`ManifestOption`] as a human-readable prompt and collects
//! the developer's selections.
//!
//! In non-interactive / headless mode (e.g. CI), [`OptionPrompter::apply_defaults`]
//! applies declared default values without any terminal I/O.
//!
//! Use [`is_ci_environment`] to detect whether the process is running inside a
//! CI system and should suppress interactive prompts.

use std::collections::HashMap;

use crate::manifest::ManifestOption;

/// The resolved values for all declared options, keyed by `option.key`.
pub type OptionValues = HashMap<String, String>;

/// Prompts the developer for each option declared in the manifest.
pub struct OptionPrompter;

impl OptionPrompter {
    /// Build a list of prompt labels from the manifest options.
    ///
    /// Returns one label string per option in declaration order. Each label
    /// includes the option's `label` field and its `kind` type hint in
    /// parentheses so the developer knows what input format is expected.
    ///
    /// # Parameters
    /// - `options` — the slice of options declared in the manifest
    ///
    /// # Returns
    /// A `Vec<String>` containing one formatted label per option.
    pub fn prompt_labels(options: &[ManifestOption]) -> Vec<String> {
        options
            .iter()
            .map(|opt| {
                let default_hint = opt
                    .default
                    .as_deref()
                    .map(|d| format!(" [default: {d}]"))
                    .unwrap_or_default();
                format!("{} ({}){}", opt.label, opt.kind, default_hint)
            })
            .collect()
    }

    /// Return the number of prompts that would be shown for the given options.
    ///
    /// # Parameters
    /// - `options` — the slice of options declared in the manifest
    ///
    /// # Returns
    /// The count of options (one prompt per option).
    pub fn prompt_count(options: &[ManifestOption]) -> usize {
        options.len()
    }

    /// Apply default values for all options without user interaction.
    ///
    /// Only options that declare a `default` value are included in the result.
    /// Options without a default are omitted — the caller must handle the
    /// missing keys explicitly (e.g. by prompting the user separately).
    ///
    /// Used in non-interactive / headless mode (e.g. CI).
    ///
    /// # Parameters
    /// - `options` — the slice of options declared in the manifest
    ///
    /// # Returns
    /// A map of `option.key → default_value` for every option that has a default.
    pub fn apply_defaults(options: &[ManifestOption]) -> OptionValues {
        options
            .iter()
            .filter_map(|opt| {
                opt.default
                    .as_deref()
                    .map(|d| (opt.key.clone(), d.to_string()))
            })
            .collect()
    }
}

/// Return `true` when the current process is running inside a known CI or
/// non-interactive environment.
///
/// MC1: installer binaries call this function to decide whether to suppress
/// interactive prompts and fall back to [`OptionPrompter::apply_defaults`]
/// instead of reading from stdin.
///
/// The following environment variables are checked (presence is sufficient;
/// the value is not inspected):
///
/// | Variable         | Set by                               |
/// |------------------|--------------------------------------|
/// | `CI`             | GitHub Actions, CircleCI, Travis CI  |
/// | `GITHUB_ACTIONS` | GitHub Actions (redundant but explicit) |
/// | `NO_COLOR`       | Terminals that disable ANSI colour — treated as non-interactive |
///
/// # Returns
/// `true` when any of the listed environment variables is set to a non-empty
/// value in the process environment.
pub fn is_ci_environment() -> bool {
    for var in &["CI", "GITHUB_ACTIONS", "NO_COLOR"] {
        if let Ok(val) = std::env::var(var)
            && !val.is_empty()
        {
            return true;
        }
    }
    false
}
