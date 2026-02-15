/**
 * Social Account Card Component
 *
 * Displays a linked social account with provider info and unlink button.
 * Shows connection date and allows users to disconnect accounts.
 */

'use client';

import { useState } from 'react';
import { Button, Card, Badge } from '@syntek/shared/design-system/components';
import type { SocialAccount } from '@syntek/shared-auth/types';

/**
 * Social account card props
 */
export interface SocialAccountCardProps {
  /** Social account data */
  account: SocialAccount;
  /** Callback when account is unlinked */
  onUnlink: (accountId: string) => Promise<void>;
  /** Disable unlink button */
  disableUnlink?: boolean;
}

/**
 * Provider icons (emoji fallback for demo, replace with real SVG icons)
 */
const PROVIDER_ICONS: Record<string, string> = {
  google: '🔵',
  github: '⚫',
  microsoft: '🟦',
  apple: '⚫',
  facebook: '🔵',
  linkedin: '🔵',
  x: '⚫',
};

/**
 * Renders social account card with unlink option
 *
 * Displays:
 * - Provider name and icon
 * - Account username/email
 * - Connection date
 * - Unlink button
 *
 * @param account - Social account object
 * @param onUnlink - Callback to unlink account
 * @param disableUnlink - Disable unlink button
 * @returns Social account card component
 */
export function SocialAccountCard({
  account,
  onUnlink,
  disableUnlink = false,
}: SocialAccountCardProps): JSX.Element {
  const [isUnlinking, setIsUnlinking] = useState(false);

  /**
   * Handles account unlinking with confirmation
   */
  const handleUnlink = async (): Promise<void> => {
    if (!confirm(`Are you sure you want to unlink your ${account.provider} account?`)) {
      return;
    }

    setIsUnlinking(true);

    try {
      await onUnlink(account.id);
    } catch (error) {
      alert(`Failed to unlink account: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUnlinking(false);
    }
  };

  const icon = PROVIDER_ICONS[account.provider] || '🔗';
  const providerName = account.provider.charAt(0).toUpperCase() + account.provider.slice(1);
  const connectedDate = new Date(account.connectedAt).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{icon}</div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-gray-900">{providerName}</h3>
              {account.isPrimary && <Badge variant="success">Primary</Badge>}
            </div>
            <p className="text-sm text-gray-600">{account.email || account.username}</p>
            <p className="text-xs text-gray-500">Connected on {connectedDate}</p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleUnlink}
          disabled={disableUnlink || isUnlinking}
        >
          {isUnlinking ? 'Unlinking...' : 'Unlink'}
        </Button>
      </div>
    </Card>
  );
}
