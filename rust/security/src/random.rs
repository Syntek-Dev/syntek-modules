//! Cryptographically secure random number generation

use anyhow::Result;
use ring::rand::{SecureRandom, SystemRandom};

/// Generate cryptographically secure random bytes
pub fn generate_random_bytes(len: usize) -> Result<Vec<u8>> {
    let rng = SystemRandom::new();
    let mut bytes = vec![0u8; len];
    rng.fill(&mut bytes)
        .map_err(|_| anyhow::anyhow!("Failed to generate random bytes"))?;
    Ok(bytes)
}

/// Generate a random token
pub fn generate_token(len: usize) -> Result<String> {
    let bytes = generate_random_bytes(len)?;
    Ok(hex::encode(bytes))
}
