# Sprint 69 — Error Handling Backend

**Sprint Goal**: Implement the error handling module — custom Django error handlers for all HTTP
error codes, structured JSON error responses with correlation IDs, GraphQL error extensions,
maintenance mode middleware, and Sentry integration.

**Total Points**: 5 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ---------------------------------------------------- | ------ | ------ | ---------------- |
| [US124](../STORIES/US124.md) | `syntek-error` — Error Handling & Custom Error Pages | 5      | Should | US010 ✓, US014 ✓ |

## Notes

- US124 is foundational infrastructure that can be installed at any point in the build order — it
  has no hard dependencies beyond US010 (tenancy) and US014 (logging). It is positioned here to be
  available before the web and mobile error UI packages in Sprint 70.
- The 401 vs 403 distinction requires a middleware that inspects `request.user.is_authenticated`
  before Django's default 403 handler fires — this is a non-trivial Django pattern; ensure it is
  well-tested.
- Correlation IDs must be propagated from the `X-Correlation-ID` request header if present (e.g. set
  by a load balancer or API gateway) so that distributed tracing chains do not break.
- The Strawberry error extension (injecting `code` and `correlationId` into GraphQL error
  extensions) integrates cleanly with `syntek-graphql-crypto` (US008) — ensure ordering does not
  conflict.
- Sprint 70 (web and mobile error UI) is blocked on this sprint completing.
