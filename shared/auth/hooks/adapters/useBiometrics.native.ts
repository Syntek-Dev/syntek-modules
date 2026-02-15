/**
 * Mobile biometric authentication adapter (iOS FaceID/TouchID, Android biometrics).
 *
 * Uses Expo LocalAuthentication for biometric authentication on mobile.
 *
 * Note: Requires expo-local-authentication package:
 * ```bash
 * npx expo install expo-local-authentication
 * ```
 */

import * as LocalAuthentication from 'expo-local-authentication';

/**
 * Biometric adapter interface.
 */
export interface BiometricAdapter {
  /**
   * Checks if biometric authentication is supported.
   *
   * @returns True if biometrics are available
   */
  isSupported(): Promise<boolean>;

  /**
   * Gets available biometric types on device.
   *
   * @returns List of biometric types (FACE_ID, TOUCH_ID, FINGERPRINT, etc.)
   */
  getAvailableTypes(): Promise<string[]>;

  /**
   * Authenticates user with biometrics.
   *
   * @param promptMessage - Message shown in biometric prompt
   * @returns True if authentication succeeded
   */
  authenticate(promptMessage?: string): Promise<boolean>;
}

/**
 * Mobile biometric implementation using Expo LocalAuthentication.
 */
export const biometricAdapter: BiometricAdapter = {
  /**
   * Checks if biometric authentication is supported.
   */
  async isSupported(): Promise<boolean> {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    return compatible && enrolled;
  },

  /**
   * Gets available biometric types.
   *
   * @returns List of biometric types
   */
  async getAvailableTypes(): Promise<string[]> {
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();

    const typeNames = types.map((type) => {
      switch (type) {
        case LocalAuthentication.AuthenticationType.FINGERPRINT:
          return 'FINGERPRINT';
        case LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION:
          return 'FACE_ID';
        case LocalAuthentication.AuthenticationType.IRIS:
          return 'IRIS';
        default:
          return 'UNKNOWN';
      }
    });

    return typeNames;
  },

  /**
   * Authenticates user with biometrics.
   *
   * @param promptMessage - Custom prompt message
   * @returns True if authentication succeeded
   */
  async authenticate(
    promptMessage: string = 'Authenticate to continue'
  ): Promise<boolean> {
    const isSupported = await this.isSupported();

    if (!isSupported) {
      throw new Error('Biometric authentication is not available on this device');
    }

    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage,
        fallbackLabel: 'Use password',
        cancelLabel: 'Cancel',
      });

      return result.success;
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return false;
    }
  },
};
