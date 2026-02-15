/**
 * Client-side hashing utility (SHA-256).
 *
 * Used for email lookup hashing (privacy-preserving constant-time lookup).
 */

/**
 * Computes SHA-256 hash of a string.
 *
 * Uses SubtleCrypto API (browser) or crypto module (Node.js).
 *
 * @param text - Text to hash
 * @returns SHA-256 hash in lowercase hexadecimal
 *
 * @example
 * ```typescript
 * const emailHash = await sha256('user@example.com');
 * // Use for privacy-preserving email lookup
 * ```
 */
export async function sha256(text: string): Promise<string> {
  // Browser environment
  if (typeof window !== 'undefined' && window.crypto?.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    return hashHex;
  }

  // Node.js environment
  if (typeof require !== 'undefined') {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(text).digest('hex');
  }

  throw new Error('SHA-256 not supported in this environment');
}

/**
 * Hashes email address for privacy-preserving lookup.
 *
 * Backend uses HMAC-based constant-time lookup to prevent email enumeration.
 * Frontend hashes email before sending to backend.
 *
 * @param email - Email address to hash
 * @returns SHA-256 hash of normalised email
 *
 * @example
 * ```typescript
 * const emailHash = await hashEmailForLookup('User@Example.COM');
 * // Send hash to backend for constant-time lookup
 * const exists = await checkEmailExists(emailHash);
 * ```
 */
export async function hashEmailForLookup(email: string): Promise<string> {
  // Normalise email (lowercase, trim)
  const normalised = email.trim().toLowerCase();

  // Hash normalised email
  return sha256(normalised);
}
