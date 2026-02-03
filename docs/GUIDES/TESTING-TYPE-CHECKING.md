# Testing & Type Checking Guide

## Overview

This project uses modern tooling for testing and type checking across all languages.

---

## Python Testing with pytest

### Test-Driven Development (TDD)

Standard pytest tests for TDD:

```python
# tests/test_authentication.py
import pytest
from backend.authentication.models import User

def test_user_creation():
    """Test user can be created with valid credentials."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='SecurePass123!'
    )
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.check_password('SecurePass123!')

def test_user_authentication():
    """Test user can authenticate with correct credentials."""
    user = User.objects.create_user(
        username='testuser',
        password='SecurePass123!'
    )
    assert user.is_authenticated
```

### Behavior-Driven Development (BDD)

Using pytest-bdd for Gherkin-style scenarios:

**Feature file:** `tests/features/authentication.feature`

```gherkin
Feature: User Authentication
  As a user
  I want to log in to the system
  So that I can access protected resources

  Scenario: Successful login with valid credentials
    Given I am a registered user with username "testuser"
    When I log in with username "testuser" and password "SecurePass123!"
    Then I should be authenticated
    And I should see the dashboard

  Scenario: Failed login with invalid credentials
    Given I am a registered user with username "testuser"
    When I log in with username "testuser" and password "WrongPassword"
    Then I should not be authenticated
    And I should see an error message "Invalid credentials"
```

**Step definitions:** `tests/step_defs/test_authentication_steps.py`

```python
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from django.contrib.auth import authenticate
from backend.authentication.models import User

scenarios('../features/authentication.feature')

@given(parsers.parse('I am a registered user with username "{username}"'))
def registered_user(username, db):
    return User.objects.create_user(
        username=username,
        password='SecurePass123!'
    )

@when(parsers.parse('I log in with username "{username}" and password "{password}"'))
def login_attempt(username, password, context):
    context['user'] = authenticate(username=username, password=password)

@then('I should be authenticated')
def check_authenticated(context):
    assert context['user'] is not None
    assert context['user'].is_authenticated

@then('I should not be authenticated')
def check_not_authenticated(context):
    assert context['user'] is None

@then(parsers.parse('I should see an error message "{message}"'))
def check_error_message(message, context):
    # Check error message in response
    pass
```

### Running Tests

```bash
# Run all tests
syntek test
# Or: uv run pytest

# Run specific test file
uv run pytest tests/test_authentication.py

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run only BDD scenarios
uv run pytest tests/features/

# Run in watch mode
uv run pytest --watch

# Run with verbose output
uv run pytest -v

# Run specific test by name
uv run pytest -k "test_user_creation"
```

### pytest Configuration

**`pytest.ini`** (create in repository root):

```ini
[pytest]
DJANGO_SETTINGS_MODULE = backend.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --reuse-db
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    bdd: marks tests as BDD scenarios
```

---

## Python Type Checking with pyright

### Why pyright?

- ⚡ **Faster** than mypy (written in TypeScript/Node.js)
- 🎯 **Better inference** for complex type scenarios
- 🔧 **Better IDE integration** (powers VS Code Pylance)
- 📊 **More helpful error messages**
- 🚀 **Modern and actively developed**

### Configuration

**`pyrightconfig.json`** (in repository root):

```json
{
  "include": ["backend/**/*.py", "tests/**/*.py"],
  "exclude": ["**/__pycache__", "**/migrations"],
  "typeCheckingMode": "basic",
  "pythonVersion": "3.14",
  "reportMissingImports": true,
  "reportUnusedImport": true,
  "reportUnusedVariable": true
}
```

### Running Type Checks

```bash
# Run pyright on all Python code
pnpm typecheck:python
# Or: pyright

# Run pyright on specific file
pyright backend/authentication/views.py

# Run with verbose output
pyright --verbose

# Watch mode (VS Code)
# Install Pylance extension - runs pyright automatically
```

### Type Hints Example

```python
from typing import Optional
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User

def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve a user by email address.

    Args:
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None

def login_view(request: HttpRequest) -> HttpResponse:
    """Handle user login."""
    username: str = request.POST.get('username', '')
    password: str = request.POST.get('password', '')

    user: Optional[User] = authenticate(
        request,
        username=username,
        password=password
    )

    if user is not None:
        login(request, user)
        return HttpResponse("Login successful")
    else:
        return HttpResponse("Invalid credentials", status=401)
```

---

## TypeScript Type Checking

For TypeScript/JavaScript code in web and mobile:

```bash
# Check all TypeScript
syntek format --check

# Or run directly
pnpm typecheck
```

---

## CI/CD Integration

### GitHub Actions

Tests and type checks run automatically on:

- Push to main/develop
- Pull requests

**`.github/workflows/test.yml`** includes:

```yaml
- name: Run Python tests
  run: uv run pytest --cov

- name: Type check Python
  run: pnpm typecheck:python

- name: Type check TypeScript
  run: pnpm typecheck
```

---

## Development Workflow

### 1. Write Test First (TDD)

```python
# tests/test_new_feature.py
def test_new_feature():
    # Write test before implementation
    result = my_new_feature()
    assert result == expected_output
```

### 2. Run Test (Should Fail)

```bash
uv run pytest tests/test_new_feature.py
# ❌ FAIL - function doesn't exist yet
```

### 3. Implement Feature

```python
# backend/my_module/views.py
def my_new_feature() -> str:
    return expected_output
```

### 4. Run Test (Should Pass)

```bash
uv run pytest tests/test_new_feature.py
# ✅ PASS
```

### 5. Type Check

```bash
pnpm typecheck:python
# ✅ No type errors
```

### 6. Commit

```bash
git add .
git commit -m "feat: add new feature with tests"
# Pre-commit hooks run automatically:
# - Ruff linting
# - Ruff formatting
# - Type checking (if configured in hooks)
# - Secret scanning
```

---

## Tools Reference

| Tool              | Purpose              | Command                         |
| ----------------- | -------------------- | ------------------------------- |
| **pytest**        | Unit testing (TDD)   | `uv run pytest`                 |
| **pytest-bdd**    | BDD scenarios        | `uv run pytest tests/features/` |
| **pytest-cov**    | Coverage reporting   | `uv run pytest --cov`           |
| **pytest-django** | Django integration   | Auto-configured                 |
| **pyright**       | Type checking        | `pnpm typecheck:python`         |
| **ruff**          | Linting + formatting | `syntek lint --fix`             |

---

## Best Practices

1. ✅ **Write tests first** (TDD approach)
2. ✅ **Use type hints** for all function signatures
3. ✅ **Run tests before committing** (`syntek test`)
4. ✅ **Check types regularly** (`pnpm typecheck:python`)
5. ✅ **Aim for >80% code coverage**
6. ✅ **Use BDD for user-facing features** (pytest-bdd)
7. ✅ **Mock external dependencies** in tests
8. ✅ **Keep tests fast** (<1s per test)

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-bdd documentation](https://pytest-bdd.readthedocs.io/)
- [pyright documentation](https://microsoft.github.io/pyright/)
- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
