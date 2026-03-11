# Sprint 12 — Email Core

**Sprint Goal**: Implement the central email engine — multi-provider sending abstraction (SendGrid,
Mailgun, SMTP), versioned template management, Jinja2 rendering, delivery event tracking via
webhooks, bounce and complaint auto-suppression, and the unsubscribe pipeline.

**Total Points**: 13 / 11 ⚠️ OVER CAPACITY **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                                    | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | -------------------------------------------------------- | ------ | ------ | ------------------------- |
| [US112](../STORIES/US112.md) | `syntek-email-core` — Email Engine & Template Management | 13     | Must   | US010 ✓, US011 ✓, US015 ✓ |

## Notes

- US112 is a single cohesive story — the provider abstraction, template versioning, suppression
  logic, and webhook pipeline are tightly coupled and cannot be split cleanly.
- **Execution order note:** Sprint 12 is positioned early (after Sprint 11) so that Sprint 15
  (`syntek-notifications-email`, US087) has its sending infrastructure available. US087 depends on
  US112. US038 (`syntek-email-marketing`, Sprint 31) also depends on US112 for template management
  and bulk sending.
- The `SMTP` backend provides no webhook events — open/click tracking is unavailable with SMTP.
  Consumers using SMTP should set `TRACK_OPENS = False` and `TRACK_CLICKS = False`.
- `publishEmailTemplate` creates an immutable `EmailTemplateVersion` snapshot. Only published
  templates may be sent via `sendEmail` or `sendBulkEmail`.
- `provider_event_id` deduplication prevents webhook replays from creating duplicate EmailEvent
  records — this is critical for SendGrid which may deliver the same event multiple times.
- Unsubscribe links are HMAC-signed — tampered or expired links must return a 400 with no state
  change.
