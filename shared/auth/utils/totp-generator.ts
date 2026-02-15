/**
 * TOTP (Time-based One-Time Password) generation utility.
 *
 * Client-side TOTP generation for verification purposes.
 * Actual authentication TOTP is generated server-side.
 */

/**
 * Generates TOTP URI for QR code display.
 *
 * Creates otpauth:// URI for authenticator apps (Google Authenticator, Authy, etc.).
 *
 * @param secret - Base32-encoded TOTP secret
 * @param email - User's email address
 * @param issuer - Issuer name (app name)
 * @returns TOTP URI for QR code
 *
 * @example
 * ```typescript
 * const uri = generateTOTPUri(secret, 'user@example.com', 'MyApp');
 * // Generate QR code from URI using qrcode library
 * ```
 */
export function generateTOTPUri(
  secret: string,
  email: string,
  issuer: string
): string {
  const encodedIssuer = encodeURIComponent(issuer);
  const encodedEmail = encodeURIComponent(email);
  const encodedSecret = encodeURIComponent(secret);

  return `otpauth://totp/${encodedIssuer}:${encodedEmail}?secret=${encodedSecret}&issuer=${encodedIssuer}`;
}

/**
 * Validates TOTP code format.
 *
 * Checks if code is 6 digits.
 *
 * @param code - TOTP code to validate
 * @returns True if code format is valid
 *
 * @example
 * ```typescript
 * const isValid = validateTOTPFormat('123456');
 * // Returns: true
 * ```
 */
export function validateTOTPFormat(code: string): boolean {
  return /^\d{6}$/.test(code);
}

/**
 * Formats TOTP code for display (splits into groups of 3).
 *
 * @param code - TOTP code
 * @returns Formatted code (e.g., '123 456')
 *
 * @example
 * ```typescript
 * const formatted = formatTOTPCode('123456');
 * // Returns: '123 456'
 * ```
 */
export function formatTOTPCode(code: string): string {
  if (code.length !== 6) return code;
  return `${code.substring(0, 3)} ${code.substring(3)}`;
}
