# Sprint 34 — Layout Shell & GDPR UI

**Sprint Goal**: Implement the application layout shell package (sidebar, top nav, breadcrumbs,
command palette) and the GDPR/cookie consent UI package.

**Total Points**: 10 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                           | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------------- | ------ | ------ | ------------------------- |
| [US047](../STORIES/US047.md) | `@syntek/layout` — Application Layout Shell     | 5      | Must   | US042 ✓, US044 ✓          |
| [US049](../STORIES/US049.md) | `@syntek/ui-gdpr` — Cookie Consent & Privacy UI | 5      | Must   | US042 ✓, US044 ✓, US029 ✓ |

## Notes

- US047 and US049 are independent of each other and can be worked in parallel.
- US047 the command palette must be keyboard-navigable and screen-reader accessible.
- US049 consent choices must be persisted and synced to the backend US029 (GDPR) module — not just
  stored in localStorage.
