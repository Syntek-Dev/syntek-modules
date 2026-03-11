# Sprint 23 — Media Upload Pipeline

**Sprint Goal**: Implement the chunked upload pipeline with real-time progress tracking, ClamAV
virus scanning, session management, and commit integration with both `syntek-media-core` and
`syntek-files`.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                            | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ---------------------------------------------------------------- | ------ | ------ | ------------------------- |
| [US106](../STORIES/US106.md) | `syntek-media-upload` — Chunked Upload Pipeline & Virus Scanning | 8      | Should | US030 ✓, US031 ✓, US015 ✓ |

## Notes

- US106 depends on US030 (`syntek-media-core`) and US031 (`syntek-files`) — Sprint 23 can only begin
  once Sprints 18 and 58 are complete.
- ClamAV is an optional runtime dependency. When `VIRUS_SCAN_ENABLED = False` (e.g., in development
  or on cost-constrained infrastructure), the scan step is skipped and a warning is logged at
  startup. The upload pipeline is otherwise identical.
- Chunk storage uses Redis by default (`CHUNK_STORAGE_BACKEND = 'redis'`). Local file storage is
  available as a development fallback.
- Session tokens are signed JWTs — only the initiating user can upload chunks to their own session.
- The cleanup periodic task must run at least every 10 minutes in production — expired sessions must
  not accumulate.
