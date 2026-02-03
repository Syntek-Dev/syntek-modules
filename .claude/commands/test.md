# Testing Modules

## Test Strategy

### Unit Tests

- Each module has its own test suite
- Tests are located within module directories
- Tests should not depend on other modules

### Integration Tests

- Located in `tests/integration/`
- Test how modules work together
- Use example applications for realistic testing

### End-to-End Tests

- Located in `tests/e2e/`
- Test complete workflows across multiple modules
- Use example applications

## Running Tests

### All Tests

```bash
# Backend
source venv/bin/activate
python manage.py test backend

# Web
npm test --workspaces

# Mobile
npm test --workspace=@syntek/mobile-*

# Rust
cargo test --manifest-path rust/encryption/Cargo.toml

# Integration
pytest tests/integration

# Everything
./scripts/test-all.sh
```

### Single Module

```bash
# Backend module
cd backend/authentication
python -m pytest

# Web module
npm test --workspace=@syntek/ui-auth

# Mobile module
npm test --workspace=@syntek/mobile-profiles

# Rust crate
cd rust/encryption && cargo test
```

### Specific Test File

```bash
# Backend
python -m pytest backend/authentication/tests/test_login.py

# Web/Mobile
npm test --workspace=@syntek/ui-auth -- LoginForm.test.tsx

# Rust
cargo test --test encryption_tests
```

### Coverage

```bash
# Backend
coverage run manage.py test backend
coverage report
coverage html

# Web/Mobile
npm test --workspaces -- --coverage

# Rust
cargo tarpaulin
```

## Test Requirements

### Backend Tests (Django)

- Use Django TestCase or pytest-django
- Mock external services (Cloudinary, GlitchTip)
- Test GraphQL queries/mutations
- Test model validation
- Test permissions

### Web/Mobile Tests (React)

- Use Jest + React Testing Library
- Test component rendering
- Test user interactions
- Test accessibility
- Mock API calls

### Rust Tests

- Use Cargo's built-in testing
- Test encryption/decryption
- Test memory zeroization
- Test PyO3 bindings
- Test error handling

## Integration Testing

### Django + Rust Integration

```python
# tests/integration/test_encryption.py
import pytest
from syntek_encryption import encrypt, decrypt

def test_django_rust_integration():
    """Test Django can use Rust encryption"""
    plaintext = "sensitive data"
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    assert decrypt(encrypted) == plaintext
```

### Web + Backend Integration

```typescript
// tests/integration/auth.test.ts
test("login flow with backend", async () => {
  const response = await graphqlClient.mutate({
    mutation: LOGIN,
    variables: { email: "test@example.com", password: "pass123" },
  });

  expect(response.data.login.token).toBeDefined();
});
```

## Example Application Testing

### Using Django Example

```bash
cd examples/django-app

# Install modules
pip install -e ../../backend/authentication
pip install -e ../../backend/profiles

# Run example tests
python manage.py test

# Manual testing
python manage.py runserver
```

### Using Next.js Example

```bash
cd examples/nextjs-app

# Install modules
npm install

# Run example tests
npm test

# Manual testing
npm run dev
```

## CI/CD Testing

GitHub Actions runs tests on:

- Every commit
- Every PR
- Before releases

```yaml
# .github/workflows/test.yml
name: Test All Modules

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test backend modules
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements-dev.txt
          python manage.py test backend

  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test web modules
        run: |
          npm install
          npm test --workspaces

  rust:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Rust modules
        run: |
          cd rust/encryption
          cargo test
```

## Test Data

### Fixtures

```bash
# Backend fixtures
backend/authentication/fixtures/test_users.json

# Load fixtures
python manage.py loaddata test_users
```

### Factories

```python
# backend/authentication/tests/factories.py
import factory
from authentication.models import User

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker('email')
    username = factory.Faker('username')
```

## Debugging Tests

### Backend

```bash
# Run with debugger
python -m pdb manage.py test backend/authentication

# Print debug output
python manage.py test backend/authentication --debug-mode
```

### Web/Mobile

```bash
# Run in watch mode
npm test --workspace=@syntek/ui-auth -- --watch

# Debug specific test
node --inspect-brk node_modules/.bin/jest LoginForm.test.tsx
```

### Rust

```bash
# Run with backtrace
RUST_BACKTRACE=1 cargo test

# Run specific test
cargo test test_encrypt_decrypt -- --nocapture
```

## Performance Testing

### Backend

```python
# tests/performance/test_encryption_perf.py
import pytest
import time
from syntek_encryption import encrypt

def test_encryption_performance():
    data = "x" * 1000000  # 1MB
    start = time.time()
    encrypted = encrypt(data)
    duration = time.time() - start
    assert duration < 0.1  # Should take < 100ms
```

### Load Testing

```bash
# Using locust
cd tests/load
locust -f locustfile.py
```

## Security Testing

```bash
# Run security checks
bandit -r backend/

# Check dependencies
safety check

# Rust audit
cargo audit
```

## Useful Test Commands

```bash
# Watch mode
npm test -- --watch

# Update snapshots
npm test -- -u

# Run tests matching pattern
pytest -k "test_login"

# Parallel testing
pytest -n auto

# Verbose output
pytest -vv
```
