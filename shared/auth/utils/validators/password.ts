/**
 * Password validation utility (wrapper for password-validator).
 *
 * Re-exports password validation functions for use in forms.
 */

export {
  validatePassword,
  getPasswordFeedback,
  type PasswordValidationResult,
} from '../password-validator';
