# Sprint 38 — Reporting UI & Settings UI

**Sprint Goal**: Implement the charts and report builder UI package, and the account, security, and
billing settings pages package.

**Total Points**: 10 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                          | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ---------------------------------------------- | ------ | ------ | ------------------------- |
| [US054](../STORIES/US054.md) | `@syntek/ui-reporting` — Reporting & Charts UI | 5      | Should | US042 ✓, US045 ✓, US028 ✓ |
| [US055](../STORIES/US055.md) | `@syntek/ui-settings` — Settings Pages UI      | 5      | Should | US042 ✓, US044 ✓, US048 ✓ |

## Notes

- US054 and US055 are independent of each other and can be worked in parallel.
- US054 charts must be responsive and accessible — include ARIA labels and data table fallbacks for
  screen readers.
- US055 settings pages must gate sections behind the appropriate permissions via US011 (RBAC).
