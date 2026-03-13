# Sandbox — Django Management Commands

The `sandbox/` directory is a minimal internal Django project used exclusively for running
management commands during development:

- `makemigrations` — generate migration files after model changes
- `migrate` — apply migrations to the local development database
- `shell` — interactive Django shell
- `dbshell` — raw `psql` shell
- `seed_dev` — populate the DB with development fixture data

It is **not a deployable application**. No URLs, no views, no WSGI entry point.

---

## First-Time Setup

### 1. Activate the venv and install Python packages

```bash
source .venv/bin/activate
uv sync --group dev
```

### 2. Set required environment variables

The two `FIELD_*` keys are the minimum required to start Django (if `syntek_auth` is in
`INSTALLED_APPS` and `AppConfig.ready()` validates them). Set them in your shell or add them to a
local `.env` file.

```bash
# Generate two separate cryptographically random 32-byte keys
export SYNTEK_AUTH_FIELD_HMAC_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export SYNTEK_AUTH_FIELD_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

> These must be **different** values. Do not reuse the same key for both encryption and HMAC.

Store them in your shell profile (`~/.zshrc` or `~/.bashrc`) so they persist across sessions.

### 3. Choose a database backend

**Default — SQLite (no extra setup required)**

SQLite is the default. No environment variable needed. Data is stored in `sandbox/db.sqlite3`
(gitignored). This is sufficient for `makemigrations`, `migrate`, `shell`, and schema inspection.

```bash
# Nothing to set — SQLite is used automatically
python sandbox/manage.py migrate
```

**Option — PostgreSQL (matches the production stack)**

Set `SANDBOX_USE_POSTGRES=1` and ensure a local PostgreSQL 18 instance is running:

```bash
createdb syntek_sandbox
export SANDBOX_USE_POSTGRES=1
```

PostgreSQL environment variables (defaults shown — override as needed):

| Variable              | Default          |
| --------------------- | ---------------- |
| `SANDBOX_DB_NAME`     | `syntek_sandbox` |
| `SANDBOX_DB_USER`     | `postgres`       |
| `SANDBOX_DB_PASSWORD` | `postgres`       |
| `SANDBOX_DB_HOST`     | `localhost`      |
| `SANDBOX_DB_PORT`     | `5432`           |

PostgreSQL requires `psycopg` or `psycopg2` to be installed:

```bash
uv add --dev psycopg[binary]
```

---

## Running Commands

### Via syntek-dev CLI (preferred)

```bash
# Generate migrations for a module
syntek-dev db makemigrations syntek_auth

# Apply all pending migrations
syntek-dev db migrate

# Apply migrations for a specific module
syntek-dev db migrate syntek_auth

# Roll back all migrations for a module
syntek-dev db rollback syntek_auth

# Roll back to a specific migration
syntek-dev db rollback syntek_auth --to 0002

# Check migration status
syntek-dev db status

# Open the Django shell
syntek-dev db shell

# Open a raw psql shell
syntek-dev db shell --raw

# Seed with development data
syntek-dev db seed
```

### Directly via manage.py

```bash
python sandbox/manage.py makemigrations syntek_auth
python sandbox/manage.py migrate
python sandbox/manage.py migrate syntek_auth 0002
python sandbox/manage.py showmigrations syntek_auth
python sandbox/manage.py shell
python sandbox/manage.py dbshell
```

---

## Adding a New Module to the Sandbox

When a new backend module gets a Django `AppConfig` and migrations, add it to `INSTALLED_APPS` in
`sandbox/settings.py`:

```python
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "syntek_auth",
    "syntek_permissions",  # add here once the package is installed
]
```

Then run:

```bash
uv sync --group dev              # install the new package into the venv
syntek-dev db makemigrations     # generate any pending migrations
syntek-dev db migrate            # apply them
```

---

## Gitignore

The following sandbox artefacts are gitignored:

```text
sandbox/db.sqlite3   # SQLite dev database
sandbox/__pycache__/
```

The `sandbox/` Python source files (`manage.py`, `settings.py`, `__init__.py`) are committed to the
repository.

---

## What the Sandbox Is NOT

- Not a Django project for consumers to copy — consumers create their own `settings.py` with
  `SYNTEK_*` dicts pointing to their own database and keys.
- Not a test runner — tests use `pytest` with in-memory SQLite via each module's own `conftest.py`.
- Not a staging or production environment.
