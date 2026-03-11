# Sprint 51 — Media UI

**Sprint Goal**: Implement the React media UI package — chunked image and video upload with
preview/crop, document file upload, media gallery with lightbox, media library browser, and all
supporting hooks.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                             | Points | MoSCoW | Dependencies Met                            |
| ---------------------------- | ------------------------------------------------- | ------ | ------ | ------------------------------------------- |
| [US107](../STORIES/US107.md) | `@syntek/ui-media` — React Media Upload & Gallery | 8      | Should | US042 ✓, US044 ✓, US030 ✓, US106 ✓, US031 ✓ |

## Notes

- US107 depends on US106 (`syntek-media-upload`) for the chunked upload pipeline — Sprint 51 can
  only begin once Sprint 23 is complete.
- `ImageUpload` crop functionality uses `react-image-crop` — no Canvas API workarounds. The cropped
  region is sent as a separate Cloudinary transformation parameter, not as a modified binary.
- `MediaGallery` lightbox must be keyboard-navigable (arrow keys + Escape) and meet WCAG 2.1 AA —
  focus must be trapped within the lightbox when open.
- `FileUpload` degrades gracefully if `syntek-files` (US031) is not installed — the component
  renders a disabled state with a tooltip explaining the missing backend module.
- `MediaLibrary` URL sync must use the `@syntek/api-client` pagination pattern — no custom URL state
  management.
