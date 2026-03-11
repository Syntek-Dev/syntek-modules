# Sprint 68 — Mobile Messaging UI

**Sprint Goal**: Implement the React Native messaging and live chat package — conversation list,
inverted chat screen, message bubbles with long-press action sheet, emoji reactions, camera and
media attachments, typing indicators, and deep-link navigation from push notifications.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                     | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | --------------------------------------------------------- | ------ | ------ | ------------------------- |
| [US123](../STORIES/US123.md) | `@syntek/mobile-messaging` — Mobile Messaging & Live Chat | 8      | Should | US057 ✓, US044 ✓, US121 ✓ |

## Notes

- US123 depends on US121 (`syntek-messaging`) completing in Sprint 66. Sprint 67 (web UI) and Sprint
  68 (mobile UI) can run in parallel — they share the same backend schema.
- The inverted FlatList pattern must be used for the chat screen — messages are rendered bottom-up;
  `inverted={true}` on FlatList with items in reverse order.
- `useMobileReadReceipts` must auto-call `markAsRead` when the chat screen gains focus via the React
  Native AppState listener and react-navigation focus events — not just on user action.
- Camera and media attachment integration reuses `@syntek/mobile-media` (US073) — expo-camera and
  expo-image-picker are already peer dependencies. If US073 is not installed, the attachment button
  is hidden gracefully.
- Deep-link navigation on push notification tap requires the consuming app to register the
  `syntek-messaging` deep-link scheme in their navigation configuration. The CLI installer prints
  the required navigation config snippet as a copy-paste next step.
- Maestro E2E coverage is required before marking this sprint complete — test the full flow: open
  conversation → send message → receive message → long-press → react → attach image.
