# Sprint 21 — Media Core

**Sprint Goal**: Implement Cloudinary-backed media management with tenant-scoped metadata in
PostgreSQL, configurable image optimisation and eager transformations, video transcoding status
tracking via webhook, and the transformation URL builder.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                             | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ------------------------------------------------- | ------ | ------ | ---------------- |
| [US030](../STORIES/US030.md) | `syntek-media-core` — Cloudinary Media Management | 13     | Must   | US010 ✓, US007 ✓ |

## Notes

- US030 is a single cohesive story — the Cloudinary SDK wrapper, model, transformation URL builder,
  and webhook receiver are tightly coupled and cannot be split cleanly.
- `syntek-files` (US031) was moved to Sprint 22 to bring dependencies on both packages into the
  correct build order: US106 (`syntek-media-upload`) depends on US030 and US031, which are now in
  sequential sprints.
- Cloudinary credentials must always come from environment variables via `SYNTEK_MEDIA` settings —
  never hardcoded or committed.
- All transformation URLs must use the `build_url` helper — no raw Cloudinary URL construction
  elsewhere in the codebase.
- The webhook endpoint for `cloudinaryWebhook` must validate the `X-Cld-Signature` header before
  processing any payload.
- Tenant isolation is enforced by folder prefix or Cloudinary tag per `TENANT_FOLDER_STRATEGY`.
