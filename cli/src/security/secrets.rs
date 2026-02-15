//! Secret handling for API keys, tokens, and passwords
//!
//! Uses the `secrecy` crate to protect sensitive data in memory.

use crate::utils::error::{CliError, Result};
use rpassword::prompt_password;
use secrecy::{ExposeSecret, SecretString};
use std::collections::HashMap;

/// Manages secrets with automatic zeroization
pub struct SecretsManager {
    secrets: HashMap<String, SecretString>,
}

impl SecretsManager {
    /// Create new secrets manager
    pub fn new() -> Self {
        Self {
            secrets: HashMap::new(),
        }
    }

    /// Get secret by name
    pub fn get(&self, name: &str) -> Option<&SecretString> {
        self.secrets.get(name)
    }

    /// Set secret
    pub fn set(&mut self, name: String, value: SecretString) {
        self.secrets.insert(name, value);
    }

    /// Require secret (error if missing)
    pub fn require(&self, name: &str) -> Result<&SecretString> {
        self.get(name)
            .ok_or_else(|| CliError::MissingEnvVar(name.to_string()))
    }

    /// Prompt for secret interactively
    pub fn prompt(&mut self, name: &str, message: &str) -> Result<&SecretString> {
        let value = prompt_password(message).map_err(|_| CliError::PromptFailed)?;

        if value.is_empty() {
            return Err(CliError::EmptyPassword);
        }

        self.set(name.to_string(), SecretString::from(value.into_boxed_str()));
        Ok(self.require(name)?)
    }

    /// Prompt with confirmation
    pub fn prompt_with_confirmation(&mut self, name: &str, message: &str) -> Result<&SecretString> {
        let password1 = prompt_password(message).map_err(|_| CliError::PromptFailed)?;

        let password2 =
            prompt_password("Confirm: ").map_err(|_| CliError::PromptFailed)?;

        if password1 != password2 {
            return Err(CliError::PasswordMismatch);
        }

        if password1.is_empty() {
            return Err(CliError::EmptyPassword);
        }

        self.set(name.to_string(), SecretString::from(password1.into_boxed_str()));
        Ok(self.require(name)?)
    }

    /// Load secret from environment variable
    pub fn from_env(&mut self, name: &str, env_var: &str) -> Result<()> {
        let value = std::env::var(env_var).map_err(|_| CliError::MissingEnvVar(env_var.to_string()))?;

        self.set(name.to_string(), SecretString::from(value.into_boxed_str()));

        // Clear from environment after reading
        std::env::remove_var(env_var);

        Ok(())
    }

    /// Load secret from environment or prompt if missing
    pub fn from_env_or_prompt(
        &mut self,
        name: &str,
        env_var: &str,
        prompt_message: &str,
    ) -> Result<&SecretString> {
        if let Ok(()) = self.from_env(name, env_var) {
            Ok(self.require(name)?)
        } else {
            self.prompt(name, prompt_message)
        }
    }

    /// Generate random secret (for keys, tokens) and return the plain text value
    pub fn generate(&mut self, name: &str, length: usize) -> String {
        use rand::Rng;
        const CHARSET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

        let mut rng = rand::thread_rng();
        let secret: String = (0..length)
            .map(|_| {
                let idx = rng.gen_range(0..CHARSET.len());
                CHARSET[idx] as char
            })
            .collect();

        // Store in secret storage
        let secret_clone = secret.clone();
        self.set(name.to_string(), SecretString::from(secret.into_boxed_str()));
        secret_clone
    }

    /// Get secret reference (for internal use)
    pub fn get_secret(&self, name: &str) -> Option<&SecretString> {
        self.secrets.get(name)
    }

    /// Clear all secrets (automatic zeroization via Drop)
    pub fn clear(&mut self) {
        self.secrets.clear();
    }

    /// Check if secret exists
    pub fn contains(&self, name: &str) -> bool {
        self.secrets.contains_key(name)
    }
}

impl Default for SecretsManager {
    fn default() -> Self {
        Self::new()
    }
}

impl Drop for SecretsManager {
    fn drop(&mut self) {
        // SecretString handles zeroization automatically
        self.secrets.clear();
    }
}

/// Password strength validator
pub fn validate_password_strength(password: &str) -> Result<()> {
    if password.len() < 12 {
        return Err(CliError::ValidationFailed(
            "Password must be at least 12 characters".to_string(),
        ));
    }

    let has_upper = password.chars().any(|c| c.is_uppercase());
    let has_lower = password.chars().any(|c| c.is_lowercase());
    let has_digit = password.chars().any(|c| c.is_ascii_digit());
    let has_special = password.chars().any(|c| !c.is_alphanumeric());

    if !has_upper || !has_lower || !has_digit || !has_special {
        return Err(CliError::ValidationFailed(
            "Password must contain uppercase, lowercase, digit, and special character".to_string(),
        ));
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_secrets_manager() {
        let mut manager = SecretsManager::new();
        let secret = SecretString::new("test_secret".to_string());

        manager.set("test".to_string(), secret);
        assert!(manager.contains("test"));
        assert!(manager.get("test").is_some());
        assert!(manager.get("missing").is_none());
    }

    #[test]
    fn test_password_validation() {
        assert!(validate_password_strength("Short1!").is_err());
        assert!(validate_password_strength("NoNumbers!abc").is_err());
        assert!(validate_password_strength("Valid1Password!").is_ok());
    }

    #[test]
    fn test_generate_secret() {
        let mut manager = SecretsManager::new();
        let secret = manager.generate("test", 32);
        assert_eq!(secret.len(), 32);
    }
}
