# Sprint 59 — Mobile Forms

**Sprint Goal**: Implement the React Native forms package with touch-optimised native field
components, keyboard-aware scrolling, swipe multi-step navigation, native platform pickers, and the
same useForm API pattern as @syntek/forms.

**Total Points**: 8 / 11 **MoSCoW Balance**: Should 100% **Status**: Planned

## Stories

| Story                        | Title                                       | Points | MoSCoW | Dependencies Met                   |
| ---------------------------- | ------------------------------------------- | ------ | ------ | ---------------------------------- |
| [US094](../STORIES/US094.md) | `@syntek/mobile-forms` — React Native Forms | 8      | Should | US057 ✓, US044 ✓, US046 ✓, US023 ✓ |

## Notes

- US094 requires `@syntek/mobile-ui` (US057) for NativeWind base styling and `@syntek/forms` (US046)
  for the shared hook layer — both must be complete before Sprint 59 begins.
- Native pickers use Expo APIs (`expo-image-picker`, `expo-document-picker`,
  `@react-native-community/datetimepicker`) — no third-party date or file picker libraries.
- `SelectField` renders an ActionSheet on iOS and a Modal flat list on Android — platform-aware with
  no configuration required.
- `DynamicForm` mirrors the React web version in API and behaviour; the only difference is that
  backend field types map to native components instead of web components.
- Swipe navigation in `MultiStepForm` requires `react-native-gesture-handler` — already a peer
  dependency of `@syntek/mobile-ui`.
- E2E tests use Maestro — iOS and Android both targeted.
