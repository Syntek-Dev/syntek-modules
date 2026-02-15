/**
 * XSS prevention utility using DOMPurify.
 *
 * Sanitizes user-generated content to prevent XSS attacks.
 *
 * Note: Install dompurify and @types/dompurify:
 * ```bash
 * pnpm add dompurify @types/dompurify
 * pnpm add -D @types/dompurify
 * ```
 */

import DOMPurify from 'dompurify';

/**
 * Sanitizes HTML string to prevent XSS.
 *
 * Removes potentially malicious HTML/JavaScript while preserving safe content.
 *
 * @param html - HTML string to sanitize
 * @returns Sanitized HTML string
 *
 * @example
 * ```typescript
 * const userInput = '<script>alert("XSS")</script><p>Hello</p>';
 * const safe = sanitizeHTML(userInput);
 * // Returns: '<p>Hello</p>'
 * ```
 */
export function sanitizeHTML(html: string): string {
  return DOMPurify.sanitize(html);
}

/**
 * Sanitizes plain text (strips all HTML tags).
 *
 * Use for user names, device names, and other plain text fields.
 *
 * @param text - Text to sanitize
 * @returns Plain text without HTML
 *
 * @example
 * ```typescript
 * const userInput = '<script>alert("XSS")</script>John Doe';
 * const safe = sanitizeText(userInput);
 * // Returns: 'John Doe'
 * ```
 */
export function sanitizeText(text: string): string {
  return DOMPurify.sanitize(text, { ALLOWED_TAGS: [] });
}

/**
 * Sanitizes user name for display.
 *
 * Removes HTML and trims whitespace.
 *
 * @param name - User name to sanitize
 * @returns Sanitized name
 */
export function sanitizeUserName(name: string): string {
  return sanitizeText(name).trim();
}

/**
 * Sanitizes device name for display.
 *
 * Removes HTML and trims whitespace.
 *
 * @param deviceName - Device name to sanitize
 * @returns Sanitized device name
 */
export function sanitizeDeviceName(deviceName: string): string {
  return sanitizeText(deviceName).trim();
}

/**
 * Escapes HTML special characters.
 *
 * Converts < > & " ' to HTML entities.
 * Use when you need to display user input as-is without parsing HTML.
 *
 * @param text - Text to escape
 * @returns Escaped text
 *
 * @example
 * ```typescript
 * const escaped = escapeHTML('<script>alert("XSS")</script>');
 * // Returns: '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'
 * ```
 */
export function escapeHTML(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
  };

  return text.replace(/[&<>"']/g, (char) => map[char]);
}
