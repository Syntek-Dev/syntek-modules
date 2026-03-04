# Coding Principles

**Last Updated**: 24/02/2026
**Version**: 1.6.0
**Maintained By**: Development Team
**Language**: British English (en_GB)
**Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [File Length](#file-length)
- [Rob Pike's 5 Rules of Programming](#rob-pikes-5-rules-of-programming)
- [Linus Torvalds' Coding Rules](#linus-torvalds-coding-rules)
- [Error Handling](#error-handling)
- [Naming Conventions](#naming-conventions)
- [Testing](#testing)
- [Comments and Documentation](#comments-and-documentation)
- [Security](#security)
- [Dependencies](#dependencies)
- [Git and Version Control](#git-and-version-control)
- [DRY vs WET — The Rule of Three](#dry-vs-wet--the-rule-of-three)
- [Logging](#logging)
- [Code Review Checklist](#code-review-checklist)

---

## Overview

These principles apply to **all code** in this project. Read and apply them before writing or reviewing any code. They are derived from two of the most influential systems programmers — Rob Pike (co-creator of Go) and Linus Torvalds (creator of Linux) — and extended with practical rules for web application development.

---

## File Length

Each coding file should be a maximum of **750 lines** with a grace of 50 lines. This includes comments. If a file exceeds 750 lines (or the grace lines), break it into modules and import them into a central file.

---

## Rob Pike's 5 Rules of Programming

> Originally from "Notes on Programming in C" (1989), cited widely in the Go community.

**Rule 1 — Don't guess bottlenecks**
You cannot tell where a programme will spend its time. Bottlenecks occur in surprising places. Do not second-guess and add speed hacks until you know where the bottleneck actually is.

**Rule 2 — Measure before tuning**
Do not tune for speed until you have measured. Even then, do not tune unless one part of the code overwhelms the rest.

**Rule 3 — Fancy algorithms are slow when N is small**
Fancy algorithms are slow when N is small, and N is usually small. Fancy algorithms have big constants. Until you know that N is frequently large, don't get fancy. Even if N does get large, apply Rule 2 first.

**Rule 4 — Fancy algorithms are buggy**
Fancy algorithms are more complex and much harder to implement correctly. Use simple, reusable, and easy-to-maintain algorithms. Use simple data structures too.

**Rule 5 — Data structures dominate**
Data dominates. If you have chosen the right data structures and organised things well, the algorithms will almost always be self-evident. Data structures are central to programming — not algorithms.

---

## Linus Torvalds' Coding Rules

> Derived from Linus Torvalds' coding style documents, talks, and mailing list contributions.

**Rule 1 — Data structures over algorithms**
*"Show me your flowcharts and conceal your tables, and I shall continue to be mystified. Show me your tables, and I won't usually need your flowcharts; they'll be obvious."*

Focus on how data is organised. A solid data model often eliminates the need for complex, messy code. The logic naturally follows from the structure.

**Rule 2 — Good taste in coding**
- Remove special cases: good code eliminates edge cases rather than adding `if` statements for them
- Simplify logic: avoid tricky expressions or complex, deeply nested control flows
- Reduce branches: fewer conditional statements make code faster and easier to reason about

**Rule 3 — Readability and maintainability**
- Short functions: functions do one thing, are short, and fit on one or two screenfuls of text
- Descriptive names: variables and functions should be descriptive but concise
- Avoid excessive indentation: deep nesting makes code hard to read

**Rule 4 — Code structure and style**
- Avoid multiple assignments on a single line
- One operation per statement — clarity beats cleverness

**Rule 5 — Favour stability over complexity**
Do not do something clever just because you can. Stability and predictability are more valuable than clever or novel approaches.

**Rule 6 — Make it work, then make it better**
Get it working first, then optimise. Do not over-optimise during initial implementation. All code should be maintainable by anyone, not just the original author.

---

## Error Handling

Prefer explicit error handling over silent failures. Never swallow an error without logging it — silent failures are the hardest class of bug to diagnose.

- Use custom exception types over generic ones. An exception that says `OrderPaymentFailed` with an order ID and reason is more actionable than a bare `Exception`.
- Every error message should answer three questions: **what** went wrong, **why** it happened, and ideally **what to do** about it.
- In PHP/Laravel, use custom exception classes and handler registration. Let exceptions bubble to the handler rather than swallowing them in service classes.
- In Python/Django, use Django's exception hierarchy and DRF's exception handling. Log unexpected exceptions to Sentry before re-raising or returning error responses.
- In TypeScript/React, use `Result`-style patterns or typed error boundaries. Never let `unknown` errors reach the UI without a fallback.
- Do not return `null` where an exception is the more honest type. Use `null` only when the absence of a value is expected and valid.
- All HTTP API errors must return structured JSON with a consistent shape: `{ "error": { "code": "...", "message": "..." } }`.

---

## Naming Conventions

Beyond Linus's "descriptive but concise" rule, follow these concrete conventions across all languages in this project:

- **Booleans** read as questions: `is_active`, `has_permission`, `can_retry`.
- **Functions and methods** are verbs: `get_user`, `validate_input`, `send_alert`.
- **Avoid abbreviations** unless universally understood in context (`url`, `id`, `cfg` are acceptable; `usr`, `mgr`, `svc` are not).
- **No single-letter variables** except in tight loops (`i`, `j`) or clear mathematical contexts.
- **PHP/Laravel:** `camelCase` for variables and methods; `PascalCase` for classes; `snake_case` for database columns and environment variables.
- **Python/Django:** `snake_case` for variables, functions, and modules; `PascalCase` for classes; `SCREAMING_SNAKE_CASE` for constants.
- **TypeScript/React:** `camelCase` for variables and functions; `PascalCase` for components, classes, and types; `SCREAMING_SNAKE_CASE` for constants; `kebab-case` for CSS classes and file names.
- **Database tables:** `snake_case`, plural nouns (e.g., `user_profiles`, `order_items`).
- **Environment variables:** `SCREAMING_SNAKE_CASE` (e.g., `DATABASE_URL`, `APP_SECRET_KEY`).

---

## Testing

Every public function, service, and API endpoint requires tests. See **[TESTING.md](TESTING.md)** for the full testing guide, patterns, and examples adapted to this project's stack.

Summary of requirements:

- Every public service method or utility function has at least one unit test.
- Every HTTP endpoint has integration tests covering the happy path, error paths, and auth failures.
- Every new database migration has a test verifying the migration runs and rolls back cleanly.
- Tests are independent — no test relies on another having run first.
- Test names describe the scenario: `test_login_fails_with_expired_token` not `test_login_2`.

---

## Comments and Documentation

Comments explain **why**, not **what**. If code needs a comment to explain what it does, rewrite the code to be clearer instead.

- **Docstrings** are mandatory on all public APIs. In PHP, use PHPDoc `/** */` blocks. In Python, use docstrings. In TypeScript, use JSDoc `/** */` comments.
- **TODO comments** must include a name or ticket reference: `// TODO(sam): remove after STORY-030 deploys`.
- Avoid commented-out code in committed files. Delete it; git history is the recovery mechanism.
- Do not restate configuration in prose. Comments should explain architectural decisions or operational constraints, not repeat what the code already says.

---

## Security

- **Never hardcode** secrets, API keys, or credentials in any file committed to this repository. All secrets live in environment variables or a secrets manager.
- **Always validate and sanitise** user input at system boundaries. Assume all external input is hostile until proven otherwise.
- **Parameterised queries** for all database access. String interpolation into SQL is never acceptable — use the ORM or prepared statements.
- **Principle of least privilege**: every service, user, role, and token has only the permissions it needs and nothing more.
- **Pin all dependencies** explicitly. Unpinned dependencies are a supply-chain risk.
- See **[SECURITY.md](SECURITY.md)** for detailed security patterns and the compliance checklist.

---

## Dependencies

Don't add a dependency for something you can write correctly in under 50 lines. Before adding any dependency, answer all five questions:

1. Can this be implemented simply without it? If yes, write it.
2. Is it actively maintained? (Recent commits, issues acknowledged and resolved)
3. Does it have a clean security track record? (Check CVE databases and `npm audit` / `pip audit` / `composer audit`)
4. Is the licence compatible? (MIT, Apache 2.0, ISC are acceptable; GPL requires careful review)
5. Is the version pinned explicitly? Never use unbounded version ranges.

In PHP, pin exact versions in `composer.json`. In Python, pin in `requirements.txt` or `pyproject.toml`. In TypeScript, use exact versions in `package.json` and commit lock files.

---

## Git and Version Control

- **Atomic commits**: each commit does exactly one thing. Mixed concerns belong in separate commits.
- **Conventional Commits format**: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`. Subject line under 72 characters. Body explains the reasoning and context, not the diff.
- **Never commit** generated files, secrets, `.env` files, or environment-specific configuration.
- **Branch naming** follows `<story-id>/<short-description>`: `us028/stripe-payments`.
- **Pull requests** require a description explaining what changed and why, with a reference to the story ID.
- Force-push is only permitted on personal feature branches before a PR is opened, never after.

---

## DRY vs WET — The Rule of Three

Don't abstract prematurely. Duplication is acceptable the first and second time you write something. On the **third occurrence**, refactor into a shared abstraction.

The wrong abstraction is worse than duplication: a premature abstraction forces every future use into a shape that doesn't quite fit, creating complexity that's painful to undo. Three clear, slightly repetitive implementations are preferable to one clever abstraction that obscures intent.

Extract a shared function, service, component, or utility when the same logic appears in three or more places.

---

## Logging

Log at the appropriate level for the audience and severity:

| Level     | Use for                                                        |
| --------- | -------------------------------------------------------------- |
| `DEBUG`   | Development detail — request payloads, query parameters        |
| `INFO`    | Significant state changes — user created, payment processed    |
| `WARNING` | Recoverable issues — retry attempted, fallback used            |
| `ERROR`   | Failures requiring attention — payment failed, write error     |

Rules:

- Include enough context to diagnose the issue without re-running: include IDs, paths, and relevant values alongside the error.
- Never log sensitive data: passwords, tokens, secret values, or PII.
- In production, use structured logging (JSON) where possible. Avoid free-text log strings that cannot be parsed or searched.
- Log at `ERROR` when an error propagates to the top of the call stack unhandled. Log at `WARNING` or `DEBUG` when it is caught and recovered from.

---

## Code Review Checklist

Before submitting code for review or marking a task complete, verify:

- [ ] Errors are handled explicitly — no silent failures or unchecked exceptions
- [ ] All public functions and service methods have tests
- [ ] Test names describe the scenario being tested
- [ ] The code follows existing patterns in the codebase
- [ ] A stranger could understand this code in six months without context
- [ ] No secrets, credentials, or API keys are present in the diff
- [ ] No new dependency was added without evaluation (see Dependencies above)
- [ ] Every modified file stays within the 750-line limit
- [ ] Relevant documentation has been updated
- [ ] No commented-out code was left in the diff
