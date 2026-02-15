/**
 * Secure logging utility with PII redaction.
 *
 * Logs authentication events without exposing sensitive data.
 *
 * SECURITY: Never log passwords, TOTP codes, recovery keys, email, phone.
 */

/**
 * Sensitive field patterns to redact.
 */
const SENSITIVE_PATTERNS = {
  email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
  phone: /\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}/g,
  password: /password["\s:=]+[^\s,}"]*/gi,
  token: /token["\s:=]+[^\s,}"]*/gi,
  secret: /secret["\s:=]+[^\s,}"]*/gi,
  apiKey: /api[_-]?key["\s:=]+[^\s,}"]*/gi,
  totpCode: /\b\d{6}\b/g,
};

/**
 * Sensitive field names to redact from objects.
 */
const SENSITIVE_FIELDS = [
  'password',
  'newPassword',
  'currentPassword',
  'confirmPassword',
  'email',
  'phoneNumber',
  'phone',
  'totpCode',
  'backupCode',
  'recoveryKey',
  'secret',
  'token',
  'authToken',
  'accessToken',
  'refreshToken',
  'apiKey',
  'sessionToken',
];

/**
 * Redacts sensitive information from string.
 *
 * @param text - Text to redact
 * @returns Redacted text
 */
function redactString(text: string): string {
  let redacted = text;

  // Redact email addresses
  redacted = redacted.replace(SENSITIVE_PATTERNS.email, '[EMAIL REDACTED]');

  // Redact phone numbers
  redacted = redacted.replace(SENSITIVE_PATTERNS.phone, '[PHONE REDACTED]');

  // Redact passwords
  redacted = redacted.replace(SENSITIVE_PATTERNS.password, 'password=[REDACTED]');

  // Redact tokens
  redacted = redacted.replace(SENSITIVE_PATTERNS.token, 'token=[REDACTED]');

  // Redact secrets
  redacted = redacted.replace(SENSITIVE_PATTERNS.secret, 'secret=[REDACTED]');

  // Redact API keys
  redacted = redacted.replace(SENSITIVE_PATTERNS.apiKey, 'api_key=[REDACTED]');

  // Redact TOTP codes (6 digits)
  redacted = redacted.replace(SENSITIVE_PATTERNS.totpCode, '[TOTP REDACTED]');

  return redacted;
}

/**
 * Redacts sensitive fields from object.
 *
 * @param obj - Object to redact
 * @returns Redacted object
 */
function redactObject(obj: any): any {
  if (typeof obj !== 'object' || obj === null) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(redactObject);
  }

  const redacted: any = {};

  for (const [key, value] of Object.entries(obj)) {
    if (SENSITIVE_FIELDS.includes(key.toLowerCase())) {
      redacted[key] = '[REDACTED]';
    } else if (typeof value === 'object') {
      redacted[key] = redactObject(value);
    } else if (typeof value === 'string') {
      redacted[key] = redactString(value);
    } else {
      redacted[key] = value;
    }
  }

  return redacted;
}

/**
 * Logs message with PII redaction (info level).
 *
 * @param message - Log message
 * @param data - Optional data to log
 *
 * @example
 * ```typescript
 * logInfo('User logged in', { email: 'user@example.com', sessionId: '123' });
 * // Logs: User logged in { email: '[EMAIL REDACTED]', sessionId: '123' }
 * ```
 */
export function logInfo(message: string, data?: any): void {
  const redactedMessage = redactString(message);
  const redactedData = data ? redactObject(data) : undefined;

  console.info(redactedMessage, redactedData);
}

/**
 * Logs error with PII redaction.
 *
 * @param message - Error message
 * @param error - Error object or data
 *
 * @example
 * ```typescript
 * logError('Login failed', { email: 'user@example.com', error: 'Invalid password' });
 * ```
 */
export function logError(message: string, error?: any): void {
  const redactedMessage = redactString(message);
  const redactedError = error ? redactObject(error) : undefined;

  console.error(redactedMessage, redactedError);
}

/**
 * Logs warning with PII redaction.
 *
 * @param message - Warning message
 * @param data - Optional data to log
 */
export function logWarning(message: string, data?: any): void {
  const redactedMessage = redactString(message);
  const redactedData = data ? redactObject(data) : undefined;

  console.warn(redactedMessage, redactedData);
}

/**
 * Logs debug message with PII redaction (only in development).
 *
 * @param message - Debug message
 * @param data - Optional data to log
 */
export function logDebug(message: string, data?: any): void {
  if (process.env.NODE_ENV !== 'production') {
    const redactedMessage = redactString(message);
    const redactedData = data ? redactObject(data) : undefined;

    console.debug(redactedMessage, redactedData);
  }
}
