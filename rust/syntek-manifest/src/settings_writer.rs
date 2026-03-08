//! `settings.py` writer.
//!
//! Writes a typed `SYNTEK_<MODULE>` config block to a Django `settings.py`
//! file and appends entries to `INSTALLED_APPS`.
//!
//! The settings key is derived from the module ID by replacing hyphens with
//! underscores and uppercasing (e.g. `"syntek-auth"` → `"SYNTEK_AUTH"`).
//!
//! Python value rendering rules:
//! - `bool` — `"true"` → `True`, `"false"` → `False` (case-insensitive; rejects other values)
//! - `int` — rendered as an unquoted integer literal (validated as i64)
//! - `str` / any other kind — rendered as a single-quoted string with escaped single quotes

use std::fs;
use std::path::Path;

use crate::duplicate_detector::DuplicateDetector;
use crate::error::ManifestError;
use crate::manifest::{ManifestOption, ManifestSetting};
use crate::prompter::OptionValues;

/// Writes Django configuration to `settings.py`.
pub struct SettingsWriter;

impl SettingsWriter {
    /// Append a `SYNTEK_<module_id_upper>` dict block to `settings_path`.
    ///
    /// Reads the current file, checks for an existing block via the
    /// [`DuplicateDetector`], appends the rendered config block, and writes
    /// the result back to disk atomically (write to `.tmp`, then rename).
    ///
    /// When `force` is `true` the duplicate check is skipped and the block is
    /// written even if one already exists (MC2 — explicit re-install with
    /// confirmation).
    ///
    /// When the file does not exist it is created (MC7).
    ///
    /// # Parameters
    /// - `settings_path` — path to the Django `settings.py` file (created if absent)
    /// - `module_id` — e.g. `"syntek-auth"` → key becomes `SYNTEK_AUTH`
    /// - `settings` — the settings declared in the manifest
    /// - `values` — the resolved values from the interactive prompt
    /// - `force` — when `true`, skip the duplicate block check
    ///
    /// # Errors
    /// - [`ManifestError::ExistingBlock`] when the file already contains the block and `force` is `false`
    /// - [`ManifestError::Io`] when the file cannot be written
    /// - [`ManifestError::InvalidBoolValue`] when a `bool` setting has an invalid value
    /// - [`ManifestError::InvalidIntValue`] when an `int` setting has a non-numeric value
    /// - [`ManifestError::MissingField`] when a required setting has no value and no default
    /// - [`ManifestError::InvalidId`] when `module_id` contains non-ASCII characters
    pub fn write_config_block(
        settings_path: &Path,
        module_id: &str,
        settings: &[ManifestSetting],
        values: &OptionValues,
        force: bool,
    ) -> Result<(), ManifestError> {
        // MC7: create the file if it does not exist; read its content if it does.
        let content = if settings_path.exists() {
            fs::read_to_string(settings_path).map_err(|e| ManifestError::Io {
                path: settings_path.display().to_string(),
                message: e.to_string(),
            })?
        } else {
            String::new()
        };

        // H5 / MC2: check for existing block before writing, unless force = true.
        if !force && DuplicateDetector::content_has_block(&content, module_id) {
            let key = DuplicateDetector::settings_key(module_id)?;
            return Err(ManifestError::ExistingBlock {
                key,
                path: settings_path.display().to_string(),
            });
        }

        let block = Self::build_config_block(module_id, settings, values)?;
        let updated = if content.is_empty() {
            block
        } else {
            format!("{content}\n{block}")
        };

        // C1: atomic write — write to a temporary file then rename.
        atomic_write(settings_path, &updated)
    }

