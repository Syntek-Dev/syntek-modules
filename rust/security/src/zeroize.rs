//! Memory zeroization utilities

pub use zeroize::{Zeroize, Zeroizing};

/// Securely clear sensitive data from memory
pub fn secure_clear<T: Zeroize>(data: &mut T) {
    data.zeroize();
}
