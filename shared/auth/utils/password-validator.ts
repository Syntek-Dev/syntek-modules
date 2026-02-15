/**
 * Password strength validation utility.
 *
 * Validates password strength against backend rules (fetched from GraphQL).
 * Implements client-side pattern detection (sequential, repeated, dictionary, etc.)
 * and strength scoring with crack time estimation.
 *
 * CRITICAL: This is client-side validation only. Backend MUST re-validate.
 *
 * @example
 * ```typescript
 * const { config } = useAuthConfig();
 * const result = validatePassword('MyP@ssw0rd!', config);
 * if (!result.isValid) {
 *   console.log(result.errors); // ['Password contains sequential characters']
 * }
 * console.log(result.strength); // 'STRONG'
 * console.log(result.crackTime); // '2 years'
 * ```
 */

import type { AuthConfig } from '../types/config';

/**
 * Password validation result.
 */
export interface PasswordValidationResult {
  /** Whether password meets all requirements */
  isValid: boolean;
  /** List of validation errors */
  errors: string[];
  /** List of warnings (non-blocking suggestions) */
  warnings: string[];
  /** Password strength score (0-4) */
  score: number;
  /** Password strength label */
  strength: 'VERY_WEAK' | 'WEAK' | 'FAIR' | 'STRONG' | 'VERY_STRONG';
  /** Estimated crack time (human-readable) */
  crackTime: string;
  /** Detected patterns */
  patterns: string[];
}

/**
 * Common password patterns (sequential, keyboard, dates).
 */
const COMMON_PATTERNS = {
  sequential: /(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)/i,
  keyboard: /(?:qwerty|asdfgh|zxcvbn|qwertz|azerty)/i,
  repeated: /(.)\1{2,}/,
  date: /(?:19|20)\d{2}|(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])/,
};

/**
 * Common weak passwords dictionary (top 100 most common).
 */
const COMMON_PASSWORDS = [
  'password',
  '123456',
  '12345678',
  'qwerty',
  'abc123',
  'monkey',
  '1234567',
  'letmein',
  'trustno1',
  'dragon',
  'baseball',
  '111111',
  'iloveyou',
  'master',
  'sunshine',
  'ashley',
  'bailey',
  'passw0rd',
  'shadow',
  '123123',
  '654321',
  'superman',
  'qazwsx',
  'michael',
  'football',
];

/**
 * Validates password against backend configuration rules.
 *
 * @param password - Password to validate
 * @param config - Authentication configuration from backend (useAuthConfig)
 * @returns Validation result with errors, warnings, and strength score
 *
 * @example
 * ```typescript
 * const { config } = useAuthConfig();
 * const result = validatePassword(password, config);
 * if (!result.isValid) {
 *   // Display errors
 * }
 * ```
 */
