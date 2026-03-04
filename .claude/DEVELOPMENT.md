# Development Workflow

**Last Updated**: 24/02/2026
**Version**: 1.6.0
**Maintained By**: Development Team
**Language**: British English (en_GB)
**Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [TALL Stack (Laravel + DDEV)](#tall-stack-laravel--ddev)
  - [Django Stack (Docker Compose)](#django-stack-docker-compose)
  - [React Stack (Docker)](#react-stack-docker)
  - [React Native / Expo Stack](#react-native--expo-stack)
  - [Shared Library Stack](#shared-library-stack)
- [Daily Development Workflow](#daily-development-workflow)
- [Environment Files](#environment-files)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Git Workflow](#git-workflow)
- [Deployment](#deployment)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers the development workflow for all stacks supported by Syntek Dev Suite. Follow the section for your project's stack. All workflows share a common structure: containerised environments, environment-specific configuration, and a consistent Git workflow.

---

## Prerequisites

**All stacks require:**
- Git
- A code editor with EditorConfig support (VS Code recommended)
- An SSH key for repository access

**TALL Stack additionally requires:**
- [DDEV](https://ddev.readthedocs.io/) (v1.23+)
- Docker Desktop or Docker Engine

**Django, React, Mobile, Shared Library stacks additionally require:**
- Docker Desktop or Docker Engine (v24+)
- Docker Compose (v2.20+)

---

## Getting Started

### TALL Stack (Laravel + DDEV)

```bash
# 1. Clone the repository
git clone <repository-url> project-name
cd project-name

# 2. Copy environment files
cp .env.dev.example .env.dev
cp .env.test.example .env.test
# Edit .env.dev and fill in required values

# 3. Start DDEV
ddev start

# 4. Install PHP dependencies
ddev composer install

# 5. Generate application key
ddev exec php artisan key:generate

# 6. Run database migrations and seeders
ddev exec php artisan migrate --seed

# 7. Install and build frontend assets
ddev exec npm install
ddev exec npm run dev

# 8. Verify setup
ddev exec php artisan test
```

Access the application at `https://<project-name>.ddev.site`

**Available DDEV commands:**

```bash
ddev start             # Start containers
ddev stop              # Stop containers
ddev ssh               # SSH into the web container
ddev exec <command>    # Run a command inside the web container
ddev logs              # View container logs
ddev describe          # Show project details and URLs
ddev restart           # Restart all containers
ddev poweroff          # Stop all DDEV projects
```

### Django Stack (Docker Compose)

```bash
# 1. Clone the repository
git clone <repository-url> project-name
cd project-name

# 2. Copy environment files
cp .env.dev.example .env.dev
cp .env.test.example .env.test
# Edit .env.dev and fill in required values

# 3. Build and start containers
docker compose up --build -d

# 4. Run database migrations
docker compose exec web python manage.py migrate

# 5. Create a superuser
docker compose exec web python manage.py createsuperuser

# 6. Collect static files (if using whitenoise or similar)
docker compose exec web python manage.py collectstatic --noinput

# 7. Verify setup
docker compose exec web pytest
```

Access the application at `http://localhost:8000`

**Available Docker Compose commands:**

```bash
docker compose up -d                        # Start containers in background
docker compose down                         # Stop and remove containers
docker compose exec web <command>           # Run a command in the web container
docker compose logs -f web                  # Follow web container logs
docker compose ps                           # Show running containers
docker compose build                        # Rebuild images
docker compose restart web                  # Restart the web container
```

### React Stack (Docker)

```bash
# 1. Clone the repository
git clone <repository-url> project-name
cd project-name

# 2. Copy environment files
cp .env.dev.example .env.dev
cp .env.test.example .env.test
# Edit .env.dev and fill in required values

# 3. Install dependencies
docker compose run --rm app npm install

# 4. Start the development server
docker compose up -d

# 5. Verify setup
docker compose exec app npm test
```

Access the application at `http://localhost:3000`

### React Native / Expo Stack

```bash
# 1. Clone the repository
git clone <repository-url> project-name
cd project-name

# 2. Copy environment files
cp .env.dev.example .env.dev
# Edit .env.dev and fill in required values

# 3. Install dependencies
docker compose run --rm app npx expo install

# 4. Start the Expo development server
docker compose up -d

# 5. Scan the QR code with Expo Go on your device
# or run on a connected emulator/simulator
```

### Shared Library Stack

```bash
# 1. Clone the repository
git clone <repository-url> project-name
cd project-name

# 2. Install dependencies
npm install

# 3. Build the library
npm run build

# 4. Run tests
npm test

# 5. Link locally for development in a consuming project
npm link
cd ../consuming-project
npm link @syntek/your-library
```

---

## Daily Development Workflow

1. **Pull latest changes** from the main branch before starting work.
2. **Create a feature branch** following the naming convention: `<story-id>/<short-description>` (e.g., `us042/stripe-payments`).
3. **Start your containers** if not already running.
4. **Write tests first** (TDD) or alongside code. See [TESTING.md](TESTING.md).
5. **Apply coding principles** from [CODING-PRINCIPLES.md](CODING-PRINCIPLES.md).
6. **Run the test suite** before committing.
7. **Commit small, atomic changes** with Conventional Commits messages.
8. **Open a pull request** when the feature is complete.

---

## Environment Files

Each environment requires a separate configuration file. **Never commit real credentials.**

| File | Purpose | Committed? |
|------|---------|-----------|
| `.env.dev.example` | Template for development config | Yes |
| `.env.test.example` | Template for test config | Yes |
| `.env.staging.example` | Template for staging config | Yes |
| `.env.production.example` | Template for production config | Yes |
| `.env.dev` | Actual development config | **No** |
| `.env.test` | Actual test config | **No** |
| `.env.staging` | Actual staging config | **No** |
| `.env.production` | Actual production config | **No** |

**Key environment variables that must differ between environments:**

| Variable | Development | Test | Production |
|----------|------------|------|-----------|
| `APP_ENV` / `DJANGO_SETTINGS_MODULE` | `development` | `testing` | `production` |
| `APP_DEBUG` | `true` | `true` | `false` |
| `DB_DATABASE` | `projectname_dev` | `projectname_test` | `projectname_production` |
| `LOG_LEVEL` | `debug` | `warning` | `error` |
| `MAIL_MAILER` | `log` | `array` | SMTP provider |

---

## Running Tests

### TALL Stack

```bash
# Run all tests
ddev exec php artisan test

# Run with coverage
ddev exec php artisan test --coverage

# Run a specific suite
ddev exec php artisan test --testsuite Unit
ddev exec php artisan test --testsuite Feature

# Run a specific file
ddev exec php artisan test tests/Unit/Services/PaymentServiceTest.php

# Run matching a pattern
ddev exec php artisan test --filter "payment"

# Run browser tests (Dusk)
ddev exec php artisan dusk
```

### Django Stack

```bash
# Run all tests
docker compose exec web pytest

# Run with coverage
docker compose exec web pytest --cov=apps --cov-report=html

# Run a specific app
docker compose exec web pytest apps/payments/

# Run matching a pattern
docker compose exec web pytest -k "payment"

# Run a specific test function
docker compose exec web pytest apps/payments/tests/test_services.py::test_charge_creates_invoice
```

### React / Shared Library Stack

```bash
# Run all tests
docker compose exec app npm test
# or: npm test (Shared Library)

# Run in watch mode
docker compose exec app npm test -- --watch

# Run with coverage
docker compose exec app npm test -- --coverage

# Run E2E tests
npx playwright test
npx playwright test --headed  # visible browser
npx playwright test --debug   # step-through mode
```

---

## Code Quality

Run linting and formatting checks before committing:

### TALL Stack

```bash
# PHP code style (Laravel Pint)
ddev exec ./vendor/bin/pint

# Static analysis (PHPStan / Larastan)
ddev exec ./vendor/bin/phpstan analyse

# Check code style without fixing
ddev exec ./vendor/bin/pint --test
```

### Django Stack

```bash
# Format code (Black)
docker compose exec web black .

# Sort imports (isort)
docker compose exec web isort .

# Lint (Ruff or Flake8)
docker compose exec web ruff check .

# Type checking (mypy)
docker compose exec web mypy apps/
```

### React / TypeScript Stack

```bash
# Lint (ESLint)
docker compose exec app npm run lint

# Format (Prettier)
docker compose exec app npm run format

# Type checking (TypeScript compiler)
docker compose exec app npm run typecheck

# All quality checks
docker compose exec app npm run quality
```

---

## Git Workflow

**Safety Protocol — never do these without explicit instruction:**
- Force push to `main` or `staging`
- Run `git reset --hard` with staged or committed changes
- Use `--no-verify` to skip hooks
- Amend commits that have been pushed

### Branch Naming

```
<story-id>/<short-description>

Examples:
  us042/stripe-payments
  us018/user-profile-page
  fix/cart-total-rounding
  chore/upgrade-laravel-11
```

### Commit Messages (Conventional Commits)

```
<type>(<scope>): <subject>

Types: feat, fix, refactor, test, docs, chore, perf, style

Examples:
  feat(payments): add Stripe payment gateway integration
  fix(cart): correct rounding error in total calculation
  refactor(auth): extract token validation to dedicated service
  test(payments): add integration tests for payment controller
  docs(api): document payment endpoint request/response shapes
  chore(deps): upgrade Laravel to 11.x
```

**Rules:**
- Subject line under 72 characters
- Imperative mood: "Add feature" not "Added feature"
- Body explains why, not what (the diff shows what)
- Reference the story ID in the body where applicable

### Pull Requests

Every PR must include:
1. A clear title summarising the change
2. A description explaining what changed and why
3. A reference to the story ID (e.g., `Closes US-042`)
4. A testing section describing how to verify the change
5. Passing CI (tests, linting, type checking)

### Creating a Commit

```bash
# Stage specific files (prefer explicit over git add -A)
git add src/services/payment.ts tests/services/payment.test.ts

# Create the commit
git commit -m "$(cat <<'EOF'
feat(payments): add Stripe payment gateway integration

Implements card payment processing via Stripe Elements.
Includes webhook handling for async payment confirmation.

Closes US-042

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"

# Verify the commit
git status
git log --oneline -5
```

---

## Deployment

### Environments

| Environment | Branch | Purpose | Access |
|-------------|--------|---------|--------|
| Development | feature branches | Local development | Developer only |
| Staging | `staging` | Pre-production testing | Team only |
| Production | `main` | Live system | Public |

### TALL Stack

```bash
# Deploy to staging (after PR merge to staging branch)
# CI/CD handles deployment automatically

# Manual deployment (emergency only)
ssh deploy@staging-server
cd /var/www/project
git pull origin staging
php artisan migrate --force
php artisan config:cache
php artisan route:cache
php artisan view:cache
npm run build
php artisan queue:restart
```

### Django Stack

```bash
# Deploy to staging (after PR merge)
# CI/CD runs: docker compose pull && docker compose up -d && python manage.py migrate

# Manual deployment (emergency only)
ssh deploy@staging-server
cd /var/www/project
docker compose pull
docker compose exec web python manage.py migrate --noinput
docker compose up -d
```

### React / Next.js Stack

```bash
# Build production bundle
npm run build

# The build output in .next/ or dist/ is deployed via CI/CD
# or served via Docker in production
```

---

## Common Tasks

### Add a New Database Migration

**TALL Stack:**
```bash
ddev exec php artisan make:migration add_status_to_orders_table
ddev exec php artisan migrate
# Rollback:
ddev exec php artisan migrate:rollback
```

**Django Stack:**
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
# Rollback:
docker compose exec web python manage.py migrate app_name 0001
```

### Add a New Package / Dependency

**TALL Stack:**
```bash
# Check security and licence before adding
ddev exec composer require vendor/package
ddev exec composer audit
```

**Django Stack:**
```bash
# Add to requirements.txt with pinned version, then:
docker compose exec web pip install -r requirements.txt
pip-audit  # check for vulnerabilities
```

**TypeScript Stack:**
```bash
# Check security and licence before adding
docker compose exec app npm install package-name
npm audit
```

### Reset the Development Database

**TALL Stack:**
```bash
ddev exec php artisan migrate:fresh --seed
```

**Django Stack:**
```bash
docker compose exec web python manage.py flush --noinput
docker compose exec web python manage.py migrate
docker compose exec web python manage.py loaddata fixtures/dev_data.json
```

---

## Troubleshooting

### Containers Won't Start

```bash
# TALL Stack
ddev restart
ddev logs

# Docker Compose stacks
docker compose down && docker compose up --build -d
docker compose logs
```

### Database Connection Errors

- Verify the correct `.env.*` file is loaded for the current environment
- Confirm the database container is running: `docker compose ps`
- Check database credentials match the container's environment variables
- For DDEV: run `ddev describe` to confirm the database hostname and port

### Tests Failing with Database Errors

- Ensure the test database exists and has run migrations
- Verify `DB_DATABASE` in `.env.test` points to the test database (not development)
- TALL Stack: confirm `RefreshDatabase` or `DatabaseTransactions` trait is used
- Django Stack: ensure `@pytest.mark.django_db` is applied to tests that need the database

### Port Conflicts

If a container fails to start because a port is already in use:

```bash
# Find what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or adjust the port in docker-compose.yml
```

### Slow Test Runs

- Run only the test suite you are actively working on rather than the full suite
- Check for missing database indexes causing slow queries in tests
- Ensure tests are using in-memory or transaction-rolled-back test databases, not creating/dropping the database on every run

### Checking Logs

```bash
# TALL Stack
ddev logs
ddev exec tail -f storage/logs/laravel.log

# Django Stack
docker compose logs -f web

# React Stack
docker compose logs -f app

# Application logs via plugin tool
python3 .claude/plugins/log-tool.py find
python3 .claude/plugins/log-tool.py errors
```
