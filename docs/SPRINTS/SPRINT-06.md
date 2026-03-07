# Sprint 06 — Rust: Authentication Backend

**Sprint Goal**: Implement the core authentication backend: JWT tokens, login/logout, session
management, MFA (TOTP + backup codes), passkeys (WebAuthn), and OAuth2 social login with Argon2id
password hashing via the Rust layer.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                     | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ----------------------------------------- | ------ | ------ | ---------------- |
| [US009](../STORIES/US009.md) | `syntek-auth` — Authentication & Identity | 13     | Must   | US007 ✓, US008 ✓ |

## Notes

- ⚠️ This story exceeds the 11-point sprint capacity. Consider splitting at sprint kick-off into:
  - **auth-core** (8pts): JWT, login, logout, Argon2id via PyO3, session management
  - **auth-extended** (5pts): MFA (TOTP + backup codes), passkeys (WebAuthn), OAuth2 social login
- Strict dependency on US007 (PyO3 bindings) and US008 (GraphQL middleware).
- All password operations must use `hash_password` / `verify_password` from the Rust layer — no
  Python-side hashing.
