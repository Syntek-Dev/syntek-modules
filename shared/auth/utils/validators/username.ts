/**
 * Username validation utility.
 *
 * Validates usernames with configurable rules (alphanumeric, underscore, length).
 */

/**
 * Username validation regex pattern.
 *
 * Allows: letters (a-z, A-Z), numbers (0-9), underscores (_), hyphens (-).
 * Must start with a letter or number.
 */
const USERNAME_REGEX = /^[a-zA-Z0-9][a-zA-Z0-9_-]*$/;

/**
 * Reserved usernames that cannot be registered.
 */
const RESERVED_USERNAMES = [
  'admin',
  'root',
  'system',
  'administrator',
  'superuser',
  'moderator',
  'support',
  'help',
  'api',
  'www',
  'ftp',
  'mail',
  'webmaster',
  'postmaster',
  'hostmaster',
  'abuse',
  'noc',
  'security',
  'privacy',
  'legal',
  'terms',
  'about',
  'contact',
  'login',
  'logout',
  'register',
  'signup',
  'signin',
  'signout',
  'settings',
  'profile',
  'account',
  'dashboard',
];

/**
 * Username validation result.
 */
export interface UsernameValidationResult {
  /** Whether username is valid */
  isValid: boolean;
  /** Validation error message */
  error?: string;
  /** Warning message (non-blocking) */
  warning?: string;
}

/**
 * Validates username.
 *
 * Checks format, length, and reserved words.
 *
 * @param username - Username to validate
 * @param options - Validation options
 * @returns Validation result with errors
 *
 * @example
 * ```typescript
 * const result = validateUsername('john_doe');
 * if (!result.isValid) {
 *   console.error(result.error);
 * }
 * ```
 */
export function validateUsername(
  username: string,
  options: {
    /** Minimum length (default: 3) */
    minLength?: number;
    /** Maximum length (default: 30) */
    maxLength?: number;
    /** Block reserved usernames (default: true) */
    blockReserved?: boolean;
  } = {}
): UsernameValidationResult {
  const { minLength = 3, maxLength = 30, blockReserved = true } = options;

  // Trim whitespace
  const trimmedUsername = username.trim();

  // Empty check
  if (!trimmedUsername) {
    return {
      isValid: false,
      error: 'Username is required',
    };
  }

  // Length check
  if (trimmedUsername.length < minLength) {
    return {
      isValid: false,
      error: `Username must be at least ${minLength} characters`,
    };
  }

  if (trimmedUsername.length > maxLength) {
    return {
      isValid: false,
      error: `Username must not exceed ${maxLength} characters`,
    };
  }

  // Format check (alphanumeric, underscore, hyphen)
  if (!USERNAME_REGEX.test(trimmedUsername)) {
    return {
      isValid: false,
      error:
        'Username can only contain letters, numbers, underscores, and hyphens, and must start with a letter or number',
    };
  }

  // Reserved username check
  if (blockReserved && RESERVED_USERNAMES.includes(trimmedUsername.toLowerCase())) {
    return {
      isValid: false,
      error: 'This username is reserved and cannot be used',
    };
  }

  // Check for confusing characters (l, I, O, 0)
  const hasConfusingChars = /[lIO0]/.test(trimmedUsername);
  const warning = hasConfusingChars
    ? 'Username contains potentially confusing characters (l, I, O, 0)'
    : undefined;

  return {
    isValid: true,
    warning,
  };
}

/**
 * Normalises username for storage.
 *
 * Converts to lowercase and trims whitespace.
 * Use this before storing usernames in database.
 *
 * @param username - Username to normalise
 * @returns Normalised username
 *
 * @example
 * ```typescript
 * const username = normaliseUsername(' JohnDoe ');
 * // Returns: 'johndoe'
 * ```
 */
export function normaliseUsername(username: string): string {
  return username.trim().toLowerCase();
}

/**
 * Generates username suggestions from email.
 *
 * Creates username variants based on email local part.
 *
 * @param email - Email address
 * @returns List of username suggestions
 *
 * @example
 * ```typescript
 * const suggestions = suggestUsernamesFromEmail('john.doe@example.com');
 * // Returns: ['johndoe', 'john_doe', 'jdoe']
 * ```
 */
export function suggestUsernamesFromEmail(email: string): string[] {
  const local = email.split('@')[0];
  const suggestions: string[] = [];

  // Remove dots
  const noDots = local.replace(/\./g, '');
  if (noDots.length >= 3) {
    suggestions.push(noDots);
  }

  // Replace dots with underscores
  const withUnderscores = local.replace(/\./g, '_');
  if (withUnderscores.length >= 3 && withUnderscores !== noDots) {
    suggestions.push(withUnderscores);
  }

  // First letter + last name (if dot-separated)
  const parts = local.split('.');
  if (parts.length === 2) {
    const initials = parts[0].charAt(0) + parts[1];
    if (initials.length >= 3) {
      suggestions.push(initials);
    }
  }

  // Add random suffix if suggestions are empty
  if (suggestions.length === 0) {
    const randomSuffix = Math.floor(Math.random() * 1000);
    suggestions.push(`user${randomSuffix}`);
  }

  return suggestions.map(normaliseUsername);
}
