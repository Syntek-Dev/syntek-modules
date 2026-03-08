//! Duplicate block detector.
//!
//! Scans a target file for an existing `SYNTEK_<MODULE>` block before the
//! settings writer attempts to write. Returns `Err(ManifestError::ExistingBlock)`
//! when a block is detected, allowing the caller to prompt for confirmation.
//!
//! The detection pattern is `SYNTEK_KEY =` — present at the start of a
//! non-comment line — to avoid false positives from commented-out blocks
//! or string values containing the pattern.

use std::fs;
use std::path::Path;

use crate::error::ManifestError;

/// Detects existing `SYNTEK_<MODULE>` blocks in Django settings files.
pub struct DuplicateDetector;

impl DuplicateDetector {
    /// Return `true` if `settings_path` already contains a block for `module_id`.
    ///
    /// The module ID is converted to a settings key (e.g. `"syntek-auth"` →
    /// `"SYNTEK_AUTH"`) and the file is scanned for the pattern `SYNTEK_AUTH =`.
    ///
    /// # Parameters
    /// - `settings_path` — path to the Django `settings.py` file
    /// - `module_id` — the module identifier from the manifest (e.g. `"syntek-auth"`)
    ///
    /// # Returns
    /// `Ok(true)` when the block is present, `Ok(false)` when absent.
    ///
    /// # Errors
    /// - [`ManifestError::Io`] when the file cannot be read
    pub fn has_existing_block(
        settings_path: &Path,
        module_id: &str,
    ) -> Result<bool, ManifestError> {
        let content = fs::read_to_string(settings_path).map_err(|e| ManifestError::Io {
            path: settings_path.display().to_string(),
            message: e.to_string(),
        })?;

        Ok(Self::content_has_block(&content, module_id))
    }

    /// Return the settings key for a given module id.
    ///
    /// Hyphens are replaced with underscores and the entire string is
    /// uppercased, producing a valid Python identifier.
    ///
    /// # Parameters
    /// - `module_id` — the module identifier (e.g. `"syntek-auth"`).
    ///   Must contain only ASCII alphanumeric characters and ASCII hyphens
    ///   (`[a-zA-Z0-9-]+`).
    ///
    /// # Returns
    /// The corresponding Python settings key (e.g. `"SYNTEK_AUTH"`).
    ///
    /// # Errors
    /// - [`ManifestError::InvalidId`] when `module_id` contains non-ASCII or
    ///   non-hyphen characters that would produce an invalid Python identifier.
    pub fn settings_key(module_id: &str) -> Result<String, ManifestError> {
        // M1: validate that the id contains only ASCII alphanumeric characters
        // and ASCII hyphens. Non-ASCII hyphens (e.g. U+2011 NON-BREAKING HYPHEN)
        // would survive the `replace('-', "_")` call unchanged and produce an
        // invalid Python identifier in the generated settings.py.
        if !module_id
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '-')
        {
            return Err(ManifestError::InvalidId {
                id: module_id.to_string(),
            });
        }
        Ok(module_id.replace('-', "_").to_uppercase())
    }

    /// Return `true` if the raw text content contains a block for `module_id`.
    ///
    /// Looks for the pattern `SYNTEK_KEY =` (with a trailing space and equals
    /// sign) at the start of a non-comment line to avoid false positives from
    /// commented-out blocks or string values containing the pattern.
    ///
    /// # Parameters
    /// - `content` — the raw text of a `settings.py` file
    /// - `module_id` — the module identifier from the manifest
    ///
    /// # Returns
    /// `true` when the settings key assignment is found on a non-comment line.
    /// Returns `false` when `module_id` is invalid (non-ASCII characters).
    pub fn content_has_block(content: &str, module_id: &str) -> bool {
        let key = match Self::settings_key(module_id) {
            Ok(k) => k,
            Err(_) => return false,
        };
        let pattern = format!("{key} =");
        // H1: require the pattern to appear at the start of a line (after optional
        // whitespace), not inside a comment or string value.
        content.lines().any(|line| {
            let trimmed = line.trim_start();
            !trimmed.starts_with('#') && trimmed.starts_with(&pattern)
        })
    }
}
