# Sprint 08 — Permissions & RBAC

**Sprint Goal**: Implement role-based access control with object-level permissions, permission
inheritance, role assignment, and GraphQL permission directives.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                            | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ------------------------------------------------ | ------ | ------ | ---------------- |
| [US011](../STORIES/US011.md) | `syntek-permissions` — RBAC & Object Permissions | 8      | Must   | US009 ✓, US010 ✓ |

## Notes

- Depends on US009 (auth) for user identity and US010 (tenancy) for tenant-scoped roles.
- Permission checks must be tenant-scoped — a role in Tenant A has no authority in Tenant B.
- GraphQL permission directives (`@hasPermission`, `@hasRole`) implemented here and used by all
  subsequent backend modules.
