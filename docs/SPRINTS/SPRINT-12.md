# Sprint 12 — Feature Flags & Groups / Teams

**Sprint Goal**: Implement per-tenant feature flag management with percentage rollout, and the groups/teams module with nested group hierarchy and org structure support.

**Total Points**: 10 / 11
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US017](../STORIES/US017.md) | `syntek-flags` — Feature Flags | 5 | Must | US010 ✓, US016 ✓ |
| [US018](../STORIES/US018.md) | `syntek-groups` — Groups & Teams | 5 | Must | US010 ✓, US011 ✓ |

## Notes

- US017 and US018 are independent of each other and can be worked in parallel.
- US017 must support per-tenant, per-user, and percentage-based flag targeting.
- US018 nested groups must enforce tenant isolation — no cross-tenant group membership possible.
