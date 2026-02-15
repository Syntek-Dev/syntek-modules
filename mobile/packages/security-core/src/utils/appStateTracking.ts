/**
 * appStateTracking.ts
 *
 * Tracks React Native app state (foreground/background) for auto-logout.
 * Integrates with shared auto-logout logic to track inactivity.
 */

import { useEffect, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';

/**
 * App state tracking configuration.
 */
export interface AppStateTrackingConfig {
  onBackground?: () => void;
  onForeground?: () => void;
  onInactive?: () => void;
}

/**
 * Tracks app state changes and triggers callbacks.
 *
 * Monitors when app goes to background, foreground, or becomes inactive.
 * Used for auto-logout functionality - tracks inactivity when app is backgrounded.
 *
 * @param config - Callbacks for different app states
 *
 * @example
 * ```ts
 * useAppStateTracking({
 *   onBackground: () => {
 *     console.log('App went to background');
 *     trackInactivity();
 *   },
 *   onForeground: () => {
 *     console.log('App came to foreground');
 *     resetInactivityTimer();
 *   },
 * });
 * ```
 */
export function useAppStateTracking(config: AppStateTrackingConfig): void {
  const appState = useRef<AppStateStatus>(AppState.currentState);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState) => {
      // App transitioning to background
      if (
        appState.current.match(/active|inactive/) &&
        nextAppState === 'background'
      ) {
        config.onBackground?.();
      }

      // App transitioning to foreground
      if (
        appState.current === 'background' &&
        nextAppState === 'active'
      ) {
        config.onForeground?.();
      }

      // App becoming inactive (e.g., notification shade pulled down)
      if (nextAppState === 'inactive') {
        config.onInactive?.();
      }

      appState.current = nextAppState;
    });

    return () => subscription.remove();
  }, [config]);
}

/**
 * Tracks time spent in background for auto-logout.
 */
export function useBackgroundTimeTracking(
  onBackgroundTimeout: (duration: number) => void,
  timeoutMs: number = 300000 // 5 minutes default
): void {
  const backgroundStartTime = useRef<number | null>(null);

  useAppStateTracking({
    onBackground: () => {
      backgroundStartTime.current = Date.now();
    },
    onForeground: () => {
      if (backgroundStartTime.current !== null) {
        const backgroundDuration = Date.now() - backgroundStartTime.current;

        if (backgroundDuration >= timeoutMs) {
          onBackgroundTimeout(backgroundDuration);
        }

        backgroundStartTime.current = null;
      }
    },
  });
}
