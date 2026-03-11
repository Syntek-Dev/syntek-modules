# Sprint 56 — Webhooks & Legal Document Management

**Sprint Goal**: Implement the outbound/inbound webhook module with HMAC-signed delivery, retry,
DLQ, and campaign event dispatch; and the legal document management module with versioned T&Cs,
Privacy Policy, user acceptance records, and GDPR-safe erasure.

**Total Points**: 16 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Should 50% / Must 50% **Status**:
Planned

## Stories

| Story                        | Title                                           | Points | MoSCoW | Dependencies Met                   |
| ---------------------------- | ----------------------------------------------- | ------ | ------ | ---------------------------------- |
| [US020](../STORIES/US020.md) | `syntek-webhooks` — Outbound & Inbound Webhooks | 8      | Should | US015 ✓, US006 ✓, US090 ✓          |
| [US091](../STORIES/US091.md) | `syntek-legal` — Legal Document Management      | 8      | Must   | US009 ✓, US010 ✓, US013 ✓, US090 ✓ |

## Notes

- ⚠️ 16 points exceeds sprint capacity. US020 and US091 are fully independent — no shared models, no
  shared files, no runtime dependencies. The over-capacity is acceptable given the parallel workload
  split.
- **Track A (US020 — Webhooks)**: `OutboundWebhookEndpoint`, `OutboundWebhookSubscription`,
  `DeliveryAttempt`, `DeliveryDeadLetter`, `InboundWebhookEndpoint`, inbound HMAC verification,
  outbound HMAC signing, retry Celery task with exponential back-off, DLQ, `syntek-bus` `syntek-bus`
  auto-subscription
- **Track B (US091 — Legal)**: `LegalDocumentType`, `LegalDocumentVersion`, `UserLegalAcceptance`,
  version immutability, `check_acceptance()`, `LegalReacceptanceRequired`, GraphQL enforcement
  extension, grace period config, GDPR SAR/erasure hooks
- **US020 moved from Sprint 19**: originally paired with US039 (api-keys), but now depends on US090
  (`syntek-bus`, Sprint 19) — moved here to preserve correct dependency ordering.
- **US020 campaign events**: all `syntek-email-marketing` domain events are automatically dispatched
  to registered webhook endpoints without any configuration in US038. The `syntek-bus` →
  `syntek-webhooks` pipeline handles this transparently.
- **US091 enforcement mode**: `ENFORCEMENT_MODE = 'error'` raises a GraphQL typed error on
  non-accepted users; `'redirect'` redirects to the acceptance page; `'none'` disables enforcement
  for testing. The acceptance grace period (`ACCEPTANCE_GRACE_PERIOD_DAYS`) prevents a new T&C
  version from immediately blocking all users.
- **US091** `UserLegalAcceptance` records are retained on GDPR erasure (contractual evidence) — only
  `ip_hash` and `user_agent_hash` are anonymised.
