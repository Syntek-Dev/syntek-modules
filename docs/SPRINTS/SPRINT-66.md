# Sprint 66 — Real-Time Messaging Backend

**Sprint Goal**: Implement the real-time messaging and live chat backend — Django Channels
consumers, conversation and message models, typing indicators, read receipts, presence tracking,
push notification dispatch for offline participants, and full GraphQL query/mutation/subscription
API.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                | Points | MoSCoW | Dependencies Met                                              |
| ---------------------------- | ---------------------------------------------------- | ------ | ------ | ------------------------------------------------------------- |
| [US121](../STORIES/US121.md) | `syntek-messaging` — Real-Time Messaging & Live Chat | 13     | Should | US009 ✓, US010 ✓, US011 ✓, US013 ✓, US015 ✓, US019 ✓, US029 ✓ |

## Notes

- US121 is a single cohesive story — the Django Channels consumer, message persistence, presence
  tracking, and push dispatch are tightly coupled through a shared channel layer and cannot be split
  cleanly.
- This sprint requires Django Channels and `channels-redis` — the package must configure
  `CHANNEL_LAYERS` with a Redis (Valkey) backend. The ASGI setup instructions are printed by the
  Rust CLI installer.
- Typing indicators are ephemeral — they are broadcast via the channel layer and never persisted to
  the database. If the Channels layer restarts, in-flight typing events are lost; this is acceptable
  behaviour.
- Presence tracking uses a Channels group per user; PRESENCE_AWAY_TIMEOUT_SECONDS is enforced via a
  Celery beat task, not via WebSocket keepalive timing.
- Push notifications to offline participants require US089 (`syntek-notifications-push`) to be
  installed. If US089 is absent, the push dispatch task logs a warning and skips silently.
- Media attachments link to URLs from syntek-media-core (US030) or syntek-files (US031) — the
  messaging module never stores binary content itself; it stores attachment metadata only.
- Sprint 67 (web UI) and Sprint 68 (mobile UI) are blocked on this sprint completing.
