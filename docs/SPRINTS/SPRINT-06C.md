# Sprint 06C — Social Login: Could Have Adapters

**Sprint Goal**: Deliver the Could Have social login adapters for `syntek-auth`: Twitter/X (OAuth
2.0 with PKCE), Patreon (OAuth2), Twitch (OAuth2 + Client-ID header), and TikTok (non-standard
OAuth2, PKCE-like flow) — completing the full US130 scope across SPRINT-06A, SPRINT-06B, and
SPRINT-06C.

**Sprint Dates**: 11/04/2026 — 24/04/2026 **Total Points**: 9 / 11 **MoSCoW Balance**: Could 100%
**Status**: Planned

---

## Stories

| Story                        | Title                                                       | Points | MoSCoW | Dependencies Met                                  | Overall |
| ---------------------------- | ----------------------------------------------------------- | ------ | ------ | ------------------------------------------------- | ------- |
| [US130](../STORIES/US130.md) | `syntek-auth` — Social Login Provider Adapters (Could Have) | 9      | Could  | SPRINT-06B ✓ (all Should Have adapters delivered) | Planned |

### Scope Included in This Sprint (Could Have items from US130)

| Item                   | MoSCoW     | Notes                                                                                                                 |
| ---------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------- |
| `TwitterXOAuthAdapter` | Could Have | OAuth 2.0 + PKCE (S256); `code_verifier` stored in `PendingOAuthSession.metadata`; user info via Twitter v2 API       |
| `PatreonOAuthAdapter`  | Could Have | OAuth2; no OIDC; user info via v2 API with explicit `?fields[user]=email,full_name,image_url` query params            |
| `TwitchOAuthAdapter`   | Could Have | OAuth2; no OIDC; `Client-ID` header required alongside Bearer token on every Helix API call; scopes `user:read:email` |
| `TikTokOAuthAdapter`   | Could Have | Non-standard OAuth2; uses `client_key` not `client_id`; PKCE-like flow; user info via TikTok Open API v2              |

---

## Sprint Status

**Overall Status:** Planned

### Completion Summary

| Category         | Total | Completed | Remaining |
| ---------------- | ----- | --------- | --------- |
| Must Have        | 0     | 0         | 0         |
| Should Have      | 0     | 0         | 0         |
| Could Have       | 4     | 0         | 4         |
| **Total Points** | 9     | 0         | 9         |

---

## Notes

- This sprint depends on SPRINT-06B being complete and SPRINT-06A being complete. The `OAuthAdapter`
  base class, adapter registry, `allowlist.py` update, and all shared infrastructure are delivered
  in SPRINT-06A; the Should Have adapters and their documentation guides are delivered in
  SPRINT-06B. This sprint only adds new adapter implementations.
- **TikTok is the highest-risk item** in this sprint. The non-standard PKCE-like flow (where TikTok
  uses `client_key` in place of the standard `client_id` in all requests), the distinct Open API v2
  response shape, and the requirement to store the `code_verifier` in `PendingOAuthSession.metadata`
  make this adapter the most complex of the four.
- **Twitch requires a `Client-ID` header alongside `Authorization: Bearer` on every Helix API
  call.** The adapter must inject both headers at request time; omitting `Client-ID` results in a
  401 from the Helix API even with a valid Bearer token.
- **Twitter/X PKCE**: the `code_verifier` is generated at `get_auth_url` time, stored in
  `PendingOAuthSession.metadata['pkce_code_verifier']`, and retrieved at `exchange_code` time. This
  pattern is established in SPRINT-06A (documented in the Twitter adapter spec in US130) and is
  reused here.
- **Patreon user info** uses the v2 API with explicit field selection in query params
  (`?fields[user]=email,full_name,image_url`). The response uses a JSON-API envelope shape rather
  than a flat object — the adapter must unpack `data.attributes` to reach the user fields.
- All four adapters route through `PendingOAuthSession` (`mfa_enforced: True`). No changes to the
  MFA gating infrastructure are required — only new adapter classes and registration in the factory.
- Provider-specific documentation (`OAUTH-TWITTER.md`, `OAUTH-PATREON.md`, `OAUTH-TWITCH.md`,
  `OAUTH-TIKTOK.md`) is in scope for this sprint (carried over from the US130 task list).
- On completion of this sprint, US130 is fully delivered: all thirteen adapters (Google, Apple,
  Facebook, Instagram, LinkedIn, Microsoft MSA, Discord, Slack, Zoom, Twitter/X, Patreon, Twitch,
  TikTok) are implemented and the full 26-point scope is closed.
- No UI work is in scope. Social login buttons and provider selection UX belong to `@syntek/ui-auth`
  (a separate frontend story).
