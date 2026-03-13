"""Settings validation for ``syntek-auth`` — US009.

Validates the ``SYNTEK_AUTH`` settings dict at Django startup.  Called from
``SyntekAuthConfig.ready()``.  Any missing required key or invalid value raises
``ImproperlyConfigured`` immediately.

All logic lives in :func:`validate_settings`.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured

# ---------------------------------------------------------------------------
# Required keys and their expected types / valid value sets
# ---------------------------------------------------------------------------

#: Set of ``LOGIN_FIELD`` values that require ``REQUIRE_USERNAME`` to be ``True``.
LOGIN_FIELD_REQUIRES_USERNAME: frozenset[str] = frozenset(
    {"username", "email_or_username"}
)

#: Set of ``LOGIN_FIELD`` values that require ``REQUIRE_PHONE`` to be set.
LOGIN_FIELD_REQUIRES_PHONE: frozenset[str] = frozenset({"phone", "email_or_phone"})

#: Valid ``LOGIN_FIELD`` values.
VALID_LOGIN_FIELDS: frozenset[str] = frozenset(
    {"email", "username", "phone", "email_or_username", "email_or_phone"}
)

#: Valid MFA method identifiers.
VALID_MFA_METHODS: frozenset[str] = frozenset({"totp", "sms", "email_otp", "passkey"})

#: Valid lockout strategy identifiers.
VALID_LOCKOUT_STRATEGIES: frozenset[str] = frozenset({"fixed", "progressive"})

#: Valid ``REQUIRE_PHONE`` values.
VALID_REQUIRE_PHONE_VALUES: frozenset[object] = frozenset(
    {False, "optional", "required"}
)

#: Keys that must be Python ``bool`` (not merely truthy/falsy).
_BOOL_KEYS: tuple[str, ...] = (
    "REQUIRE_EMAIL",
    "REQUIRE_USERNAME",
    "PASSWORD_REQUIRE_UPPERCASE",
    "PASSWORD_REQUIRE_LOWERCASE",
    "PASSWORD_REQUIRE_DIGITS",
    "PASSWORD_REQUIRE_SYMBOLS",
    "PASSWORD_BREACH_CHECK",
    "MFA_REQUIRED",
    "ROTATE_REFRESH_TOKENS",
    "REGISTRATION_ENABLED",
    "EMAIL_VERIFICATION_REQUIRED",
    "USERNAME_CASE_SENSITIVE",
    "PASSWORD_RESET_INVALIDATES_SESSIONS",
    "PASSWORD_CHANGE_INVALIDATES_OTHER_SESSIONS",
)

#: Keys that must be non-negative integers.
_NON_NEGATIVE_INT_KEYS: tuple[str, ...] = (
    "PASSWORD_MIN_LENGTH",
    "PASSWORD_MAX_LENGTH",
    "PASSWORD_HISTORY",
    "PASSWORD_EXPIRY_DAYS",
    "MFA_BACKUP_CODES_COUNT",
    "ACCESS_TOKEN_LIFETIME",
    "REFRESH_TOKEN_LIFETIME",
    "LOCKOUT_THRESHOLD",
    "LOCKOUT_DURATION",
    "USERNAME_MIN_LENGTH",
    "USERNAME_MAX_LENGTH",
    "PASSWORD_RESET_TOKEN_TTL",
)


def validate_settings(syntek_auth_settings: dict) -> None:  # type: ignore[type-arg]
    """Validate the ``SYNTEK_AUTH`` settings dict.

    Raises ``ImproperlyConfigured`` with a descriptive message for any of:

    - A value is of the wrong type.
    - ``LOGIN_FIELD`` is not a recognised value.
    - ``LOGIN_FIELD`` is ``'username'`` or ``'email_or_username'`` but
      ``REQUIRE_USERNAME`` is ``False``.
    - ``LOGIN_FIELD`` is ``'phone'`` or ``'email_or_phone'`` but ``REQUIRE_PHONE``
      is ``False``.
    - ``MFA_METHODS`` is an empty list or not a list.
    - An MFA method identifier is not recognised.
    - ``LOCKOUT_STRATEGY`` is not ``'fixed'`` or ``'progressive'``.
    - Integer settings carry negative values where only non-negative is valid.

    Parameters
    ----------
    syntek_auth_settings:
        The full ``SYNTEK_AUTH`` dict from ``settings.py``.

    Raises
    ------
    ImproperlyConfigured
        With a message that names the offending key and describes the problem.
    """
    cfg = syntek_auth_settings

    # --- Boolean type checks ------------------------------------------------
    for key in _BOOL_KEYS:
        if key in cfg:
            value = cfg[key]
            if not isinstance(value, bool):
                raise ImproperlyConfigured(
                    f"SYNTEK_AUTH['{key}'] must be a bool (True or False); "
                    f"got {type(value).__name__!r} with value {value!r}."
                )

    # --- Non-negative integer checks ----------------------------------------
    for key in _NON_NEGATIVE_INT_KEYS:
        if key in cfg:
            value = cfg[key]
            if not isinstance(value, int) or isinstance(value, bool):
                raise ImproperlyConfigured(
                    f"SYNTEK_AUTH['{key}'] must be a non-negative integer; "
                    f"got {type(value).__name__!r} with value {value!r}."
                )
            if value < 0:
                raise ImproperlyConfigured(
                    f"SYNTEK_AUTH['{key}'] must be a non-negative integer; "
                    f"got {value!r}."
                )

    # --- LOGIN_FIELD validation ---------------------------------------------
    if "LOGIN_FIELD" in cfg:
        login_field = cfg["LOGIN_FIELD"]
        if login_field not in VALID_LOGIN_FIELDS:
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['LOGIN_FIELD'] must be one of "
                f"{sorted(VALID_LOGIN_FIELDS)!r}; got {login_field!r}."
            )

        # Cross-field: username-requiring fields
        if login_field in LOGIN_FIELD_REQUIRES_USERNAME:
            require_username = cfg.get("REQUIRE_USERNAME", False)
            if require_username is not True:
                raise ImproperlyConfigured(
                    f"SYNTEK_AUTH['LOGIN_FIELD'] = {login_field!r} requires "
                    f"REQUIRE_USERNAME = True, but got {require_username!r}."
                )

        # Cross-field: phone-requiring fields
        if login_field in LOGIN_FIELD_REQUIRES_PHONE:
            require_phone = cfg.get("REQUIRE_PHONE", False)
            if require_phone is False:
                raise ImproperlyConfigured(
                    f"SYNTEK_AUTH['LOGIN_FIELD'] = {login_field!r} requires "
                    f"REQUIRE_PHONE to be 'required' or 'optional', "
                    f"but got {require_phone!r}."
                )

    # --- MFA_METHODS validation ---------------------------------------------
    if "MFA_METHODS" in cfg:
        mfa_methods = cfg["MFA_METHODS"]
        if not isinstance(mfa_methods, list):
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['MFA_METHODS'] must be a list; "
                f"got {type(mfa_methods).__name__!r}."
            )
        if len(mfa_methods) == 0:
            raise ImproperlyConfigured(
                "SYNTEK_AUTH['MFA_METHODS'] must not be empty — "
                "at least one MFA method is required."
            )
        for method in mfa_methods:
            if method not in VALID_MFA_METHODS:
                raise ImproperlyConfigured(
                    f"SYNTEK_AUTH['MFA_METHODS'] contains unrecognised method "
                    f"{method!r}. Valid methods are: {sorted(VALID_MFA_METHODS)!r}."
                )

    # --- LOCKOUT_STRATEGY validation ----------------------------------------
    if "LOCKOUT_STRATEGY" in cfg:
        strategy = cfg["LOCKOUT_STRATEGY"]
        if strategy not in VALID_LOCKOUT_STRATEGIES:
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['LOCKOUT_STRATEGY'] must be one of "
                f"{sorted(VALID_LOCKOUT_STRATEGIES)!r}; got {strategy!r}."
            )

    # --- PASSWORD_RESET_TOKEN_TTL minimum check ------------------------------
    if "PASSWORD_RESET_TOKEN_TTL" in cfg:
        ttl = cfg["PASSWORD_RESET_TOKEN_TTL"]
        # Type already checked above in non-negative int pass; enforce minimum.
        if isinstance(ttl, int) and not isinstance(ttl, bool) and ttl < 300:
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['PASSWORD_RESET_TOKEN_TTL'] must be at least 300 "
                f"seconds (5 minutes); got {ttl!r}."
            )

    # --- OAUTH_MFA_PENDING_TTL validation ------------------------------------
    if "OAUTH_MFA_PENDING_TTL" in cfg:
        ttl = cfg["OAUTH_MFA_PENDING_TTL"]
        if not isinstance(ttl, int) or isinstance(ttl, bool):
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['OAUTH_MFA_PENDING_TTL'] must be an integer; "
                f"got {type(ttl).__name__!r} with value {ttl!r}."
            )
        if ttl < 60 or ttl > 3600:
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['OAUTH_MFA_PENDING_TTL'] must be between 60 and 3600 "
                f"seconds inclusive; got {ttl!r}."
            )

    # --- FIELD_HMAC_KEY validation ------------------------------------------
    if "FIELD_HMAC_KEY" in cfg:
        key = cfg["FIELD_HMAC_KEY"]
        if not isinstance(key, (str, bytes)):
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['FIELD_HMAC_KEY'] must be a str or bytes; "
                f"got {type(key).__name__!r}."
            )
        key_len = len(key) if isinstance(key, bytes) else len(key.encode("utf-8"))
        if key_len < 32:
            raise ImproperlyConfigured(
                f"SYNTEK_AUTH['FIELD_HMAC_KEY'] must be at least 32 bytes "
                f"(256 bits) for security; got {key_len} bytes."
            )
