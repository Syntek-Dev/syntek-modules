# Development Environment

## Module Development

This repository contains **modules** not a deployable application. Development focuses on:

1. Creating new modules
2. Testing modules independently
3. Testing module integrations
4. Documenting module usage

## Virtual Environments

### Python (Backend Modules)

```bash
# Install uv (much faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate
source .venv/bin/activate

# Install root project with dev dependencies
uv pip install -e ".[dev]"

# Or install specific module in development mode
uv pip install -e backend/authentication

# Or install all modules
uv pip install -e backend/authentication -e backend/profiles -e backend/media
```

### Node.js (Web/Mobile Modules)

```bash
# Install all workspace dependencies
npm install

# Build all modules
npm run build --workspaces

# Build specific module
npm run build --workspace=@syntek/ui-auth

# Link for local development
cd web/packages/ui-auth
npm link
```

### Rust (Security Modules)

```bash
# Build
cd rust/encryption
cargo build

# Run tests
cargo test

# Build Python bindings
cd rust/encryption
maturin develop
```

## Running Tests

### Backend Tests

```bash
# Activate venv
source venv/bin/activate

# Test specific module
cd backend/authentication
python manage.py test

# Test all modules
python manage.py test backend
```

### Web/Mobile Tests

```bash
# Test all workspaces
npm test --workspaces

# Test specific module
npm test --workspace=@syntek/ui-auth
```

### Rust Tests

```bash
cd rust/encryption
cargo test
```

### Integration Tests

```bash
# Run integration test suite
pytest tests/integration
```

## Docker (Optional)

Optional Docker setup for testing module integrations:

```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up backend

# Run tests in containers
docker-compose run backend pytest
docker-compose run web npm test
```

## Working on a Module

1. Navigate to module directory
2. Activate appropriate environment (venv/npm)
3. Make changes
4. Run tests
5. Update module documentation
6. Commit changes

## Example Workflow

### Creating a New Backend Module

```bash
# 1. Create module structure
mkdir -p backend/subscriptions/{models,views,tests,migrations}

# 2. Create pyproject.toml
cat > backend/subscriptions/pyproject.toml << 'EOF'
[project]
name = "syntek-subscriptions"
version = "0.1.0"
description = "Django subscription module with recurring billing"
requires-python = ">=3.14"
dependencies = [
    "django>=6.0.2",
    "strawberry-graphql>=0.291.0",
    "syntek-authentication>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["syntek_subscriptions"]
EOF

# 3. Create __init__.py
cat > backend/subscriptions/__init__.py << 'EOF'
default_app_config = 'syntek_subscriptions.apps.SubscriptionsConfig'
__version__ = '0.1.0'
EOF

# 4. Create apps.py
cat > backend/subscriptions/apps.py << 'EOF'
from django.apps import AppConfig

class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'syntek_subscriptions'
    verbose_name = 'Syntek Subscriptions'
EOF

# 5. Install in development mode
uv pip install -e backend/subscriptions

# 6. Write tests (TDD)
# 7. Implement module
# 8. Document in README
```

### Testing Module in Example App

```bash
# 1. Install module in example
cd examples/django-app
source .venv/bin/activate
uv pip install -e ../../backend/subscriptions

# 2. Configure Django settings
# Add to settings/base.py:
cat >> config/settings/base.py << 'EOF'

# Syntek Modules
INSTALLED_APPS += [
    'syntek_subscriptions',
]

SYNTEK_SUBSCRIPTIONS = {
    'TRIAL_PERIOD_DAYS': 14,
    'ALLOW_DOWNGRADES': True,
    'PRORATE_UPGRADES': True,
    'PAYMENT_GRACE_PERIOD': 3,
}
EOF

# 3. Run migrations
python manage.py migrate

# 4. Test functionality
python manage.py runserver
```

## Hot Reload

### Django

```bash
python manage.py runserver
# Changes to modules hot-reload automatically
```

### Next.js

```bash
npm run dev --workspace=@syntek/ui-auth
# Changes hot-reload automatically
```

### React Native

```bash
npm start --workspace=@syntek/mobile-auth
# Use Expo Go for hot reload
```

## Useful Commands

```bash
# List all modules
ls -la backend/ web/packages/ mobile/packages/

# Check module versions
.claude/plugins/project-tool.py info

# Run all tests
./scripts/test-all.sh

# Build all modules
./scripts/build-all.sh

# Format code
./scripts/format.sh
```
