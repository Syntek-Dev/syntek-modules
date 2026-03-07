# Sprint 44 — Mobile Notifications & Media

**Sprint Goal**: Implement the mobile push notifications package with FCM/APNs support and deep-link
routing, and the mobile media package with camera, photo library access, and chunked upload.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 75% / Should 25% **Status**: Planned

## Stories

| Story                        | Title                                                 | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------------------- | ------ | ------ | ------------------------- |
| [US059](../STORIES/US059.md) | `@syntek/mobile-notifications` — Mobile Notifications | 5      | Must   | US057 ✓, US019 ✓          |
| [US073](../STORIES/US073.md) | `@syntek/mobile-media` — Mobile Media Capture         | 3      | Should | US057 ✓, US030 ✓, US044 ✓ |

## Notes

- US059 and US073 are independent of each other and can be worked in parallel.
- US059 push token registration must handle token rotation — stale tokens must be automatically
  refreshed.
- US059 notification tap must deep-link to the correct in-app screen — generic "open app" is not
  acceptable.
- US073 chunked upload must resume after network interruption — never require a full re-upload on
  failure.
