# Syntek Ecosystem — Architecture Overview

This document describes the full Syntek ecosystem: how each repository fits into the whole, how they relate to one another, and the principles that govern their design. Every repository in the Syntek organisation contains this file so that any developer — whether working on infrastructure, a client project, or an internal product — can understand the complete picture before diving into a single repo.

---

## Table of Contents

1. [Guiding Principles](#guiding-principles)
2. [Repository Map](#repository-map)
3. [Repository Descriptions](#repository-descriptions)
   - [syntek-infrastructure](#syntek-infrastructure)
   - [syntek-modules](#syntek-modules)
   - [syntek-platform](#syntek-platform)
   - [syntek-ai](#syntek-ai)
   - [syntek-extensions](#syntek-extensions)
   - [syntek-saas](#syntek-saas)
   - [syntek-licensing](#syntek-licensing)
   - [syntek-docs](#syntek-docs)
   - [syntek-templates](#syntek-templates)
   - [syntek-premium](#syntek-premium)
   - [syntek-store](#syntek-store)
   - [syntek-marketplace](#syntek-marketplace)
4. [AI Products](#ai-products)
5. [Data Flow & Integration Map](#data-flow--integration-map)
6. [Licensing & Access Model](#licensing--access-model)
7. [Self-Hosting](#self-hosting)
8. [Technology Stack Summary](#technology-stack-summary)
9. [Development Conventions](#development-conventions)

---

## Guiding Principles

- **Open core.** The platform itself is free and self-hostable. Revenue comes from extensions, premium templates, licensed modules, and managed hosting — not from locking up the foundation.
- **Modules are the foundation.** `syntek-modules` is the shared building block layer. Every Syntek-built product — platform, extensions, templates, saas products — is built on top of modules, not the other way around.
- **Composability first.** Every piece — modules, extensions, AI rules, templates — is designed to be independently usable and combinable without tight coupling.
- **Configuration over code.** Styling is token-based, settings are schema-driven, and behaviour is declared rather than hard-coded wherever possible.
- **One source of truth.** Licensing state lives in `syntek-licensing`. Documentation lives in `syntek-docs`. Infrastructure state lives in `syntek-infrastructure`. No duplication.
- **Syntek clients get everything.** Any paid client of Syntek Studio has access to all extensions and premium templates as part of their managed package. The licensing system enforces this automatically.
- **Self-hosting is a first-class concern.** Developers can run the entire stack on their own infrastructure without any dependency on Syntek's Hetzner server. Syntek's server is for Syntek's own managed clients only.
- **Community revenue sharing.** Third-party developers can publish modules, templates, and extensions to the Syntek Store and receive the full sale price minus payment processing fees. Syntek does not take a platform cut.

---

## Repository Map

```
Syntek Organisation
│
├── syntek-infrastructure     # NixOS / Hetzner — hosts Syntek-managed client services only
│
├── syntek-modules            # Foundation: reusable npm + Python packages (Apache 2.0)
│   │                         # All other Syntek products build on top of this
│   ├── syntek-platform       # Free, self-hostable CMS core (AGPL v3)
│   │   ├── syntek-extensions # Paid add-ons for the platform (commercial license)
│   │   ├── syntek-templates  # Free starter templates
│   │   └── syntek-premium    # Paid premium starter templates
│   └── syntek-saas           # Internal: Syntek-owned SaaS UI products
│
├── syntek-ai                 # Internal: Prompt Management, Tasks & Rules (YAML/MD)
│
├── syntek-licensing          # License management UI + PostgreSQL (Rust key server in infra)
│
├── syntek-store              # Third-party developer marketplace (sell modules/templates/extensions)
│
├── syntek-docs               # All documentation for the ecosystem
│
└── syntek-marketplace        # Internal: Claude Code plugins for Syntek development workflow
```

---

## Repository Descriptions

---

### syntek-infrastructure

**Purpose:** Declarative NixOS configuration for the Hetzner AX162-R bare-metal server. This server hosts **Syntek-managed client services only** — it is not required to use the platform or any Syntek product. Developers self-hosting `syntek-platform` run it on their own infrastructure.

**Hosts on behalf of Syntek's managed clients:**

- Per-client `syntek-platform` application runtimes (Django + Next.js OCI containers, one stack per client)
- `ai.syntekstudio.com` — the Syntek AI chatbot (public-facing; free and paid tiers)
- `syntek-ai` internal services
- `syntek-licensing` license server (Rust key generation + validation API)
- `syntek-docs` static site
- `syntek-store` application
- Supporting infrastructure: PostgreSQL, PgBouncer, Valkey, Nginx, Cloudflare Tunnels, Defguard VPN, OpenBao secrets, Vaultwarden, Mattermost, Forgejo, RustDesk, OpenCloud/Collabora, Plausible Analytics

**Key components unique to this repo:**

- `rust-tools/ai-gateway/` — Rust LLM routing, caching, rate limiting, failover
- `rust-tools/license-server/` — Rust license key generation and cryptographic validation API
- `modules/services/` — NixOS modules for every hosted service
- `n8n/workflows/` — operational automation (client provisioning, license issuance, billing)

**Key design decisions:**

- NixOS flake-based configuration for full reproducibility
- ZFS for per-client storage isolation with snapshots and encryption
- All secrets via `agenix` (boot-time) and OpenBao (runtime) — nothing committed in plaintext
- All services declared as NixOS systemd services or OCI containers
- Cloudflare Tunnels for all public-facing endpoints — no ports exposed to the internet directly

**Depends on:** Nothing. This is the foundation everything else runs on.

**Who manages this:** Syntek Studio internal team only.

---

### syntek-modules

**Purpose:** The foundational building block layer for the entire Syntek ecosystem. A monorepo of reusable, licenseable packages — npm packages (React/TypeScript), Python/PyPI packages (Django utilities), and GraphQL schema fragments — that every Syntek-built product is constructed from. Also available for any developer to use independently in their own projects.

**This is upstream of everything.** `syntek-platform`, `syntek-extensions`, `syntek-saas`, `syntek-templates`, and `syntek-premium` all consume modules as their shared component foundation. Building on modules means consistent behaviour, shared bug fixes, and faster development across all products.

**Package categories:**

| Category          | Language/Runtime         | Examples                                                       |
| ----------------- | ------------------------ | -------------------------------------------------------------- |
| Frontend UI       | React / TypeScript / npm | Form components, data tables, navigation, modals, chat widgets |
| Backend utilities | Python / Django / PyPI   | Auth helpers, file handling, API clients, task queues          |
| GraphQL           | TypeScript + Python      | Shared schema types, query builders, resolvers                 |
| React Native      | TypeScript / npm         | Mobile UI primitives, navigation patterns                      |

**Design constraints:**

- All styling uses design tokens — no hardcoded colours, sizes, or spacing. Tokens are defined within the modules package itself as the canonical default theme. All Syntek products override tokens through configuration, not by modifying this repo.
- All configuration is schema-driven via a settings object passed at initialisation
- Packages are independently versioned and publishable
- Each package declares its own license tier (free / licensed)

**Licensing tiers:**

- **Free packages (Apache 2.0):** Open source, available to anyone, usable in any project including commercial and proprietary ones
- **Licensed packages:** Require a valid developer license key verified against `syntek-licensing`; Syntek clients get access automatically as part of their managed package

**Depends on:** `syntek-licensing` (for licensed package verification only)

---

### syntek-platform

**Purpose:** A free, open-source, **self-hostable** CMS and web application framework. Developers deploy it on their own infrastructure — their own VPS, their own NixOS server, their own Docker host — with no dependency on Syntek's servers whatsoever. Analogous in scope to WordPress, but built for modern Python/TypeScript developers targeting Django and Next.js.

**Self-hosting is fully supported and encouraged.** Syntek's Hetzner server hosts instances for Syntek's own managed clients. Any developer can run an identical stack independently.

**Core capabilities:**

- Multi-site management from a single installation
- Django backend with a GraphQL API layer (Strawberry)
- Next.js frontend with SSR/SSG support; Next.js `.next` output handles all static file caching and asset minification
- React Native (Expo) mobile frontend — mobile editing and content management are first-class capabilities alongside web
- Built-in user/role/permission management
- Page builder with block-based content modelling
- Cloudinary for all media (images, video) — metadata stored in PostgreSQL, assets served via Cloudinary CDN
- MinIO for document storage only (PDFs, spreadsheets, office files) — presigned URLs for access; not used for images or static assets
- Extension hook system (consumed by `syntek-extensions` and third-party extensions from `syntek-store`)
- Template loader (integrates `syntek-templates`, `syntek-premium`, and `syntek-store` templates)
- Module loader (integrates `syntek-modules` packages)
- AI hook system (delegates to `syntek-ai` if configured, or accepts developer-supplied bot configs and API keys)
- License validation client (calls `syntek-licensing` API to gate paid features)

**Free tier includes:**

- Full platform core with no feature restrictions
- All free templates from `syntek-templates`
- All free modules from `syntek-modules`
- AI bot execution engine — developers bring their own bot configs and LLM API keys
- Provider interface for all integrations — developers wire up their own Plausible, Sentry, etc.

**Paid features surface via:**

- `syntek-extensions` (individually purchasable extensions)
- `syntek-premium` (paid starter templates)
- Licensed tiers of `syntek-modules` packages
- Extensions purchased from `syntek-store` (third-party community extensions)

**Built-in AI assistant:** The platform ships with an AI assistant for two audiences — developers (code help, debugging, generator scaffolding, available online or via the `infra ai code` CLI offline) and end-users building content (SEO suggestions, styling guidance, copy writing, content generation). A free tier is included with the platform core. Higher-usage tiers (more requests, more capable models, advanced features) are gated via `syntek-licensing`. Bot configurations for the platform assistant are provided by `syntek-ai` and can be overridden by developers supplying their own configs. Full detail: `docs/PLANS/PLAN-SYNTEK-AI-AND-MULTI-TENANCY.md` and `docs/PLANS/AI-LICENSING-REPO-SEPARATION.md`.

**License:** AGPL v3. Modifications to the platform must be shared. Agencies that need a commercial license (to avoid AGPL obligations) purchase one from Syntek — as the copyright holder, Syntek can offer dual licensing.

**Stack:** Django 6.0.4, Python 3.14.3, PostgreSQL 18.3, GraphQL (Strawberry), Next.js 16.1.6, React 19.2, TypeScript 5.9, Tailwind CSS 4.2 (token-based), React Native 0.84.x (Expo), NativeWind 4

**Depends on:** `syntek-modules` (UI + backend building blocks), `syntek-licensing` (to gate paid features), `syntek-ai` (AI hooks, optional), `syntek-docs` (developer reference)

---

### syntek-ai

**Purpose:** Syntek-owned internal knowledge layer. Pure declarative files — no executable code. YAML bot definitions, markdown system prompts, YAML rule/guardrail definitions, and tool configuration files. This is where Syntek's domain expertise (ministry, charity, SME operations) is encoded as a product that the platform's AI module loads at runtime.

**The three AI layers across the ecosystem:**

| Repository              | Role          | Responsibility                                                                                          |
| ----------------------- | ------------- | ------------------------------------------------------------------------------------------------------- |
| `syntek-infrastructure` | **Engine**    | Rust AI Gateway: routing, caching, rate limiting, failover, cost tracking                               |
| `syntek-platform`       | **Brain**     | Django AI module: bot config loading, conversation state, RAG pipeline, tool execution, prompt assembly |
| `syntek-ai`             | **Knowledge** | YAML bot definitions, markdown prompts, safeguarding rules, domain expertise                            |

**Two AI-powered products powered by this layer:**

1. **`ai.syntekstudio.com` chatbot** — public-facing ChatGPT-style chatbot. Free anonymous tier (rate-limited, Claude Haiku) as a lead-generation tool for Syntek services. Paid tiers unlock higher usage, more capable models, and persistent conversation history. Multi-tenant: each Syntek client gets their own branded workspace. Full detail: `docs/PLANS/PLAN-SYNTEK-AI-AND-MULTI-TENANCY.md`.

2. **`syntek-platform` AI assistant** — embedded within the platform for developers (coding help, scaffolding, debugging) and content editors (SEO, styling guidance, copy writing, content generation). Free tier included with the platform. Paid tiers via `syntek-licensing` unlock higher usage and more capable models.

**Why pure files, not code:**

Bot configurations are deliberately framework-agnostic. A youth worker with some technical confidence can tweak a system prompt in a markdown file without touching Python or Rust. Configs are version-controlled, reviewable in pull requests, and portable to any system that can read YAML and markdown.

**Pre-built bot products (sold via syntek-store):**

- Youth Ministry Bot — crafted prompts, safeguarding rules, age group filtering
- Church Admin Bot — meeting notes, communication drafts, pastoral task management
- Charity Fundraising Bot — grant application assistance, donor communication, impact reporting

**Custom agent format:** The same YAML/markdown format used here is what developers produce when building custom agents with the AI Agent & Plugin Builder extension. Custom agents are loaded by the exact same Django AI module and Rust gateway — there is no separate runtime for community-built agents. Developers who prefer to write configs by hand without the builder UI can do so; the format is the contract, not the tool.

**Access model:** Internal service. Not directly accessible by external developers. `syntek-platform`'s Django AI module loads configs from this repo at startup or on demand. Developers building on `syntek-platform` can supply their own bot configs and API keys — they do not need access to this repo.

**Stack:** YAML, Markdown. No code. Loaded by `syntek-platform`'s Django AI module.

**Depends on:** Nothing. Pure data files.

---

### syntek-extensions

**Purpose:** Individually purchasable extensions that add significant functionality to `syntek-platform`. Each extension is its own commercial product. All extensions are included automatically for Syntek-managed clients.

**Built on `syntek-modules`.** Every extension uses modules as its shared component foundation rather than implementing UI components or backend utilities from scratch. This ensures consistency and reduces development time.

**Examples:**

- E-commerce (product catalogue, cart, checkout via Stripe/Square/GoCardless)
- Membership and subscriptions
- Events and bookings
- Advanced forms and surveys
- Email marketing integration
- Analytics dashboard (Plausible integration)
- Observability suite (Grafana + GlitchTip)
- n8n workflow integration
- Multi-site management
- White-labelling
- Payment and donations (Stripe, GoCardless, Square, gift aid for UK charities)
- Social media post tracking
- **AI Agent & Plugin Builder** — see below

**AI Agent & Plugin Builder:**

A paid extension that gives developers a visual interface to build, test, and deploy custom AI agents and plugins in the same YAML/markdown format used by `syntek-ai`. Once built, a custom agent can be deployed to any AI surface in the ecosystem:

- `infra ai` CLI (developer tooling in the Nix devshell)
- Platform AI assistant (coding help, content editing)
- Email AI (tone, drafting, replies)
- Docs AI (documentation generation and improvement)
- Calendar AI (natural language scheduling)
- `ai.syntekstudio.com` chatbot (as a named assistant)
- Customer website chatbot (via the `syntek-modules` ChatWidget — the agent pairs directly with the widget, giving developers a complete branded AI chatbot for client sites out of the box)

Custom agents built with the builder follow the same YAML/markdown format as `syntek-ai` configs — they are loaded by the same Django AI module, use the same Rust gateway, and benefit from the same caching and rate limiting. Developers can sell their finished agents and plugins in `syntek-store`.

**Architecture pattern:**

- Each extension is a self-contained Django app + optional Next.js component chunk
- Extensions register themselves via the platform's hook system — they never modify platform core files
- Each extension declares its required `syntek-modules` as dependencies
- Licensing is checked at activation time via `syntek-licensing`

**Licensing model:** Per-developer annual license. One payment covers unlimited client installations. Syntek clients have all extensions included automatically.

**Depends on:** `syntek-platform` (hook system), `syntek-modules` (building blocks), `syntek-licensing` (entitlement checks), `syntek-ai` (where AI features are used)

---

### syntek-saas

**Purpose:** Syntek-owned repository for standalone SaaS products that Syntek builds and operates — email UI kits, app UI kits, web UI kits, and future standalone tools.

**Inherits from `syntek-modules`.** `syntek-saas` products are built using modules as their component foundation, exactly as any other Syntek product. `syntek-saas` does not define the design token system — it consumes and optionally extends it. There is no upstream dependency from modules to saas.

**Contains:**

- Email UI product (web-based email client built on `syntek-modules` React components)
- App UI kit (React Native, built on `syntek-modules` React Native packages)
- Web UI kit (Next.js, built on `syntek-modules` React components)
- Prototype SaaS products in early development

**Access model:** Internal to Syntek Studio. Products may be offered to Syntek clients or sold independently.

**Depends on:** `syntek-modules` (building blocks and design tokens)

---

### syntek-licensing

**Purpose:** License management for the Syntek ecosystem. Provides the developer-facing portal UI, the admin interface for Syntek to manage licenses, and the PostgreSQL database that is the source of truth for all entitlements.

**Split architecture — two components, two repos:**

| Component         | Repo                                                   | Description                                                                   |
| ----------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------- |
| License portal UI | `syntek-licensing`                                     | Django + Next.js developer portal; admin UI; PostgreSQL schema and migrations |
| Rust key server   | `syntek-infrastructure` (`rust-tools/license-server/`) | Cryptographic key generation and validation API; NixOS deployment             |

The Rust key server handles the security-critical cryptographic operations and high-volume validation requests. The Django application handles the business logic, developer accounts, and the human-facing portal. They communicate internally on the Hetzner server.

**Developer portal features:**

- View purchased licenses (extensions, modules, templates)
- Retrieve license keys
- Manage renewals
- View installation count (informational — not a hard limit)

**Admin features (Syntek internal):**

- Issue and revoke licenses
- View all developer accounts and their entitlements
- Manage Syntek client all-access accounts
- Monitor usage and renewal pipeline

**Licensing model enforced:**

- **Per-developer annual license** — one license key per developer per extension/module/template tier, valid for unlimited client installations
- **Syntek clients** — all-access entitlement automatically applied; no individual purchases needed
- **Validation is online** — extensions call the Rust validation API at activation time. If the API is unreachable, the last known entitlement state is cached with a 24-hour TTL so a brief outage does not take client sites down.

**n8n integration (in `syntek-infrastructure`):**

- Payment confirmed → n8n generates license key via Rust API → stores record → emails developer
- Renewal reminder emails (30 days, 7 days before expiry)
- Expired license → automatic revocation via Rust API

**Stack:** Django + Next.js (portal UI), PostgreSQL (hosted on `syntek-infrastructure`)

**Depends on:** `syntek-infrastructure` (Rust key server, hosting), `syntek-modules` (UI components for the portal)

---

### syntek-docs

**Purpose:** Canonical documentation for the entire Syntek ecosystem — platform setup, module API reference, extension development guide, template development guide, and licensing documentation.

**Contains:**

- Getting started guides for self-hosted platform developers
- API reference for `syntek-modules` (npm + PyPI)
- Extension development guide (building, testing, submitting to `syntek-store`)
- Template development guide (building, submitting to `syntek-store`)
- `syntek-ai` task and prompt reference (public-facing portion only)
- Infrastructure runbooks (internal, restricted section)
- Licensing, billing, and renewal documentation
- Changelogs per product

**Format:** Markdown source, rendered as a static documentation site (Docusaurus or equivalent) deployed to `syntek-infrastructure`.

**Contribution model:**

- Platform core changes must include a docs update in the same PR
- Extension or template authors must submit docs before their product is listed in `syntek-store`
- All public API changes are documented before release

**Depends on:** Nothing. All other repos link to this one.

---

### syntek-templates

**Purpose:** Curated free starter templates for `syntek-platform` developers. Each template is a complete, working starting point — pages, content structure, and styling — that developers clone and customise.

**Built on `syntek-modules`.** Templates use module UI components and the module design token system for all styling. No custom CSS is required — all styling overrides go through token configuration.

**Template types:**

- Church and ministry websites
- Charity and non-profit websites
- Small business landing pages
- Portfolio sites
- Event and campaign microsites

**Technical structure:**

- Each template: Django fixtures (initial content/pages), Next.js page components, manifest file declaring required modules and minimum platform version
- Zero custom CSS — token overrides only

**Access model:** Free. No license required. Available to all `syntek-platform` users.

**Third-party templates:** Community developers can publish free templates to `syntek-store`. They follow the same manifest and structure format as official templates.

**Depends on:** `syntek-platform` (runtime), `syntek-modules` (UI components and design tokens)

---

### syntek-premium

**Purpose:** Paid premium starter templates. More polished designs, more page types, and more advanced content structures than the free tier. Ongoing updates and support from Syntek.

**Built on `syntek-modules`.** Identical technical structure to `syntek-templates` — same manifest schema, same module and token system. The only difference is the licensing gate.

**Difference from `syntek-templates`:**

- Higher design quality and complexity
- More page types per template (blog, events, shop stubs, membership area)
- May include pre-configured extension stubs ready to activate with a valid extension license
- Ongoing Syntek support and updates

**Access model:**

- Individual developers: per-developer annual license (unlimited client installations)
- Syntek clients: all premium templates included automatically
- Entitlement verified via `syntek-licensing` at download/install time

**Third-party premium templates:** Community developers can sell premium templates via `syntek-store`. They define their own price and receive the full sale amount minus Square processing fees.

**Depends on:** `syntek-platform`, `syntek-modules`, `syntek-licensing`

---

### syntek-store

**Purpose:** The community marketplace where third-party developers publish and sell their own modules, templates (free and premium), and extensions for the Syntek ecosystem. Syntek does not take a platform cut — developers receive the full sale price minus Square payment processing fees.

**What developers can list:**

- npm packages extending `syntek-modules`
- PyPI packages extending the platform backend
- Free templates (same format as `syntek-templates`)
- Premium templates (same format as `syntek-premium`, developer sets the price)
- Extensions (same hook system as `syntek-extensions`, developer sets the price)
- Custom AI agents and plugins (YAML/markdown configs built with the AI Agent & Plugin Builder or by hand, deployable to any AI surface in the ecosystem)

**Revenue model:**

- Free listings: no cost to list, no revenue
- Paid listings: developer receives 100% of sale price minus Square processing fees (~1.4% + 25p for UK cards)
- Syntek takes no platform percentage — the goal is ecosystem growth, not store revenue

**Requirements to list a paid product:**

- Passes automated compatibility check (correct manifest format, declared platform version, declared module dependencies)
- Documentation submitted to `syntek-docs` or hosted in the listing itself
- For extensions: passes a basic security review by Syntek before listing

**Developer accounts:**

- Linked to `syntek-licensing` — purchasing a listing auto-issues a license key via the Rust key server
- Revenue dashboard showing earnings, sales, and payout history
- Square-based payouts

**Stack:** Django + Next.js, PostgreSQL, Square payments API

**Depends on:** `syntek-licensing` (license key issuance on purchase), `syntek-modules` (UI components), `syntek-infrastructure` (hosting)

---

### syntek-marketplace

**Purpose:** Internal Syntek Studio development tooling. Houses the Claude Code plugins used by the Syntek development team to accelerate work across all repositories.

**Contains:**

- `syntek-dev-suite` Claude Code plugin — user stories, sprints, git workflow, code review, and all general development skills
- `syntek-infra-plugin` Claude Code plugin — NixOS configuration, secrets management, deployment, Wireguard, Hyprland

**Access model:** Internal to Syntek Studio. Not published or available to external developers.

**Depends on:** Nothing. Pure configuration and prompt files.

---

## AI Products

Syntek's AI capability surfaces in two distinct products, both powered by the same three-layer architecture (`syntek-infrastructure` engine → `syntek-platform` brain → `syntek-ai` knowledge).

### ai.syntekstudio.com — Public Chatbot

A public-facing ChatGPT-style chatbot serving as a lead-generation and brand-building tool. The goal is for people to interact with Syntek's AI, experience the quality of what Syntek builds, and consider Syntek for MSP, web, app, server, or networking services.

| Tier                 | Access            | Models                   | Limits                                                                   |
| -------------------- | ----------------- | ------------------------ | ------------------------------------------------------------------------ |
| **Free (anonymous)** | No login required | Claude Haiku only        | 5 msg/conversation, 10/hr, 50/day per IP. Conversations purged after 24h |
| **Paid tiers**       | Account required  | Higher-capability models | Higher usage limits, persistent history, assistant library               |

Multi-tenant: each Syntek client gets a branded AI workspace at `ai.clientdomain.com`. Tenant isolation is enforced at the data layer — no client data ever crosses tenant boundaries.

### syntek-platform AI Assistant — In-Platform AI

An AI assistant embedded directly in the platform, serving two audiences:

- **Developers** — code generation, scaffolding, debugging, available both online (in the platform admin) and offline (via `infra ai code` CLI in the Nix devshell)
- **Content editors and site builders** — SEO suggestions, styling guidance, copy writing, content generation, block layout recommendations

| Tier     | Included with                            | Capability                                           |
| -------- | ---------------------------------------- | ---------------------------------------------------- |
| **Free** | Platform core (all self-hosted installs) | Basic AI assistance, rate-limited                    |
| **Paid** | Developer license via `syntek-licensing` | Higher usage, more capable models, advanced features |

### Custom AI Agents & Plugins — Community-Built AI

A third AI surface created by the developer ecosystem, not by Syntek. Developers use the **AI Agent & Plugin Builder** extension to create agents in the same YAML/markdown format as `syntek-ai`. A finished agent can be attached to any AI surface (CLI, platform assistant, email, calendar, docs, public chatbot, customer website widget) and paired with the `syntek-modules` ChatWidget to deliver a complete branded AI chatbot for any client site.

| Who builds it                            | How                                                     | Where it runs                                                            | Where it's sold                                         |
| ---------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------- |
| Any developer with the builder extension | AI Agent & Plugin Builder UI or by hand (YAML/markdown) | Any AI surface — CLI, platform, email, calendar, chatbot, website widget | `syntek-store` (developer keeps 100% minus Square fees) |

The combination of the builder extension + `syntek-modules` ChatWidget is the fastest path to a fully customised, client-branded AI chatbot — no LLM integration code required from the developer.

Full architecture and implementation detail: `docs/PLANS/PLAN-SYNTEK-AI-AND-MULTI-TENANCY.md` and `docs/PLANS/AI-LICENSING-REPO-SEPARATION.md`.

---

## Data Flow & Integration Map

```
                        ┌─────────────────────┐
                        │   syntek-modules     │  ← Foundation layer
                        │  (npm + PyPI pkgs)   │    All products build on this
                        │    Apache 2.0        │
                        └──────────┬──────────┘
                                   │ consumed by
          ┌────────────────────────┼──────────────────────┐
          ▼                        ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  syntek-platform │   │   syntek-saas    │   │ syntek-templates │
│  (CMS core)      │   │  (SaaS products) │   │ syntek-premium   │
│  AGPL v3         │   │  (internal)      │   │ (starters)       │
└────────┬─────────┘   └──────────────────┘   └──────────────────┘
         │ hook system
         ▼
┌──────────────────┐       ┌──────────────────┐
│ syntek-extensions│──────►│ syntek-licensing  │
│ + syntek-store   │       │ (entitlement API) │
│ (third-party)    │       │ ← Rust key server │
└────────┬─────────┘       │   in infra        │
         │ uses            └──────────────────┘
         ▼
┌──────────────────┐       ┌──────────────────┐
│   syntek-ai      │       │  syntek-store    │
│ (prompts, tasks, │       │  (marketplace)   │
│  rules — YAML/MD)│       └──────────────────┘
└────────┬─────────┘
         │ loaded by platform AI module
         ▼
┌──────────────────────────────────────────┐
│         syntek-infrastructure            │
│   (NixOS / Hetzner — Syntek clients)    │
│                                          │
│  rust-tools/ai-gateway/    (LLM routing) │
│  rust-tools/license-server/ (key crypto) │
└──────────────────────────────────────────┘

All documentation:
┌──────────────────┐
│   syntek-docs    │
└──────────────────┘

Internal dev tooling:
┌──────────────────────┐
│  syntek-marketplace  │
│  (Claude Code plugins│
│   for Syntek team)   │
└──────────────────────┘
```

---

## Licensing & Access Model

### Developer License Model

Licenses are **per-developer, not per installation.** A developer purchases one annual license per product (extension, licensed module tier, or premium template) and can deploy it across all their client projects with no installation limit.

| Product                              | Free users                             | Licensed devs                                  | Syntek clients        |
| ------------------------------------ | -------------------------------------- | ---------------------------------------------- | --------------------- |
| `syntek-platform` core               | ✅ Full access (AGPL)                  | ✅ Full access                                 | ✅ Full access        |
| `syntek-templates`                   | ✅ All free templates                  | ✅ All free templates                          | ✅ All free templates |
| `syntek-modules` (Apache 2.0)        | ✅ Full access                         | ✅ Full access                                 | ✅ Full access        |
| `syntek-modules` (licensed tiers)    | ❌                                     | ✅ Per-developer annual license                | ✅ All included       |
| `syntek-extensions`                  | ❌                                     | ✅ Per-developer annual license                | ✅ All included       |
| `syntek-premium` templates           | ❌                                     | ✅ Per-developer annual license                | ✅ All included       |
| `syntek-store` free listings         | ✅                                     | ✅                                             | ✅                    |
| `syntek-store` paid listings         | ❌                                     | ✅ Per-developer annual license                | ✅ All included       |
| `syntek-ai` pre-built bots           | ❌                                     | ✅ Per-developer annual license                | ✅ Included quota     |
| `ai.syntekstudio.com` free tier      | ✅ Anonymous, rate-limited, Haiku only | ✅                                             | ✅                    |
| `ai.syntekstudio.com` paid tiers     | ❌                                     | ✅ Subscription (higher usage, capable models) | ✅ Included           |
| Platform AI assistant (free tier)    | ✅ Basic usage included with platform  | ✅ Basic usage included                        | ✅ Full quota         |
| Platform AI assistant (paid tiers)   | ❌                                     | ✅ Per-developer license (higher usage/models) | ✅ Included           |
| AI Agent & Plugin Builder extension  | ❌                                     | ✅ Per-developer annual license                | ✅ Included           |
| Community agents from `syntek-store` | ❌ (free listings only)                | ✅ Per listing (developer sets price)          | ✅ Included           |

### Non-Profit Pricing

Churches and charities receive approximately 50% off all paid products. Word-of-mouth within faith and charity networks is the primary growth channel — a community discount that enables recommendations is worth more than the lost margin.

### License Validation Behaviour

Validation is online via the Rust key server at `license.syntekstudio.com`. If the API is unreachable, the last known entitlement state is cached with a 24-hour TTL so a brief outage does not affect live client sites.

---

## Self-Hosting

`syntek-platform` is fully self-hostable. Developers deploy it on their own infrastructure — a VPS, a home server, a NixOS machine, a Docker host — with no dependency on Syntek's Hetzner server.

**What self-hosted developers need:**

- PostgreSQL
- Redis or Valkey (for caching and queues)
- A process manager (systemd, Docker Compose, or NixOS OCI containers)
- An LLM API key (Anthropic, OpenAI, or any supported provider) if using AI features
- Their own license key from `syntek-licensing` for any paid extensions or modules (validation calls `license.syntekstudio.com`)

**What self-hosted developers do NOT need:**

- Access to Syntek's Hetzner server
- Defguard VPN
- OpenBao
- Any Syntek internal service

**Syntek's Hetzner server** manages infrastructure for Syntek's own paying clients only. It is not a shared hosting platform for platform developers.

---

## Technology Stack Summary

| Layer                                     | Technology                                                            |
| ----------------------------------------- | --------------------------------------------------------------------- |
| Infrastructure                            | NixOS, Hetzner AX162-R, ZFS, Cloudflare Tunnels, agenix, OpenBao      |
| License key crypto                        | Rust (`rust-tools/license-server/`)                                   |
| AI LLM routing                            | Rust (`rust-tools/ai-gateway/`)                                       |
| Backend (platform, extensions, licensing) | Python 3.14.3, Django 6.0.4, PostgreSQL 18.3, Celery                  |
| API layer                                 | GraphQL (Strawberry), Django REST Framework (licensing/internal APIs) |
| Frontend                                  | Next.js 16.1.6, React 19.2, TypeScript 5.9, Tailwind CSS 4.2 (token-based) |
| Static files / asset pipeline             | Next.js `.next` output — caching, bundling, and minification          |
| Mobile                                    | React Native 0.84.x (Expo), NativeWind 4, TypeScript 5.9              |
| Media (images, video)                     | Cloudinary — metadata in PostgreSQL, assets served via Cloudinary CDN |
| Documents (PDFs, office files)            | MinIO — presigned URLs; not used for images or static assets          |
| Package distribution                      | PyPI (Python packages), npm (TypeScript/JS packages)                  |
| Payments                                  | Square (developer store + licensing renewal)                          |
| Documentation                             | Markdown → Docusaurus static site                                     |
| Secrets                                   | agenix (NixOS boot-time), OpenBao (runtime)                           |
| VPN                                       | Defguard (WireGuard-based, Syntek internal only)                      |
| Operational automation                    | n8n (hosted on `syntek-infrastructure`)                               |

---

## Development Conventions

- **Modules are the foundation.** Before building a UI component or backend utility in any product repo, check if it belongs in `syntek-modules` first. If two products would need the same thing, it goes in modules.
- **Design tokens, not hardcoded values.** Never hardcode a colour, font size, spacing, or shadow value in any product. Always reference a design token. The token default values are defined in `syntek-modules` and overridden through configuration in consuming products.
- **Settings schema.** Every module and extension must expose a typed settings schema. Configuration is always explicit, never implicit.
- **Per-developer licensing.** Licenses are issued to the developer, not to individual client installations. The key server tracks developer entitlements, not deployment counts.
- **Licensing checks are non-blocking on failure.** If `syntek-licensing` is unreachable, licensed features degrade gracefully using the 24-hour cached entitlement state. A licensing outage must never take down a live client site.
- **Self-hosting is a first-class concern.** Any change to `syntek-platform` that would make it harder to self-host without Syntek's infrastructure is a breaking change and requires explicit justification.
- **Docs are not optional.** No feature ships without a corresponding entry in `syntek-docs`. PRs that add or change public APIs must include a docs update. Products listed in `syntek-store` must have documentation before listing.
- **Store listings require a security review.** Third-party extensions that use the platform hook system must pass a Syntek security review before being listed in `syntek-store`. Free modules and templates require format validation only.
- **Infrastructure is immutable.** Changes to `syntek-infrastructure` go through a PR and are applied via `nixos-rebuild` against a staging environment before production. No ad-hoc server changes.
- **Monorepo within repos.** `syntek-modules` and `syntek-extensions` use a monorepo structure internally. Each package or extension is independently versioned following semver.
- **Secrets never in git.** All secrets are managed via `agenix` in `syntek-infrastructure` or passed as environment variables in CI. Never committed to any repository.
- **Community revenue sharing.** When adding payment flows to `syntek-store`, the developer receives 100% minus Square processing fees. Do not introduce a Syntek platform percentage.

---

_This document is maintained by Syntek Studio. For corrections or additions, open a PR against the relevant repository and update this file accordingly. The canonical version of this document lives in each repository root._
