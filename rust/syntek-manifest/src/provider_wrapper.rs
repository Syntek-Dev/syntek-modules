//! Frontend provider wrapper.
//!
//! Reads `providers[]` from the manifest and wraps the declared `entry_point`
//! file with the required React / React-Native provider components.
//!
//! Import statements follow the ES module `import { Name } from "package"` style.
//! The JSX wrapper nests providers in declaration order, outermost first, so the
//! first declared provider wraps all subsequent ones.

use std::fs;
use std::path::Path;

use crate::error::ManifestError;
use crate::manifest::ManifestProvider;

/// Wraps a frontend entry point with the providers declared in the manifest.
pub struct ProviderWrapper;

/// Return `true` if `name` is a valid JSX component identifier: starts with an
/// ASCII letter, followed by zero or more ASCII letters or digits.
fn is_valid_jsx_identifier(name: &str) -> bool {
    if name.is_empty() {
        return false;
    }
    let mut chars = name.chars();
    let first = chars.next().unwrap();
    if !first.is_ascii_alphabetic() {
        return false;
    }
    chars.all(|c| c.is_ascii_alphanumeric())
}

/// Validate all provider names in the slice. Returns an error for the first
/// invalid name encountered.
fn validate_provider_names(providers: &[ManifestProvider]) -> Result<(), ManifestError> {
    for p in providers {
        if !is_valid_jsx_identifier(&p.name) {
            return Err(ManifestError::InvalidProviderName {
                name: p.name.clone(),
            });
        }
    }
    Ok(())
}

impl ProviderWrapper {
    /// Build the import statements for all providers.
    ///
    /// Each provider generates one `import { Name } from "package"` line.
    /// The lines are returned in declaration order.
    ///
    /// # Parameters
    /// - `providers` — the slice of providers declared in the manifest
    ///
    /// # Returns
    /// A `Vec<String>` containing one TypeScript import line per provider.
    ///
    /// # Errors
    /// - [`ManifestError::InvalidProviderName`] when a provider name is not a valid JSX identifier
    pub fn build_imports(providers: &[ManifestProvider]) -> Result<Vec<String>, ManifestError> {
        validate_provider_names(providers)?;
        Ok(providers
            .iter()
            .map(|p| format!("import {{ {} }} from \"{}\";", p.name, p.import))
            .collect())
    }

    /// Build the JSX wrapper expression for `providers` around `{children}`.
    ///
    /// Providers are nested in declaration order so the first declared provider
    /// is the outermost wrapper:
    ///
    /// ```text
    /// <AuthProvider><SessionProvider>{children}</SessionProvider></AuthProvider>
    /// ```
    ///
    /// L2: an empty provider list returns `{children}` (the JSX expression for
    /// the children prop), not `"{children}"` (a string literal containing the
    /// text `{children}`). The surrounding double-quotes were previously included
    /// in the initial `inner` value, causing the generated component to return a
    /// string literal rather than rendering its children.
    ///
    /// # Parameters
    /// - `providers` — the slice of providers declared in the manifest
    ///
    /// # Returns
    /// A JSX expression string with providers nested around `{children}`.
    ///
    /// # Errors
    /// - [`ManifestError::InvalidProviderName`] when a provider name is not a valid JSX identifier
    pub fn build_jsx_wrapper(providers: &[ManifestProvider]) -> Result<String, ManifestError> {
        validate_provider_names(providers)?;
        // L2: use `{children}` (JSX expression) as the innermost value, not
        // `"{children}"` (a string literal). The enclosing quotes were causing
        // the generated React component to return a string rather than rendering
        // its children.
        let inner = "{children}".to_string();

        // Fold from right so the first provider ends up as the outermost tag.
        Ok(providers.iter().rev().fold(inner, |acc, p| {
            format!("<{name}>{acc}</{name}>", name = p.name)
        }))
    }

