# Sprint 07 — Rust: Multi-Tenancy Backend

**Sprint Goal**: Implement schema-based multi-tenancy with per-tenant PostgreSQL schema isolation, subdomain/domain routing middleware, tenant bootstrapping, and cross-tenant query guards.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US010](../STORIES/US010.md) | `syntek-tenancy` — Multi-Tenancy | 13 | Must | US009 ✓ |

## Notes

- ⚠️ This story exceeds the 11-point sprint capacity. Consider splitting at sprint kick-off into:
  - **tenancy-core** (8pts): Schema isolation, tenant middleware, domain routing, tenant model
  - **tenancy-extended** (5pts): Tenant bootstrapping commands, cross-tenant guards, admin tooling
- Strict dependency on US009 (Authentication) — tenant resolution relies on authenticated sessions.
- After this sprint the core security perimeter is in place; all subsequent backend modules build on top.
