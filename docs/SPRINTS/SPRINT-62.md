# Sprint 62 — Email Builder UI

**Sprint Goal**: Implement the React drag-and-drop email template builder — all 10 block types with
property editors, variable picker with token insertion, desktop and mobile preview, send test,
save/publish to `syntek-email-core`, and undo/redo history.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                    | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | -------------------------------------------------------- | ------ | ------ | ------------------------- |
| [US113](../STORIES/US113.md) | `@syntek/ui-email-builder` — Drag-and-Drop Email Builder | 13     | Should | US042 ✓, US044 ✓, US112 ✓ |

## Notes

- US113 is a single cohesive story — the builder canvas, DnD block library, Tiptap text editor,
  variable picker, and preview iframe are all tightly coupled through shared builder state.
- Block serialisation is JSON stored in `EmailTemplate.html_body`. The client never generates final
  email HTML — all rendering is server-side via `previewEmailTemplate`.
- `ColumnsBlock` supports nested block lists within each column — the DnD implementation must handle
  nested drop targets without conflicting with the parent canvas drop zone.
- The `TestSendDialog` calls `previewEmailTemplate` to render current blocks before calling
  `sendEmail` — it does not send the unrendered JSON. A published template is not required for test
  sends.
- Undo/redo stack is capped at 50 states to prevent memory growth on long editing sessions.
- `EmailBuilder` can be used in two modes: standalone page (full-screen) or embedded modal — the
  layout is responsive to its container width, not the viewport.
