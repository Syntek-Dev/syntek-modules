/**
 * Secure storage adapter interface.
 *
 * Platform-agnostic interface for secure token storage.
 * Implementations:
 * - Web: useSecureStorage.web.ts (httpOnly cookies)
 * - Mobile: useSecureStorage.native.ts (SecureStore)
 */

export interface SecureStorageAdapter {
  /**
   * Stores value securely.
   *
   * @param key - Storage key
   * @param value - Value to store
   */
  setItem(key: string, value: string): Promise<void>;

  /**
   * Retrieves value from secure storage.
   *
   * @param key - Storage key
   * @returns Stored value or null if not found
   */
  getItem(key: string): Promise<string | null>;

  /**
   * Removes value from secure storage.
   *
   * @param key - Storage key
   */
  removeItem(key: string): Promise<void>;

  /**
   * Clears all values from secure storage.
   */
  clear(): Promise<void>;
}

/**
 * Gets platform-specific secure storage adapter.
 *
 * Automatically selects web or native implementation based on environment.
 *
 * @returns Secure storage adapter for current platform
 *
 * @example
 * ```typescript
 * import { getSecureStorage } from '@syntek/shared-auth/hooks/adapters';
 *
 * const storage = getSecureStorage();
 * await storage.setItem('authToken', token);
 * ```
 */
export function getSecureStorage(): SecureStorageAdapter {
  // Detect platform (React Native)
  if (typeof navigator !== 'undefined' && navigator.product === 'ReactNative') {
    // Load native implementation
    const { secureStorage } = require('./useSecureStorage.native');
    return secureStorage;
  }

  // Default to web implementation
  const { secureStorage } = require('./useSecureStorage.web');
  return secureStorage;
}
