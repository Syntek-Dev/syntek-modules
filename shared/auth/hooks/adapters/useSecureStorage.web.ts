/**
 * Web secure storage adapter (httpOnly cookies).
 *
 * Uses httpOnly cookies for secure token storage on web.
 * Cookies are set by server-side (Next.js API routes) to ensure httpOnly flag.
 *
 * SECURITY: Never use localStorage for authentication tokens (XSS risk).
 */

import type { SecureStorageAdapter } from './useSecureStorage';

/**
 * Web secure storage implementation using httpOnly cookies.
 *
 * IMPORTANT: Actual cookie setting is done server-side via Set-Cookie headers.
 * This adapter only manages client-side cookie reading/deletion.
 */
export const secureStorage: SecureStorageAdapter = {
  /**
   * Sets value in httpOnly cookie (via server-side API).
   *
   * Sends request to server to set httpOnly cookie.
   * Client-side JavaScript cannot set httpOnly cookies directly.
   *
   * @param key - Cookie name
   * @param value - Cookie value
   */
  async setItem(key: string, value: string): Promise<void> {
    // Send request to server to set httpOnly cookie
    const response = await fetch('/api/auth/set-cookie', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ key, value }),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to set secure cookie');
    }
  },

  /**
   * Retrieves value from cookie.
   *
   * IMPORTANT: httpOnly cookies are not accessible via document.cookie.
   * This method returns null for httpOnly cookies (by design).
   * Use server-side session validation instead.
   *
   * @param key - Cookie name
   * @returns Cookie value or null
   */
  async getItem(key: string): Promise<string | null> {
    // httpOnly cookies cannot be read client-side
    // Return null (server validates token via Cookie header)
    return null;
  },

  /**
   * Removes value from cookie (via server-side API).
   *
   * Sends request to server to clear httpOnly cookie.
   *
   * @param key - Cookie name
   */
  async removeItem(key: string): Promise<void> {
    // Send request to server to clear cookie
    const response = await fetch('/api/auth/clear-cookie', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ key }),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to clear secure cookie');
    }
  },

  /**
   * Clears all authentication cookies (via server-side API).
   */
  async clear(): Promise<void> {
    // Send request to server to clear all auth cookies
    const response = await fetch('/api/auth/clear-all-cookies', {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to clear all cookies');
    }
  },
};

/**
 * Fallback: Client-side cookie utilities (non-httpOnly only).
 *
 * These utilities work for regular cookies but NOT httpOnly cookies.
 * Use only for non-sensitive data.
 */

/**
 * Reads non-httpOnly cookie value.
 *
 * @param name - Cookie name
 * @returns Cookie value or null
 */
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null;
  }

  return null;
}

/**
 * Sets non-httpOnly cookie (client-side).
 *
 * WARNING: Do NOT use for authentication tokens (use httpOnly cookies instead).
 *
 * @param name - Cookie name
 * @param value - Cookie value
 * @param days - Expiry in days
 */
function setCookie(name: string, value: string, days: number = 7): void {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; Secure; SameSite=Strict`;
}

/**
 * Deletes non-httpOnly cookie.
 *
 * @param name - Cookie name
 */
function deleteCookie(name: string): void {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}
