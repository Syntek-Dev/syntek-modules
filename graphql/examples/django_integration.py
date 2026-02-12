"""Example: Integrating syntek-graphql-auth into a Django project.

This example shows how to set up the GraphQL authentication layer
in your Django project.
"""

import os
from pathlib import Path

from django.urls import path
from strawberry.django.views import GraphQLView
from syntek_graphql_auth.schema import schema

# 1. Install the package
# uv pip install syntek-graphql-auth

# 2. Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "strawberry.django",
    # Syntek modules
    "syntek_authentication",  # Required dependency
    "syntek_audit",  # Required dependency
    "syntek_graphql_auth",  # GraphQL layer
    # Your apps
    "apps.core",
]

# 3. Add middleware in settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # GraphQL authentication middleware
    "syntek_graphql_auth.middleware.GraphQLAuthenticationMiddleware",
]

# 4. Configure JWT settings
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = True  # Set appropriately for your environment

# JWT Configuration
JWT_PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", BASE_DIR / "keys" / "private.pem")
JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", BASE_DIR / "keys" / "public.pem")
JWT_ACCESS_TOKEN_LIFETIME = 900  # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME = 604800  # 7 days
JWT_ALGORITHM = "RS256"

# Session settings
MAX_CONCURRENT_SESSIONS = 5

# TOTP settings
TOTP_ISSUER_NAME = "MyApp"
TOTP_PERIOD = 30
TOTP_DIGITS = 6
TOTP_WINDOW = 1

# CAPTCHA settings (Google reCAPTCHA v3)
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
RECAPTCHA_MIN_SCORE = 0.5

# GraphQL security settings
GRAPHQL_MAX_DEPTH = 10
GRAPHQL_MAX_COMPLEXITY = 1000
GRAPHQL_DISABLE_INTROSPECTION = not DEBUG  # Disable in production

# 5. Add GraphQL URL in urls.py
urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]

# 6. Generate RSA keys for JWT (run once)
# python -c "from apps.core.utils.jwt_keys import generate_keys; generate_keys()"

# 7. Run migrations
# python manage.py migrate

# 8. Test the GraphQL endpoint
# curl -X POST http://localhost:8000/graphql/ \
#   -H "Content-Type: application/json" \
#   -d '{"query": "{ hello }"}'
