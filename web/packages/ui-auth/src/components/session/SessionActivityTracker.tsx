/**
 * Session Activity Tracker Component
 *
 * Tracks user activity events (clicks, keypresses, mouse movement) to determine
 * if user is active. Used for auto-logout functionality.
 */

'use client';

import { useEffect, useRef } from 'react';

/**
 * Session activity tracker props
 */
export interface SessionActivityTrackerProps {
  /** Callback when user activity is detected */
  onActivity: () => void;
  /** Throttle activity events (ms) */
  throttleMs?: number;
  /** Enable/disable tracking */
  enabled?: boolean;
}

/**
 * Activity event types to track
 */
const ACTIVITY_EVENTS = [
  'mousedown',
  'mousemove',
  'keydown',
  'scroll',
  'touchstart',
  'click',
] as const;

/**
 * Tracks user activity for auto-logout functionality
 *
 * Monitors DOM events to detect user interaction:
 * - Mouse clicks and movement
 * - Keyboard input
 * - Touch events
 * - Scroll events
 *
 * Throttles activity events to avoid excessive callback invocations.
 * Does not track activity when user is on different browser tab.
 *
 * @param onActivity - Callback when activity is detected
 * @param throttleMs - Throttle period in milliseconds (default: 1000ms)
 * @param enabled - Enable/disable tracking (default: true)
 * @returns Session activity tracker component (renders nothing)
 */
export function SessionActivityTracker({
  onActivity,
  throttleMs = 1000,
  enabled = true,
}: SessionActivityTrackerProps): null {
  const lastActivityRef = useRef<number>(0);

  useEffect(() => {
    if (!enabled) return;

    /**
     * Handles activity event with throttling
     */
    const handleActivity = (): void => {
      const now = Date.now();

      // Throttle: Only fire if enough time has passed
      if (now - lastActivityRef.current >= throttleMs) {
        lastActivityRef.current = now;
        onActivity();
      }
    };

    // Attach event listeners to document
    ACTIVITY_EVENTS.forEach((event) => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    // Cleanup on unmount
    return () => {
      ACTIVITY_EVENTS.forEach((event) => {
        document.removeEventListener(event, handleActivity);
      });
    };
  }, [onActivity, throttleMs, enabled]);

  // This component renders nothing
  return null;
}
