//! Field-level encryption for individual sensitive fields

use anyhow::Result;
use chacha20poly1305::{
    aead::{Aead, KeyInit},
    ChaCha20Poly1305, Nonce,
};
use zeroize::Zeroize;

/// Encrypt a single field value
pub fn encrypt_field(plaintext: &str, key: &[u8]) -> Result<Vec<u8>> {
    let cipher = ChaCha20Poly1305::new_from_slice(key)
        .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;
    let nonce = Nonce::from_slice(b"unique nonce"); // TODO: Generate proper nonce
    let ciphertext = cipher
        .encrypt(nonce, plaintext.as_bytes())
        .map_err(|e| anyhow::anyhow!("Encryption failed: {}", e))?;
    Ok(ciphertext)
}

/// Decrypt a single field value
pub fn decrypt_field(ciphertext: &[u8], key: &[u8]) -> Result<String> {
    let cipher = ChaCha20Poly1305::new_from_slice(key)
        .map_err(|e| anyhow::anyhow!("Invalid key length: {}", e))?;
    let nonce = Nonce::from_slice(b"unique nonce"); // TODO: Use proper nonce
    let plaintext_bytes = cipher
        .decrypt(nonce, ciphertext)
        .map_err(|e| anyhow::anyhow!("Decryption failed: {}", e))?;
    let mut plaintext = String::from_utf8(plaintext_bytes)?;
    let result = plaintext.clone();
    plaintext.zeroize();
    Ok(result)
}
