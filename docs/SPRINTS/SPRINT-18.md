# Sprint 18 — Media & Document Storage

**Sprint Goal**: Implement Cloudinary-backed media management with metadata in the database, and MinIO-backed document storage with presigned URLs and PDF/doc support.

**Total Points**: 10 / 11
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US030](../STORIES/US030.md) | `syntek-media` — Media Storage (Cloudinary) | 5 | Must | US010 ✓, US011 ✓ |
| [US031](../STORIES/US031.md) | `syntek-documents` — Document Storage (MinIO) | 5 | Must | US010 ✓, US011 ✓ |

## Notes

- US030 and US031 are independent of each other and can be worked in parallel.
- US030 Cloudinary credentials must come from `SYNTEK_MEDIA` settings — never hardcoded.
- US031 MinIO credentials must come from `SYNTEK_DOCUMENTS` settings; presigned URLs must have short TTLs (default 15 minutes).
- Both modules must enforce tenant-scoped access — a tenant cannot access another tenant's media or documents.
