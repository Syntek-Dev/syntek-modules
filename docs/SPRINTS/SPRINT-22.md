# Sprint 22 — Invoicing

**Sprint Goal**: Implement PDF invoice generation with UK VAT support, Making Tax Digital (MTD)
compliance, and automated invoice delivery via the notifications module.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ------------------------------------ | ------ | ------ | ---------------- |
| [US026](../STORIES/US026.md) | `syntek-invoicing` — Invoicing & VAT | 8      | Must   | US010 ✓, US025 ✓ |

## Notes

- Depends on US025 (payments) for payment reference linking.
- UK VAT rates and MTD submission formats must be configurable via `SYNTEK_INVOICING` settings.
- Invoice PDFs must be stored via US031 (documents/MinIO) — not on the filesystem.
- Invoice emails must dispatch via US019 (notifications).