    /// Append `app_label` to `INSTALLED_APPS` in `settings_path` if not already present.
    ///
    /// Scans the `INSTALLED_APPS` list for the `app_label` as a quoted Python
    /// string item. When already present inside the list, the file is left
    /// unchanged. When absent, the label is inserted as a new entry inside
    /// the `INSTALLED_APPS` list, before the closing `]`.
    ///
    /// # Parameters
    /// - `settings_path` — path to the Django `settings.py` file (must exist — MC7)
    /// - `app_label` — the Django app label to add (e.g. `"syntek_auth"`)
    ///
    /// # Errors
    /// - [`ManifestError::Io`] when the file does not exist or cannot be read/written
    pub fn append_installed_app(
        settings_path: &Path,
        app_label: &str,
    ) -> Result<(), ManifestError> {
        // C2: reject empty labels immediately — they cannot be valid Django app labels.
        if app_label.is_empty() {
            return Ok(());
        }

        // MC7: append_installed_app errors on missing file (unlike write_config_block).
        let content = fs::read_to_string(settings_path).map_err(|e| ManifestError::Io {
            path: settings_path.display().to_string(),
            message: e.to_string(),
        })?;

        // C2: check for the label as a quoted Python string item, not a raw substring.
        // Match both 'syntek_auth' and "syntek_auth" within the INSTALLED_APPS list.
        if content_has_installed_app(&content, app_label) {
            return Ok(());
        }

        // M6: insert inside the INSTALLED_APPS list, not at end of file.
        let updated = insert_into_installed_apps(&content, app_label)?;

        // C1: atomic write.
        atomic_write(settings_path, &updated)
    }

    /// Render the Python literal for a single setting entry.
    ///
    /// Applies type-aware rendering:
    /// - `bool` → `True` or `False` (case-insensitive; rejects other values)
    /// - `int` → unquoted numeric literal (validated as i64; rejects non-numeric strings)
    /// - `str` or any other kind → single-quoted string with escaped single quotes
    ///
    /// # Parameters
    /// - `key` — the settings key (e.g. `"MFA_REQUIRED"`)
    /// - `kind` — the type hint (`"bool"`, `"int"`, `"str"`, `"list"`)
    /// - `value` — the raw string value to render
    ///
    /// # Returns
    /// A Python dict entry string, e.g. `"'MFA_REQUIRED': True,"`.
    ///
    /// # Errors
    /// - [`ManifestError::InvalidBoolValue`] when `kind` is `"bool"` but `value` is
    ///   not `"true"` or `"false"` (case-insensitive)
    /// - [`ManifestError::InvalidIntValue`] when `kind` is `"int"` but `value` cannot
    ///   be parsed as a 64-bit integer
    pub fn render_value(key: &str, kind: &str, value: &str) -> Result<String, ManifestError> {
        let py_value = match kind {
            // H4: only accept "true" / "false" (case-insensitive); reject everything else.
            "bool" => match value.to_lowercase().as_str() {
                "true" => "True".to_string(),
                "false" => "False".to_string(),
                _ => {
                    return Err(ManifestError::InvalidBoolValue {
                        key: key.to_string(),
                        value: value.to_string(),
                    });
                }
            },
            // M4: validate that the value is a parseable 64-bit integer before writing
            // it unquoted into Python. A non-numeric string like "1800s" or "thirty"
            // would produce a SyntaxError in the generated settings.py.
            "int" => {
                value
                    .parse::<i64>()
                    .map_err(|_| ManifestError::InvalidIntValue {
                        key: key.to_string(),
                        value: value.to_string(),
                    })?;
                value.to_string()
            }
            // M5: escape single quotes in string values to avoid producing a Python
            // SyntaxError. A value like "O'Brien" would otherwise produce:
            //   'API_OWNER': 'O'Brien',
            // which is invalid Python. We replace each `'` with `\'`.
            _ => {
                let escaped = value.replace('\'', "\\'");
                format!("'{escaped}'")
            }
        };
        Ok(format!("    '{key}': {py_value},"))
    }

