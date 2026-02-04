"""
Minimal Django settings for testing Syntek modules.

This is NOT a production settings file - it's only for:
1. Running pytest-django tests on the modules
2. Type checking with django-stubs/Pyright
3. Development testing when working on the modules

For production usage examples, see: examples/django-settings-example.py
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings (test only - not for production)
SECRET_KEY = "test-secret-key-for-syntek-modules-not-for-production-use"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Minimal installed apps needed for testing
INSTALLED_APPS = [
    # Django core apps (minimal set)
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    # Third-party
    "strawberry.django",
    # Syntek modules - add as needed for testing
    # Uncomment modules as you need to test them:
    # "syntek_authentication",
    # "syntek_jwt",
    # "syntek_sessions",
    # "syntek_mfa",
    # "syntek_profiles",
    # "syntek_media",
    # "syntek_logging",
    # "syntek_notifications",
    # "syntek_payments",
    # "syntek_analytics",
    # "syntek_reporting",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

# No URL routing needed for library testing
ROOT_URLCONF = None

# Use SQLite in-memory for fast testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        # For debugging tests, you can use a file instead:
        # "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

# Internationalization
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (not needed for testing but Django expects this)
STATIC_URL = "/static/"

# Templates configuration (minimal)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Password validation (minimal for tests)
AUTH_PASSWORD_VALIDATORS = []

# ============================================================================
# SYNTEK MODULE CONFIGURATION (for testing)
# ============================================================================
# Add minimal test configurations for your modules here as needed

# Example - Authentication Module (uncomment when testing auth modules):
# SYNTEK_AUTH = {
#     "TOTP_REQUIRED": False,
#     "PASSWORD_LENGTH": 8,  # Relaxed for testing
#     "MAX_LOGIN_ATTEMPTS": 5,
#     "JWT_EXPIRY": 3600,
# }

# Example - Security Core (uncomment when testing security modules):
# SYNTEK_SECURITY_CORE = {
#     "RATE_LIMITING": {"BACKEND": "memory", "DEFAULT_RATE": "1000/hour"},
#     "CSRF": {"TOKEN_ROTATION": False},
# }
