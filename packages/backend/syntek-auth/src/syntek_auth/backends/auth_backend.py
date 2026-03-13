"""Authentication backend for ``syntek-auth`` — US009.

Routes authentication lookup to the correct model field(s) based on the
``LOGIN_FIELD`` setting.

Because PII columns (``email``, ``phone``, ``username``) are encrypted with
AES-256-GCM (non-deterministic), DB lookups cannot use the ciphertext column
directly.  Instead, ``resolve_login_field`` computes the HMAC-SHA256 token for
the supplied identifier and queries the companion ``*_token`` column.

``SyntekAuthBackend`` is a Django authentication backend that delegates
identity lookup to ``resolve_login_field`` and password verification to
Django's built-in ``check_password`` method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser


def resolve_login_field(identifier: str, login_field: str) -> AbstractBaseUser | None:
    """Look up a user by the supplied identifier using the configured login field.

    Queries via the HMAC-SHA256 ``*_token`` companion column rather than the
    ciphertext column directly.  All lookups are performed at runtime to avoid
    circular imports.

    Parameters
    ----------
    identifier:
        The value submitted in the login form (e.g. an email address, username,
        or phone number).
    login_field:
        The value of ``SYNTEK_AUTH['LOGIN_FIELD']``.  Supported values:
        ``'email'``, ``'username'``, ``'phone'``, ``'email_or_username'``,
        ``'email_or_phone'``.

    Returns
    -------
    AbstractBaseUser | None
        The matching user, or ``None`` if no user is found or the
        ``login_field`` value is not recognised.
    """
    from django.conf import settings
    from django.contrib.auth import get_user_model

    from syntek_auth.services.lookup_tokens import (
        make_email_token,
        make_phone_token,
        make_username_token,
    )

    UserModel = get_user_model()  # noqa: N806
    cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
    case_sensitive: bool = bool(cfg.get("USERNAME_CASE_SENSITIVE", False))

    if login_field == "email":
        return UserModel.objects.filter(  # type: ignore[return-value]
            email_token=make_email_token(identifier)
        ).first()

    if login_field == "username":
        return UserModel.objects.filter(  # type: ignore[return-value]
            username_token=make_username_token(
                identifier, case_sensitive=case_sensitive
            )
        ).first()

    if login_field == "phone":
        return UserModel.objects.filter(  # type: ignore[return-value]
            phone_token=make_phone_token(identifier)
        ).first()

    if login_field == "email_or_username":
        return (  # type: ignore[return-value]
            UserModel.objects.filter(email_token=make_email_token(identifier)).first()
            or UserModel.objects.filter(
                username_token=make_username_token(
                    identifier, case_sensitive=case_sensitive
                )
            ).first()
        )

    if login_field == "email_or_phone":
        return (  # type: ignore[return-value]
            UserModel.objects.filter(email_token=make_email_token(identifier)).first()
            or UserModel.objects.filter(
                phone_token=make_phone_token(identifier)
            ).first()
        )

    return None


class SyntekAuthBackend:
    """Django authentication backend for ``syntek-auth``.

    Delegates user lookup to :func:`resolve_login_field` and password
    verification to Django's ``AbstractBaseUser.check_password``.

    Register in ``AUTHENTICATION_BACKENDS`` settings as
    ``'syntek_auth.backends.auth_backend.SyntekAuthBackend'``.
    """

    def authenticate(
        self,
        request: object,  # noqa: ARG002
        username: str | None = None,
        password: str | None = None,
        **kwargs: object,  # noqa: ARG002
    ) -> AbstractBaseUser | None:
        """Attempt to authenticate a user with the given credentials.

        Returns ``None`` — rather than raising — on any authentication failure,
        as required by the Django authentication backend protocol.

        Parameters
        ----------
        request:
            The current HTTP request (may be ``None`` in non-HTTP contexts).
        username:
            The login identifier (email, username, or phone depending on
            ``LOGIN_FIELD``).
        password:
            The plaintext password to verify.
        **kwargs:
            Unused additional keyword arguments forwarded by Django.

        Returns
        -------
        AbstractBaseUser | None
            The authenticated user, or ``None`` if authentication fails.
        """
        if not username or password is None:
            return None

        from django.conf import settings

        cfg: dict = getattr(settings, "SYNTEK_AUTH", {})  # type: ignore[type-arg]
        login_field: str = cfg.get("LOGIN_FIELD", "email")

        user = resolve_login_field(username, login_field)

        if user is None or not user.is_active or not user.check_password(password):  # type: ignore[union-attr]
            return None

        return user

    def get_user(self, user_id: int) -> AbstractBaseUser | None:
        """Return the user associated with ``user_id``, or ``None``.

        Parameters
        ----------
        user_id:
            Primary key of the user to retrieve.

        Returns
        -------
        AbstractBaseUser | None
            The matching user, or ``None`` if not found.
        """
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()  # noqa: N806
        try:
            return UserModel.objects.get(pk=user_id)  # type: ignore[return-value]
        except UserModel.DoesNotExist:
            return None
