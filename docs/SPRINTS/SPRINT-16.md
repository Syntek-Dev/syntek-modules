# Sprint 16 — Webhooks & API Keys

**Sprint Goal**: Implement inbound/outbound webhook management with HMAC-SHA256 signature verification and retry logic, and the developer API key issuance module with scopes and rate limiting.

**Total Points**: 11 / 11
**MoSCoW Balance**: Must 73% / Should 27%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US020](../STORIES/US020.md) | `syntek-webhooks` — Webhooks | 8 | Must | US010 ✓, US015 ✓ |
| [US039](../STORIES/US039.md) | `syntek-api-keys` — API Key Management | 3 | Should | US009 ✓, US010 ✓, US011 ✓ |

## Notes

- US020 and US039 are independent of each other and can be worked in parallel.
- US020 outbound webhook delivery must be async via Celery with exponential backoff retry.
- US039 API key values must be stored as Argon2id hashes — the raw key is only shown once at creation.
