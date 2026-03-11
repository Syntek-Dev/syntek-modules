# Sprint 05 — Rust: GraphQL Encryption Middleware + Security Policy

**Sprint Goal**: Implement the Strawberry GraphQL middleware that encrypts mutation inputs and
decrypts query responses — making the GraphQL layer the single encryption boundary for the entire
system — and define the security policies (MFA-enforcing SSO, key rotation, network architecture)
that all subsequent modules must comply with.

**Total Points**: 13 / 13 **MoSCoW Balance**: Must 100% **Status**: In Progress (US008 Completed
10/03/2026 — US076 pending)

## Stories

| Story                        | Title                                                                  | Points | MoSCoW | Status      | Dependencies Met                |
| ---------------------------- | ---------------------------------------------------------------------- | ------ | ------ | ----------- | ------------------------------- |
| [US008](../STORIES/US008.md) | `syntek-graphql-crypto` — GraphQL Encryption Middleware                | 13     | Must   | Completed   | US007 ✓                         |
| [US076](../STORIES/US076.md) | Security Policy: MFA-Enforcing SSO, Key Rotation, Network Architecture | 10     | Must   | Not Started | US006 ✓ (US009 depends on this) |

## Notes

- US008 increased from 8 to 13 points — the write-path middleware (mutation encryption), batch
  grouping via `@encrypted(batch: "group_name")`, group failure policy, and full integration test
  added significant scope.
- **US076 can run in parallel with US008** — policy definition and documentation work does not block
  the US008 implementation, and US008 does not block US076. Both can proceed simultaneously.
- US076 introduces a **key versioning prefix** to the ciphertext layout defined in US006. The US006
  implementation must be updated to support the 2-byte version prefix before the green phase of
  US006 is marked complete. The red-phase tests for US006 should also be extended to cover this.
- After this sprint the full Rust security layer is operational and the security policies are
  defined. Backend module development (US009+) can begin — US009 depends on the SSO allowlist policy
  from US076.
- US009 (`syntek-auth`) must list US076 as a dependency and implement the provider allowlist check
  defined there.

---

## Story Status

| Story | Title                                                                  | Points | BE  | Rust | Overall     |
| ----- | ---------------------------------------------------------------------- | ------ | --- | ---- | ----------- |
| US008 | `syntek-graphql-crypto` — GraphQL Encryption Middleware                | 13     | ✅  | ✅   | Completed   |
| US076 | Security Policy: MFA-Enforcing SSO, Key Rotation, Network Architecture | 10     | ⬜  | ➖   | Not Started |

---

## US008 Completion Detail

**Completed:** 10/03/2026 **Branch:** `us008/syntek-graphql-crypto` **Tests:** 55/55 passing (13
Rust unit + 42 Python unit + 4 integration — green phase) **Linters:** ruff, basedpyright, prettier,
markdownlint, clippy — all clean

### What was built

- `rust/syntek-graphql-crypto/src/lib.rs` — `EncryptedFieldSpec` struct and `MiddlewareError` enum
- `rust/syntek-graphql-crypto/Cargo.toml` — updated with correct dependencies and `crate-type`
- `rust/syntek-graphql-crypto/tests/middleware_tests.rs` — 13 Rust unit tests
- `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/middleware.py` — full write-path and
  read-path `SchemaExtension` implementation
- `packages/backend/syntek-graphql-crypto/syntek_graphql_crypto/directives.py` — `@encrypted` and
  `@encrypted(batch: "group_name")` schema directives
- `packages/backend/syntek-graphql-crypto/README.md` — setup guide, annotation guide, key naming
  convention (`SYNTEK_FIELD_KEY_<MODEL>_<FIELD>`)
- `packages/backend/syntek-graphql-crypto/syntek.manifest.toml` — crate ID + Forgejo registry
  coordinates; no user-configurable options
- `packages/backend/syntek-graphql-crypto/tests/test_write_path.py` — 10 unit tests (AC1–AC3)
- `packages/backend/syntek-graphql-crypto/tests/test_read_path.py` — 9 unit tests (AC4–AC6)
- `packages/backend/syntek-graphql-crypto/tests/test_error_handling.py` — 11 unit tests (AC7–AC9)
- `packages/backend/syntek-graphql-crypto/tests/test_auth_guard.py` — 6 unit tests (AC10–AC11)
- `packages/backend/syntek-graphql-crypto/tests/test_directives.py` — 6 unit tests
- `tests/graphql_crypto/test_integration.py` — 4 integration tests (AC1+AC4, AC2+AC5, AC7, AC10)

### All acceptance criteria satisfied

| AC   | Description                                               | Status    |
| ---- | --------------------------------------------------------- | --------- |
| AC1  | Individual `@encrypted` write → ciphertext to resolver    | Satisfied |
| AC2  | Batch `@encrypted` write → single `encrypt_fields_batch`  | Satisfied |
| AC3  | Mixed individual + batch → correct routing, no mixing     | Satisfied |
| AC4  | Individual `@encrypted` read → plaintext to frontend      | Satisfied |
| AC5  | Batch `@encrypted` read → single `decrypt_fields_batch`   | Satisfied |
| AC6  | Non-annotated fields → passthrough, zero overhead         | Satisfied |
| AC7  | Decrypt failure (individual) → null + structured error    | Satisfied |
| AC8  | Decrypt failure (batch) → all null, one error             | Satisfied |
| AC9  | Encrypt failure → mutation rejected, no partial ORM write | Satisfied |
| AC10 | Unauthenticated → null + auth error + logged              | Satisfied |
| AC11 | Resolver isolation — no crypto logic in resolvers         | Satisfied |

### Test summary

| Suite             | Tests  | Passed | Failed | Skipped |
| ----------------- | ------ | ------ | ------ | ------- |
| Rust unit         | 13     | 13     | 0      | 0       |
| Python unit       | 42     | 42     | 0      | 0       |
| Integration       | 4      | 4      | 0      | 0       |
| **Total (green)** | **59** | **59** | **0**  | **0**   |

> Note: the red-phase test status file recorded 56 tests (10 Rust, 42 Python unit, 4 integration).
> The final green-phase count is 59 — 3 additional Rust unit tests were added during implementation
> to reach full variant coverage in `MiddlewareError`.

---

## Sprint 05 Partial Completion Summary

**US008 completed 10/03/2026. US076 (Security Policy) remains outstanding.**

| Category         | Total | Completed | Remaining |
| ---------------- | ----- | --------- | --------- |
| Must Have        | 2     | 1         | 1         |
| Should Have      | 0     | 0         | 0         |
| Could Have       | 0     | 0         | 0         |
| **Total Points** | 23    | 13        | 10        |
