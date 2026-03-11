# Sprint 52 — Security Validator & Secrets Management

**Sprint Goal**: Implement the input validation and XSS protection module
(syntek-security-validator) and the provider-agnostic secrets management module
(syntek-security-secrets), completing the full security layer for all Syntek backend applications.

**Total Points**: 16 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                                            | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ---------------------------------------------------------------- | ------ | ------ | ---------------- |
| [US080](../STORIES/US080.md) | `syntek-security-validator` — Input Validation & XSS Protection  | 8      | Must   | US012 ✓, US014 ✓ |
| [US081](../STORIES/US081.md) | `syntek-security-secrets` — Provider-Agnostic Secrets Management | 8      | Must   | US001 ✓, US014 ✓ |

## Notes

- ⚠️ 16 points exceeds the 11-point sprint capacity. US080 and US081 are fully independent of each
  other — they share no files, no database tables, and no runtime dependencies. The over-capacity is
  acceptable given the parallel workload split.
- **US080** depends on US012 (`syntek-security`) for CSRF configuration context and US014
  (`syntek-logging`) for validation failure logging. Can start immediately after Sprint 09.
- **US081** depends on US001 (monorepo workspace) and US014 (`syntek-logging`). It is largely
  independent of other backend modules and can start in parallel with US080.
- Both modules are stateless — US080 has no database migrations; US081 uses in-process caching only
  (secrets must never be stored in Redis or any shared cache).
- **US081 provider priority**: `env` provider ships first (no extra packages); OpenBao provider
  ships second (recommended production target); remaining cloud providers (AWS, GCP, Azure, Vault)
  ship in the same sprint as parallel sub-tasks.
- **US080 multi-schema validation**: `ALLOW_MULTI_SCHEMA_VALIDATION: True` is the default.
  `SANITISE_GRAPHQL_INPUTS: True` is the opt-out default — benchmark on representative schemas
  before disabling.
- **US081 DB recycling**: built-in `ROTATION_DB_RECYCLE: True` default calls
  `django.db.connections.close_all()` when a DB password key rotates. Consumers override via
  `ROTATION_ON_CHANGE` for other long-lived resources (Redis pools, SMTP clients, SDK sessions).
- This sprint can begin as soon as Sprint 09 (US012, US014) is complete.