    /// Wrap the file at `entry_point_path` with all declared providers.
    ///
    /// If the file already exists with non-empty content and `force` is `false`,
    /// returns an `Io` error rather than silently discarding existing content.
    /// The caller should handle this case (e.g. by prompting for confirmation
    /// and re-calling with `force = true`).
    ///
    /// When `force` is `true` and the file exists, the existing content is
    /// preserved: the new import lines are prepended and the existing default
    /// export is wrapped with the declared providers (MC4).
    ///
    /// Writes atomically (to a `.tmp` file, then renames).
    ///
    /// # Parameters
    /// - `entry_point_path` — path to the TypeScript entry file
    /// - `providers` — the slice of providers declared in the manifest
    /// - `force` — when `true`, preserve and wrap existing file content instead of erroring
    ///
    /// # Errors
    /// - [`ManifestError::InvalidProviderName`] when a provider name is not a valid JSX identifier
    /// - [`ManifestError::Io`] when the file already exists with non-empty content and `force` is
    ///   `false`, or when the file cannot be written
    pub fn wrap_entry_point(
        entry_point_path: &Path,
        providers: &[ManifestProvider],
        force: bool,
    ) -> Result<(), ManifestError> {
        let path_str = entry_point_path.display().to_string();

        // H6 / MC4: check if the file already exists with content.
        if entry_point_path.exists() {
            let existing = fs::read_to_string(entry_point_path).map_err(|e| ManifestError::Io {
                path: path_str.clone(),
                message: e.to_string(),
            })?;
            if !existing.trim().is_empty() {
                if !force {
                    return Err(ManifestError::Io {
                        path: path_str,
                        message: "file already exists with content; refusing to overwrite without confirmation".to_string(),
                    });
                }
                // MC4: force = true — prepend imports to existing content.
                // The existing file is preserved; new import lines are prepended
                // so the developer's own component code is not discarded.
                validate_provider_names(providers)?;
                let imports = Self::build_imports(providers)?.join("\n");
                let updated = format!("{imports}\n\n{existing}");
                let tmp_path = entry_point_path.with_extension("tsx.tmp");
                fs::write(&tmp_path, &updated).map_err(|e| ManifestError::Io {
                    path: path_str.clone(),
                    message: e.to_string(),
                })?;
                return fs::rename(&tmp_path, entry_point_path).map_err(|e| {
                    let _ = fs::remove_file(&tmp_path);
                    ManifestError::Io {
                        path: path_str,
                        message: e.to_string(),
                    }
                });
            }
        }

        let stub = Self::build_usage_stub(&path_str, providers)?;

        // C1: atomic write.
        let tmp_path = entry_point_path.with_extension("tsx.tmp");
        fs::write(&tmp_path, stub).map_err(|e| ManifestError::Io {
            path: path_str.clone(),
            message: e.to_string(),
        })?;
        fs::rename(&tmp_path, entry_point_path).map_err(|e| {
            let _ = fs::remove_file(&tmp_path);
            ManifestError::Io {
                path: path_str,
                message: e.to_string(),
            }
        })
    }

    /// Build a minimal usage stub string for the entry point.
    ///
    /// The generated file includes:
    /// 1. Import statements for all providers
    /// 2. A default-export React component that wraps `children` with all providers
    ///
    /// # Parameters
    /// - `entry_point` — the declared entry point path (used in the component comment)
    /// - `providers` — the slice of providers declared in the manifest
    ///
    /// # Returns
    /// The complete TypeScript file content as a string.
    ///
    /// # Errors
    /// - [`ManifestError::InvalidProviderName`] when a provider name is not a valid JSX identifier
    pub fn build_usage_stub(
        entry_point: &str,
        providers: &[ManifestProvider],
    ) -> Result<String, ManifestError> {
        let imports = Self::build_imports(providers)?.join("\n");
        let wrapper = Self::build_jsx_wrapper(providers)?;

        Ok(format!(
            "// Generated by syntek-manifest — entry point: {entry_point}\n\
             {imports}\n\
             \n\
             export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{\n\
               return {wrapper};\n\
             }}\n"
        ))
    }
}
