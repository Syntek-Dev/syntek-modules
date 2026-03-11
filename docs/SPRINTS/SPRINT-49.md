# Sprint 49 — Mobile Notifications & Media

**Sprint Goal**: Implement the mobile push notifications package with FCM/APNs support and deep-link
routing, and the expanded mobile media package with camera, photo library, video picker, document
picker, chunked upload, and resumable network recovery.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 38% / Should 62% **Status**:
Planned

## Stories

| Story                        | Title                                                 | Points | MoSCoW | Dependencies Met                   |
| ---------------------------- | ----------------------------------------------------- | ------ | ------ | ---------------------------------- |
| [US059](../STORIES/US059.md) | `@syntek/mobile-notifications` — Mobile Notifications | 5      | Must   | US057 ✓, US019 ✓                   |
| [US073](../STORIES/US073.md) | `@syntek/mobile-media` — Mobile Media Capture         | 8      | Should | US057 ✓, US030 ✓, US106 ✓, US044 ✓ |

## Notes

- US059 and US073 are fully independent — no shared code, no shared models. Assign one per developer
  and run in parallel. Sprint exceeds capacity at 13 pts.
- US059 push token registration must handle token rotation — stale tokens must be automatically
  refreshed.
- US059 notification tap must deep-link to the correct in-app screen — generic "open app" is not
  acceptable.
- US073 chunked upload must resume after network interruption — never require a full re-upload on
  failure. Resumable state is stored in AsyncStorage and keyed by session token.
- US073 depends on `syntek-media-upload` (US106) for the chunked upload pipeline; Sprint 49 can only
  begin once Sprint 23 (US106) is complete.
