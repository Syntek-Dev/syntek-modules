/**
 * Auto-Logout Warning Component
 *
 * Displays countdown modal warning user of impending automatic logout due to
 * inactivity. Allows user to extend session before timeout expires.
 */

'use client';

import { useEffect, useState } from 'react';
import { Button, Alert } from '@syntek/shared/design-system/components';

/**
 * Auto-logout warning props
 */
export interface AutoLogoutWarningProps {
  /** Seconds remaining until logout */
  secondsRemaining: number;
  /** Callback to extend session */
  onExtendSession: () => void;
  /** Callback when session expires */
  onSessionExpired: () => void;
  /** Show warning modal */
  show: boolean;
}

/**
 * Formats seconds as MM:SS countdown
 */
function formatCountdown(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Renders auto-logout warning modal with countdown timer
 *
 * Features:
 * - Live countdown timer (MM:SS format)
 * - Extend session button
 * - Warning message
 * - Automatically logs out when timer expires
 *
 * **UX Behaviour:**
 * - Shows 5 minutes before session expires
 * - Updates countdown every second
 * - Allows user to extend session with one click
 * - Auto-dismisses if session extended
 *
 * @param secondsRemaining - Seconds until automatic logout
 * @param onExtendSession - Callback to extend session
 * @param onSessionExpired - Callback when session expires
 * @param show - Display warning modal
 * @returns Auto-logout warning component
 */
export function AutoLogoutWarning({
  secondsRemaining: initialSeconds,
  onExtendSession,
  onSessionExpired,
  show,
}: AutoLogoutWarningProps): JSX.Element | null {
  const [secondsRemaining, setSecondsRemaining] = useState(initialSeconds);

  useEffect(() => {
    setSecondsRemaining(initialSeconds);
  }, [initialSeconds]);

  useEffect(() => {
    if (!show || secondsRemaining <= 0) return;

    const interval = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onSessionExpired();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [show, secondsRemaining, onSessionExpired]);

  if (!show) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="logout-warning-title"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6 space-y-4">
        <Alert variant="warning" title="Session Expiring Soon">
          <div className="space-y-2">
            <p>
              You will be automatically logged out due to inactivity in:{' '}
              <strong className="text-lg font-bold">{formatCountdown(secondsRemaining)}</strong>
            </p>
            <p className="text-sm">
              Click "Stay Logged In" to extend your session, or you will be logged out for security.
            </p>
          </div>
        </Alert>

        <div className="flex gap-3">
          <Button variant="primary" fullWidth onClick={onExtendSession}>
            Stay Logged In
          </Button>
          <Button variant="outline" fullWidth onClick={onSessionExpired}>
            Log Out Now
          </Button>
        </div>
      </div>
    </div>
  );
}
