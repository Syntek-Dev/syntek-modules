# Sprint 58 — Bulk Export

**Sprint Goal**: Implement async bulk CSV/Excel export with export templates, scheduled recurring
exports, and optional email delivery via syntek-notifications-email.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                              | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ---------------------------------- | ------ | ------ | ---------------- |
| [US093](../STORIES/US093.md) | `syntek-bulk-export` — Bulk Export | 8      | Should | US010 ✓, US015 ✓ |

## Notes

- US093 depends on `syntek-tasks` (US015) and `syntek-tenancy` (US010) — both complete by Sprint 11.
- Email delivery feature requires `syntek-notifications-email` (US087, Sprint 15) to be installed in
  the consuming project. If US087 is absent, delivery mode silently falls back to storage-only — no
  exception raised.
- PDF export uses WeasyPrint — consuming projects can supply a Jinja2 HTML template per model via
  `PDF_TEMPLATE_HOOKS`; a default paginated table template is used when none is configured.
- `syntek-bulk-import` (US021) is the import counterpart — Sprint 24.
