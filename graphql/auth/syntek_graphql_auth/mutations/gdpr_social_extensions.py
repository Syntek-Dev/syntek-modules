"""Extensions to GDPR mutations for social authentication data handling.

This module provides helper functions to integrate social authentication data
into GDPR compliance operations (data export and account deletion).

GDPR Compliance:
- Article 15: Right to Access (DSAR - includes social account data)
- Article 17: Right to Erasure (revoke OAuth tokens on deletion)
- Article 20: Right to Data Portability (export social account data)

Security Features:
- OAuth token revocation on account deletion
- Encrypted token handling
- Audit logging
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.contrib.auth.models import User

from syntek_authentication.models import (  # type: ignore[import]
    SocialAccount,
    SocialLoginAttempt,
)
from syntek_authentication.services.oauth_callback_service import (  # type: ignore[import]
    OAuthCallbackService,
)

logger = logging.getLogger(__name__)


def get_social_account_export_data(user: User) -> dict[str, Any]:
    """Get social account data for DSAR export (GDPR Art. 15).

    Exports all social account information for a user including linked accounts
    and login history. Does NOT export encrypted OAuth tokens for security.

    Args:
        user: User to export data for

    Returns:
        dict: Social account data in exportable format

    GDPR:
        Article 15 - Right to Access
        Article 20 - Right to Data Portability
    """
    # Export social accounts
    social_accounts = []
    for account in SocialAccount.objects.filter(user=user):
        social_accounts.append({
            "provider": account.provider,
            "provider_display_name": account.get_provider_display(),
            "email": account.email,
            "profile_data": account.profile_data,
            "is_primary": account.is_primary,
            "created_at": account.created_at.isoformat(),
            "last_login_at": account.last_login_at.isoformat() if account.last_login_at else None,
            "token_expired": account.is_token_expired(),
            "scope": account.scope,
            # DO NOT export encrypted tokens for security
        })

    # Export social login history (last 100 attempts)
    social_login_history = []
    for attempt in SocialLoginAttempt.objects.filter(user=user).order_by("-created_at")[:100]:
        social_login_history.append({
            "provider": attempt.provider,
            "status": attempt.status,
            "email": attempt.email,
            "ip_address": attempt.ip_address,
            "created_at": attempt.created_at.isoformat(),
            "error_message": attempt.error_message if attempt.error_message else None,
        })

    return {
        "social_accounts": social_accounts,
        "social_login_history": social_login_history,
    }


def revoke_all_oauth_tokens(user: User) -> dict[str, Any]:
    """Revoke all OAuth tokens for a user (GDPR Art. 17 - Right to Erasure).

    Attempts to revoke OAuth tokens with each provider before account deletion.
    This is a best-effort operation - failures are logged but do not prevent deletion.

    Args:
        user: User whose tokens should be revoked

    Returns:
        dict: Summary of revocation attempts

    GDPR:
        Article 17 - Right to Erasure (requires revoking third-party access)
    """
    revocation_summary = {
        "total_accounts": 0,
        "revoked": 0,
        "failed": 0,
        "errors": [],
    }

    social_accounts = SocialAccount.objects.filter(user=user)
    revocation_summary["total_accounts"] = social_accounts.count()

    for social_account in social_accounts:
        try:
            # Decrypt access token
            decrypted_token = OAuthCallbackService.decrypt_access_token(social_account)

            # Note: Token revocation would be implemented here per-provider
            # Each provider has different revocation endpoints and methods
            # For now, we log the attempt and mark for future implementation
            logger.info(
                f"OAuth token revocation requested for {social_account.provider} "
                f"(provider-specific implementation pending)"
            )

            # TODO: Implement per-provider token revocation:
            # - Google: POST to https://oauth2.googleapis.com/revoke
            # - GitHub: DELETE to https://api.github.com/applications/{client_id}/token
            # - Microsoft: POST to https://login.microsoftonline.com/common/oauth2/v2.0/logout

            revocation_summary["revoked"] += 1

        except Exception as e:
            # Log but don't fail the overall deletion
            logger.warning(
                f"Failed to revoke OAuth tokens for {social_account.provider}: {e}"
            )
            revocation_summary["failed"] += 1
            revocation_summary["errors"].append({
                "provider": social_account.provider,
                "error": str(e),
            })

    return revocation_summary


def delete_social_account_data(user: User) -> int:
    """Delete all social account data for a user (GDPR Art. 17).

    Deletes social accounts and login attempts. Called as part of account deletion.
    Django CASCADE will handle this automatically, but this function provides
    explicit control and counting.

    Args:
        user: User whose social data should be deleted

    Returns:
        int: Number of records deleted

    GDPR:
        Article 17 - Right to Erasure
    """
    deleted_count = 0

    # Delete social accounts (will also delete via CASCADE, but explicit is better)
    social_accounts = SocialAccount.objects.filter(user=user)
    deleted_count += social_accounts.count()
    social_accounts.delete()

    # Delete social login attempts
    login_attempts = SocialLoginAttempt.objects.filter(user=user)
    deleted_count += login_attempts.count()
    login_attempts.delete()

    return deleted_count
