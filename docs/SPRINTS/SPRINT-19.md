# Sprint 19 — Internal Event Bus & API Keys

**Sprint Goal**: Implement the internal domain event bus (`syntek-events`) — the foundation for
decoupled inter-module communication and webhook fan-out — and the developer API key issuance module
with scopes and rate limiting. The outbound webhook module (`syntek-webhooks`, US020) is delivered
in Sprint 56 after this foundation is in place.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 63% / Should 37% **Status**: Planned

## Stories

| Story                        | Title                                    | Points | MoSCoW | Dependencies Met          |
| ---------------------------- | ---------------------------------------- | ------ | ------ | ------------------------- |
| [US090](../STORIES/US090.md) | `syntek-bus` — Internal Domain Event Bus | 5      | Must   | US010 ✓, US015 ✓          |
| [US039](../STORIES/US039.md) | `syntek-api-keys` — API Key Management   | 3      | Should | US009 ✓, US010 ✓, US011 ✓ |

## Notes

- US090 and US039 are independent of each other and can be worked in parallel.
- **US090** (`syntek-bus`) is the internal event bus. It is NOT `syntek-webhooks` (US020, which
  handles external HTTP delivery). The two are complementary: US090 fires events in-process; US020
  subscribes to them and dispatches HTTP webhooks to consumer endpoints.
- **US090** must be in place before US020 (`syntek-webhooks`, Sprint 56), US038
  (`syntek-email-marketing`, Sprint 31), and US091 (`syntek-legal`, Sprint 56) — all of these fire
  domain events via the event bus.
- **US090** webhook auto-subscription: when `syntek-webhooks` is installed, it registers a global
  async subscriber in `AppConfig.ready()` — no manual wiring in US090.
- **US039** API key values must be stored as Argon2id hashes — the raw key is only shown once at
  creation.
- **US020 moved to Sprint 56**: `syntek-webhooks` (the external HTTP delivery layer) now depends on
  US090 and has been moved to Sprint 56 to preserve correct dependency ordering.
