//! Memory-only storage utilities

use secrecy::SecretString;

/// Store sensitive data in memory only
pub type SecureString = SecretString;

/// Create a secure string that zeroizes on drop
pub fn secure_string(value: String) -> SecretString {
    SecretString::new(value.into())
}
