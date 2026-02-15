/**
 * Phone number validation utility.
 *
 * Uses libphonenumber-js for international phone number validation.
 * Supports E.164 format and country-specific validation.
 *
 * Note: Install libphonenumber-js package:
 * ```bash
 * pnpm add libphonenumber-js
 * ```
 */

import { parsePhoneNumber, isValidPhoneNumber } from 'libphonenumber-js';

/**
 * Phone validation result.
 */
export interface PhoneValidationResult {
  /** Whether phone number is valid */
  isValid: boolean;
  /** Validation error message */
  error?: string;
  /** Normalised phone number (E.164 format) */
  normalised?: string;
  /** Country code (e.g., 'GB', 'US') */
  country?: string;
  /** National format (e.g., '07700 900000') */
  nationalFormat?: string;
  /** International format (e.g., '+44 7700 900000') */
  internationalFormat?: string;
}

/**
 * Validates phone number.
 *
 * Checks format and validity for the specified country.
 * If no country specified, attempts to detect from international prefix.
 *
 * @param phone - Phone number to validate
 * @param defaultCountry - Default country code (e.g., 'GB', 'US')
 * @returns Validation result with normalised formats
 *
 * @example
 * ```typescript
 * const result = validatePhone('+447700900000', 'GB');
 * if (result.isValid) {
 *   console.log(result.normalised); // '+447700900000'
 *   console.log(result.nationalFormat); // '07700 900000'
 * }
 * ```
 */
export function validatePhone(
  phone: string,
  defaultCountry?: string
): PhoneValidationResult {
  // Trim whitespace
  const trimmedPhone = phone.trim();

  // Empty check
  if (!trimmedPhone) {
    return {
      isValid: false,
      error: 'Phone number is required',
    };
  }

  try {
    // Parse phone number
    const phoneNumber = parsePhoneNumber(trimmedPhone, defaultCountry as any);

    // Validate
    if (!phoneNumber || !phoneNumber.isValid()) {
      return {
        isValid: false,
        error: 'Phone number is not valid',
      };
    }

    return {
      isValid: true,
      normalised: phoneNumber.number, // E.164 format
      country: phoneNumber.country,
      nationalFormat: phoneNumber.formatNational(),
      internationalFormat: phoneNumber.formatInternational(),
    };
  } catch (error) {
    return {
      isValid: false,
      error: 'Phone number is not valid',
    };
  }
}

/**
 * Normalises phone number to E.164 format.
 *
 * E.164 format: +[country code][number] (e.g., +447700900000).
 * Use this before storing phone numbers in database.
 *
 * @param phone - Phone number to normalise
 * @param defaultCountry - Default country code
 * @returns Normalised phone number or undefined if invalid
 *
 * @example
 * ```typescript
 * const normalised = normalisePhone('07700 900 000', 'GB');
 * // Returns: '+447700900000'
 * ```
 */
export function normalisePhone(
  phone: string,
  defaultCountry?: string
): string | undefined {
  const result = validatePhone(phone, defaultCountry);
  return result.normalised;
}

/**
 * Masks phone number for display.
 *
 * Hides part of the phone number for privacy.
 *
 * @param phone - Phone number to mask
 * @returns Masked phone number
 *
 * @example
 * ```typescript
 * const masked = maskPhone('+447700900000');
 * // Returns: '+44 •••• •• 0000'
 * ```
 */
export function maskPhone(phone: string): string {
  try {
    const phoneNumber = parsePhoneNumber(phone);

    if (!phoneNumber) {
      return phone;
    }

    const national = phoneNumber.formatNational();
    const parts = national.split(' ');

    // Mask middle parts, show first and last
    if (parts.length >= 3) {
      const masked = parts.map((part, index) => {
        if (index === 0 || index === parts.length - 1) {
          return part;
        }
        return '••••';
      });

      return masked.join(' ');
    }

    // Fallback: show last 4 digits
    const digits = phone.replace(/\D/g, '');
    const lastFour = digits.slice(-4);
    return `+${phoneNumber.countryCallingCode} •••• •• ${lastFour}`;
  } catch (error) {
    // Fallback masking if parsing fails
    const digits = phone.replace(/\D/g, '');
    const lastFour = digits.slice(-4);
    return `••• ••• ${lastFour}`;
  }
}

/**
 * Formats phone number for display.
 *
 * Returns national format for domestic numbers, international for foreign.
 *
 * @param phone - Phone number to format
 * @param userCountry - User's country code (for domestic/international detection)
 * @returns Formatted phone number
 *
 * @example
 * ```typescript
 * const formatted = formatPhone('+447700900000', 'GB');
 * // Returns: '07700 900000' (national format)
 *
 * const formatted2 = formatPhone('+447700900000', 'US');
 * // Returns: '+44 7700 900000' (international format)
 * ```
 */
export function formatPhone(phone: string, userCountry?: string): string {
  try {
    const phoneNumber = parsePhoneNumber(phone);

    if (!phoneNumber) {
      return phone;
    }

    // If same country, use national format
    if (userCountry && phoneNumber.country === userCountry) {
      return phoneNumber.formatNational();
    }

    // Otherwise, use international format
    return phoneNumber.formatInternational();
  } catch (error) {
    return phone;
  }
}
