# Testing Guide — syntek-modules

**Last Updated**: 06/03/2026\
**Version**: 0.1.0\
**Language**: British English (en_GB)\
**Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [Testing Matrix](#testing-matrix)
- [Running Tests](#running-tests)
- [Python / Django](#python--django)
- [TypeScript / React (Web)](#typescript--react-web)
- [React Native / Mobile](#react-native--mobile)
- [Rust Crates](#rust-crates)
- [GraphQL](#graphql)
- [Database Isolation](#database-isolation)
- [Test Data and Factories](#test-data-and-factories)
- [Rules and Principles](#rules-and-principles)

---

## Overview

This repo uses different testing frameworks per layer. All layers follow
**Arrange–Act–Assert** and the testing pyramid: many unit, some integration, few E2E.

---

## Testing Matrix

| Layer | Unit / Integration | E2E / Browser | Framework |
| ----- | ------------------ | ------------- | --------- |
| Python / Django | pytest + factory\_boy + hypothesis | — | pytest-django, testcontainers-python |
| GraphQL (Python) | pytest | — | pytest-django + strawberry test client |
| Web (React/TS) | Vitest + RTL + MSW | Playwright | vitest, @testing-library/react, msw |
| GraphQL (TS resolvers) | Vitest + MSW | — | vitest, msw |
| Mobile (RN) | Jest + RNTL | Maestro | jest, @testing-library/react-native |
| Rust | cargo test | — | built-in + proptest |
| Postgres | pytest transactional fixtures | — | testcontainers-python |

---

## Running Tests

### Full suite (all layers)

```bash
syntek-dev test
```

### Per layer

```bash
# Python
pytest packages/backend/syntek-auth/tests/

# TypeScript (all packages via Turborepo)
pnpm test

# Single package
pnpm --filter @syntek/ui-auth test

# Rust
cargo test --all

# Markdown linting
pnpm lint:md
```

---

## Python / Django

**Tools:** pytest-django, factory\_boy, pytest-cov, testcontainers-python

Each backend module has its own `tests/` directory and a minimal `tests/settings.py`
for Django configuration during testing. There is no project-level `manage.py` — tests
run via pytest directly.

```bash
# Run with coverage
pytest packages/backend/syntek-auth/ --cov=syntek_auth --cov-report=html

# Run only unit tests
pytest packages/backend/syntek-auth/ -m unit

# Run only integration tests (spins up Postgres via testcontainers)
pytest packages/backend/syntek-auth/ -m integration
```

### Module test settings

Each backend module provides `tests/settings.py`:

```python
# packages/backend/syntek-auth/tests/settings.py
SECRET_KEY = "test-secret-key"  # noqa: S105
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "syntek_auth",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "syntek_test",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

### Postgres via testcontainers

Use `testcontainers-python` for integration tests that need a real PostgreSQL 18.3
instance — no external database setup required:

```python
# packages/backend/syntek-auth/tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:18.3") as pg:
        yield pg
```

### factory\_boy example

```python
# packages/backend/syntek-auth/tests/factories.py
import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "secret-password-123")
    is_active = True
```

---

## TypeScript / React (Web)

**Tools:** Vitest, React Testing Library, MSW, Playwright, Cypress

Each `packages/web/*` package uses Vitest for unit and integration tests, and
Playwright or Cypress for E2E tests. Tests live alongside source files.

```bash
# Unit + integration (watch mode)
pnpm --filter @syntek/ui test --watch

# Coverage
pnpm --filter @syntek/ui-auth test --coverage

# E2E (Playwright)
pnpm --filter @syntek/ui-auth test:e2e
```

### Vitest component test example

```typescript
// packages/web/ui-auth/src/LoginForm.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { LoginForm } from "./LoginForm";

describe("LoginForm", () => {
  it("calls onSubmit with email and password when form is submitted", async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "secret123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      email: "user@example.com",
      password: "secret123",
    });
  });
});
```

### MSW for GraphQL mocking

```typescript
// packages/web/ui-auth/tests/msw/handlers.ts
import { graphql, HttpResponse } from "msw";

export const handlers = [
  graphql.mutation("Login", () => {
    return HttpResponse.json({
      data: { login: { token: "test-token", user: { id: "1" } } },
    });
  }),
];
```

---

## React Native / Mobile

**Tools:** Jest, React Native Testing Library (RNTL), Maestro

```bash
# Unit + integration
pnpm --filter @syntek/mobile-auth test

# Watch
pnpm --filter @syntek/mobile-auth test --watch

# Maestro E2E (requires device/emulator)
maestro test mobile/mobile-auth/.maestro/
```

### RNTL component test example

```typescript
// mobile/mobile-auth/src/BiometricPrompt.test.tsx
import { render, fireEvent } from "@testing-library/react-native";
import { describe, it, expect, vi } from "vitest";

import { BiometricPrompt } from "./BiometricPrompt";

describe("BiometricPrompt", () => {
  it("calls onAuthenticate when the prompt button is pressed", () => {
    const onAuthenticate = vi.fn();
    const { getByText } = render(<BiometricPrompt onAuthenticate={onAuthenticate} />);

    fireEvent.press(getByText("Use Face ID"));

    expect(onAuthenticate).toHaveBeenCalledOnce();
  });
});
```

---

## Rust Crates

**Tools:** cargo test (built-in), proptest for property-based testing

```bash
# Run all tests
cargo test --all

# Run tests for a specific crate
cargo test -p syntek-crypto

# Run with output
cargo test --all -- --nocapture
```

### Cryptographic test requirements

Every cryptographic function must have:

1. A round-trip test (encrypt → decrypt returns original plaintext)
2. A test confirming different inputs produce different ciphertexts
3. A test confirming tampered ciphertext fails authentication (GCM tag failure)
4. A test confirming memory is zeroised after use (where possible)

---

## GraphQL

### Python (Strawberry) — use pytest

```python
# packages/backend/syntek-auth/tests/test_schema.py
import pytest
from strawberry.test import Client

from syntek_auth.schema import schema


@pytest.mark.django_db
def test_login_mutation_returns_token(user_factory):
    user = user_factory(email="test@example.com")
    client = Client(schema)

    result = client.execute(
        """
        mutation Login($email: String!, $password: String!) {
          login(email: $email, password: $password) {
            token
          }
        }
        """,
        variables={"email": "test@example.com", "password": "secret-password-123"},
    )

    assert result.errors is None
    assert result.data["login"]["token"] is not None
```

### TypeScript resolvers — use Vitest with direct unit tests + MSW

Direct resolver unit tests do not need a network:

```typescript
// packages/web/api-client/src/resolvers/auth.test.ts
import { describe, it, expect, vi } from "vitest";
import { loginResolver } from "./auth";

describe("loginResolver", () => {
  it("returns user and token on valid credentials", async () => {
    const mockContext = { dataSources: { authApi: { login: vi.fn().mockResolvedValue({ token: "tok_1" }) } } };
    const result = await loginResolver(null, { email: "a@b.com", password: "pw" }, mockContext);
    expect(result.token).toBe("tok_1");
  });
});
```

Use MSW to mock the GraphQL endpoint in component-level tests.

---

## Database Isolation

- **Python integration tests:** use `@pytest.mark.django_db` with transaction rollback
  (default in pytest-django). Each test starts from a clean state.
- **Testcontainers:** spin up an ephemeral PostgreSQL 18.3 container per session for
  integration tests. Never point tests at the dev database.
- **TypeScript:** mock the data layer via MSW or `vi.mock()`. No real DB in unit tests.

---

## Test Data and Factories

- **Python:** use `factory_boy` (`DjangoModelFactory`) for all model fixtures.
  Never build model instances inline across tests.
- **TypeScript:** use plain builder functions in `tests/helpers/builders.ts`.
- **Rust:** use `Default` trait and explicit construction. Use `proptest` for
  property-based tests on cryptographic functions.

---

## Property-Based Testing with Hypothesis

Use `hypothesis` for any function that must hold across a wide range of inputs —
especially cryptographic functions, validators, and data transformations.

Install: `uv pip install hypothesis` (included in `install.sh`).

```python
# packages/backend/syntek-crypto-bridge/tests/test_crypto.py
from hypothesis import given, settings
from hypothesis import strategies as st

from syntek_crypto_bridge import encrypt_field, decrypt_field


@given(plaintext=st.text(min_size=1, max_size=500))
@settings(max_examples=200)
def test_encrypt_decrypt_round_trip(plaintext: str) -> None:
    """AES-256-GCM round-trip: decrypt(encrypt(x)) == x for any input."""
    key = b"a" * 32
    ciphertext = encrypt_field(plaintext, key)
    assert decrypt_field(ciphertext, key) == plaintext


@given(
    value=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)),
    length=st.integers(min_value=1, max_value=64),
)
def test_password_validator_never_raises(value: object, length: int) -> None:
    """Password validator must not raise; it returns True or False."""
    from syntek_auth.validators import meets_minimum_length
    result = meets_minimum_length(str(value), min_length=length)
    assert isinstance(result, bool)
```

**Where to use hypothesis:**

- Cryptographic functions (`syntek-crypto` / `syntek-pyo3`) — round-trip, tamper detection
- Input validators — must never raise; must return a bool or raise a specific exception
- Data transformation functions — idempotency, associativity
- HMAC / signature functions — different inputs produce different outputs

**Where NOT to use hypothesis:**

- Tests that require database state (use factory\_boy + pytest fixtures instead)
- E2E or integration tests (too slow for property-based iteration)

---

## Per-Package Testing Files

Every package in this repo carries two testing files:

### `TEST-STATUS.md`

Tracks the automated test suite: what tests exist, what each one verifies, and
whether it currently passes. Updated after each test run by the contributor or CI.

Location:
- `packages/backend/syntek-{name}/TEST-STATUS.md`
- `packages/web/{name}/TEST-STATUS.md`
- `mobile/{name}/TEST-STATUS.md`

Template: `docs/GUIDES/templates/TEST-STATUS.md`

### `docs/MANUAL-TESTING.md`

Step-by-step guide for a human tester to verify the package works correctly.
Covers happy paths, error paths, security edge cases, and a regression checklist.

Location:
- `packages/backend/syntek-{name}/docs/MANUAL-TESTING.md`
- `packages/web/{name}/docs/MANUAL-TESTING.md`
- `mobile/{name}/docs/MANUAL-TESTING.md`

Template: `docs/GUIDES/templates/MANUAL-TESTING.md`

**Convention:** Both files are created when a new module is scaffolded (`/add-module`).
`TEST-STATUS.md` is kept up to date as tests are written. `MANUAL-TESTING.md` is
written alongside the first implementation PR and updated whenever behaviour changes.

---

## Rules and Principles

1. Every new public function has at least one unit test.
2. Every GraphQL mutation/query has an integration test covering the happy path,
   an auth failure, and an invalid input case.
3. Tests are deterministic — no real time, random values, or live network calls.
4. Tests are independent — each test sets up its own state.
5. Follow Arrange–Act–Assert in every test.
6. Test behaviour, not implementation.
7. Unit tests complete in under 100ms each.
8. Security-critical paths (auth, encryption, RBAC) have negative tests that verify
   rejection of invalid or malicious input.
9. Test code is held to the same standard as production code.
