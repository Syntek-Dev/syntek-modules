# Sprint 15 — Payments

**Sprint Goal**: Implement the Stripe payments module with one-off charges, subscription management, refunds, webhook handling, and PCI-compliant card data flow.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US025](../STORIES/US025.md) | `syntek-payments` — Payments (Stripe) | 13 | Must | US009 ✓, US010 ✓, US019 ✓ |

## Notes

- ⚠️ This story exceeds the 11-point sprint capacity. Consider splitting at sprint kick-off into:
  - **payments-core** (8pts): Stripe customer/payment intent, one-off charges, refunds, webhook verification
  - **payments-subscriptions** (5pts): Subscription plans, billing cycles, trial periods, cancellation flow
- Stripe API keys must come from `SYNTEK_PAYMENTS` settings — never hardcoded.
- Webhook endpoint must verify Stripe signatures using HMAC-SHA256 before processing any event.
