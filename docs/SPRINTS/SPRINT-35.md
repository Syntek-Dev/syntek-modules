# Sprint 35 — Authentication UI

**Sprint Goal**: Implement the web authentication UI package covering login, registration, MFA flows, OAuth social login buttons, and passkey prompts.

**Total Points**: 8 / 11
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US048](../STORIES/US048.md) | `@syntek/ui-auth` — Authentication UI | 8 | Must | US042 ✓, US044 ✓, US009 ✓ |

## Notes

- All auth UI components must be accessible and keyboard-navigable (WCAG 2.2 AA).
- OAuth social login buttons must be icon-slot driven — Font Awesome Pro brand icons recommended.
- MFA input must accept both TOTP codes and backup codes with clear visual distinction.
- Passkey UI must gracefully degrade on browsers that do not support WebAuthn.
