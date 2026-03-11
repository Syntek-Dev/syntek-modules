# Sprint 60 — Reporting UI

**Sprint Goal**: Implement the charts and report builder UI package — Recharts wrapper components,
`useReportData` and `useChart` hooks, full `ReportBuilder`, `ReportViewer`, `ExportButton`,
`ScheduledReportForm`, chart export (PNG/SVG), and ARIA data table fallbacks.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                               | Points | MoSCoW | Dependencies Met                            |
| ---------------------------- | --------------------------------------------------- | ------ | ------ | ------------------------------------------- |
| [US054](../STORIES/US054.md) | `@syntek/ui-reporting` — Charts & Report Builder UI | 13     | Should | US042 ✓, US044 ✓, US045 ✓, US028 ✓, US101 ✓ |

## Notes

- US054 is a single cohesive story — the chart components, hooks, ReportBuilder, and ExportButton
  are tightly coupled through shared data flow and cannot be split cleanly.
- Charts must be responsive and accessible — all components include ARIA `role="img"` labels and
  hidden `<table>` data fallbacks for screen readers.
- PNG export uses `html2canvas`; SVG export serialises the Recharts SVG directly.
- `ReportBuilder` live preview must debounce parameter changes — fire no more than one query per 300
  ms of idle time.
- `ExportButton` format picker targets `syntek-reporting-export` (US101) mutations — US101 must be
  complete before export integration can be wired up, but all chart and hook logic is testable with
  mock data independently.
- `@syntek/ui-analytics` (US103, Sprint 61) imports `LineChart` from this package — Sprint 60 must
  complete before the dashboard chart in US103 can be fully integrated.
