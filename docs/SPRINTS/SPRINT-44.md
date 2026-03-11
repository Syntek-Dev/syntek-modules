# Sprint 44 — Onboarding UI & Donations UI

**Sprint Goal**: Implement the multi-step onboarding wizard with resumable state, and the donation
form UI with Gift Aid capture and campaign progress display.

**Total Points**: 10 / 11 **MoSCoW Balance**: Should 80% / Could 20% **Status**: Planned

## Stories

| Story                        | Title                                          | Points | MoSCoW | Dependencies Met                   |
| ---------------------------- | ---------------------------------------------- | ------ | ------ | ---------------------------------- |
| [US056](../STORIES/US056.md) | `@syntek/ui-onboarding` — Onboarding Wizard UI | 5      | Should | US042 ✓, US046 ✓                   |
| [US068](../STORIES/US068.md) | `@syntek/ui-donations` — Donations UI          | 5      | Should | US042 ✓, US044 ✓, US027 ✓, US052 ✓ |

## Notes

- US056 and US068 are independent of each other and can be worked in parallel.
- US056 wizard state must be resumable — progress must persist across page reloads and sessions.
- US068 Gift Aid checkbox must display the full HMRC-required declaration text — this is a legal
  requirement.
