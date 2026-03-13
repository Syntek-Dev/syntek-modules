"""Sandbox Django settings for syntek-modules development.

This settings file is used exclusively by ``sandbox/manage.py`` for running
management commands (makemigrations, migrate, shell, seed, etc.) during
development.  It is NOT a production or consumer settings file.

Environment variables (set in your shell or a local .env file):

    SANDBOX_SECRET_KEY   — Django SECRET_KEY (defaults to an insecure dev key)
    SANDBOX_DB_NAME      — PostgreSQL database name (default: syntek_sandbox)
    SANDBOX_DB_USER      — PostgreSQL user (default: postgres)
    SANDBOX_DB_PASSWORD  — PostgreSQL password (default: postgres)
    SANDBOX_DB_HOST      — PostgreSQL host (default: localhost)
    SANDBOX_DB_PORT      — PostgreSQL port (default: 5432)
    SYNTEK_AUTH_FIELD_HMAC_KEY  — HMAC key for auth lookup tokens (required)
    SYNTEK_AUTH_FIELD_KEY       — AES-256-GCM key for auth encryption (required)

For quick local use without PostgreSQL, set SANDBOX_USE_SQLITE=1 to use an
in-memory SQLite database instead (migrations and shell work, data is not
persisted across runs).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "SANDBOX_SECRET_KEY",
    "django-insecure-sandbox-key-not-for-production-use",
)

DEBUG = True

ALLOWED_HOSTS: list[str] = []

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

_use_postgres = os.environ.get("SANDBOX_USE_POSTGRES", "").strip() == "1"

if _use_postgres:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("SANDBOX_DB_NAME", "syntek_sandbox"),
            "USER": os.environ.get("SANDBOX_DB_USER", "postgres"),
            "PASSWORD": os.environ.get("SANDBOX_DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("SANDBOX_DB_HOST", "localhost"),
            "PORT": os.environ.get("SANDBOX_DB_PORT", "5432"),
        }
    }
else:
    # Default: SQLite — no extra dependencies, works immediately after `uv sync`.
    # Set SANDBOX_USE_POSTGRES=1 to use PostgreSQL instead.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(os.path.dirname(__file__), "db.sqlite3"),
        }
    }

# ---------------------------------------------------------------------------
# Installed apps
#
# Add each backend module here as it gains a Django AppConfig.
# Only include modules that are installed in the venv (via `uv sync --group dev`
# or `syntek-dev build --python`).
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django core
    "django.contrib.contenttypes",
    "django.contrib.auth",
    # Syntek backend modules
    "syntek_auth",
    # "syntek_security",   # uncomment when syntek-security has migrations
    # "syntek_permissions", # uncomment when implemented
    # "syntek_tenancy",     # uncomment when implemented
]

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "syntek_auth.User"

# ---------------------------------------------------------------------------
# Core settings
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# auth.E003 requires USERNAME_FIELD to have unique=True at the DB level.
# syntek-auth enforces email uniqueness via the companion email_token column
# (HMAC-SHA256) rather than on the AES-256-GCM ciphertext column, which is
# non-deterministic and cannot carry a meaningful unique constraint.
# The functional guarantee is identical. See ENCRYPTION-GUIDE.md.
SILENCED_SYSTEM_CHECKS = ["auth.E003"]

USE_TZ = True

TIME_ZONE = "Europe/London"

LANGUAGE_CODE = "en-gb"

# ---------------------------------------------------------------------------
# Syntek module settings
#
# All keys read from environment variables — never hardcoded.
# See docs/GUIDES/SANDBOX.md for how to set these locally.
# ---------------------------------------------------------------------------

SYNTEK_AUTH = {
    # Required for encrypted field lookup tokens (HMAC-SHA256).
    # Minimum 32 bytes.  Must differ from FIELD_KEY.
    # The fallback is a dev-only placeholder — NEVER use it outside the sandbox.
    "FIELD_HMAC_KEY": os.environ.get(
        "SYNTEK_AUTH_FIELD_HMAC_KEY",
        "sandbox-dev-hmac-key-do-not-use-in-production-aaaaaaaaaaaaaaa",
    ),

    # Required for field-level AES-256-GCM encryption.
    # Minimum 32 bytes.  Must differ from FIELD_HMAC_KEY.
    # The fallback is a dev-only placeholder — NEVER use it outside the sandbox.
    "FIELD_KEY": os.environ.get(
        "SYNTEK_AUTH_FIELD_KEY",
        "sandbox-dev-field-key-do-not-use-in-production-bbbbbbbbbbbbbb",
    ),

    # Sensible development defaults — override in production consumer settings.
    "MFA_REQUIRED": False,
    "PASSWORD_MIN_LENGTH": 12,
    "PASSWORD_REQUIRE_UPPERCASE": True,
    "PASSWORD_REQUIRE_LOWERCASE": True,
    "PASSWORD_REQUIRE_DIGITS": True,
    "PASSWORD_REQUIRE_SYMBOLS": False,
    "PASSWORD_BREACH_CHECK": False,
    "ACCESS_TOKEN_LIFETIME": 900,
    "REFRESH_TOKEN_LIFETIME": 604800,
    "LOGIN_FIELD": "email",
    "REQUIRE_EMAIL": True,
    "REQUIRE_USERNAME": False,
    "REQUIRE_PHONE": False,
    "MFA_METHODS": ["totp"],
    "LOCKOUT_THRESHOLD": 5,
    "LOCKOUT_DURATION": 900,
    "LOCKOUT_STRATEGY": "fixed",
    "REGISTRATION_ENABLED": True,
    "EMAIL_VERIFICATION_REQUIRED": True,
    "USERNAME_CASE_SENSITIVE": False,
    "PASSWORD_RESET_INVALIDATES_SESSIONS": True,
    "PASSWORD_CHANGE_INVALIDATES_OTHER_SESSIONS": False,
    "PASSWORD_HISTORY": 5,
    "PASSWORD_EXPIRY_DAYS": 0,
    "PASSWORD_MAX_LENGTH": 128,
    "PASSWORD_RESET_TOKEN_TTL": 3600,
    "MFA_BACKUP_CODES_COUNT": 8,
    "USERNAME_MIN_LENGTH": 3,
    "USERNAME_MAX_LENGTH": 50,
    "ROTATE_REFRESH_TOKENS": True,
}
