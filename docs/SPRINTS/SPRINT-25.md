# Sprint 25 — Membership & Integrations Framework

**Sprint Goal**: Implement the membership tiers and renewals module with member directory, and the integrations framework providing OAuth bridges for EspoCRM, CalDav, and third-party services.

**Total Points**: 10 / 11
**MoSCoW Balance**: Must 60% / Should 40%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US032](../STORIES/US032.md) | `syntek-membership` — Membership & Renewals | 5 | Must | US009 ✓, US010 ✓, US025 ✓ |
| [US033](../STORIES/US033.md) | `syntek-integrations` — Integrations Framework | 5 | Should | US009 ✓, US010 ✓ |

## Notes

- US032 and US033 are independent of each other and can be worked in parallel.
- US032 membership renewal reminders must dispatch via US019 (notifications).
- US033 OAuth bridge tokens must be stored encrypted via the Rust layer — never plaintext.
