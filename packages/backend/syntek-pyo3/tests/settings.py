"""Minimal Django settings for syntek-pyo3 EncryptedField tests.

No database is exercised — these tests validate field-level behaviour only.
"""

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