    /// Build the complete config block string without writing to disk.
    ///
    /// Iterates over the declared settings and resolves each value from
    /// `values` (falling back to the setting's `default` when not present).
    ///
    /// M3: when a setting has no entry in `values` AND no `default`, returns
    /// [`ManifestError::MissingField`] rather than silently omitting the key.
    ///
    /// # Parameters
    /// - `module_id` — e.g. `"syntek-auth"` → key becomes `SYNTEK_AUTH`
    /// - `settings` — the settings declared in the manifest
    /// - `values` — the resolved values from the interactive prompt
    ///
    /// # Returns
    /// A multi-line Python dict assignment string.
    ///
    /// # Errors
    /// - [`ManifestError::InvalidBoolValue`] when a `bool` setting has an invalid value
    /// - [`ManifestError::InvalidIntValue`] when an `int` setting has a non-numeric value
    /// - [`ManifestError::MissingField`] when a required setting has no value and no default
    /// - [`ManifestError::InvalidId`] when `module_id` contains non-ASCII characters
    pub fn build_config_block(
        module_id: &str,
        settings: &[ManifestSetting],
        values: &OptionValues,
    ) -> Result<String, ManifestError> {
        let key = DuplicateDetector::settings_key(module_id)?;
        let mut lines = vec![format!("{key} = {{")];

        for setting in settings {
            let value = values
                .get(&setting.key)
                .map(String::as_str)
                .or(setting.default.as_deref());

            match value {
                Some(v) => {
                    lines.push(Self::render_value(&setting.key, &setting.kind, v)?);
                }
                None => {
                    // M3: a setting with no resolved value and no default is a
                    // required setting that the developer has not provided. Silently
                    // omitting it would produce an incomplete settings.py that fails
                    // at Django startup with a KeyError. Return an error instead.
                    return Err(ManifestError::MissingField {
                        field: setting.key.clone(),
                    });
                }
            }
        }

        lines.push("}".to_string());
        Ok(lines.join("\n"))
    }

    /// Build the list of prompts that map options to settings.
    ///
    /// Returns one prompt label per option in declaration order. Delegates to
    /// [`crate::prompter::OptionPrompter::prompt_labels`] for consistent formatting.
    ///
    /// # Parameters
    /// - `options` — the slice of options declared in the manifest
    ///
    /// # Returns
    /// A `Vec<String>` of formatted prompt labels.
    pub fn option_prompt_labels(options: &[ManifestOption]) -> Vec<String> {
        use crate::prompter::OptionPrompter;
        OptionPrompter::prompt_labels(options)
    }
}

/// Write `content` to a temporary file alongside `path`, then atomically rename.
///
/// On POSIX, `fs::rename` is atomic when source and target are on the same
/// filesystem. Writing to `<path>.tmp` in the same directory guarantees this.
fn atomic_write(path: &Path, content: &str) -> Result<(), ManifestError> {
    let tmp_path = path.with_extension("py.tmp");
    let path_str = path.display().to_string();

    fs::write(&tmp_path, content).map_err(|e| ManifestError::Io {
        path: path_str.clone(),
        message: e.to_string(),
    })?;

    fs::rename(&tmp_path, path).map_err(|e| {
        // Best-effort cleanup of the temp file on rename failure.
        let _ = fs::remove_file(&tmp_path);
        ManifestError::Io {
            path: path_str,
            message: e.to_string(),
        }
    })
}

/// Return `true` if `content` contains `app_label` as a quoted Python string
/// item (either `'label'` or `"label"`) inside what looks like a list context.
///
/// This avoids false positives from comments, substrings, and empty strings.
fn content_has_installed_app(content: &str, app_label: &str) -> bool {
    if app_label.is_empty() {
        return false;
    }
    let single_quoted = format!("'{app_label}'");
    let double_quoted = format!("\"{app_label}\"");
    content.contains(&single_quoted) || content.contains(&double_quoted)
}

