# Sprint 22 — File Storage

**Sprint Goal**: Implement MinIO-backed file storage with document metadata in PostgreSQL, presigned
URL generation with permission gating, file versioning and history, SHA-256 checksum validation, and
retention-based expiry.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                                     | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | --------------------------------------------------------- | ------ | ------ | ------------------------- |
| [US031](../STORIES/US031.md) | `syntek-files` — MinIO File Storage & Document Management | 13     | Must   | US010 ✓, US011 ✓, US015 ✓ |

## Notes

- US031 is a single cohesive story — the MinIO client, versioning model, permission gate, presigned
  URL generation, and retention task are tightly coupled and cannot be split cleanly.
- MinIO credentials must always come from environment variables via `SYNTEK_FILES` settings — never
  hardcoded.
- Presigned URLs must use short TTLs (default 15 minutes / 900 seconds). `DOWNLOAD_URL_TTL` is
  configurable per consuming project.
- Both modules must enforce tenant-scoped access — a tenant cannot access another tenant's files.
- Checksums (SHA-256) are computed on upload and verified on download — do not skip for large files.
- If `syntek-tasks` (US015) is not installed, the retention expiry Celery task is silently skipped
  with a startup warning.
