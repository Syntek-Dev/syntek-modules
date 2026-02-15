/**
 * Constant-time comparison utility.
 *
 * Prevents timing attacks by ensuring comparison takes constant time.
 */

/**
 * Constant-time string comparison.
 *
 * Compares two strings in constant time to prevent timing attacks.
 * Always compares full length of both strings.
 *
 * WARNING: This is client-side only. Backend MUST use cryptographic
 * constant-time comparison (from Rust layer).
 *
 * @param a - First string
 * @param b - Second string
 * @returns True if strings are equal
 *
 * @example
 * ```typescript
 * const isEqual = constantTimeCompare(userInput, storedValue);
 * ```
 */
export function constantTimeCompare(a: string, b: string): boolean {
  // Different lengths always fail, but still compare to prevent timing leak
  const aLen = a.length;
  const bLen = b.length;

  let result = 0;

  // XOR lengths (will be non-zero if lengths differ)
  result |= aLen ^ bLen;

  // Compare characters (use longer length to prevent timing leak)
  const maxLen = Math.max(aLen, bLen);

  for (let i = 0; i < maxLen; i++) {
    const charA = i < aLen ? a.charCodeAt(i) : 0;
    const charB = i < bLen ? b.charCodeAt(i) : 0;
    result |= charA ^ charB;
  }

  return result === 0;
}
