//! Encryption/decryption module for Syntek
//!
//! Provides field-level and batch encryption using AES-256-GCM and ChaCha20-Poly1305.

pub mod batch;
pub mod field_level;
pub mod key_management;
pub mod validators;

pub use batch::{decrypt_batch, encrypt_batch};
pub use field_level::{decrypt_field, encrypt_field};
pub use validators::{validate_email, validate_ip_address, validate_phone_number};
