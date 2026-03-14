# Version History

| Version | Date       | Type  | Summary                                                                                                          |
| ------- | ---------- | ----- | ---------------------------------------------------------------------------------------------------------------- |
| 0.17.0  | 14/03/2026 | MINOR | `syntek-pyo3` US007 QA fixes — KeyRing API (breaking), zeroize, exception classes, audit CLI command             |
| 0.16.2  | 13/03/2026 | PATCH | AES-GCM helper extraction, 2 further crypto fixes, pytest-xdist parallelism, fast Argon2id test params           |
| 0.16.1  | 13/03/2026 | PATCH | `syntek-crypto` QA fixes — 13 security findings resolved from US006 review                                       |
| 0.16.0  | 13/03/2026 | MINOR | `syntek-auth` complete — full auth module, 13 test files, migrations, MFA, OAuth, US009 done                     |
| 0.15.0  | 11/03/2026 | MINOR | Security policy: SSO allowlist, key versioning/rotation in `syntek-crypto`, `syntek-security` module, US076 done |
| 0.14.0  | 11/03/2026 | MINOR | `syntek-graphql-crypto` complete — GraphQL encryption middleware, 59 tests, US008 done                           |
| 0.13.0  | 09/03/2026 | MINOR | `syntek-pyo3` complete — PyO3 Django bindings, EncryptedField, 65 tests, US007 done                              |
| 0.12.1  | 09/03/2026 | PATCH | Fix `cargo deny check` failures — cargo-deny 0.16+ config, SPDX identifiers, wildcard path deps                  |
| 0.12.0  | 09/03/2026 | MINOR | `syntek-crypto` complete — AES-256-GCM, Argon2id, HMAC-SHA256, batch APIs, 49 tests, US006 done                  |
| 0.11.0  | 08/03/2026 | MINOR | `TOKEN_MANIFEST`, `TAILWIND_COLOURS`, colour utils, theme utils in `@syntek/tokens`, US075 done                  |
| 0.10.0  | 08/03/2026 | MINOR | `syntek-manifest` Rust crate — module manifest spec & CLI shared framework, 127 tests, US074 done                |
| 0.9.0   | 08/03/2026 | MINOR | CI/CD pipeline complete — security audit, affected-only tests, coverage PR comments, Sprint 02 done              |
| 0.8.0   | 08/03/2026 | MINOR | `@syntek/tokens` design token system, no-hardcoded-design-values ESLint rule, Sprint 02 complete                 |
| 0.7.0   | 08/03/2026 | MINOR | Security policy, CodeQL/Semgrep SAST, Dependabot/Renovate dependency automation, branch docs                     |
| 0.6.0   | 08/03/2026 | MINOR | `syntek-dev lint --fix` covers Prettier + markdownlint; `--prettier` flag added; Sprint 01 docs                  |
| 0.5.2   | 08/03/2026 | PATCH | Fix pnpm version conflict in CI — remove hardcoded `version` from `pnpm/action-setup@v4`                         |
| 0.5.1   | 08/03/2026 | PATCH | Fix overly broad `.gitignore` `lib/` pattern; restore `shared/graphql/src/lib/fetcher.ts` to CI                  |
| 0.5.0   | 07/03/2026 | MINOR | Add `syntek-dev ci` command, fix CI markdownlint (175 → 0), add coverage, upgrade lefthook                       |
| 0.4.2   | 07/03/2026 | PATCH | Fix CI markdownlint failures (175), add vitest coverage, upgrade lefthook to 2.1.0                               |
| 0.4.1   | 07/03/2026 | PATCH | Tooling fixes, Rust Clippy warnings, CI normalisation, docs reformatting                                         |
| 0.4.0   | 06/03/2026 | MINOR | `@syntek/graphql` shared GraphQL operations package, 29/29 tests green, Sprint 01 complete                       |
| 0.3.0   | 06/03/2026 | MINOR | `@syntek/types` shared TypeScript types package, 46/46 tests green, US002 complete                               |
| 0.2.0   | 06/03/2026 | MINOR | Test infrastructure, uv lockfile, PyO3 0.28.2, US001 complete                                                    |
| 0.1.0   | 06/03/2026 | MINOR | Initial monorepo scaffold, Rust CLI, 74 stories, 45 sprints                                                      |
