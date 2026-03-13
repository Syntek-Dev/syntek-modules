"""GraphQL password mutations for ``syntek-auth`` — US009.

Strawberry mutations for password change, reset request, reset confirmation,
email verification, phone verification, and their resend counterparts.

All resolvers delegate to the service layer; no business logic lives directly
in mutation methods.  Service imports are placed inside each resolver body
to avoid circular imports between the mutation layer, the model layer, and
the service layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import strawberry

from syntek_auth.types.auth import (  # noqa: TC001
    ChangePasswordInput,
    ResetPasswordConfirmInput,
    ResetPasswordRequestInput,
    VerifyEmailInput,
    VerifyPhoneInput,
)

if TYPE_CHECKING:
    from strawberry.types import Info


@strawberry.type
class PasswordMutations:
    """Strawberry mutation type for password and verification operations."""

    @strawberry.mutation
    def change_password(self, info: Info, input: ChangePasswordInput) -> bool:  # noqa: A002
        """Change the authenticated user's password.

        Verifies the current password, validates the new password against
        ``SYNTEK_AUTH`` policy, then persists the new hash and invalidates all
        other active sessions when ``PASSWORD_CHANGE_INVALIDATES_OTHER_SESSIONS``
        is ``True``.

        Parameters
        ----------
        info:
            Strawberry resolver context carrying the HTTP request.
        input:
            Current password and desired new password.

        Returns
        -------
        bool
            ``True`` on success.

        Raises
        ------
        ValueError
            If the request is unauthenticated, the current password is wrong,
            or the new password violates policy or history rules.
        """
        from django.conf import settings

        from syntek_auth.services.password_change import change_password

        request = getattr(info.context, "request", None)

        if request is None or not request.user.is_authenticated:
            raise ValueError("Authentication required.")

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        result = change_password(
            user_id=request.user.pk,
            current_password=input.current_password,
            new_password=input.new_password,
            current_refresh_jti=None,
            password_policy=cfg,
        )

        if not result.success:
            raise ValueError(result.message)

        return True

    @strawberry.mutation
    def reset_password_request(
        self,
        info: Info,  # noqa: ARG002
        input: ResetPasswordRequestInput,  # noqa: A002
    ) -> bool:
        """Request a password-reset link for the supplied email address.

        Always returns ``True`` regardless of whether the email matches an
        existing account (anti-enumeration).  When the account exists and is
        verified, a single-use reset token is created and the caller should
        arrange delivery (e.g. via a signal or email backend).

        Parameters
        ----------
        info:
            Strawberry resolver context (unused).
        input:
            The email address for which a reset link is requested.

        Returns
        -------
        bool
            Always ``True`` (anti-enumeration guarantee).
        """
        from syntek_auth.services.password_reset import request_password_reset

        request_password_reset(input.email)
        return True

    @strawberry.mutation
    def reset_password_confirm(
        self,
        info: Info,  # noqa: ARG002
        input: ResetPasswordConfirmInput,  # noqa: A002
    ) -> bool:
        """Complete the password reset using the supplied token and new password.

        Validates that the token is single-use and unexpired, checks the new
        password against policy and password history, persists the new hash,
        and invalidates all existing refresh tokens when
        ``PASSWORD_RESET_INVALIDATES_SESSIONS`` is ``True``.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused).
        input:
            Single-use reset token and the desired new password.

        Returns
        -------
        bool
            ``True`` on success.

        Raises
        ------
        ValueError
            If the token is invalid, expired, already used, or the new
            password violates policy or history rules.
        """
        from django.conf import settings

        from syntek_auth.services.password_reset import confirm_password_reset

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        result = confirm_password_reset(
            token=input.token,
            new_password=input.new_password,
            password_policy=cfg,
        )

        if not result.success:
            raise ValueError(result.message)

        return True

    @strawberry.mutation
    def verify_email(
        self,
        info: Info,  # noqa: ARG002
        input: VerifyEmailInput,  # noqa: A002
    ) -> bool:
        """Verify the user's email address using the supplied single-use token.

        Marks the account's ``email_verified`` flag on success.  Returns a
        clear error when the token is expired or already used.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused).
        input:
            The single-use email verification token from the email link.

        Returns
        -------
        bool
            ``True`` when the email is now verified.

        Raises
        ------
        ValueError
            If the token is invalid, expired, or already used.
        """
        from syntek_auth.services.email_verification import verify_email_token

        result = verify_email_token(input.token)

        if not result.success:
            raise ValueError(result.message)

        return True

    @strawberry.mutation
    def resend_verification_email(
        self,
        info: Info,  # noqa: ARG002
        user_id: int,
    ) -> bool:
        """Issue a new email verification token for the given user.

        Returns ``False`` when the account is already verified.  Otherwise
        invalidates any pending tokens and issues a fresh one.  The caller
        is responsible for delivering the token.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused).
        user_id:
            Primary key of the user requesting a new verification email.

        Returns
        -------
        bool
            ``True`` if a new token was issued; ``False`` if already verified.

        Raises
        ------
        ValueError
            If the account is already verified.
        """
        from syntek_auth.services.email_verification import resend_verification_email

        issued = resend_verification_email(user_id)
        if not issued:
            raise ValueError("Email address is already verified.")
        return True

    @strawberry.mutation
    def verify_phone(
        self,
        info: Info,  # noqa: ARG002
        input: VerifyPhoneInput,  # noqa: A002
    ) -> bool:
        """Verify the user's phone number using the supplied OTP.

        Increments the attempt counter on incorrect submissions.  Invalidates
        the OTP after three consecutive incorrect attempts.  Marks
        ``phone_verified=True`` on the user record on success.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused).
        input:
            The user's primary key and the 6-character OTP.

        Returns
        -------
        bool
            ``True`` when the phone is now verified.

        Raises
        ------
        ValueError
            If the OTP is invalid, expired, or has been invalidated by too
            many incorrect attempts.
        """
        from syntek_auth.services.phone_verification import verify_phone_otp

        result = verify_phone_otp(user_id=input.user_id, otp=input.otp)

        if not result.success:
            raise ValueError(result.message)

        return True

    @strawberry.mutation
    def resend_phone_otp(
        self,
        info: Info,  # noqa: ARG002
        user_id: int,
    ) -> bool:
        """Issue a new phone OTP for the given user.

        Invalidates any existing pending OTPs and generates a replacement.
        The caller is responsible for delivering the OTP via SMS.

        Parameters
        ----------
        info:
            Strawberry resolver context (unused).
        user_id:
            Primary key of the user requesting a new OTP.

        Returns
        -------
        bool
            Always ``True`` once the new OTP has been generated.
        """
        from syntek_auth.services.phone_verification import resend_phone_otp

        resend_phone_otp(user_id)
        return True
