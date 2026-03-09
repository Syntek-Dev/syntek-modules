# Sprint 05 — Rust: GraphQL Encryption Middleware + Security Policy

**Sprint Goal**: Implement the Strawberry GraphQL middleware that encrypts mutation inputs and
decrypts query responses — making the GraphQL layer the single encryption boundary for the entire
system — and define the security policies (MFA-enforcing SSO, key rotation, network architecture)
that all subsequent modules must comply with.

**Total Points**: 23 / 28 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                                                  | Points | MoSCoW | Dependencies Met                |
| ---------------------------- | ---------------------------------------------------------------------- | ------ | ------ | ------------------------------- |
| [US008](../STORIES/US008.md) | `syntek-graphql-crypto` — GraphQL Encryption Middleware                | 13     | Must   | US007 ✓                         |
| [US076](../STORIES/US076.md) | Security Policy: MFA-Enforcing SSO, Key Rotation, Network Architecture | 10     | Must   | US006 ✓ (US009 depends on this) |

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
