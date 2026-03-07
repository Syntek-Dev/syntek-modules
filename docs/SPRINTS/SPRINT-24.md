# Sprint 24 — Reporting & Exports

**Sprint Goal**: Implement the reporting module with PDF, Excel, and CSV export support, scheduled
report delivery, and role-based report access control.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                    | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ---------------------------------------- | ------ | ------ | ------------------------- |
| [US028](../STORIES/US028.md) | `syntek-reporting` — Reporting & Exports | 8      | Must   | US010 ✓, US011 ✓, US015 ✓ |

## Notes

- Report generation must be async via Celery (US015) — large reports must not block the request
  cycle.
- Generated report files must be stored via US031 (documents/MinIO) with presigned download URLs.
- Report access must be permission-checked via US011 (RBAC) — tenant-scoped.
- Scheduled reports must dispatch via US019 (notifications) when ready.
