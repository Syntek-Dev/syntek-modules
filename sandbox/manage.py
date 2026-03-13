#!/usr/bin/env python
"""Django management script for the syntek-modules sandbox.

The sandbox is a minimal internal Django project used exclusively for running
management commands (makemigrations, migrate, shell, dbshell, seed_dev, etc.)
against the backend modules during development.

It is NOT a deployable application.  No URLs, no views, no WSGI/ASGI entry
point.  Its sole purpose is to give Django's management commands a project
context so they can discover installed apps and their migrations.

Usage (from the repo root with .venv activated):

    python sandbox/manage.py makemigrations syntek_auth
    python sandbox/manage.py migrate
    python sandbox/manage.py shell

Or via the syntek-dev CLI (preferred):

    syntek-dev db makemigrations syntek_auth
    syntek-dev db migrate
    syntek-dev db shell

See docs/GUIDES/SANDBOX.md for first-time setup instructions.
"""

import os
import sys

# Ensure the repo root is on sys.path so that ``sandbox.settings`` is importable
# regardless of the working directory from which manage.py is invoked.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sandbox.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Could not import Django.  Make sure your .venv is activated:\n"
            "    source .venv/bin/activate\n"
            "Then install Python dependencies:\n"
            "    uv sync --group dev"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
