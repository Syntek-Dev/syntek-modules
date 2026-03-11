# Sprint 16 — Notification Push Channel

**Sprint Goal**: Implement the FCM and APNs push notification channel adapter with device token
management, automatic invalid token removal, multi-device fan-out, and a React Native registration
helper consumed by `@syntek/mobile-notifications` (US059).

**Total Points**: 5 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                      | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ------------------------------------------ | ------ | ------ | ---------------- |
| [US089](../STORIES/US089.md) | `syntek-notifications-push` — Push Channel | 5      | Must   | US019 ✓          |

## Notes

- Sprint 16 is intentionally light — US089 is a self-contained adapter with its own device token
  model and React Native client helper. The push adapter is the most platform-specific of the three
  channel sub-modules, warranting its own sprint for focused review.
- US089 depends on US019 (`syntek-notifications-core`). Sprint 16 can begin as soon as Sprint 14 is
  complete; it does not need to wait for Sprint 15.
- US089 React Native registration helper (`packages/backend/syntek-notifications-push/client/`) is a
  TypeScript/JS file consumed by `@syntek/mobile-notifications` (US059, Sprint 49). Sprint 49
  therefore has a soft dependency on Sprint 16.
- FCM service account JSON and APNs private key must come from `SYNTEK_NOTIFICATIONS_PUSH` settings
  — never committed to source control. Advise consumers to use `syntek-security-secrets` (US081) for
  rotation.
- Invalid token removal must be async — never block the delivery Celery task. Token deletions are
  batched post-send via a separate cleanup task.
- APNs HTTP/2 connection pooling must be reused across sends — do not open a new connection per
  notification.
