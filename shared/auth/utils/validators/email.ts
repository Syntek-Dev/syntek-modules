/**
 * Email validation utility.
 *
 * RFC 5322 compliant email validation with additional security checks.
 */

/**
 * RFC 5322 email regex pattern.
 *
 * This is a simplified but practical regex that covers most valid emails.
 * Full RFC 5322 compliance would require a much more complex regex.
 */
const EMAIL_REGEX =
  /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

/**
 * Disposable email domain list (common temporary email providers).
 */
const DISPOSABLE_DOMAINS = [
  '10minutemail.com',
  'guerrillamail.com',
  'mailinator.com',
  'tempmail.com',
  'throwaway.email',
  'temp-mail.org',
  'getnada.com',
  'maildrop.cc',
  'yopmail.com',
];

/**
 * Email validation result.
 */
export interface EmailValidationResult {
  /** Whether email is valid */
  isValid: boolean;
  /** Validation error message */
  error?: string;
  /** Warning message (non-blocking) */
  warning?: string;
  /** Normalised email address */
  normalised?: string;
}

/**
 * Validates email address.
 *
 * Checks RFC 5322 compliance, length limits, and disposable domains.
 *
 * @param email - Email address to validate
 * @param options - Validation options
 * @returns Validation result with errors and normalised email
 *
 * @example
 * ```typescript
 * const result = validateEmail('user@example.com');
 * if (!result.isValid) {
 *   console.error(result.error);
 * }
 * ```
 */
export function validateEmail(
  email: string,
  options: {
    /** Block disposable email addresses (default: false) */
    blockDisposable?: boolean;
    /** Maximum email length (default: 254 per RFC 5321) */
    maxLength?: number;
  } = {}
): EmailValidationResult {
  const { blockDisposable = false, maxLength = 254 } = options;

  // Trim whitespace
  const trimmedEmail = email.trim();

  // Empty check
  if (!trimmedEmail) {
    return {
      isValid: false,
      error: 'Email address is required',
    };
  }

  // Length check (RFC 5321: max 254 characters)
  if (trimmedEmail.length > maxLength) {
    return {
      isValid: false,
      error: `Email address must not exceed ${maxLength} characters`,
    };
  }

  // Format check (RFC 5322)
  if (!EMAIL_REGEX.test(trimmedEmail)) {
    return {
      isValid: false,
      error: 'Email address is not valid',
    };
  }

  // Extract domain
  const domain = trimmedEmail.split('@')[1].toLowerCase();

  // Disposable domain check
  if (blockDisposable && DISPOSABLE_DOMAINS.includes(domain)) {
    return {
      isValid: false,
      error: 'Disposable email addresses are not allowed',
    };
  }

  // Normalise email (lowercase)
  const normalised = trimmedEmail.toLowerCase();

  return {
    isValid: true,
    normalised,
  };
}

/**
 * Normalises email address for storage.
 *
 * Converts to lowercase and trims whitespace.
 * Use this before storing emails in database.
 *
 * @param email - Email address to normalise
 * @returns Normalised email address
 *
 * @example
 * ```typescript
 * const email = normaliseEmail(' User@Example.COM ');
 * // Returns: 'user@example.com'
 * ```
 */
export function normaliseEmail(email: string): string {
  return email.trim().toLowerCase();
}

/**
 * Masks email address for display.
 *
 * Hides part of the email for privacy (e.g., 'u***@example.com').
 *
 * @param email - Email address to mask
 * @returns Masked email address
 *
 * @example
 * ```typescript
 * const masked = maskEmail('user@example.com');
 * // Returns: 'u***@example.com'
 * ```
 */
export function maskEmail(email: string): string {
  const [local, domain] = email.split('@');

  if (local.length <= 1) {
    return `${local}***@${domain}`;
  }

  const visibleChars = Math.min(2, Math.floor(local.length / 3));
  const masked = local.substring(0, visibleChars) + '***';

  return `${masked}@${domain}`;
}

/**
 * Extracts domain from email address.
 *
 * @param email - Email address
 * @returns Domain part of email
 *
 * @example
 * ```typescript
 * const domain = extractEmailDomain('user@example.com');
 * // Returns: 'example.com'
 * ```
 */
export function extractEmailDomain(email: string): string {
  return email.split('@')[1]?.toLowerCase() || '';
}
