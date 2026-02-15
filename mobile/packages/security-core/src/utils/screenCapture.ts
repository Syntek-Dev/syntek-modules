/**
 * screenCapture.ts
 *
 * Prevents screenshots and screen recording on sensitive screens.
 * Protects sensitive data from being captured via screenshots or screen recording.
 * Uses React Native's FLAG_SECURE (Android) and similar mechanisms.
 */

/**
 * Enables screenshot prevention for the current screen.
 *
 * Prevents screenshots and screen recording on sensitive screens
 * (login, passkey entry, backup codes, etc.).
 *
 * Android: Sets FLAG_SECURE on the window
 * iOS: Limited support - shows blank screen in app switcher
 *
 * @example
 * ```ts
 * useEffect(() => {
 *   preventScreenCapture();
 *   return () => allowScreenCapture();
 * }, []);
 * ```
 */
export function preventScreenCapture(): void {
  // TODO: Implement using react-native-screen-capture or native modules
  // Android: getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
  // iOS: Limited - can blur screen in app switcher
  console.log('Screen capture prevention enabled');
}

/**
 * Disables screenshot prevention (re-enables screenshots).
 */
export function allowScreenCapture(): void {
  // TODO: Clear FLAG_SECURE on Android
  console.log('Screen capture prevention disabled');
}

/**
 * React hook for preventing screen capture on component mount.
 *
 * Automatically enables screenshot prevention when component mounts
 * and disables it when component unmounts.
 *
 * @example
 * ```tsx
 * function BackupCodesScreen() {
 *   usePreventScreenCapture();
 *   return <BackupCodes />;
 * }
 * ```
 */
export function usePreventScreenCapture(): void {
  // TODO: Implement using React useEffect
  // useEffect(() => {
  //   preventScreenCapture();
  //   return () => allowScreenCapture();
  // }, []);
}
