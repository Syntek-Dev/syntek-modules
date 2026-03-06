# Sprint 10 — Audit Logging & Internationalisation

**Sprint Goal**: Implement immutable audit trail logging with GDPR-compliant retention policies, and the internationalisation module covering translations, locale handling, and UK date/currency formatting.

**Total Points**: 11 / 11
**MoSCoW Balance**: Must 73% / Should 27%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US013](../STORIES/US013.md) | `syntek-audit` — Immutable Audit Logging | 8 | Must | US010 ✓, US011 ✓ |
| [US034](../STORIES/US034.md) | `syntek-i18n` — Internationalisation | 3 | Should | US010 ✓ |

## Notes

- US013 and US034 are independent of each other and can be worked in parallel.
- US013 audit records must be append-only — no update or delete operations permitted on the audit table.
- US034 locale detection must respect per-tenant locale configuration in addition to user preference.
