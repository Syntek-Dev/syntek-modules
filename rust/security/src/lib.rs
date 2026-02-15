//! Memory safety and security primitives for Syntek
//!
//! Provides zeroization, memory locking, secure random generation, and OAuth security.

pub mod hmac;
pub mod memory;
pub mod oauth;
pub mod random;
pub mod tokens;
pub mod zeroize;

pub use hmac::{hash_email, hash_for_lookup, hash_ip, hash_phone, verify_hmac};
pub use oauth::{
    generate_pkce_code_challenge, generate_pkce_code_verifier, generate_pkce_pair,
};
pub use tokens::{
    generate_api_key, generate_backup_codes, generate_token, generate_verification_code,
};
