/**
 * Remember Me Checkbox Component
 *
 * Checkbox for "Keep me logged in" option with security information tooltip.
 * Explains session duration differences between enabled and disabled states.
 */

'use client';

import { useState } from 'react';
import { Checkbox } from '@syntek/shared/design-system/components';

/**
 * Remember me checkbox props
 */
export interface RememberMeCheckboxProps {
  /** Checked state */
  checked: boolean;
  /** Callback when checked state changes */
  onChange: (checked: boolean) => void;
  /** Disable checkbox */
  disabled?: boolean;
  /** Session duration when unchecked (minutes) */
  defaultSessionDuration?: number;
  /** Session duration when checked (days) */
  extendedSessionDuration?: number;
}

/**
 * Renders "Remember Me" checkbox with security tooltip
 *
 * Provides context about session duration:
 * - Unchecked: Short session (default: 30 minutes)
 * - Checked: Extended session (default: 30 days)
 *
 * Security considerations explained to user:
 * - Only use on trusted devices
 * - Longer session = higher risk if device compromised
 * - Session can be revoked from account settings
 *
 * @param checked - Checkbox checked state
 * @param onChange - Callback when state changes
 * @param disabled - Disable checkbox
 * @param defaultSessionDuration - Short session duration (minutes)
 * @param extendedSessionDuration - Extended session duration (days)
 * @returns Remember me checkbox component
 */
export function RememberMeCheckbox({
  checked,
  onChange,
  disabled = false,
  defaultSessionDuration = 30,
  extendedSessionDuration = 30,
}: RememberMeCheckboxProps): JSX.Element {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Checkbox
          id="remember-me"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          label="Keep me logged in"
        />
        <button
          type="button"
          onClick={() => setShowInfo(!showInfo)}
          className="text-gray-400 hover:text-gray-600"
          aria-label="Show session information"
        >
          <svg
            className="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      {showInfo && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-900">
          <p className="font-medium mb-1">Session Duration:</p>
          <ul className="list-disc list-inside space-y-1 text-blue-800">
            <li>
              <strong>Unchecked:</strong> {defaultSessionDuration} minutes (logs out after inactivity)
            </li>
            <li>
              <strong>Checked:</strong> {extendedSessionDuration} days (stays logged in)
            </li>
          </ul>
          <p className="mt-2 text-xs text-blue-700">
            ⚠️ Only enable on trusted devices. You can revoke sessions from account settings.
          </p>
        </div>
      )}
    </div>
  );
}
