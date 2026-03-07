# Sprint 05 — Rust: GraphQL Encryption Middleware

**Sprint Goal**: Implement the Strawberry GraphQL middleware that intercepts resolver output,
decrypts `@encrypted` fields before serialisation, and ensures no ciphertext is ever returned raw in
a GraphQL response.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                                   | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ------------------------------------------------------- | ------ | ------ | ---------------- |
| [US008](../STORIES/US008.md) | `syntek-graphql-crypto` — GraphQL Encryption Middleware | 8      | Must   | US007 ✓          |

## Notes

- Strict dependency on US007 completing in Sprint 04.
- After this sprint the full Rust security layer is operational and backend module development
  (US009+) can begin.
