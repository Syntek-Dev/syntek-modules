# Sprint 37 — Session Management & API Client

**Sprint Goal**: Implement the session context package with token refresh and idle timeout, and the
generated typed GraphQL API client package.

**Total Points**: 10 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                     | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ----------------------------------------- | ------ | ------ | ---------------- |
| [US043](../STORIES/US043.md) | `@syntek/session` — Session Management    | 5      | Must   | US042 ✓, US009 ✓ |
| [US044](../STORIES/US044.md) | `@syntek/api-client` — GraphQL API Client | 5      | Must   | US001 ✓, US004 ✓ |

## Notes

- US043 and US044 are independent of each other and can be worked in parallel.
- US043 token refresh must be silent — the user must never see a forced logout due to token expiry
  during active use.
- US044 the generated client must be type-safe from the GraphQL schema — no `any` types.
- US044 is a foundational dependency for most subsequent web packages.
