# Reporting Issues — syntek-modules

**Last Updated:** 08/03/2026 | **Maintained By:** Syntek Development Team

---

## Table of Contents

- [Before Reporting](#before-reporting)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)
- [Security Vulnerabilities](#security-vulnerabilities)
- [Where to Report](#where-to-report)

---

## Before Reporting

Before opening an issue:

1. **Search existing issues** — the issue may already be reported and have a fix in progress
2. **Check the latest version** — confirm you are on the most recent release (`VERSION` at repo
   root)
3. **Read the docs** — check `docs/GUIDES/GETTING-STARTED.md` and `.claude/CLI-TOOLING.md` first
4. **Reproduce it** — confirm the issue occurs consistently with a minimal test case

---

## Bug Reports

Use the bug report template when opening an issue. Include:

### Required information

| Field                   | What to provide                                              |
| ----------------------- | ------------------------------------------------------------ |
| **Version**             | Contents of the `VERSION` file                               |
| **OS / Platform**       | e.g., Ubuntu 24.04, macOS 15, Windows 11 (WSL2)              |
| **Layer**               | Which layer is affected: Python / TypeScript / Rust / Mobile |
| **Package**             | Which module or package, e.g. `syntek-auth`, `@syntek/ui`    |
| **Steps to reproduce**  | Numbered steps from a clean state                            |
| **Expected behaviour**  | What should have happened                                    |
| **Actual behaviour**    | What actually happened                                       |
| **Logs / error output** | Full stack trace or terminal output                          |

### Template

```markdown
## Bug Report

**Version:** (contents of VERSION file) **OS:** (e.g. Ubuntu 24.04) **Layer:** (Python / TypeScript
/ Rust / Mobile) **Package:** (e.g. syntek-auth)

### Steps to Reproduce

1.
2.
3.

### Expected Behaviour

### Actual Behaviour

### Logs / Error Output
```

---

## Feature Requests

Feature requests should align with an existing or new user story. Before requesting:

- Check `docs/STORIES/OVERVIEW.md` — the feature may already be planned
- Check `docs/SPRINTS/OVERVIEW.md` — it may be scheduled for a future sprint

When opening a feature request, describe:

- **The problem** you are trying to solve (not the solution)
- **Who it affects** — which projects or teams would benefit
- **Rough scope** — is this a small enhancement or a new module?

Feature requests that are accepted will be converted into user stories and scheduled in a sprint.

---

## Security Vulnerabilities

**Do not open a public issue for security vulnerabilities.**

Report security issues privately to:

**Email:** `security@syntek-studio.com`

Include:

- A description of the vulnerability
- Steps to reproduce or a proof-of-concept
- The affected version(s)
- Any suggested mitigations

We aim to acknowledge security reports within 2 working days and provide a fix timeline within 7
working days.

---

## Where to Report

| Type             | Where                                             |
| ---------------- | ------------------------------------------------- |
| Bug report       | GitHub Issues or Forgejo Issues (when live)       |
| Feature request  | GitHub Issues or Forgejo Issues (when live)       |
| Security issue   | `security@syntek-studio.com` (private email only) |
| General question | GitHub Discussions or `dev@syntek-studio.com`     |
| Feedback         | See `docs/GUIDES/FEEDBACK.md`                     |

> **GitHub:** [github.com/Syntek-Dev/syntek-modules](https://github.com/Syntek-Dev/syntek-modules)\
> **Forgejo (coming soon):**
> [git.syntek-studio.com/syntek/syntek-modules](https://git.syntek-studio.com/syntek/syntek-modules)
