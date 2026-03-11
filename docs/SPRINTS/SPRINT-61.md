# Sprint 61 — Reporting Export & Analytics UI

**Sprint Goal**: Implement async PDF/Excel/CSV report export with email delivery and branded
templates, and the analytics UI package with GDPR-gated page tracking and an admin dashboard built
on the reporting chart components.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                | Points | MoSCoW | Dependencies Met                            |
| ---------------------------- | ---------------------------------------------------- | ------ | ------ | ------------------------------------------- |
| [US101](../STORIES/US101.md) | `syntek-reporting-export` — Report Export & Delivery | 8      | Should | US028 ✓, US015 ✓, US093 ✓, US087 ✓, US031 ✓ |
| [US103](../STORIES/US103.md) | `@syntek/ui-analytics` — Analytics UI & Dashboard    | 5      | Should | US042 ✓, US044 ✓, US054 ✓, US063 ✓          |

## Notes

- US101 and US103 are fully independent — no shared files, no shared models. Assign one per
  developer and run in parallel.
- **US101** reuses the storage backend and pre-signed URL infrastructure from `syntek-bulk-export`
  (US093). If US093 is not installed, US101 falls back to local file storage with a startup warning.
- **US101** email delivery is skipped silently if `syntek-notifications-email` (US087) is not
  installed — a warning is logged.
- **US101** PDF export uses WeasyPrint with Jinja2 templates. A default paginated table template is
  provided; consuming projects can override per report ID via `PDF_TEMPLATE_HOOKS`.
- **US103** `AdminAnalyticsDashboard` depends on chart components from `@syntek/ui-reporting`
  (US054) — Sprint 60 must complete before US103 can be fully integrated, but component shells and
  hook logic can be built and tested with mock data independently.
- **US103** `AnalyticsProvider` does not inject any client-side analytics script — all tracking is
  server-side via `syntek-analytics`. The provider manages consent state only.
