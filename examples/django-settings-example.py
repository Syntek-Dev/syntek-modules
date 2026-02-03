"""
Example Django settings showing how to configure Syntek modules.

This would typically be in your Django project's settings/base.py file.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "strawberry.django",
    # Syntek Modules
    "syntek_authentication",
    "syntek_profiles",
    "syntek_media",
    "syntek_logging",
    "syntek_notifications",
    "syntek_payments",
    "syntek_subscriptions",
    "syntek_analytics",
    "syntek_reporting",
    # Your apps
    # 'myapp',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# ============================================================================
# SYNTEK MODULE CONFIGURATION
# ============================================================================

# Authentication Module
# ----------------------
SYNTEK_AUTH = {
    # TOTP Configuration
    "TOTP_REQUIRED": False,  # Set to True to require TOTP for all users
    "TOTP_ISSUER_NAME": "My Platform",
    "TOTP_BACKUP_CODES_COUNT": 10,
    # Password Requirements
    "PASSWORD_LENGTH": 12,
    "SPECIAL_CHARS_REQUIRED": True,
    "UPPERCASE_REQUIRED": True,
    "LOWERCASE_REQUIRED": True,
    "NUMBERS_REQUIRED": True,
    "COMMON_PASSWORD_CHECK": True,
    "PASSWORD_HISTORY_COUNT": 5,
    # Login Security
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOCKOUT_DURATION": 300,  # 5 minutes
    "LOCKOUT_INCREMENT": True,
    "LOG_LOGIN_ATTEMPTS": True,
    "NOTIFY_FAILED_LOGINS": True,
    "NOTIFY_NEW_DEVICE_LOGIN": True,
    # JWT Configuration
    "JWT_EXPIRY": 3600,  # 1 hour
    "REFRESH_TOKEN_EXPIRY": 86400,  # 24 hours
    "JWT_ALGORITHM": "HS256",
    "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY"),
    # Session Configuration
    "SESSION_TIMEOUT": 1800,  # 30 minutes inactivity
    "SESSION_ABSOLUTE_TIMEOUT": 43200,  # 12 hours absolute
    "ALLOW_SIMULTANEOUS_SESSIONS": False,
}

# Profiles Module
# ---------------
SYNTEK_PROFILES = {
    "AVATAR_UPLOAD_TO": "avatars/",
    "ALLOWED_AVATAR_EXTENSIONS": ["jpg", "jpeg", "png", "webp"],
    "MAX_AVATAR_SIZE": 5 * 1024 * 1024,  # 5MB
    "REQUIRE_EMAIL_VERIFICATION": True,
    "ALLOW_USERNAME_CHANGE": False,
    "ALLOWED_PROFILE_FIELDS": [
        "first_name",
        "last_name",
        "phone",
        "bio",
        "location",
        "website",
    ],
}

# Media Module (Cloudinary)
# --------------------------
SYNTEK_MEDIA = {
    "CLOUDINARY_CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "CLOUDINARY_API_KEY": os.getenv("CLOUDINARY_API_KEY"),
    "CLOUDINARY_API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100MB
    "ALLOWED_FILE_TYPES": [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "video/mp4",
        "video/webm",
        "application/pdf",
    ],
    "AUTO_FORMAT": True,  # Cloudinary auto-format
    "AUTO_OPTIMIZE": True,  # Cloudinary optimization
}

# Logging Module (GlitchTip)
# ---------------------------
SYNTEK_LOGGING = {
    "GLITCHTIP_DSN": os.getenv("GLITCHTIP_DSN"),
    "GLITCHTIP_ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
    "GLITCHTIP_TRACES_SAMPLE_RATE": 1.0 if DEBUG else 0.1,
    "LOG_LEVEL": "DEBUG" if DEBUG else "INFO",
    "LOG_FILE": "logs/django.log",
    "LOG_MAX_BYTES": 10 * 1024 * 1024,  # 10MB
    "LOG_BACKUP_COUNT": 5,
}

# Notifications Module
# --------------------
SYNTEK_NOTIFICATIONS = {
    # Email
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": os.getenv("EMAIL_HOST"),
    "EMAIL_PORT": int(os.getenv("EMAIL_PORT", "587")),
    "EMAIL_USE_TLS": True,
    "EMAIL_HOST_USER": os.getenv("EMAIL_HOST_USER"),
    "EMAIL_HOST_PASSWORD": os.getenv("EMAIL_HOST_PASSWORD"),
    "DEFAULT_FROM_EMAIL": os.getenv("DEFAULT_FROM_EMAIL"),
    # In-app notifications
    "ENABLE_PUSH_NOTIFICATIONS": True,
    "ENABLE_EMAIL_NOTIFICATIONS": True,
    "ENABLE_SMS_NOTIFICATIONS": False,
    "NOTIFICATION_RETENTION_DAYS": 90,
}

# Payments Module
# ---------------
SYNTEK_PAYMENTS = {
    # Stripe
    "STRIPE_PUBLIC_KEY": os.getenv("STRIPE_PUBLIC_KEY"),
    "STRIPE_SECRET_KEY": os.getenv("STRIPE_SECRET_KEY"),
    "STRIPE_WEBHOOK_SECRET": os.getenv("STRIPE_WEBHOOK_SECRET"),
    # Square (optional)
    "SQUARE_APPLICATION_ID": os.getenv("SQUARE_APPLICATION_ID"),
    "SQUARE_ACCESS_TOKEN": os.getenv("SQUARE_ACCESS_TOKEN"),
    "SQUARE_LOCATION_ID": os.getenv("SQUARE_LOCATION_ID"),
    # Settings
    "DEFAULT_CURRENCY": "USD",
    "CAPTURE_METHOD": "automatic",
    "PAYMENT_METHODS": ["card", "bank_account"],
    "SAVE_PAYMENT_METHODS": True,
}

# Subscriptions Module
# --------------------
SYNTEK_SUBSCRIPTIONS = {
    "TRIAL_PERIOD_DAYS": 14,
    "ALLOW_DOWNGRADES": True,
    "PRORATE_UPGRADES": True,
    "PRORATE_DOWNGRADES": False,
    "PAYMENT_GRACE_PERIOD": 3,  # days
    "CANCEL_AT_PERIOD_END": True,
    "SEND_RENEWAL_REMINDERS": True,
    "RENEWAL_REMINDER_DAYS": [7, 3, 1],
}

# Analytics Module
# ----------------
SYNTEK_ANALYTICS = {
    "TRACK_PAGE_VIEWS": True,
    "TRACK_EVENTS": True,
    "TRACK_USER_PROPERTIES": True,
    "ANONYMIZE_IP": True,
    "RETENTION_DAYS": 365,
}

# Reporting Module
# ----------------
SYNTEK_REPORTING = {
    "EXPORT_FORMATS": ["pdf", "excel", "csv", "json"],
    "MAX_EXPORT_ROWS": 100000,
    "ASYNC_EXPORT_THRESHOLD": 10000,
    "REPORT_RETENTION_DAYS": 30,
}

# ============================================================================
# RUST ENCRYPTION CONFIGURATION
# ============================================================================

SYNTEK_ENCRYPTION = {
    "ENCRYPTION_KEY": os.getenv("RUST_ENCRYPTION_KEY"),
    "ALGORITHM": "ChaCha20-Poly1305",
    "KEY_ROTATION_DAYS": 90,
    # Field-level encryption
    "ENCRYPT_INDIVIDUALLY": [
        "ip_address",
        "credit_card",
        "ssn",
    ],
    # Batch encryption (for performance)
    "ENCRYPT_BATCHED": [
        "user_profile",  # first_name, last_name, phone, email together
        "address",  # street, city, state, zip together
    ],
}

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============================================================================
# GRAPHQL CONFIGURATION
# ============================================================================

STRAWBERRY_DJANGO = {
    "FIELD_DESCRIPTION_FROM_HELP_TEXT": True,
    "TYPE_DESCRIPTION_FROM_MODEL_DOCSTRING": True,
}

GRAPHQL_DEBUG = DEBUG
GRAPHQL_PLAYGROUND = DEBUG
GRAPHQL_INTROSPECTION = DEBUG
