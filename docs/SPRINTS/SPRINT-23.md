# Sprint 23 — Donations

**Sprint Goal**: Implement the donations module with one-off and recurring donation processing, UK
Gift Aid declaration management, campaign tracking, and donor receipts.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                     | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------- | ------ | ------ | ------------------------- |
| [US027](../STORIES/US027.md) | `syntek-donations` — Donations & Gift Aid | 8      | Must   | US009 ✓, US010 ✓, US025 ✓ |

## Notes

- Depends on US025 (payments) for Stripe charge processing.
- Gift Aid declarations must be stored with a full audit trail (US013) — HMRC compliance
  requirement.
- Donor receipts must dispatch via US019 (notifications).
- Recurring donations must integrate with the Stripe subscription mechanism from US025.
