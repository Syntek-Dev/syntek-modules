# Sprint 32 — Accounting

**Sprint Goal**: Implement double-entry accounting with VAT calculation, and optional
Xero/Sage/QuickBooks Online export integration.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                  | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | -------------------------------------- | ------ | ------ | ------------------------- |
| [US037](../STORIES/US037.md) | `syntek-accounting` — Accounting & VAT | 8      | Should | US010 ✓, US025 ✓, US026 ✓ |

## Notes

- Depends on US025 (payments) and US026 (invoicing) for transaction source data.
- Double-entry journal entries must be immutable after posting — corrections via reversal entries
  only.
- Third-party accounting system credentials (Xero, Sage, QBO) must come from `SYNTEK_ACCOUNTING`
  settings.
- VAT rates must be configurable per tenant — UK standard 20% is the default.
