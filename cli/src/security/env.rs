//! Environment variable handling and sanitization
//!
//! Securely manages environment variables and prevents secret leakage.

use crate::utils::error::{CliError, Result};
use secrecy::SecretString;
use std::collections::HashMap;

/// Secure environment variable manager
pub struct SecureEnv {
    prefix: String,
    loaded: HashMap<String, SecretString>,
}

impl SecureEnv {
    /// Create new environment manager with prefix
    pub fn new(prefix: &str) -> Self {
        Self {
            prefix: prefix.to_uppercase(),
            loaded: HashMap::new(),
        }
    }

    /// Get environment variable
    pub fn get(&mut self, name: &str) -> Option<&SecretString> {
        let full_name = format!("{}_{}", self.prefix, name.to_uppercase());

        let full_name_clone = full_name.clone();
        if !self.loaded.contains_key(&full_name) {
            if let Ok(value) = std::env::var(&full_name) {
                // Clear from environment after reading
                std::env::remove_var(&full_name);
                self.loaded.insert(full_name_clone.clone(), SecretString::from(value.into_boxed_str()));
            }
        }

        self.loaded.get(&full_name_clone)
    }

    /// Require environment variable (error if missing)
    pub fn require(&mut self, name: &str) -> Result<&SecretString> {
        let prefix_copy = self.prefix.clone();
        self.get(name).ok_or_else(|| {
            CliError::MissingEnvVar(format!("{}_{}", prefix_copy, name.to_uppercase()))
        })
    }

    /// Load all secrets at startup, then clear from environment
    pub fn preload(&mut self, names: &[&str]) -> Result<()> {
        for name in names {
            self.require(name)?;
        }
        Ok(())
    }
}

impl Drop for SecureEnv {
    fn drop(&mut self) {
        // SecretString handles zeroization
        self.loaded.clear();
    }
}

/// Remove sensitive environment variables from process
pub fn sanitize_environment(keep_vars: &[&str]) {
    let sensitive_patterns = [
        "PASSWORD",
        "SECRET",
        "KEY",
        "TOKEN",
        "CREDENTIAL",
        "API_KEY",
        "PRIVATE",
        "ENCRYPTION",
    ];

    let vars_to_remove: Vec<String> = std::env::vars()
        .filter_map(|(key, _)| {
            let key_upper = key.to_uppercase();

            // Keep explicitly allowed vars
            if keep_vars.iter().any(|k| k.to_uppercase() == key_upper) {
                return None;
            }

            // Remove sensitive vars
            if sensitive_patterns.iter().any(|p| key_upper.contains(p)) {
                Some(key)
            } else {
                None
            }
        })
        .collect();

    for var in vars_to_remove {
        std::env::remove_var(&var);
    }
}

/// Set environment variable temporarily for child processes
pub struct TempEnvVar {
    key: String,
    old_value: Option<String>,
}

impl TempEnvVar {
    /// Set temporary environment variable
    pub fn new(key: &str, value: &str) -> Self {
        let old_value = std::env::var(key).ok();
        std::env::set_var(key, value);

        Self {
            key: key.to_string(),
            old_value,
        }
    }
}

impl Drop for TempEnvVar {
    fn drop(&mut self) {
        match &self.old_value {
            Some(value) => std::env::set_var(&self.key, value),
            None => std::env::remove_var(&self.key),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_secure_env() {
        std::env::set_var("TEST_VAR", "secret_value");

        let mut env = SecureEnv::new("TEST");
        let secret = env.get("VAR");

        assert!(secret.is_some());

        // Should be cleared from environment
        assert!(std::env::var("TEST_VAR").is_err());
    }

    #[test]
    fn test_temp_env_var() {
        std::env::remove_var("TEMP_TEST");

        {
            let _temp = TempEnvVar::new("TEMP_TEST", "value");
            assert_eq!(std::env::var("TEMP_TEST").unwrap(), "value");
        }

        // Should be restored
        assert!(std::env::var("TEMP_TEST").is_err());
    }
}
