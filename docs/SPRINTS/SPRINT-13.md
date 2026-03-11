# Sprint 13 — Feature Flags & Groups / Teams

**Sprint Goal**: Implement the full feature flag module with static registry, dynamic DB overrides,
deterministic percentage rollout, evaluation hierarchy, Redis caching, audit trail, and GraphQL API
— and the configurable groups module with GROUP_TYPES registry, GROUP_SCHEMA custom fields,
invitation lifecycle, bulk membership, and nested org hierarchy support.

**Total Points**: 16 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                            | Points | MoSCoW | Dependencies Met                   |
| ---------------------------- | -------------------------------- | ------ | ------ | ---------------------------------- |
| [US017](../STORIES/US017.md) | `syntek-flags` — Feature Flags   | 8      | Must   | US010 ✓, US013 ✓, US016 ✓, US077 ✓ |
| [US018](../STORIES/US018.md) | `syntek-groups` — Groups & Teams | 8      | Must   | US010 ✓, US011 ✓                   |

## Notes

- ⚠️ 16 points exceeds sprint capacity. US017 and US018 are fully independent — no shared files, no
  shared database tables. The over-capacity is acceptable given the parallel workload.
- **US017 scope increase** (5 → 8 points): Full `SYNTEK_FLAGS` config contract with a static flag
  registry (`FLAGS` dict), dynamic `FeatureFlag` DB model, per-user override model, deterministic
  HMAC-SHA256 percentage rollout with configurable `ROLLOUT_HASH_SALT`, evaluation hierarchy
  (per-user > tenant kill switch > percentage rollout > global default), Redis caching with short
  TTL (60s default), audit log integration (conditional on syntek-audit), and GraphQL API
  (`featureFlags`, `flagStatus` queries; `updateFlag`, `resetFlag`, `setUserFlagOverride`
  mutations).
- **US017 deterministic rollout**: HMAC-SHA256 over `flag_name + user_id + ROLLOUT_HASH_SALT`
  assigns a stable 0–99 bucket per (flag, user) pair. Changing the salt reshuffles all buckets.
  Rollout distribution is verified in tests via a 10,000-user sample (±2% tolerance).
- **US017 tenant kill switch**: A tenant DB record with `enabled: False` is an absolute override —
  it takes precedence over per-user overrides. Tenant admins can always shut off a flag for their
  entire organisation.
- **US018 scope increase** (5 → 8 points): Full `SYNTEK_GROUPS` config contract — `GROUP_TYPES`
  registry where each type independently configures label, roles, nesting depth, self-join,
  invitation requirement, and single-membership enforcement; `GROUP_SCHEMA` for custom group
  metadata fields (str/text/int/float/bool/date/email/url/choice/json) stored in a validated
  JSONField; configurable invitation system with per-invitation `max_uses` (0 = shareable link),
  expiry hours, and revocation; `bulkAddGroupMembers` capped at `BULK_ASSIGN_MAX` with per-user
  error collection (no full-batch abort); soft delete with `ActiveGroupManager` + `all_objects`;
  permission inheritance propagation via syntek-permissions.
- **US018** nested groups must enforce tenant isolation — no cross-tenant group membership possible.
- **US085** (`@syntek/ui-flags` — React hook + admin UI) is the frontend companion to US017,
  scheduled in Sprint 54.
