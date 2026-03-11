# Sprint 33 — Subscriptions & Comments

**Sprint Goal**: Implement the recurring subscription lifecycle module (distinct from Stripe
subscriptions — business-level subscription management), and the threaded comments module with
moderation and reactions.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 75% / Could 25% **Status**: Planned

## Stories

| Story                        | Title                                           | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------------- | ------ | ------ | ------------------------- |
| [US062](../STORIES/US062.md) | `syntek-subscriptions` — Subscription Lifecycle | 5      | Should | US025 ✓, US019 ✓, US010 ✓ |
| [US040](../STORIES/US040.md) | `syntek-comments` — Threaded Comments           | 3      | Could  | US009 ✓, US010 ✓, US011 ✓ |

## Notes

- US062 and US040 are independent of each other and can be worked in parallel.
- US062 subscription state transitions (active → past_due → cancelled) must be recorded via US013
  (audit log).
- US040 moderation actions must be permission-checked via US011 (RBAC).
