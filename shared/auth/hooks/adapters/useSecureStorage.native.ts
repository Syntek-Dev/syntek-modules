/**
 * Mobile secure storage adapter (Expo SecureStore).
 *
 * Uses Expo SecureStore for encrypted token storage on iOS/Android.
 * Backed by Keychain (iOS) and EncryptedSharedPreferences (Android).
 *
 * Note: Requires expo-secure-store package:
 * ```bash
 * npx expo install expo-secure-store
 * ```
 */

import * as SecureStore from 'expo-secure-store';
import type { SecureStorageAdapter } from './useSecureStorage';

/**
 * Mobile secure storage implementation using Expo SecureStore.
 *
 * Provides encrypted storage on iOS (Keychain) and Android (EncryptedSharedPreferences).
 */
export const secureStorage: SecureStorageAdapter = {
  /**
   * Stores value securely in device keychain.
   *
   * @param key - Storage key
   * @param value - Value to store
   */
  async setItem(key: string, value: string): Promise<void> {
    await SecureStore.setItemAsync(key, value);
  },

  /**
   * Retrieves value from device keychain.
   *
   * @param key - Storage key
   * @returns Stored value or null if not found
   */
  async getItem(key: string): Promise<string | null> {
    return await SecureStore.getItemAsync(key);
  },

  /**
   * Removes value from device keychain.
   *
   * @param key - Storage key
   */
  async removeItem(key: string): Promise<void> {
    await SecureStore.deleteItemAsync(key);
  },

  /**
   * Clears all authentication values from keychain.
   *
   * Note: SecureStore doesn't provide a "clear all" method.
   * This implementation clears known authentication keys.
   */
  async clear(): Promise<void> {
    const keysToRemove = [
      'authToken',
      'refreshToken',
      'sessionId',
      'userId',
      'mfaToken',
    ];

    await Promise.all(
      keysToRemove.map((key) => SecureStore.deleteItemAsync(key))
    );
  },
};
