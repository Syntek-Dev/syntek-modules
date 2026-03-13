# Sprint 06B — Social Login: Should Have + Could Have Adapters

**Sprint Goal**: Deliver the Should Have social login provider adapters for `syntek-auth`: LinkedIn
(OIDC), Microsoft MSA (v2.0 OIDC), Discord (OAuth2 + User API), Slack (OAuth2 + identity API), and
Zoom (OIDC-compliant) — with the Could Have adapters (Twitter/X, Patreon, Twitch, TikTok) deferred
to SPRINT-06C.

**Sprint Dates**: 28/03/2026 — 10/04/2026 **Total Points**: 10 / 11 **MoSCoW Balance**: Should 100%
**Status**: Planned

---

## Stories

| Story                        | Title                                                        | Points | MoSCoW | Dependencies Met                                              | Overall |
| ---------------------------- | ------------------------------------------------------------ | ------ | ------ | ------------------------------------------------------------- | ------- |
| [US130](../STORIES/US130.md) | `syntek-auth` — Social Login Provider Adapters (Should Have) | 10     | Should | SPRINT-06A ✓ (OAuthAdapter base class and registry delivered) | Planned |

### Scope Included in This Sprint (Should Have + Could Have items from US130)

| Item                       | MoSCoW      | Notes                                                                                                                   |
| -------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| `LinkedInOAuthAdapter`     | Should Have | OIDC-compliant via discovery URL; scopes `openid email profile w_member_social`; RS256 token validation                 |
| `MicrosoftMSAOAuthAdapter` | Should Have | v2.0 OIDC discovery (`/common/v2.0/.well-known/openid-configuration`); consumer MSA only (not Entra); RS256             |
| `DiscordOAuthAdapter`      | Should Have | No OIDC discovery; hardcoded token endpoint + `https://discord.com/api/users/@me`; avatar hash → URL conversion         |
| `SlackOAuthAdapter`        | Should Have | OAuth2 only (not OIDC); hardcoded endpoints; user info via `https://slack.com/api/users.identity`; scopes `identity.*`  |
| `ZoomOAuthAdapter`         | Should Have | OIDC discovery from `https://zoom.us/.well-known/openid-configuration`; scopes `openid email profile`; RS256 validation |

---

## Sprint Status

**Overall Status:** Planned

### Completion Summary

| Category         | Total | Completed | Remaining |
| ---------------- | ----- | --------- | --------- |
| Must Have        | 0     | 0         | 0         |
| Should Have      | 5     | 0         | 5         |
| Could Have       | 0     | 0         | 0         |
| **Total Points** | 10    | 0         | 10        |

---

## Notes

- This sprint depends on SPRINT-06A being complete. The `OAuthAdapter` base class,
  `SocialUserProfile` dataclass, `OAuthProfile` model, adapter registry, settings validation,
  account linking, MFA gating via `PendingOAuthSession`, PII encryption, account enumeration
  prevention, updated GraphQL mutations, and the `allowlist.py` update are all delivered in
  SPRINT-06A. This sprint only adds new adapter implementations.
- LinkedIn, Microsoft MSA, and Zoom all use the generic OIDC path (OIDC discovery + RS256 token
  validation). They follow the same pattern as `GoogleOAuthAdapter` from SPRINT-06A and are
  therefore lower-risk than the custom adapters.
- Discord follows the same non-discovery pattern as `FacebookOAuthAdapter` from SPRINT-06A:
  hardcoded endpoints, no ID token, user info fetched via a separate API call. The additional
  complexity is the avatar hash conversion
  (`https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png`).
- Slack is OAuth2 only (not OIDC). It uses hardcoded endpoints and a dedicated identity API rather
  than token claims for profile data — similar in pattern to Discord.
- Twitter/X has moved to SPRINT-06C along with the other Could Have adapters (Patreon, Twitch,
  TikTok). All five items in this sprint are Should Have.
- All five adapters route through `PendingOAuthSession` (`mfa_enforced: True`). No changes to the
  MFA gating infrastructure are required — only new adapter classes and registration in the factory.
- Provider-specific documentation (`OAUTH-LINKEDIN.md`, `OAUTH-MICROSOFT.md`, `OAUTH-DISCORD.md`,
  `OAUTH-SLACK.md`, `OAUTH-ZOOM.md`) is in scope for this sprint (carried over from the US130 task
  list; the first three guides are delivered in SPRINT-06A).
- On completion of this sprint, all Should Have adapters are delivered. US130 is fully closed on
  completion of SPRINT-06C (Could Have adapters: Twitter/X, Patreon, Twitch, TikTok).
- No UI work is in scope. Social login buttons and provider selection UX belong to `@syntek/ui-auth`
  (a separate frontend story).
