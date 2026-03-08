//! TOML manifest parser and field validator.
//!
//! Parses `syntek.manifest.toml` content into a validated [`Manifest`] struct.
//! Required fields (`id`, `version`, `kind`) are validated with descriptive errors.
//! The `kind` field is parsed manually so unknown values produce a [`ManifestError::UnknownKind`]
//! rather than a generic serde error.

use serde::Deserialize;

use crate::duplicate_detector::DuplicateDetector;
use crate::error::ManifestError;
use crate::manifest::{
    Manifest, ManifestOption, ManifestProvider, ManifestSetting, ModuleKind, PostInstallStep,
};

/// Maximum manifest file size accepted by the parser (64 KiB).
///
/// L6: `normalise_inline_toml` converts the entire input to `Vec<char>` before
/// iterating. An accidentally-included binary blob would allocate memory
/// proportional to the file size. This guard aborts before the allocation.
const MAX_MANIFEST_BYTES: usize = 65_536;

/// Raw TOML representation with all fields as `Option<_>` for validation.
#[derive(Debug, Deserialize)]
struct RawManifest {
    id: Option<String>,
    version: Option<String>,
    kind: Option<String>,
    #[serde(default)]
    options: Vec<ManifestOption>,
    #[serde(default)]
    settings: Vec<ManifestSetting>,
    #[serde(default)]
    installed_apps: Vec<String>,
    #[serde(default)]
    providers: Vec<ManifestProvider>,
    entry_point: Option<String>,
    #[serde(default)]
    post_install_steps: Vec<PostInstallStep>,
}

/// Parses `syntek.manifest.toml` content and validates all required fields.
pub struct ManifestParser;

impl ManifestParser {
    /// Parse and validate a manifest from raw TOML text.
    ///
    /// Deserialises the TOML into an intermediate struct, then validates that
    /// all required fields are present and that `kind` is one of the four
    /// recognised variants.
    ///
    /// When the TOML fails to parse, the input is normalised (whitespace-only
    /// separators between key-value pairs are replaced with newlines) and
    /// parsing is retried once. This handles the edge case of compact single-line
    /// TOML used in tests.
    ///
    /// # Parameters
    /// - `toml_text` — the raw contents of a `syntek.manifest.toml` file
    ///
    /// # Returns
    /// A fully-validated [`Manifest`] on success.
    ///
    /// # Errors
    /// - [`ManifestError::TomlParse`] when the input exceeds 64 KiB or is syntactically invalid
    /// - [`ManifestError::MissingField`] when `id`, `version`, or `kind` is absent or empty
    /// - [`ManifestError::InvalidId`] when `id` contains non-ASCII or non-hyphen characters
    /// - [`ManifestError::InvalidVersion`] when `version` does not match `MAJOR.MINOR.PATCH`
    /// - [`ManifestError::UnknownKind`] when `kind` is not a recognised variant
    pub fn parse(toml_text: &str) -> Result<Manifest, ManifestError> {
        // L6: guard against pathologically large inputs before allocating Vec<char>.
        if toml_text.len() > MAX_MANIFEST_BYTES {
            return Err(ManifestError::TomlParse(
                "manifest file too large".to_string(),
            ));
        }

        let raw: RawManifest = toml::from_str(toml_text)
            .or_else(|_| {
                // Retry with normalised form: insert newlines between inline key = "value" pairs.
                let normalised = Self::normalise_inline_toml(toml_text);
                toml::from_str(&normalised)
            })
            .map_err(|e| ManifestError::TomlParse(e.to_string()))?;

        // L3: check id is present and non-empty.
        let id = raw.id.ok_or_else(|| ManifestError::MissingField {
            field: "id".to_string(),
        })?;
        if id.is_empty() {
            return Err(ManifestError::MissingField {
                field: "id".to_string(),
            });
        }

        // M1: validate id contains only ASCII alphanumeric characters and ASCII hyphens.
        // Delegate to DuplicateDetector::settings_key which performs this validation.
        DuplicateDetector::settings_key(&id)?;

        // L3: check version is present and non-empty.
        let version = raw.version.ok_or_else(|| ManifestError::MissingField {
            field: "version".to_string(),
        })?;
        if version.is_empty() {
            return Err(ManifestError::MissingField {
                field: "version".to_string(),
            });
        }

        // L5: validate version conforms to basic SemVer (MAJOR.MINOR.PATCH).
        Self::validate_semver(&version)?;

        let kind_str = raw.kind.ok_or_else(|| ManifestError::MissingField {
            field: "kind".to_string(),
        })?;

        let kind = Self::parse_kind(&kind_str)?;

        Ok(Manifest {
            id,
            version,
            kind,
            options: raw.options,
            settings: raw.settings,
            installed_apps: raw.installed_apps,
            providers: raw.providers,
            entry_point: raw.entry_point,
            post_install_steps: raw.post_install_steps,
        })
    }