export function validatePassword(
  password: string,
  config: AuthConfig
): PasswordValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const patterns: string[] = [];

  // Length validation (backend rule)
  if (password.length < config.passwordMinLength) {
    errors.push(
      `Password must be at least ${config.passwordMinLength} characters`
    );
  }

  if (password.length > config.passwordMaxLength) {
    errors.push(
      `Password must not exceed ${config.passwordMaxLength} characters`
    );
  }

  // Character requirement validation (backend rules)
  if (config.uppercaseRequired && !/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (config.lowercaseRequired && !/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (config.numbersRequired && !/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  if (config.specialCharsRequired && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }

  // Pattern detection (client-side security)
  if (COMMON_PATTERNS.sequential.test(password)) {
    warnings.push('Password contains sequential characters');
    patterns.push('sequential');
  }

  if (COMMON_PATTERNS.keyboard.test(password)) {
    warnings.push('Password contains keyboard patterns');
    patterns.push('keyboard');
  }

  if (COMMON_PATTERNS.repeated.test(password)) {
    warnings.push('Password contains repeated characters');
    patterns.push('repeated');
  }

  if (COMMON_PATTERNS.date.test(password)) {
    warnings.push('Password contains date patterns');
    patterns.push('date');
  }

  // Common password check (client-side dictionary)
  if (
    config.commonPasswordCheck &&
    COMMON_PASSWORDS.some((common) =>
      password.toLowerCase().includes(common.toLowerCase())
    )
  ) {
    errors.push('Password is too common and easily guessable');
    patterns.push('dictionary');
  }

  // Calculate strength score (0-4)
  const score = calculateStrengthScore(password, patterns);

  // Map score to strength label
  const strengthLabels: PasswordValidationResult['strength'][] = [
    'VERY_WEAK',
    'WEAK',
    'FAIR',
    'STRONG',
    'VERY_STRONG',
  ];
  const strength = strengthLabels[score];

  // Estimate crack time
  const crackTime = estimateCrackTime(password, score);

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    score,
    strength,
    crackTime,
    patterns,
  };
}

/**
 * Calculates password strength score (0-4).
 *
 * Scoring factors:
 * - Length (longer is better)
 * - Character diversity (uppercase, lowercase, numbers, symbols)
 * - Absence of common patterns
 *
 * @param password - Password to score
 * @param patterns - Detected patterns (reduces score)
 * @returns Score from 0 (very weak) to 4 (very strong)
 */
function calculateStrengthScore(password: string, patterns: string[]): number {
  let score = 0;

  // Length bonus
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (password.length >= 16) score += 1;

  // Character diversity bonus
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

  const diversity = [hasLower, hasUpper, hasNumber, hasSpecial].filter(
    Boolean
  ).length;

  if (diversity >= 3) score += 1;
  if (diversity === 4) score += 1;

  // Pattern penalty
  score -= patterns.length;

  // Clamp score to 0-4
  return Math.max(0, Math.min(4, score));
}

/**
 * Estimates password crack time based on strength score.
 *
 * Assumes attacker using moderate hardware (1 billion guesses/second).
 * Real crack time depends on password entropy and attacker resources.
 *
 * @param password - Password to estimate
 * @param score - Strength score (0-4)
 * @returns Human-readable crack time estimate
 */
function estimateCrackTime(password: string, score: number): string {
  // Simplified entropy calculation
  let charsetSize = 0;
  if (/[a-z]/.test(password)) charsetSize += 26;
  if (/[A-Z]/.test(password)) charsetSize += 26;
  if (/\d/.test(password)) charsetSize += 10;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) charsetSize += 32;

  const combinations = Math.pow(charsetSize, password.length);
  const guessesPerSecond = 1e9; // 1 billion guesses/second

  const seconds = combinations / guessesPerSecond / 2; // Average case

  // Score penalty for patterns
  const adjustedSeconds = seconds / Math.pow(10, 4 - score);

  if (adjustedSeconds < 1) return 'Less than a second';
  if (adjustedSeconds < 60) return `${Math.round(adjustedSeconds)} seconds`;
  if (adjustedSeconds < 3600) return `${Math.round(adjustedSeconds / 60)} minutes`;
  if (adjustedSeconds < 86400) return `${Math.round(adjustedSeconds / 3600)} hours`;
  if (adjustedSeconds < 2592000) return `${Math.round(adjustedSeconds / 86400)} days`;
  if (adjustedSeconds < 31536000) return `${Math.round(adjustedSeconds / 2592000)} months`;

  return `${Math.round(adjustedSeconds / 31536000)} years`;
}

/**
 * Generates password strength feedback for users.
 *
 * Provides actionable suggestions to improve password strength.
 *
 * @param result - Password validation result
 * @returns List of feedback messages
 *
 * @example
 * ```typescript
 * const result = validatePassword(password, config);
 * const feedback = getPasswordFeedback(result);
 * // ['Add uppercase letters', 'Avoid sequential characters']
 * ```
 */
export function getPasswordFeedback(
  result: PasswordValidationResult
): string[] {
  const feedback: string[] = [];

  if (result.score < 3) {
    feedback.push('Consider using a longer password (16+ characters)');
  }

  if (result.patterns.includes('sequential')) {
    feedback.push('Avoid sequential characters (abc, 123, etc.)');
  }

  if (result.patterns.includes('keyboard')) {
    feedback.push('Avoid keyboard patterns (qwerty, asdf, etc.)');
  }

  if (result.patterns.includes('repeated')) {
    feedback.push('Avoid repeated characters (aaa, 111, etc.)');
  }

  if (result.patterns.includes('date')) {
    feedback.push('Avoid dates in your password');
  }

  if (result.patterns.includes('dictionary')) {
    feedback.push('Avoid common words and phrases');
  }

  if (result.warnings.length === 0 && result.score < 4) {
    feedback.push('Add more character variety for stronger security');
  }

  return feedback;
}
