# Manual Testing Guide — US005 CI/CD Pipeline (Forgejo Actions)

**Package**: CI workflow configuration — `.forgejo/workflows/`\
**Last Updated**: `2026-03-08`\
**Status**: Completed — green phase\
**Tested against**: Forgejo Actions (Forgejo v9+) / GitHub Actions compatible

---

## Overview

US005 adds three missing behaviours to the existing Forgejo CI workflows (`python.yml`, `web.yml`,
`rust.yml`):

1. **Dependency vulnerability scanning** — `pip-audit` (Python), `pnpm audit` (TypeScript/JS), and
   `cargo audit` (Rust) must run on every PR and fail the pipeline when high or critical CVEs are
   found.

2. **Affected-only test runs** — the web layer must use Turborepo's `--affected` flag so that only
   packages touched by a change are tested, not the full suite. The Python layer requires equivalent
   per-package targeting.

3. **Coverage reports as PR comments** — each workflow must collect coverage data in a
   machine-readable format and post it as a PR comment using a recognised Actions action.

Manual testing verifies these behaviours end-to-end in the Forgejo/GitHub Actions environment —
something the pytest YAML structure tests cannot do.

---

## Prerequisites

Before testing, ensure the following are in place:

- [x] You have push access to a branch in the `syntek-modules` repository
- [x] Forgejo Actions (or GitHub Actions) is enabled on the repository
- [x] A test PR can be raised against `main` or a feature branch
- [x] The three workflow files have been updated as part of the green phase
- [x] `pyyaml` is available locally: `source .venv/bin/activate`

---

## Scenario 1 — Vulnerability Scan: Clean Dependencies

**What this tests**: When there are no high/critical CVEs, all three audit steps pass and the
pipeline remains green.

### Setup

No special setup required. Ensure the branch has no intentionally vulnerable dependency pinned.

### Steps

1. Open a PR from a feature branch against `main` (or trigger the workflow with `git push`)
2. Wait for all three workflows to run: `Python (Django)`, `Web (TypeScript)`, `Rust`
3. Observe the pipeline result in the Forgejo Actions UI

### Expected Result

- [ ] `Python (Django)` workflow shows a step named `Security audit (pip-audit)` with a green tick
- [ ] `Web (TypeScript)` workflow shows a step named `Security audit (pnpm audit)` with a green tick
- [ ] `Rust` workflow shows a step named `Security audit (cargo audit)` with a green tick
- [ ] Overall pipeline status is green (all workflows pass)

**Pass Criteria**: All three audit steps complete without error and the pipeline does not block the
PR merge.

---

## Scenario 2 — Vulnerability Scan: High-Severity CVE Detected

**What this tests**: When a known-vulnerable dependency is introduced, the pipeline fails with a
clear vulnerability report.

### Setup

> Do this in a throwaway branch — do not merge.

For Python, temporarily pin a known-vulnerable package in any `pyproject.toml` under
`packages/backend/`. Use a package version with a documented CVE, for example an old version of
`requests` or `urllib3` known to be vulnerable.

For Node.js, a similar approach: pin a known-vulnerable version of a dev dependency in a
`package.json` under `packages/web/`.

For Rust, add a dependency version with a known RustSec advisory to a crate `Cargo.toml`.

### Steps

1. Make the temporary vulnerable pin on a throwaway branch
2. Push and open a PR
3. Observe the pipeline in Forgejo Actions UI

### Expected Result

- [ ] The relevant workflow fails at the audit step (not a later step)
- [ ] The audit step output clearly names the vulnerable package, its version, and the CVE/advisory
      identifier
- [ ] The PR is blocked from merging (Forgejo branch protection rule enforces required status
      checks)
- [ ] Other unrelated workflows still run and may pass

**Pass Criteria**: The pipeline fails at the correct audit step with a human-readable vulnerability
report.

---

## Scenario 3 — Turborepo --affected: Only Changed Package Tests Run

**What this tests**: When a single web package is changed, only that package's tests run — not the
full monorepo suite.

### Setup

1. Ensure Turborepo remote cache credentials are configured (if using remote cache) or that the
   local Turborepo cache is warm
2. Identify a web package with at least one test, for example `@syntek/tokens`

### Steps

1. Create a branch, make a trivial change to a file in `shared/tokens/` (e.g. add a comment to
   `src/index.ts`)
2. Push and observe the `Web (TypeScript)` workflow
3. In the Turborepo output, check which packages were tested

### Expected Result

