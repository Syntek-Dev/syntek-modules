# Sprint 67 — Web Messaging UI

**Sprint Goal**: Implement the web messaging and live chat UI package — conversation list, chat
window with real-time subscription, message bubbles, typing indicators, read receipts, presence
dots, attachment previews, and admin group management controls.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                 | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ----------------------------------------------------- | ------ | ------ | ------------------------- |
| [US122](../STORIES/US122.md) | `@syntek/ui-messaging` — Web Messaging & Live Chat UI | 8      | Should | US042 ✓, US044 ✓, US121 ✓ |

## Notes

- US122 depends on US121 (`syntek-messaging`) completing in Sprint 66 — this sprint cannot begin
  until the backend subscription schema is finalised.
- The `@syntek/api-client` (US044) must support WebSocket subscription transport — this is required
  for `messageAdded`, `typingChanged`, `presenceChanged`, and `readReceiptUpdated` subscriptions.
  Confirm the WS transport is wired up before beginning Sprint 67.
- The `MessageList` must use a virtualised list (react-window or TanStack Virtual) — do not render
  all messages in the DOM. Long conversations can contain thousands of messages.
- Message input auto-grow must cap at a configurable max height (default 5 lines) to prevent the
  input consuming the entire chat area.
- All WCAG 2.1 AA requirements apply — focus must be managed correctly when the conversation list or
  modal dialogs open. Screen reader announcements must fire when new messages arrive.
- Sprint 68 (mobile UI) can begin in parallel with this sprint — they share the same backend schema
  from Sprint 66.
