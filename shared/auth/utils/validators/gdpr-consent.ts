/**
 * GDPR consent validation utility.
 *
 * Validates that required consents are granted before registration.
 */

/**
 * Consent validation result.
 */
export interface ConsentValidationResult {
  /** Whether all required consents are granted */
  isValid: boolean;
  /** List of missing required consents */
  errors: string[];
}

/**
 * Validates GDPR consent checkboxes.
 *
 * Ensures required consents (Terms of Service, Privacy Policy) are accepted.
 *
 * @param consents - Consent values
 * @returns Validation result
 *
 * @example
 * ```typescript
 * const result = validateConsent({
 *   termsAccepted: true,
 *   privacyAccepted: true,
 *   marketingAccepted: false // optional
 * });
 * ```
 */
export function validateConsent(consents: {
  termsAccepted: boolean;
  privacyAccepted: boolean;
  marketingAccepted?: boolean;
}): ConsentValidationResult {
  const errors: string[] = [];

  if (!consents.termsAccepted) {
    errors.push('You must accept the Terms of Service');
  }

  if (!consents.privacyAccepted) {
    errors.push('You must accept the Privacy Policy');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}
