# Sprint 57 — Legal Documents UI

**Sprint Goal**: Implement the legal documents and acceptance UI package — versioned T&Cs and
Privacy Policy display, prompted re-acceptance modal, registration integration, route guarding, and
acceptance history in the Privacy Centre.

**Total Points**: 5 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                        | Points | MoSCoW | Dependencies Met                            |
| ---------------------------- | -------------------------------------------- | ------ | ------ | ------------------------------------------- |
| [US092](../STORIES/US092.md) | `@syntek/ui-legal` — Legal Docs & Acceptance | 5      | Must   | US042 ✓, US044 ✓, US091 ✓, US048 ✓, US049 ✓ |

## Notes

- Sprint 57 is intentionally focused — US092 completes the cross-stack legal document story
  alongside `syntek-legal` (US091, Sprint 56).
- US092 can begin as soon as Sprint 56 (US091 backend) and Sprint 37 (US044 API client) are
  complete.
- **Registration integration**: `@syntek/ui-auth` accepts a `legalDocuments` prop on
  `SyntekAuthProvider`. `RegisterForm` renders `LegalCheckboxes` as a peer dependency — if
  `@syntek/ui-legal` is not installed, the section silently renders nothing. This is a zero-config
  opt-in: the consuming project sets `legalDocuments={['terms', 'privacy']}` on the provider and the
  rest is automatic.
- **Privacy Centre integration**: `@syntek/ui-gdpr` renders `AcceptanceHistory` as a tab in
  `PrivacyCentre` when `@syntek/ui-legal` is installed. Same peer-dependency pattern — no import
  required in the consuming app.
- **Route guarding**: `withLegalGate` is a Next.js middleware wrapper, not a React component.
  Server-side check avoids a client-side flash before the modal appears.
- **`AcceptanceGate`** should wrap only authenticated routes. Unauthenticated users are never
  prompted for T&C acceptance.
