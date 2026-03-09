# Security Policy

**Maintained By:** Syntek Development Team\
**Language:** British English (en_GB)

---

## Supported Versions

Security fixes are applied to the **latest released version** of each module only. Older versions do
not receive backported patches.

| Version | Supported |
| ------- | --------- |
| Latest  | Yes       |
| Older   | No        |

---

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Use GitHub's **private vulnerability reporting** feature to disclose vulnerabilities confidentially:

1. Go to the [Security tab](../../security) of this repository.
2. Click **Report a vulnerability**.
3. Fill in the details — what you found, how to reproduce it, and the potential impact.

We will acknowledge your report within **3 business days** and aim to provide an initial assessment
within **7 business days**.

If you are unable to use private vulnerability reporting, email: **<security@syntek-studio.com>**

Please include:

- A clear description of the vulnerability
- Steps to reproduce (proof of concept if possible)
- The affected package(s) and version(s)
- Your assessment of severity and impact

---

## Response Timeline

| Stage                  | Target timeframe           |
| ---------------------- | -------------------------- |
| Acknowledgement        | 3 business days            |
| Initial assessment     | 7 business days            |
| Fix or mitigation plan | 30 days (critical: 7 days) |
| Public disclosure      | After fix is released      |

We follow coordinated disclosure. We will keep you informed throughout the process and credit you in
the security advisory unless you prefer to remain anonymous.

---

## Scope

### In scope

- All packages under `packages/backend/` (Django / Python)
- All packages under `packages/web/` (React / TypeScript)
- All packages under `mobile/` (React Native)
- All Rust crates under `rust/` (encryption layer)
- Shared types and GraphQL operations under `shared/`

### Out of scope

- Vulnerabilities in third-party dependencies (report to the upstream maintainer; we will apply
  patches as they are released)
- Issues in downstream consuming projects that are not caused by a flaw in this library
- Social engineering or phishing attacks
- Denial-of-service attacks

---

## Security Standards

This library is built to the following standards:

| Standard        | Scope                                           |
| --------------- | ----------------------------------------------- |
| OWASP Top 10    | All packages                                    |
| NIST SP 800-132 | Password hashing (Argon2id)                     |
| NIST SP 800-38D | Field-level encryption (AES-256-GCM)            |
| FIPS 198-1      | Data integrity (HMAC-SHA-256)                   |
| GDPR Article 32 | Encryption and access control for personal data |
| UK DPA 2018     | Data protection obligations                     |
| NCSC guidance   | Secure development and deployment               |

---

## Dependency Security

Dependency updates are automated via **GitHub Dependabot** for all four package stacks: Python
(pip), JavaScript (pnpm/npm), Rust (cargo), and GitHub Actions.

Critical and high severity vulnerabilities are patched within **7 days** of a fix being available
upstream. Moderate and low severity within **30 days**.

---

## Internal Security Guide

For contributors, the internal coding security standards are documented in
[`.claude/SECURITY.md`](.claude/SECURITY.md). That guide covers OWASP mitigations, authentication
rules, database security, and the Rust encryption layer.
