# Sprint 63 — Mobile Email Builder

**Sprint Goal**: Implement the React Native email template editor — tap-to-add block model with
bottom sheet editors, variable picker keyboard accessory, drag-to-reorder, server-rendered WebView
preview, and save/publish to `syntek-email-core`.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                                         | Points | MoSCoW | Dependencies Met                   |
| ---------------------------- | ------------------------------------------------------------- | ------ | ------ | ---------------------------------- |
| [US114](../STORIES/US114.md) | `@syntek/mobile-email-builder` — Mobile Email Template Editor | 8      | Should | US057 ✓, US044 ✓, US112 ✓, US113 ✓ |

## Notes

- US114 shares the block serialisation schema from US113 (`@syntek/ui-email-builder`) — both read
  and write the same JSON format to `EmailTemplate.html_body`. A template edited on mobile and
  loaded on desktop (or vice versa) must render correctly.
- `ColumnsBlock`, `HtmlBlock`, `SocialLinksBlock`, and `HeaderBlock` are view-only on mobile — the
  block list shows them with an "Edit on desktop" badge. They are never stripped or lost.
- The WebView preview always fetches server-rendered HTML via `previewEmailTemplate` — local HTML
  rendering is explicitly not implemented to guarantee parity with the actual sent email.
- `react-native-draggable-flatlist` requires Reanimated 3 — already a peer dependency of
  `@syntek/mobile-ui`.
- Maestro E2E must cover: add TextBlock → insert variable → switch to Preview tab → verify WebView
  loads → tap Save → verify dirty flag clears.
