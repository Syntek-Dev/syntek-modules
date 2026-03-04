# Syntek Modules

**Reusable, modular library of Django, React, React Native, and Rust components for Syntek projects.**

> Versioned and hosted on the Syntek Hetzner Forgejo instance.

---

## What Is This Repository?

`syntek-modules` is a library of independently installable modules that developers drop into any Syntek project. It is **not a deployable application** — it is a collection of packages.

Each module is designed to:

- Be installed on its own via `uv` / `pip` (Django), `pnpm` / `npm` (React / React Native), or `cargo` (Rust)
- Be configured through a single settings file in the consuming project (no hardcoded values)
- Be versioned independently using semantic versioning, managed via Forgejo on the Syntek Hetzner server

---

## Module Categories

### Backend (Django + Python)

Security bundles, authentication, user profiles, media, payments, accounting, notifications, search, audit logging, forms, bookings, comments, analytics, reporting, uploads, feature flags, webhooks, contact, internationalisation, and CMS primitives.

Install example:

```bash
uv pip install syntek-security-core
uv pip install syntek-authentication
uv pip install syntek-payments
```

### Web (Next.js + React + TypeScript)

Client-side security, authentication UI, profile UI, media UI, notifications, search, forms, comments, analytics, bookings, payments, webhooks, and feature flags.

Install example:

```bash
pnpm add @syntek/security-core
pnpm add @syntek/ui-auth
pnpm add @syntek/ui-payments
```

### Mobile (React Native + TypeScript + NativeWind)

Mobile security, biometric authentication, and mobile-specific counterparts to all web UI modules.

Install example:

```bash
pnpm add @syntek/mobile-auth
pnpm add @syntek/mobile-payments
```

### Shared (Cross-Platform)

TypeScript types, GraphQL operations, React hooks, utilities, and design system components shared between web and mobile. Always the first place to look before writing platform-specific code.

### Rust

High-performance encryption (AES-256-GCM), Argon2 hashing, PyO3 bindings for Django, LLM gateway, and the project CLI tool.

### GraphQL

Modular Strawberry GraphQL layers: core security, authentication, audit logging, and GDPR compliance.

---

## Configuration

Every module is controlled entirely through Django settings. Nothing is hardcoded in the frontend. Frontends fetch all configuration from Django via GraphQL.

Example Django settings:

```python
SYNTEK_SECURITY_CORE = {
    'RATE_LIMITING': {'BACKEND': 'redis', 'DEFAULT_RATE': '100/hour'},
}

SYNTEK_AUTH = {
    'PASSWORD_LENGTH': 12,
    'MFA_REQUIRED': True,
    'SESSION_TIMEOUT': 1800,
}
```

---

## Versioning

All modules are versioned using **semantic versioning** (`MAJOR.MINOR.PATCH`).

Releases are managed through **Forgejo** on the **Syntek Hetzner server**. Each module has its own version tracked independently. Changelogs are maintained per module.

---

## The Syntek Repository Ecosystem

`syntek-modules` is one of five repositories that form the Syntek development platform:

| Repository | Purpose |
|---|---|
| **syntek-infrastructure** | NixOS configuration and Rust CLI tooling for server design and provisioning |
| **syntek-modules** | *(this repo)* Reusable modular library — auth, payments, profiles, CMS, and more |
| **syntek-ai** | AI systems for Syntek infrastructure and client projects |
| **syntek-platform** | The core CMS platform — Django / GraphQL / PostgreSQL backend, React / TypeScript / Tailwind web frontend, React Native / TypeScript / NativeWind mobile frontend |
| **syntek-template** | Starter templates with Docker, CI/CD workflows, and pre-built designs for e-commerce, church, charity, SMB, estate agent, high street shop, corporate, restaurant/pub, and more |

### How They Work Together

1. **syntek-infrastructure** provisions and hardens the servers
2. **syntek-modules** provides reusable packages installed into projects
3. **syntek-ai** provides AI capabilities consumed by the platform and client projects
4. **syntek-platform** is the production-ready CMS used as the foundation for client projects
5. **syntek-template** provides starting-point templates built on top of the platform

Each client project starts from a **syntek-template**, is customised, and pulls in **syntek-modules** packages as needed — making development significantly faster across all client work.

---

## Security Compliance

All modules are built to comply with OWASP Top 10, NIST Cybersecurity Framework, NCSC Guidelines, GDPR (EU/UK), CIS Benchmarks, and SOC 2. Sensitive data is always encrypted via the Rust layer, called through Django — never directly from the frontend.

---

**Maintained by:** Syntek Development Team
**Language:** British English (en-GB)
**Versioning:** Forgejo — Syntek Hetzner Server
**Last Updated:** 04.03.2026
