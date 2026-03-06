# Sprint 26 — Email Marketing & Loyalty / Referrals

**Sprint Goal**: Implement the email marketing module with campaign management, subscriber lists, and GDPR opt-out; and the loyalty and referrals module with points, tiers, and referral attribution.

**Total Points**: 10 / 11
**MoSCoW Balance**: Should 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US038](../STORIES/US038.md) | `syntek-email-marketing` — Email Marketing | 5 | Should | US010 ✓, US019 ✓, US029 ✓ |
| [US041](../STORIES/US041.md) | `syntek-loyalty` — Loyalty & Referrals | 5 | Should | US009 ✓, US010 ✓, US025 ✓ |

## Notes

- US038 and US041 are independent of each other and can be worked in parallel.
- US038 all subscriber lists must respect GDPR consent recorded via US029 — no mailing to non-opted-in contacts.
- US041 loyalty point transactions must be recorded in the audit log via US013.
