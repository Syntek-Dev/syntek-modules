/**
 * Have I Been Pwned (HIBP) password checker utility.
 *
 * Checks passwords against the HIBP Pwned Passwords database using k-anonymity.
 * Never sends full password or hash to the API (privacy-preserving).
 *
 * API: https://haveibeenpwned.com/API/v3#PwnedPasswords
 *
 * @example
 * ```typescript
 * const isPwned = await checkPasswordPwned('password123');
 * if (isPwned) {
 *   // Warn user that password has been compromised
 * }
 * ```
 */

/**
 * HIBP API endpoint for password range queries.
 */
const HIBP_API_URL = 'https://api.pwnedpasswords.com/range/';

/**
 * Rate limiter for HIBP API calls.
 * HIBP rate limit: Unthrottled, but respectful usage recommended (1/second).
 */
class HIBPRateLimiter {
  private lastCallTime: number = 0;
  private readonly minInterval: number = 1000; // 1 second

  /**
   * Waits until rate limit allows next call.
   */
  async waitForRateLimit(): Promise<void> {
    const now = Date.now();
    const timeSinceLastCall = now - this.lastCallTime;

    if (timeSinceLastCall < this.minInterval) {
      const waitTime = this.minInterval - timeSinceLastCall;
      await new Promise((resolve) => setTimeout(resolve, waitTime));
    }

    this.lastCallTime = Date.now();
  }
}

const rateLimiter = new HIBPRateLimiter();

/**
 * Computes SHA-1 hash of a string.
 *
 * Uses SubtleCrypto API (browser) or crypto module (Node.js).
 *
 * @param text - Text to hash
 * @returns SHA-1 hash in uppercase hexadecimal
 */
async function sha1(text: string): Promise<string> {
  // Browser environment
  if (typeof window !== 'undefined' && window.crypto?.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await window.crypto.subtle.digest('SHA-1', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    return hashHex.toUpperCase();
  }

  // Node.js environment
  if (typeof require !== 'undefined') {
    const crypto = require('crypto');
    return crypto.createHash('sha1').update(text).digest('hex').toUpperCase();
  }

  throw new Error('SHA-1 not supported in this environment');
}

/**
 * Checks if password has been compromised in a data breach.
 *
 * Uses HIBP k-anonymity API (sends only first 5 characters of SHA-1 hash).
 * Returns true if password appears in breach database.
 *
 * PRIVACY: Password is never sent to the API, only first 5 chars of hash.
 *
 * @param password - Password to check
 * @returns True if password has been pwned, false otherwise
 *
 * @example
 * ```typescript
 * const isPwned = await checkPasswordPwned('password123');
 * if (isPwned) {
 *   alert('This password has been compromised in a data breach!');
 * }
 * ```
 */
export async function checkPasswordPwned(password: string): Promise<boolean> {
  try {
    // Rate limit to respect HIBP API
    await rateLimiter.waitForRateLimit();

    // Compute SHA-1 hash of password
    const hash = await sha1(password);

    // k-anonymity: Send only first 5 characters of hash
    const prefix = hash.substring(0, 5);
    const suffix = hash.substring(5);

    // Fetch password range from HIBP API
    const response = await fetch(`${HIBP_API_URL}${prefix}`, {
      headers: {
        'User-Agent': 'Syntek-Auth-Module',
      },
    });

    if (!response.ok) {
      // API error - fail open (don't block user)
      console.error(`HIBP API error: ${response.status}`);
      return false;
    }

    const text = await response.text();

    // Check if our hash suffix appears in the response
    const lines = text.split('\n');
    for (const line of lines) {
      const [hashSuffix] = line.split(':');
      if (hashSuffix === suffix) {
        return true; // Password found in breach database
      }
    }

    return false; // Password not found in breaches
  } catch (error) {
    // Network error or other failure - fail open (don't block user)
    console.error('HIBP check failed:', error);
    return false;
  }
}

/**
 * Checks password with debouncing to prevent excessive API calls.
 *
 * Useful for real-time password validation as user types.
 *
 * @param password - Password to check
 * @param debounceMs - Debounce delay in milliseconds (default: 500ms)
 * @returns Promise that resolves to true if password is pwned
 *
 * @example
 * ```typescript
 * const [isPwned, setIsPwned] = useState(false);
 *
 * const handlePasswordChange = async (value: string) => {
 *   const result = await checkPasswordPwnedDebounced(value, 1000);
 *   setIsPwned(result);
 * };
 * ```
 */
export async function checkPasswordPwnedDebounced(
  password: string,
  debounceMs: number = 500
): Promise<boolean> {
  return new Promise((resolve) => {
    const timerId = setTimeout(async () => {
      const result = await checkPasswordPwned(password);
      resolve(result);
    }, debounceMs);

    // Store timer ID for potential cancellation
    (checkPasswordPwnedDebounced as any).timerId = timerId;
  });
}

/**
 * Cancels pending debounced HIBP check.
 *
 * Call this when component unmounts to prevent memory leaks.
 */
export function cancelPendingHIBPCheck(): void {
  const timerId = (checkPasswordPwnedDebounced as any).timerId;
  if (timerId) {
    clearTimeout(timerId);
  }
}

/**
 * Gets the count of times a password has been pwned.
 *
 * Returns number of times password appears in breach database.
 * Higher counts indicate more widespread compromise.
 *
 * @param password - Password to check
 * @returns Number of times password has been pwned (0 if not pwned)
 *
 * @example
 * ```typescript
 * const count = await getPasswordPwnedCount('password123');
 * console.log(`This password has been seen ${count} times in breaches`);
 * ```
 */
export async function getPasswordPwnedCount(
  password: string
): Promise<number> {
  try {
    await rateLimiter.waitForRateLimit();

    const hash = await sha1(password);
    const prefix = hash.substring(0, 5);
    const suffix = hash.substring(5);

    const response = await fetch(`${HIBP_API_URL}${prefix}`, {
      headers: {
        'User-Agent': 'Syntek-Auth-Module',
      },
    });

    if (!response.ok) {
      return 0;
    }

    const text = await response.text();
    const lines = text.split('\n');

    for (const line of lines) {
      const [hashSuffix, count] = line.split(':');
      if (hashSuffix === suffix) {
        return parseInt(count.trim(), 10);
      }
    }

    return 0;
  } catch (error) {
    console.error('HIBP count check failed:', error);
    return 0;
  }
}
