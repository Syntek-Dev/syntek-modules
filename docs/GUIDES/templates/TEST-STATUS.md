# Test Status — {PACKAGE_NAME}

> **Template**: Copy to `packages/backend/syntek-{name}/TEST-STATUS.md` (backend),
> `packages/web/{name}/TEST-STATUS.md` (web), or `mobile/{name}/TEST-STATUS.md` (mobile). Update
> after each test run. Replace all `{PLACEHOLDER}` values.

---

**Package**: `{PACKAGE_NAME}` (e.g. `syntek-auth` / `@syntek/ui-auth`)\
**Last Run**: `{YYYY-MM-DDTHH:MM:SSZ}`\
**Run by**: `{contributor name or CI}`\
**Overall Result**: `PASS` / `FAIL` / `PARTIAL`\
**Coverage**: `{N}%`

---

## Summary

| Suite       | Tests | Passed | Failed | Skipped |
| ----------- | ----- | ------ | ------ | ------- |
| Unit        | 0     | 0      | 0      | 0       |
| Integration | 0     | 0      | 0      | 0       |
| E2E         | 0     | 0      | 0      | 0       |
| **Total**   | **0** | **0**  | **0**  | **0**   |

---

## Unit Tests

Mark each test case with `[x]` (pass), `[ ]` (fail / not run), or `[~]` (skipped). Add a short note
for any failure.

### {Category, e.g. Authentication}

- [ ] `test_{behaviour}_{condition}` — _{what this test verifies}_
- [ ] `test_{behaviour}_{condition}` — _{what this test verifies}_

### {Category, e.g. Password Hashing}

- [ ] `test_{behaviour}_{condition}` — _{what this test verifies}_

---

## Integration Tests

- [ ] `test_{behaviour}_{condition}` — _{what this test verifies}_
- [ ] `test_{behaviour}_{condition}` — _{what this test verifies}_

---

## E2E Tests

> Only applicable to web/mobile packages and the sandbox integration. Leave blank for backend-only
> modules.

- [ ] `{scenario name}` — _{what this flow verifies}_

---

## Known Failures

List any tests that are failing, with cause and tracking reference:

| Test           | Failure reason | Story / Issue |
| -------------- | -------------- | ------------- |
| `test_example` | _description_  | US-000        |

---

## How to Run

```bash
# Full suite for this package
syntek-dev test --python-package {package-name}

# Unit tests only
syntek-dev test --python-package {package-name} -m unit

# Integration tests only
syntek-dev test --python-package {package-name} -m integration

# With coverage report
syntek-dev test --python-package {package-name} --coverage
```

---

## Notes

_Any additional context about the test suite, known flaky tests, or testing environment
requirements._
