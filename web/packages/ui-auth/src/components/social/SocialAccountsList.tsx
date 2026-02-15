/**
 * Social Accounts List Component
 *
 * Displays all linked social accounts with management options.
 * Shows primary account and allows linking/unlinking providers.
 */

'use client';

import { SocialAccountCard } from './SocialAccountCard';
import { Button, Alert } from '@syntek/shared/design-system/components';
import type { SocialAccount, SocialProvider } from '@syntek/shared-auth/types';

/**
 * Social accounts list props
 */
export interface SocialAccountsListProps {
  /** List of linked social accounts */
  accounts: SocialAccount[];
  /** Available providers to link */
  availableProviders: SocialProvider[];
  /** Callback when account is unlinked */
  onUnlink: (accountId: string) => Promise<void>;
  /** Callback when linking new provider */
  onLink: (provider: SocialProvider) => void;
  /** Loading state */
  loading?: boolean;
}

/**
 * Renders list of social accounts with link/unlink options
 *
 * Features:
 * - Shows all linked accounts
 * - Highlights primary account
 * - Prevents unlinking last authentication method
 * - Allows linking additional providers
 *
 * @param accounts - Linked social accounts
 * @param availableProviders - Providers available to link
 * @param onUnlink - Callback to unlink account
 * @param onLink - Callback to link new provider
 * @param loading - Loading state
 * @returns Social accounts list component
 */
export function SocialAccountsList({
  accounts,
  availableProviders,
  onUnlink,
  onLink,
  loading = false,
}: SocialAccountsListProps): JSX.Element {
  const linkedProviders = new Set(accounts.map((acc) => acc.provider));
  const unlinkableProviders = availableProviders.filter((p) => !linkedProviders.has(p));

  // Cannot unlink last account
  const canUnlink = accounts.length > 1;

  if (loading) {
    return <div className="text-center py-8 text-gray-600">Loading social accounts...</div>;
  }

  return (
    <div className="space-y-6">
      {accounts.length === 0 ? (
        <Alert variant="info" title="No Social Accounts">
          You have not linked any social accounts yet. Link an account below for faster login.
        </Alert>
      ) : (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-900">Linked Accounts</h3>
          {accounts.map((account) => (
            <SocialAccountCard
              key={account.id}
              account={account}
              onUnlink={onUnlink}
              disableUnlink={!canUnlink}
            />
          ))}
          {!canUnlink && (
            <p className="text-xs text-gray-500">
              You must have at least one authentication method linked
            </p>
          )}
        </div>
      )}

      {unlinkableProviders.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-900">Link Additional Accounts</h3>
          <div className="grid grid-cols-2 gap-3">
            {unlinkableProviders.map((provider) => (
              <Button
                key={provider}
                variant="outline"
                onClick={() => onLink(provider)}
              >
                Link {provider.charAt(0).toUpperCase() + provider.slice(1)}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
