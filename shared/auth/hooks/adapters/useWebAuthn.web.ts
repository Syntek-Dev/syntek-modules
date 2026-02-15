/**
 * Web WebAuthn adapter (Browser WebAuthn API).
 *
 * Uses browser WebAuthn API for passkey authentication on web.
 */

/**
 * WebAuthn adapter interface.
 */
export interface WebAuthnAdapter {
  /**
   * Checks if WebAuthn is supported in current browser.
   *
   * @returns True if WebAuthn is available
   */
  isSupported(): boolean;

  /**
   * Creates new WebAuthn credential (registration).
   *
   * @param options - PublicKeyCredentialCreationOptions from server
   * @returns Credential response
   */
  create(
    options: PublicKeyCredentialCreationOptions
  ): Promise<PublicKeyCredential>;

  /**
   * Gets existing WebAuthn credential (authentication).
   *
   * @param options - PublicKeyCredentialRequestOptions from server
   * @returns Credential response
   */
  get(options: PublicKeyCredentialRequestOptions): Promise<PublicKeyCredential>;
}

/**
 * Web WebAuthn implementation using browser WebAuthn API.
 */
export const webAuthnAdapter: WebAuthnAdapter = {
  /**
   * Checks if WebAuthn is supported.
   */
  isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      typeof window.PublicKeyCredential !== 'undefined'
    );
  },

  /**
   * Creates new passkey credential.
   *
   * @param options - Creation options from server
   * @returns Public key credential
   */
  async create(
    options: PublicKeyCredentialCreationOptions
  ): Promise<PublicKeyCredential> {
    if (!this.isSupported()) {
      throw new Error('WebAuthn is not supported in this browser');
    }

    try {
      const credential = await navigator.credentials.create({
        publicKey: options,
      });

      if (!credential) {
        throw new Error('Failed to create credential');
      }

      return credential as PublicKeyCredential;
    } catch (error) {
      if (error instanceof Error) {
        // Handle specific WebAuthn errors
        if (error.name === 'NotAllowedError') {
          throw new Error('User cancelled passkey creation');
        }
        if (error.name === 'InvalidStateError') {
          throw new Error('Passkey already exists for this device');
        }
      }
      throw error;
    }
  },

  /**
   * Authenticates with existing passkey credential.
   *
   * @param options - Request options from server
   * @returns Public key credential
   */
  async get(
    options: PublicKeyCredentialRequestOptions
  ): Promise<PublicKeyCredential> {
    if (!this.isSupported()) {
      throw new Error('WebAuthn is not supported in this browser');
    }

    try {
      const credential = await navigator.credentials.get({
        publicKey: options,
      });

      if (!credential) {
        throw new Error('Failed to get credential');
      }

      return credential as PublicKeyCredential;
    } catch (error) {
      if (error instanceof Error) {
        // Handle specific WebAuthn errors
        if (error.name === 'NotAllowedError') {
          throw new Error('User cancelled authentication');
        }
        if (error.name === 'InvalidStateError') {
          throw new Error('No matching credentials found');
        }
      }
      throw error;
    }
  },
};