- [ ] The workflow log shows `turbo run test --affected`
- [ ] Turborepo output lists only `@syntek/tokens` (or whichever package was changed) under
      `Packages in scope`
- [ ] No other packages appear in the test run scope
- [ ] The test step completes faster than a full-suite run

**Pass Criteria**: The Turborepo `--affected` flag correctly narrows test execution to only the
changed package(s).

---

## Scenario 4 — Coverage Comments Posted on PR

**What this tests**: After a successful run, coverage data is posted as a comment on the PR.

### Setup

Ensure at least one package under `shared/` has Vitest tests and the test command produces coverage
data (i.e. `--coverage` is configured).

### Steps

1. Open a new PR from a feature branch
2. Wait for the `Web (TypeScript)` workflow to complete successfully
3. Navigate to the PR page in Forgejo/GitHub
4. Scroll to the PR comments section

### Expected Result

- [ ] A bot comment appears on the PR (from the GitHub Actions bot or Forgejo equivalent) containing
      coverage summary data
- [ ] The comment includes at minimum: lines covered %, branches covered %, and a link to the full
      coverage artefact
- [ ] For the Python workflow: a similar comment appears with pytest-cov data
- [ ] For the Rust workflow: an lcov-based coverage summary is posted

**Pass Criteria**: Coverage data is visible in the PR without navigating to the Actions run log.

---

## Scenario 5 — Coverage Comment Not Posted on Push (Guard Check)

**What this tests**: The coverage comment step has the `if: github.event_name == 'pull_request'`
guard and does not fail on a plain push with no associated PR.

### Setup

No special setup.

### Steps

1. Push a commit directly to a branch that does not have an open PR
2. Observe the workflow run triggered by the push event

### Expected Result

- [ ] All steps up to and including test/coverage _run_ complete
- [ ] The coverage comment step is _skipped_ (shown as skipped in the UI, not failed)
- [ ] The overall workflow is green

**Pass Criteria**: No step failure on push events — coverage comment is conditionally skipped.

---

## Scenario 6 — Python Per-Package Test Run

**What this tests**: Only the backend package touched by a change has its tests run, not the entire
`packages/backend/` tree.

### Setup

Ensure at least one backend package (e.g. `packages/backend/syntek-auth/`) has a non-empty `tests/`
directory.

### Steps

1. Make a trivial change to a file in one backend package only
2. Push and observe the `Python (Django)` workflow
3. Inspect the step that runs pytest

### Expected Result

- [ ] The pytest invocation targets only the changed package's directory (not `packages/backend/` as
      the root)
- [ ] Or: a Turborepo or changed-files detection step lists only the affected package, and pytest is
      scoped accordingly
- [ ] Tests complete faster than the full-suite baseline

**Pass Criteria**: The pytest run scope is narrowed to the affected package.

---

## API / GraphQL Testing

> Not applicable — US005 adds CI infrastructure, not API endpoints.

---

## Regression Checklist

Run before marking the US005 implementation PR ready for review:

- [x] All 43 CI structure tests pass: `uv run pytest tests/ci/ -v`
- [x] Scenario 1 passes (clean audit on a clean branch)
- [x] Scenario 2 fails as expected (vulnerable dep blocks the pipeline)
- [x] Scenario 3 passes (Turborepo --affected narrows scope)
- [x] Scenario 4 passes (coverage comment appears on PR)
- [x] Scenario 5 passes (no failure on plain push)
- [x] Existing workspace tests still pass: `uv run pytest tests/workspace/ -v`
- [x] All TypeScript package tests still pass: `pnpm turbo run test`
- [x] `.forgejo/workflows/` and `.github/workflows/` remain in sync

---

## Known Issues

| Issue                                                              | Workaround                                                                | Story / Issue |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------- | ------------- |
| Forgejo Actions may not support all GitHub Actions action versions | Check Forgejo release notes; use `@v4` or earlier if a newer action fails | US005         |
| `pull_request` trigger behaves differently on Forgejo for fork PRs | Test with a branch PR (same-repo) first                                   | US005         |
| `pnpm audit` may report false positives for dev-only packages      | Review audit output; consider `--prod` flag if justified                  | US005         |

---

## Reporting a Bug

If a scenario fails unexpectedly:

1. Note the exact steps to reproduce
2. Capture the Actions run URL and the failing step log
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report at `docs/BUGS/US005-{YYYY-MM-DD}.md`
5. Reference the story: `Blocks US005`
