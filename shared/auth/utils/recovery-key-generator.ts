/**
 * Recovery key generation and formatting utility.
 *
 * Generates and formats recovery keys for account recovery.
 */

/**
 * Validates recovery key format.
 *
 * Recovery keys are typically 16-24 alphanumeric characters, divided into groups.
 * Example: ABCD-1234-EFGH-5678
 *
 * @param key - Recovery key to validate
 * @returns True if key format is valid
 *
 * @example
 * ```typescript
 * const isValid = validateRecoveryKeyFormat('ABCD-1234-EFGH-5678');
 * // Returns: true
 * ```
 */
export function validateRecoveryKeyFormat(key: string): boolean {
  // Format: XXXX-XXXX-XXXX-XXXX (16 alphanumeric characters)
  return /^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(key);
}

/**
 * Formats recovery key for display (adds hyphens).
 *
 * @param key - Unformatted recovery key
 * @returns Formatted recovery key
 *
 * @example
 * ```typescript
 * const formatted = formatRecoveryKey('ABCD1234EFGH5678');
 * // Returns: 'ABCD-1234-EFGH-5678'
 * ```
 */
export function formatRecoveryKey(key: string): string {
  // Remove existing hyphens
  const clean = key.replace(/-/g, '');

  // Split into groups of 4
  const groups: string[] = [];
  for (let i = 0; i < clean.length; i += 4) {
    groups.push(clean.substring(i, i + 4));
  }

  return groups.join('-');
}

/**
 * Normalises recovery key for backend verification.
 *
 * Removes hyphens and converts to uppercase.
 *
 * @param key - Recovery key to normalise
 * @returns Normalised recovery key
 *
 * @example
 * ```typescript
 * const normalised = normaliseRecoveryKey('abcd-1234-efgh-5678');
 * // Returns: 'ABCD1234EFGH5678'
 * ```
 */
export function normaliseRecoveryKey(key: string): string {
  return key.replace(/-/g, '').toUpperCase();
}
