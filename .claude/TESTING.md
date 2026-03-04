# Testing Guide

**Last Updated**: 24/02/2026
**Version**: 1.6.0
**Maintained By**: Development Team
**Language**: British English (en_GB)
**Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [Stack and Tooling](#stack-and-tooling)
- [Directory Structure](#directory-structure)
- [Naming Conventions](#naming-conventions)
- [The Testing Pyramid](#the-testing-pyramid)
  - [Unit Tests](#1-unit-tests)
  - [Integration Tests](#2-integration-tests)
  - [Feature and End-to-End Tests](#3-feature-and-end-to-end-tests)
  - [API Tests](#4-api-tests)
- [TDD Methodology](#tdd-test-driven-development)
- [Test Data and Factories](#test-data-and-factories)
- [Mocking Patterns](#mocking-patterns)
- [Database Isolation](#database-isolation)
- [Security-Critical Tests](#security-critical-tests)
- [Rules and Principles](#rules-and-principles)

---

## Overview

This guide defines how to write, organise, and run tests across all project stacks. Follow these conventions regardless of which agent writes the tests — consistency makes the test suite trustworthy and maintainable.

---

## Stack and Tooling

### TALL Stack (Laravel + Livewire + Alpine + Tailwind)

| Tool | Purpose | Command |
|------|---------|---------|
| **Pest PHP** | Primary test runner (unit + feature) | `ddev exec php artisan test` |
| **Pest Arch** | Architecture and convention tests | `ddev exec php artisan test --filter arch` |
| **Laravel HTTP tests** | Feature/API endpoint tests | Built into Pest/PHPUnit |
| **Livewire testing** | Livewire component interaction tests | `Livewire::test()` helper |
| **Laravel Dusk** | Browser-based E2E tests | `ddev exec php artisan dusk` |
| **Faker** | Generating realistic test data | Used in factories |

```bash
# Run the full test suite
ddev exec php artisan test

# Run a specific test file
ddev exec php artisan test tests/Unit/Services/PaymentServiceTest.php

# Run tests matching a name pattern
ddev exec php artisan test --filter "payment"

# Run with coverage report
ddev exec php artisan test --coverage
```

### Django Stack (Django + Wagtail + PostgreSQL)

| Tool | Purpose | Command |
|------|---------|---------|
| **pytest-django** | Primary test runner | `docker compose exec web pytest` |
| **factory_boy** | Test data factories | Used in fixtures/conftest.py |
| **pytest-cov** | Coverage reports | `pytest --cov=app` |
| **Django test client** | HTTP request simulation | `client.get("/api/...")` |
| **DRF APIClient** | REST Framework API tests | `APIClient()` |
| **Playwright** | Browser E2E tests | `docker compose exec web pytest --playwright` |

```bash
# Run the full test suite
docker compose exec web pytest

# Run a specific test file
docker compose exec web pytest apps/payments/tests/test_services.py

# Run tests matching a name pattern
docker compose exec web pytest -k "payment"

# Run with coverage report
docker compose exec web pytest --cov=apps --cov-report=html
```

### React Stack (React + Next.js + TypeScript)

| Tool | Purpose | Command |
|------|---------|---------|
| **Vitest** | Primary unit/integration test runner | `docker compose exec app npm test` |
| **React Testing Library** | Component rendering and interaction | Used in component tests |
| **MSW (Mock Service Worker)** | API mocking for integration tests | `server.use(...)` |
| **Playwright** | Browser E2E tests | `npx playwright test` |
| **Storybook** | Visual component testing | `npm run storybook` |

```bash
# Run the full test suite
docker compose exec app npm test

# Run in watch mode
docker compose exec app npm test -- --watch

# Run with coverage
docker compose exec app npm test -- --coverage

# Run E2E tests
npx playwright test
```

### React Native / Expo Stack

| Tool | Purpose | Command |
|------|---------|---------|
| **Jest** | Primary test runner | `docker compose exec app npx jest` |
| **React Native Testing Library** | Component rendering and interaction | Used in component tests |
| **MSW** | API mocking | `server.use(...)` |

```bash
# Run the full test suite
docker compose exec app npx jest

# Run in watch mode
docker compose exec app npx jest --watch

# Run with coverage
docker compose exec app npx jest --coverage
```

### Shared Library (TypeScript / NPM)

| Tool | Purpose | Command |
|------|---------|---------|
| **Vitest** | Primary test runner | `npm test` |
| **Vitest coverage** | Coverage reports | `npm run test:coverage` |

```bash
# Run the full test suite
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

---

## Directory Structure

### TALL Stack

```
tests/
├── Unit/
│   ├── Services/           # Service class unit tests
│   │   └── PaymentServiceTest.php
│   ├── Models/             # Model method unit tests
│   └── Helpers/            # Helper function tests
├── Feature/
│   ├── Api/                # API endpoint tests
│   │   └── PaymentControllerTest.php
│   ├── Livewire/           # Livewire component tests
│   │   └── CheckoutFormTest.php
│   └── Auth/               # Authentication flow tests
├── Browser/                # Laravel Dusk E2E tests
│   └── CheckoutTest.php
└── Arch/                   # Architecture tests (Pest Arch)
    └── ArchTest.php
```

### Django Stack

```
apps/
├── payments/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py      # Model method tests
│   │   ├── test_services.py    # Service unit tests
│   │   ├── test_views.py       # API endpoint tests
│   │   └── test_serializers.py # Serialiser tests
│   └── factories.py            # factory_boy factories
├── users/
│   └── tests/
│       ├── test_auth.py
│       └── test_models.py
tests/
├── conftest.py                 # Shared fixtures and test setup
├── test_integration.py         # Cross-app integration tests
└── e2e/                        # Playwright E2E tests
    └── test_checkout.py
```

### React / Shared Library Stack

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx     # Component tests next to source
│   │   └── Button.stories.tsx  # Storybook stories
│   └── Form/
│       ├── Form.tsx
│       └── Form.test.tsx
├── services/
│   ├── payment.ts
│   └── payment.test.ts         # Service unit tests next to source
├── hooks/
│   ├── useAuth.ts
│   └── useAuth.test.ts
tests/
├── integration/                # Cross-module integration tests
│   └── checkout-flow.test.ts
└── e2e/                        # Playwright E2E tests
    └── checkout.spec.ts
```

---

## Naming Conventions

| Convention | Pattern | Example |
|------------|---------|---------|
| PHP test class | `<Subject>Test` | `PaymentServiceTest` |
| PHP test method | `test_<behaviour>_<condition>` | `test_charge_fails_when_card_declined` |
| Python test file | `test_<module>.py` | `test_payment_service.py` |
| Python test function | `test_<behaviour>_<condition>` | `test_charge_fails_when_card_declined` |
| TypeScript test file | `<subject>.test.ts(x)` | `payment-service.test.ts` |
| TypeScript test name | `<behaviour> when <condition>` | `"returns error when card is declined"` |
| E2E test file | `<flow>.spec.ts` or `Test.php` | `checkout.spec.ts` |

**Avoid:**
- `test_1`, `test_2` — no scenario is described
- Mirroring the method name without a scenario: `test_charge` is useless; `test_charge_creates_invoice_on_success` is not

---

## The Testing Pyramid

Write tests in this ratio: many unit, some integration, few E2E.

```
          /    E2E     \       <- Few, slow, high confidence (user flows)
         / Integration  \      <- Some, moderate speed (service boundaries)
        /  Unit Tests    \     <- Many, fast, focused (function/method level)
```

### 1. Unit Tests

Test a single class, function, or method in complete isolation. Mock or stub all external dependencies.

**What to unit test:**
- Service classes (business logic)
- Model methods and scopes (computed properties, custom queries)
- Helper and utility functions
- Validation rules
- Transformers/serialisers

**TALL Stack example (Pest):**

```php
// tests/Unit/Services/PaymentServiceTest.php

use App\Services\PaymentService;
use App\Exceptions\PaymentFailedException;

it('creates an invoice when payment succeeds', function () {
    $mockGateway = mock(PaymentGateway::class)
        ->shouldReceive('charge')
        ->with(5000, 'gbp')
        ->andReturn(new ChargeResult(success: true, transactionId: 'txn_123'))
        ->getMock();

    $service = new PaymentService($mockGateway);
    $invoice = $service->charge(order: $this->order, amountPence: 5000);

    expect($invoice)->toBeInstanceOf(Invoice::class)
        ->and($invoice->transaction_id)->toBe('txn_123');
});

it('throws PaymentFailedException when the gateway declines the card', function () {
    $mockGateway = mock(PaymentGateway::class)
        ->shouldReceive('charge')
        ->andReturn(new ChargeResult(success: false, errorCode: 'card_declined'))
        ->getMock();

    $service = new PaymentService($mockGateway);

    expect(fn () => $service->charge(order: $this->order, amountPence: 5000))
        ->toThrow(PaymentFailedException::class, 'card_declined');
});
```

**Django example (pytest-django):**

```python
# apps/payments/tests/test_services.py

import pytest
from unittest.mock import MagicMock, patch
from apps.payments.services import PaymentService
from apps.payments.exceptions import PaymentFailedException

def test_charge_creates_invoice_when_payment_succeeds(db, order_factory):
    order = order_factory()
    mock_gateway = MagicMock()
    mock_gateway.charge.return_value = {"success": True, "transaction_id": "txn_123"}

    service = PaymentService(gateway=mock_gateway)
    invoice = service.charge(order=order, amount_pence=5000)

    assert invoice.transaction_id == "txn_123"
    mock_gateway.charge.assert_called_once_with(5000, "gbp")

def test_charge_raises_when_card_declined(db, order_factory):
    order = order_factory()
    mock_gateway = MagicMock()
    mock_gateway.charge.return_value = {"success": False, "error_code": "card_declined"}

    service = PaymentService(gateway=mock_gateway)

    with pytest.raises(PaymentFailedException, match="card_declined"):
        service.charge(order=order, amount_pence=5000)
```

**TypeScript example (Vitest):**

```typescript
// src/services/payment.test.ts

import { describe, it, expect, vi } from "vitest";
import { PaymentService } from "./payment";

describe("PaymentService.charge", () => {
  it("returns invoice when payment succeeds", async () => {
    const mockGateway = { charge: vi.fn().mockResolvedValue({ success: true, transactionId: "txn_123" }) };
    const service = new PaymentService(mockGateway);

    const invoice = await service.charge({ orderId: "ord_1", amountPence: 5000 });

    expect(invoice.transactionId).toBe("txn_123");
  });

  it("throws PaymentError when card is declined", async () => {
    const mockGateway = { charge: vi.fn().mockResolvedValue({ success: false, errorCode: "card_declined" }) };
    const service = new PaymentService(mockGateway);

    await expect(service.charge({ orderId: "ord_1", amountPence: 5000 }))
      .rejects.toThrow("card_declined");
  });
});
```

### 2. Integration Tests

Verify that multiple units work together across a real database or service boundary. Integration tests use a dedicated test database — never the development database.

**What to integration test:**
- Controller/view actions with real database queries
- API endpoints from request to response
- Service methods that coordinate multiple repositories
- Queue jobs and event listeners

**TALL Stack example (Pest Feature test):**

```php
// tests/Feature/Api/PaymentControllerTest.php

use App\Models\User;
use App\Models\Order;

it('returns 201 and invoice when payment is accepted', function () {
    $user = User::factory()->create();
    $order = Order::factory()->for($user)->create(['total_pence' => 5000]);

    $this->actingAs($user, 'sanctum')
        ->postJson("/api/orders/{$order->id}/pay", ['payment_method' => 'pm_card_visa'])
        ->assertStatus(201)
        ->assertJsonStructure(['invoice' => ['id', 'transaction_id', 'amount_pence']]);
});

it('returns 422 when the order has already been paid', function () {
    $user = User::factory()->create();
    $order = Order::factory()->for($user)->paid()->create();

    $this->actingAs($user, 'sanctum')
        ->postJson("/api/orders/{$order->id}/pay", ['payment_method' => 'pm_card_visa'])
        ->assertStatus(422)
        ->assertJsonPath('error.code', 'ORDER_ALREADY_PAID');
});

it('returns 401 when the user is not authenticated', function () {
    $order = Order::factory()->create();

    $this->postJson("/api/orders/{$order->id}/pay", ['payment_method' => 'pm_card_visa'])
        ->assertStatus(401);
});
```

**Django example (pytest-django with APIClient):**

```python
# apps/payments/tests/test_views.py

import pytest
from rest_framework.test import APIClient
from apps.payments.factories import OrderFactory

@pytest.fixture
def api_client():
    return APIClient()

def test_pay_order_returns_201_with_invoice(db, api_client, user_factory, order_factory):
    user = user_factory()
    order = order_factory(user=user, total_pence=5000, paid=False)
    api_client.force_authenticate(user=user)

    response = api_client.post(f"/api/orders/{order.id}/pay/", {"payment_method": "pm_card_visa"})

    assert response.status_code == 201
    assert "invoice" in response.data

def test_pay_order_returns_401_when_unauthenticated(db, api_client, order_factory):
    order = order_factory()

    response = api_client.post(f"/api/orders/{order.id}/pay/", {})

    assert response.status_code == 401
```

### 3. Feature and End-to-End Tests

Simulate real user interactions through the browser. These tests are slow and should cover critical user journeys only.

**What to E2E test:**
- Checkout and payment flows
- Authentication flows (login, registration, password reset)
- Key CRUD journeys (create order, submit form, etc.)

**TALL Stack Livewire component test:**

```php
// tests/Feature/Livewire/CheckoutFormTest.php

use App\Livewire\CheckoutForm;
use Livewire\Livewire;

it('submits order and shows confirmation when valid card is entered', function () {
    $user = User::factory()->create();
    $cart = Cart::factory()->for($user)->withItems(3)->create();

    Livewire::actingAs($user)
        ->test(CheckoutForm::class, ['cartId' => $cart->id])
        ->set('paymentMethod', 'pm_card_visa')
        ->call('placeOrder')
        ->assertDispatched('order-placed')
        ->assertSee('Order confirmed');
});
```

**Playwright E2E example (TypeScript):**

```typescript
// tests/e2e/checkout.spec.ts

import { test, expect } from "@playwright/test";

test("completes checkout with a valid card", async ({ page }) => {
  await page.goto("/login");
  await page.fill('[name="email"]', "test@example.com");
  await page.fill('[name="password"]', "secret");
  await page.click('[type="submit"]');

  await page.goto("/cart");
  await page.click('[data-testid="checkout-button"]');
  await page.fill('[data-testid="card-number"]', "4242424242424242");
  await page.click('[data-testid="pay-button"]');

  await expect(page.locator('[data-testid="confirmation"]')).toBeVisible();
});
```

### 4. API Tests

Verify API contracts: request shape, response shape, status codes, and auth requirements. Every public API endpoint must have at minimum:

1. Happy path with valid data
2. Validation failure (422/400)
3. Unauthenticated request (401)
4. Unauthorised request (403) where applicable
5. Not found case (404) where applicable

---

## TDD (Test-Driven Development)

**Cycle:** Red → Green → Refactor

1. **Red** — Write a failing test for the next piece of behaviour.
2. **Green** — Write the minimum code to make it pass.
3. **Refactor** — Clean up without breaking the test.

Use TDD for:
- All service class methods
- All API endpoint handlers
- All complex validation logic
- Any function with clear inputs and outputs

---

## Test Data and Factories

Use factories for all test data. Avoid constructing model instances inline in every test — factories ensure consistent, valid state.

**TALL Stack (Laravel Factories):**

```php
// database/factories/OrderFactory.php

class OrderFactory extends Factory
{
    public function definition(): array
    {
        return [
            'user_id'     => User::factory(),
            'status'      => 'pending',
            'total_pence' => $this->faker->numberBetween(500, 100000),
        ];
    }

    public function paid(): static
    {
        return $this->state(['status' => 'paid', 'paid_at' => now()]);
    }
}
```

**Django Stack (factory_boy):**

```python
# apps/payments/factories.py

import factory
from django.contrib.auth import get_user_model
from apps.payments.models import Order

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "secret")

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    total_pence = factory.Faker("random_int", min=500, max=100000)
    status = "pending"
```

**TypeScript (test helpers):**

```typescript
// tests/helpers/factories.ts

export function buildOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: "ord_test_1",
    userId: "usr_test_1",
    totalPence: 5000,
    status: "pending",
    createdAt: new Date("2026-01-01"),
    ...overrides,
  };
}
```

---

## Mocking Patterns

### TALL Stack

Use Mockery (included with Pest) for service interfaces:

```php
$mock = mock(PaymentGateway::class)
    ->shouldReceive('charge')
    ->once()
    ->andReturn(new ChargeResult(success: true))
    ->getMock();
```

Use Laravel's `Http::fake()` for outbound HTTP calls:

```php
Http::fake([
    'api.stripe.com/*' => Http::response(['id' => 'pi_123'], 200),
]);
```

### Django Stack

Use `unittest.mock` for service dependencies:

```python
from unittest.mock import patch, MagicMock

@patch("apps.payments.services.stripe.Charge.create")
def test_charge_calls_stripe(mock_create, db, order_factory):
    mock_create.return_value = {"id": "ch_123", "status": "succeeded"}
    ...
```

Use `responses` library for outbound HTTP calls:

```python
import responses

@responses.activate
def test_webhook_delivery(db):
    responses.add(responses.POST, "https://hooks.example.com/", json={"ok": True})
    ...
```

### TypeScript / React Stack

Use `vi.fn()` or `vi.mock()` for function mocking:

```typescript
import { vi } from "vitest";
vi.mock("../services/payment", () => ({ charge: vi.fn() }));
```

Use MSW for API mocking in component and integration tests:

```typescript
import { http, HttpResponse } from "msw";
import { server } from "../tests/server";

server.use(
  http.post("/api/orders/:id/pay", () => {
    return HttpResponse.json({ invoice: { id: "inv_1" } }, { status: 201 });
  })
);
```

### General Rules

- Mock at the boundary closest to the unit under test.
- Never mock the module you are testing.
- Always verify mock expectations (assert call counts and arguments where it matters).
- Each test creates its own fresh mock instances — no shared mock state between tests.

---

## Database Isolation

**Critical:** Tests must never use the development database.

- **TALL Stack:** Use `RefreshDatabase` or `DatabaseTransactions` trait in Pest. Set `DB_DATABASE` to `projectname_test` in `.env.test`.
- **Django Stack:** Use `@pytest.mark.django_db` or `pytest-django`'s automatic test database creation. Set `DATABASES` to the test database in `settings/testing.py`.
- **TypeScript Stack:** Use in-memory databases (SQLite via Prisma) or mock the data layer entirely for unit tests. Use a dedicated test database for integration tests.

Each test run must start from a known clean state. Never assume data left by a previous test.

---

## Security-Critical Tests

For input validation, authentication, and authorisation logic, write tests for the following attack scenarios in addition to the happy path:

- **SQL injection:** Attempt SQL meta-characters in user-controlled fields
- **XSS:** Attempt script injection in text inputs and verify output is escaped
- **Mass assignment:** Attempt to set protected attributes via API payloads
- **IDOR:** Attempt to access another user's resources using a valid auth token
- **Privilege escalation:** Attempt actions that require a higher role than the authenticated user holds

---

## Rules and Principles

1. **Every new public service method has at least one unit test.** No exceptions.

2. **Every new API endpoint has integration tests** covering at minimum: the happy path, a validation failure, an unauthenticated request, and a not-found case.

3. **Tests must be deterministic.** No reliance on real time, random values, or external network services. Mock everything at the boundary.

4. **Tests must be independent.** Each test sets up its own state and cleans up after itself. No test depends on another having run first.

5. **Follow Arrange-Act-Assert:**
   - **Arrange**: set up test data and mocks
   - **Act**: call the function or trigger the action
   - **Assert**: verify the outcome

6. **Test behaviour, not implementation.** Assert on outputs and observable side effects, not on which internal methods were called (unless verifying a critical security boundary).

7. **Keep unit tests fast.** Unit tests should complete in under 100ms each. If a test needs a real database or network, it belongs in the integration test suite.

8. **Security-critical paths have negative tests.** Authentication, authorisation, and input validation all need tests that verify rejection of invalid or malicious input.

9. **Test code is held to the same standard as production code.** A clear, slightly repetitive test is better than a clever abstraction that obscures what is being verified.
