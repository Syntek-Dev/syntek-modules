# Sprint 15 — Notification Email & SMS Channels

**Sprint Goal**: Implement the email and SMS notification channel adapters — SMTP/SES/SendGrid/
Mailgun email delivery with HTML templates, unsubscribe, and bounce tracking; and Twilio/Bandwidth
SMS delivery with OTP support and bulk batching.

**Total Points**: 10 / 11 **MoSCoW Balance**: Must 50% / Should 50% **Status**: Planned

## Stories

| Story                        | Title                                        | Points | MoSCoW | Dependencies Met |
| ---------------------------- | -------------------------------------------- | ------ | ------ | ---------------- |
| [US087](../STORIES/US087.md) | `syntek-notifications-email` — Email Channel | 5      | Must   | US019 ✓, US112 ✓ |
| [US088](../STORIES/US088.md) | `syntek-notifications-sms` — SMS Channel     | 5      | Should | US019 ✓          |

## Notes

- US087 and US088 are independent of each other — no shared models, no shared files. Both register
  separately with the `syntek-notifications-core` channel registry and can be developed in parallel.
- US087 depends on US019 (`syntek-notifications-core`) **and US112** (`syntek-email-core`,
  Sprint 12) — US112 provides the underlying multi-provider sending infrastructure that US087
  delegates to. Sprint 15 therefore cannot begin until both Sprint 14 and Sprint 12 are complete.
- US087 is also a dependency of US038 (`syntek-email-marketing`, Sprint 31) — its send
  infrastructure is reused by the campaign module. Sprint 31 therefore cannot begin until Sprint 15
  is complete.
- US088 OTP via SMS must integrate with `syntek-auth` (US009) — a thin hook from auth calls the OTP
  dispatch function; no circular dependency because auth depends on notifications-core, not on the
  SMS sub-module.
- Both adapters use the retry and DLQ infrastructure provided by US019 — no separate retry logic is
  needed in the adapters.
- Provider credentials (SendGrid API key, Twilio Auth Token, etc.) must always come from
  `SYNTEK_NOTIFICATIONS_EMAIL` and `SYNTEK_NOTIFICATIONS_SMS` settings — never hardcoded.
