# Sprint 53 — Web & Mobile Security Packages

**Sprint Goal**: Implement the Next.js security package (CSP nonce injection, security headers, XSS
sanitisation, CSRF helpers) and the React Native security package (input sanitisation, deep link and
WebView URL validation, screenshot prevention), completing the cross-platform security layer for all
Syntek frontend applications.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                             | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ------------------------------------------------- | ------ | ------ | ------------------------- |
| [US082](../STORIES/US082.md) | `@syntek/ui-security` — Next.js Security Package  | 5      | Must   | US012 ✓, US044 ✓, US042 ✓ |
| [US083](../STORIES/US083.md) | `@syntek/mobile-security` — React Native Security | 3      | Must   | US057 ✓, US012 ✓          |

## Notes

- US082 and US083 are independent of each other and can be worked in parallel.
- **US082** depends on US012 (`syntek-security`) for backend CSRF and header context, US044
  (`@syntek/api-client`) as a peer dependency for CSRF token endpoint resolution, and US042
  (`@syntek/ui`) as the design system peer. Can start after US044 is complete (Sprint ~37).
- **US083** depends on US057 (`@syntek/mobile-ui`) for the design system peer and US012 for backend
  security context. Can start after US057 is complete (Sprint 47).
- **US082 CSP nonce flow**: `withSyntekCsp` middleware generates `crypto.randomUUID()` per request,
  injects nonce into the CSP header, and stores it in `x-nonce` for RSC components to read via
  `getCspNonce()`. The middleware merges the nonce into the existing consumer CSP policy — it does
  not replace it.
- **US082 security headers**: `syntekSecurityHeaders()` returns `{ key, value }[]` for
  `next.config.ts`. COEP, COOP, and CORP are all independently configurable (empty string = header
  omitted). No insecure defaults are silently applied.
- **US083 WebView validation**: `validateWebViewUrl` enforces an origin allowlist, requires HTTPS by
  default, and blocks `data:` and `javascript:` URIs. WebView URL injection is a real mobile attack
  surface — this is in scope by default, not tracked as a future improvement.
- **US083 documented no-ops**: CSP, HSTS, X-Frame-Options, and CSRF are not applicable to React
  Native and are documented with rationale in `SECURITY-MOBILE-NOTES.md` and the exported
  `MOBILE_SECURITY_NOTES` constant.
- DOMPurify is a peer dependency of `@syntek/ui-security/sanitise` only. `stripTags` and
  `escapeHtml` have no external dependencies in either package.

- **Cross-platform security** (Sprint 53): Next.js security headers + CSP nonce, React Native input
  sanitisation + WebView URL validation