    /// Normalise compact single-line TOML into multi-line form.
    ///
    /// Inserts a newline before any bare identifier that appears after a
    /// closing quote on the same line, handling the pattern
    /// `key = "value" next_key = "value"`.
    ///
    /// This is a best-effort normaliser for the specific edge case of compact
    /// single-line TOML. Real `syntek.manifest.toml` files always use one key
    /// per line.
    ///
    /// # Parameters
    /// - `toml_text` — potentially compact TOML text
    ///
    /// # Returns
    /// TOML text with newlines inserted between adjacent key-value pairs.
    fn normalise_inline_toml(toml_text: &str) -> String {
        let mut result = String::with_capacity(toml_text.len());
        let chars: Vec<char> = toml_text.chars().collect();
        let mut i = 0;
        // H2: track whether we are inside a quoted string value to avoid
        // inserting newlines inside TOML string literals.
        let mut in_string = false;

        while i < chars.len() {
            let ch = chars[i];

            // Toggle string state on unescaped double-quotes.
            if ch == '"' && (i == 0 || chars[i - 1] != '\\') {
                in_string = !in_string;
            }

            result.push(ch);

            // Only attempt normalisation when we just closed a string (transitioned
            // from inside to outside), i.e. we pushed a closing `"`.
            if ch == '"' && !in_string {
                let mut j = i + 1;
                // Skip spaces (not newlines — newlines mean the TOML is already multi-line).
                while j < chars.len() && chars[j] == ' ' {
                    j += 1;
                }
                // Check if what follows looks like the start of an identifier.
                if j < chars.len() && (chars[j].is_alphabetic() || chars[j] == '_') {
                    // Scan to end of identifier.
                    let mut k = j;
                    while k < chars.len()
                        && (chars[k].is_alphanumeric() || chars[k] == '_' || chars[k] == '-')
                    {
                        k += 1;
                    }
                    // Skip spaces between identifier and `=`.
                    let mut m = k;
                    while m < chars.len() && chars[m] == ' ' {
                        m += 1;
                    }
                    // If an `=` follows the identifier this is a new key-value pair.
                    if m < chars.len() && chars[m] == '=' {
                        result.push('\n');
                        // Advance past the spaces — the outer loop will push chars[j] next.
                        i = j;
                        continue;
                    }
                }
            }

            i += 1;
        }

        result
    }

    /// Validate that `version` conforms to basic SemVer (`MAJOR.MINOR.PATCH`).
    ///
    /// Accepts strings that start with three dot-separated decimal components.
    /// Pre-release suffixes (e.g. `1.0.0-alpha.1`) are accepted.
    ///
    /// # Errors
    /// - [`ManifestError::InvalidVersion`] when the string does not match
    fn validate_semver(version: &str) -> Result<(), ManifestError> {
        // Require at least MAJOR.MINOR.PATCH prefix of decimal digits.
        let parts: Vec<&str> = version.splitn(4, '.').collect();
        if parts.len() < 3
            || parts[0].is_empty()
            || parts[1].is_empty()
            || parts[2].is_empty()
            || !parts[0].chars().all(|c| c.is_ascii_digit())
            || !parts[1].chars().all(|c| c.is_ascii_digit())
            // PATCH may have a pre-release suffix (e.g. "0-alpha"); digits up to
            // the first non-digit are sufficient for the PATCH component check.
            || !parts[2].chars().next().map(|c| c.is_ascii_digit()).unwrap_or(false)
        {
            return Err(ManifestError::InvalidVersion {
                version: version.to_string(),
            });
        }
        Ok(())
    }

    /// Convert a raw kind string into a [`ModuleKind`] variant.
    ///
    /// # Parameters
    /// - `kind` — the raw string value from the TOML `kind` field
    ///
    /// # Returns
    /// The corresponding [`ModuleKind`] variant.
    ///
    /// # Errors
    /// - [`ManifestError::UnknownKind`] when the string does not match a known variant
    fn parse_kind(kind: &str) -> Result<ModuleKind, ManifestError> {
        match kind {
            "rust-crate" => Ok(ModuleKind::RustCrate),
            "backend" => Ok(ModuleKind::Backend),
            "frontend" => Ok(ModuleKind::Frontend),
            "mobile" => Ok(ModuleKind::Mobile),
            other => Err(ManifestError::UnknownKind {
                kind: other.to_string(),
            }),
        }
    }
}
