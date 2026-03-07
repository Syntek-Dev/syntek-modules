# Sprint 03 — Rust: Cryptographic Primitives

**Sprint Goal**: Implement the core Rust encryption crate providing AES-256-GCM field encryption,
Argon2id password hashing, HMAC-SHA256 integrity verification, and memory zeroisation — the security
foundation that all backend modules depend on.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                           | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ----------------------------------------------- | ------ | ------ | ---------------- |
| [US006](../STORIES/US006.md) | `syntek-crypto` — Core Cryptographic Primitives | 8      | Must   | — none —         |

## Notes

- US006 has no story-level dependencies and can start as soon as Sprint 01 scaffolding is in place.
- **Parallel opportunity**: A frontend team can begin US042 (`@syntek/ui`) in parallel from this
  sprint — it only requires US002 and US003 which are done.
- This sprint is intentionally focused — the crypto crate is security-critical and warrants its own
  sprint for thorough review.
