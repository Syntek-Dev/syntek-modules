"""CAPTCHA verification helpers for authentication mutations.

Provides reusable CAPTCHA verification logic with audit logging.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strawberry.types import Info

from apps.core.services.audit_service import AuditService  # type: ignore[import]
from apps.core.services.captcha_service import captcha_service  # type: ignore[import]
from syntek_graphql_core.errors import AuthenticationError, ErrorCode  # type: ignore[import]
from syntek_graphql_core.utils.context import get_ip_address  # type: ignore[import]


def verify_captcha_or_raise(info: Info, captcha_token: str, action: str, email: str | None = None) -> float:
    """Verify CAPTCHA token or raise authentication error.

    Implements CAPTCHA protection (M001) with comprehensive audit logging.

    Args:
        info: GraphQL execution info
        captcha_token: CAPTCHA token from client
        action: Action name (register, login, etc.)
        email: Optional email for audit logging

    Returns:
        float: CAPTCHA score (0.0-1.0)

    Raises:
        AuthenticationError: If CAPTCHA verification fails
    """
    ip_address = get_ip_address(info)

    # Verify CAPTCHA token
    is_valid, score, error = captcha_service.verify_token(
        token=captcha_token,
        action=action,
        remote_ip=ip_address,
    )

    if not is_valid:
        # Log CAPTCHA failure
        metadata = {
            "action": action,
            "score": score,
            "error": error,
        }
        if email:
            metadata["email"] = email

        AuditService.log_event(
            action="captcha_failed",
            user=None,
            organisation=None,
            ip_address=ip_address,
            metadata=metadata,
        )
        raise AuthenticationError(
            ErrorCode.CAPTCHA_FAILED,
            error or "CAPTCHA verification failed",
        )

    # Log CAPTCHA score for monitoring
    AuditService.log_event(
        action="captcha_verified",
        user=None,
        organisation=None,
        ip_address=ip_address,
        metadata={
            "action": action,
            "score": score,
        },
    )

    return score
