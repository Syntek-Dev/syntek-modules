# Sprint 30 — Inventory & Feedback

**Sprint Goal**: Implement the inventory management module with stock levels, movements, and multi-location reservations; and the feedback module with surveys, NPS scoring, and conditional question logic.

**Total Points**: 10 / 11
**MoSCoW Balance**: Should 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US066](../STORIES/US066.md) | `syntek-inventory` — Inventory Management | 5 | Should | US010 ✓, US019 ✓ |
| [US067](../STORIES/US067.md) | `syntek-feedback` — Surveys & Feedback | 5 | Should | US010 ✓, US023 ✓, US029 ✓ |

## Notes

- US066 and US067 are independent of each other and can be worked in parallel.
- US066 stock movement records must be immutable — corrections via counter-movement entries only.
- US067 survey response data is personal data — GDPR retention rules from US029 must apply.
- US067 depends on US023 (dynamic forms) for conditional question logic implementation.