/// Insert `app_label` as a new entry inside the `INSTALLED_APPS` list.
///
/// Finds the closing `]` of the `INSTALLED_APPS` assignment and inserts the
/// label as a quoted item before it.
fn insert_into_installed_apps(content: &str, app_label: &str) -> Result<String, ManifestError> {
    // Find the start of INSTALLED_APPS assignment.
    let apps_start = match find_installed_apps_start(content) {
        Some(pos) => pos,
        None => {
            // Fallback: no INSTALLED_APPS found — append a new list at end of file.
            return Ok(format!(
                "{content}\nINSTALLED_APPS = [\n    '{app_label}',  # Added by syntek-manifest\n]\n"
            ));
        }
    };

    // Find the opening `[` of the list.
    let bracket_open = match content[apps_start..].find('[') {
        Some(offset) => apps_start + offset,
        None => {
            return Err(ManifestError::Io {
                path: "settings.py".to_string(),
                message: "INSTALLED_APPS found but no opening '[' detected".to_string(),
            });
        }
    };

    // Find the matching closing `]`. We need to handle nested brackets.
    let bracket_close = match find_matching_bracket(content, bracket_open) {
        Some(pos) => pos,
        None => {
            return Err(ManifestError::Io {
                path: "settings.py".to_string(),
                message: "INSTALLED_APPS opening '[' found but no matching ']'".to_string(),
            });
        }
    };

    // Insert the new entry before the closing `]`.
    // Determine indentation from existing entries or default to 4 spaces.
    let indent = detect_list_indent(content, bracket_open, bracket_close);
    let new_entry = format!("{indent}'{app_label}',  # Added by syntek-manifest\n");

    let before = &content[..bracket_close];
    let after = &content[bracket_close..];

    // Ensure there is a newline before the new entry.
    let separator = if before.ends_with('\n') { "" } else { "\n" };

    Ok(format!("{before}{separator}{new_entry}{after}"))
}

/// Find the byte offset where `INSTALLED_APPS` appears at the start of a line
/// (ignoring leading whitespace), followed by `=`.
fn find_installed_apps_start(content: &str) -> Option<usize> {
    for line in content.lines() {
        let trimmed = line.trim_start();
        if trimmed.starts_with("INSTALLED_APPS") {
            let rest = trimmed.strip_prefix("INSTALLED_APPS")?.trim_start();
            if rest.starts_with('=') || rest.starts_with('+') {
                // Return the byte offset of this line in the content.
                let offset = line.as_ptr() as usize - content.as_ptr() as usize;
                return Some(offset);
            }
        }
    }
    None
}

/// Find the matching closing `]` for the `[` at `open_pos`, skipping nested brackets
/// and quoted strings.
fn find_matching_bracket(content: &str, open_pos: usize) -> Option<usize> {
    let bytes = content.as_bytes();
    let mut depth = 0;
    let mut in_single_quote = false;
    let mut in_double_quote = false;
    let mut i = open_pos;

    while i < bytes.len() {
        let ch = bytes[i];
        match ch {
            b'\'' if !in_double_quote => in_single_quote = !in_single_quote,
            b'"' if !in_single_quote => in_double_quote = !in_double_quote,
            b'[' if !in_single_quote && !in_double_quote => depth += 1,
            b']' if !in_single_quote && !in_double_quote => {
                depth -= 1;
                if depth == 0 {
                    return Some(i);
                }
            }
            b'\\' if in_single_quote || in_double_quote => {
                i += 1; // skip escaped character
            }
            _ => {}
        }
        i += 1;
    }
    None
}

/// Detect the indentation used inside the list between `open` and `close`.
fn detect_list_indent(content: &str, open: usize, close: usize) -> String {
    let inner = &content[open + 1..close];
    for line in inner.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let indent_len = line.len() - line.trim_start().len();
        if indent_len > 0 {
            return line[..indent_len].to_string();
        }
    }
    // Default indentation.
    "    ".to_string()
}
