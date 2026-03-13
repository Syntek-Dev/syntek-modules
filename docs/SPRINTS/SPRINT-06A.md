# Sprint 06A — Social Login: Must Have Adapters

**Sprint Goal**: Implement the Must Have social login provider adapters for `syntek-auth`: Google
(OIDC), Apple (signed JWT client secret, ES256), Facebook (Graph API), and Instagram (Facebook Graph
API, same credentials), together with the shared `OAuthAdapter` base class, `SocialUserProfile`
dataclass, `OAuthProfile` model, adapter registry, account-linking logic, MFA gating via
`PendingOAuthSession`, PII encryption, account enumeration prevention, and the
`backends/allowlist.py` update that registers Slack, Zoom, Patreon, Twitch, and TikTok as MFA-gated
providers (required before SPRINT-06B and SPRINT-06C adapters can register at startup).

**Sprint Dates**: 13/03/2026 — 27/03/2026 **Total Points**: 15 / 11 ⚠️ OVER CAPACITY **MoSCoW
Balance**: Must 100% **Status**: Planned

---

## Stories

| Story                        | Title                                                      | Points | MoSCoW | Dependencies Met          | Overall |
| ---------------------------- | ---------------------------------------------------------- | ------ | ------ | ------------------------- | ------- |
| [US130](../STORIES/US130.md) | `syntek-auth` — Social Login Provider Adapters (Must Have) | 13     | Must   | US009 ✓, US007 ✓, US008 ✓ | Planned |

### Scope Included in This Sprint (Must Have items from US130)

| Item                                             | Notes                                                                                                     |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `OAuthAdapter` base class                        | Abstract interface — `get_auth_url`, `exchange_code`, `get_user_info`                                     |
| `SocialUserProfile` dataclass                    | `provider_id`, `email`, `name`, `avatar_url`, `raw`                                                       |
| `OAuthProfile` model                             | FK to user, encrypted PII fields, unique `(provider, provider_user_id)` constraint                        |
| Adapter registry / factory                       | Maps `provider_type` to adapter class; validates config at `AppConfig.ready()`                            |
| Settings validation                              | `ImproperlyConfigured` on missing keys; Apple private key format validation                               |
| `GoogleOAuthAdapter`                             | OIDC discovery, RS256 token validation, profile extraction                                                |
| `AppleOAuthAdapter`                              | JWT client secret generation (ES256, 1-hour expiry), POST-body user object, ES256 validation              |
| `FacebookOAuthAdapter`                           | Hardcoded endpoints, Graph API `/me` call, nested picture extraction                                      |
| `InstagramOAuthAdapter`                          | Subclass of `FacebookOAuthAdapter`; same Graph API, scopes `user_profile,user_media`; 1-point add-on      |
| `allowlist.py` update                            | Add `slack`, `zoom`, `patreon`, `tiktok`, `twitch` to `MFA_GATED_PROVIDERS` (`instagram` already present) |
| Account linking                                  | Email-matched existing accounts linked; no duplicates created                                             |
| MFA gating                                       | `PendingOAuthSession` creation and consumption for `mfa_enforced: True` providers                         |
| PII encryption                                   | `email`, `name`, `avatar_url` encrypted via `EncryptedField` / `encrypt_field` before storage             |
| Account enumeration prevention                   | Identical response for existing vs. new email — server-side logging only                                  |
| `OAuthError` class                               | `provider_id`, `reason_code`, `details`; user-friendly mutation responses                                 |
| Updated `oidcAuthUrl` / `oidcCallback` mutations | Accept `provider` parameter; delegate to adapter registry                                                 |
| GraphQL schema updates                           | `OAuthError` type, `PendingOAuthSessionResponse` with `mfa_required` flag                                 |

---

## Sprint Status

**Overall Status:** Planned

### Completion Summary

| Category         | Total | Completed | Remaining |
| ---------------- | ----- | --------- | --------- |
| Must Have        | 1     | 0         | 1         |
| Should Have      | 0     | 0         | 0         |
| Could Have       | 0     | 0         | 0         |
| **Total Points** | 15    | 0         | 15        |

---

## Notes

- ⚠️ This sprint exceeds the 11-point sprint capacity. The 15-point estimate reflects the complexity
  of four Must Have provider protocols (OIDC, Apple JWT, Graph API, Instagram as Facebook subclass)
  plus the shared adapter scaffolding and the allowlist update. Consider splitting at kick-off into:
  - **adapters-core** (8pts): base class, registry, Google adapter, account linking, MFA gating,
    `OAuthProfile` model, PII encryption, GraphQL mutations
  - **adapters-apple-facebook-instagram** (7pts): Apple JWT client secret generation + ES256,
    Facebook Graph API, Instagram subclass, allowlist update, enumeration prevention, error handling
- This sprint covers **Must Have scope only** from US130. The Should Have (LinkedIn, Microsoft MSA,
  Discord, Slack, Zoom) adapters are deferred to SPRINT-06B; the Could Have (Twitter/X, Patreon,
  Twitch, TikTok) adapters are deferred to SPRINT-06C.
- All four providers route through `PendingOAuthSession` (`mfa_enforced: True`). The MFA gating
  infrastructure is already in place from US009 — this sprint wires the adapter output into it.
- Apple adapter complexity is a primary driver of the over-capacity estimate: signed JWT client
  secret generation, ES256 token validation, and the first-auth-only POST-body `user` object are
  each non-trivial.
- The `allowlist.py` update (adding Slack, Zoom, Patreon, Twitch, TikTok to `MFA_GATED_PROVIDERS`)
  is a prerequisite for the SPRINT-06B and SPRINT-06C adapters to register correctly at startup. It
  is a trivial change but must land before those adapters are integrated.
- No UI work is in scope. Social login buttons and provider selection UX belong to `@syntek/ui-auth`
  (a separate frontend story).
- SPRINT-06B (LinkedIn, Microsoft MSA, Discord, Slack, Zoom) can begin immediately after this sprint
  or run in parallel on a separate track — it has no dependency on this sprint's output beyond the
  `OAuthAdapter` base class and registry, which are delivered here.
