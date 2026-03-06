# Sprint 42 — Mobile Design System (@syntek/mobile-ui)

**Sprint Goal**: Implement the NativeWind component library for React Native with iOS/Android adaptive components, covering all primitive and composite UI components for mobile.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US057](../STORIES/US057.md) | `@syntek/mobile-ui` — Mobile Design System | 13 | Must | US003 ✓, US001 ✓ |

## Notes

- ⚠️ This story exceeds the 11-point sprint capacity. Consider splitting at sprint kick-off into:
  - **mobile-ui-primitives** (~8pts): Button, Input, Text, View primitives, typography scale, colour tokens, spacing
  - **mobile-ui-composite** (~5pts): Modal, BottomSheet, ActionSheet, List, Card, Avatar, Badge, Toast
- **Parallel opportunity**: This sprint can start from Sprint 3 onwards — it only requires US001 and US003 (completed Sprint 2). Mobile work runs entirely in parallel with backend and web streams.
- All components must respect iOS and Android platform conventions — no forced cross-platform uniformity where it harms UX.
- Design tokens must map to the same token names as `@syntek/ui` where possible for consistency.
