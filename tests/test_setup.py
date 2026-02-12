"""
Basic test to verify pytest-django setup is working.

This test file can be used as a template for integration tests across modules.
"""

import pytest
from django.conf import settings


def test_django_settings_configured():
    """Verify Django settings are properly configured."""
    assert settings.configured
    assert settings.SECRET_KEY == "test-secret-key-for-syntek-modules-not-for-production-use"
    # pytest-django may override DEBUG, so just check it's set
    assert hasattr(settings, "DEBUG")


def test_django_apps_loaded():
    """Verify Django apps are loaded."""
    from django.apps import apps

    # Check core Django apps are loaded
    assert apps.is_installed("django.contrib.contenttypes")
    assert apps.is_installed("django.contrib.auth")
    assert apps.is_installed("django.contrib.sessions")


@pytest.mark.django_db
def test_database_connection():
    """Verify database connection works (in-memory SQLite)."""
    from django.contrib.auth.models import User

    # Should be able to interact with the database
    user_count = User.objects.count()
    assert user_count >= 0  # Initially 0, but test passes


def test_time_zone_settings():
    """Verify internationalisation settings."""
    assert settings.TIME_ZONE == "UTC"
    assert settings.USE_TZ is True
    assert settings.LANGUAGE_CODE == "en-gb"
