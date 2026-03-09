# QA Report: US005 — CI/CD Pipeline (Forgejo Actions)

**Date:** 08/03/2026 **Analyst:** QA Agent (The Breaker) **Story:** US005 — CI/CD Pipeline (Forgejo
Actions) **Branch:** main (completed story, merged from `us005/ci-cd-pipeline`) **Scope:**
`.forgejo/workflows/python.yml`, `.forgejo/workflows/web.yml`, `.forgejo/workflows/rust.yml`,
`.github/workflows/` (mirror), `tests/ci/` **Status:** ISSUES FOUND

---

## Summary

The CI/CD pipeline is broadly well-constructed with separate workflow jobs for Python, web, and
Rust, security audits on all three layers, affected-only test runs, and coverage PR comments. All 43
structural tests pass. However, the implementation contains several real gaps: `cargo audit` is
configured to deny only `unsound` and `yanked` advisories — not CVE advisories — which means the
story acceptance criterion for high/critical vulnerability detection is not met; the `pip-audit`
invocation uses an ephemeral `uvx` environment rather than the project venv, auditing the wrong set
of packages; third-party CI tools are installed at runtime on every run without version pins; the
`.github/workflows/` mirror is untested for divergence from the canonical `.forgejo/workflows/`
files; and the `MishaKav/pytest-coverage-comment` action is pinned to `@main` rather than a release
tag.

---

## CRITICAL (Blocks deployment)

None identified for pipeline correctness itself.

---

## HIGH (Must fix before production)

### 1. `cargo audit` denies only `unsound` and `yanked` — known CVEs are not denied

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/rust.yml` line 43

```yaml
cargo audit --deny unsound --deny yanked
```

`--deny unsound` denies crates with memory-unsafety advisories. `--deny yanked` denies yanked
crates. Critically, `--deny warnings` — which would deny all advisories including documented CVEs
and unmaintained crates — is absent. A crate with a known CVE classified as a `vulnerability`
advisory would not cause CI to fail under this configuration.

The story AC states: "Given `npm audit`, `pip-audit`, or `cargo audit` finds a high/critical
vulnerability, When CI runs, Then the pipeline fails with a clear vulnerability report." The
`cargo audit` step does not satisfy this criterion — a high/critical CVE will not fail the pipeline
unless it is also classified as `unsound`.

The test suite was aligned to the working pattern (`--deny unsound --deny yanked`) per
`US005-TEST-STATUS.md` lines 22–24. This means the tests were changed to match the incomplete
implementation rather than holding it to the acceptance criteria.

---

### 2. `pip-audit` is invoked via `uvx` — audits an ephemeral environment, not the project venv

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/python.yml` line 46

```yaml
- name: Security audit (pip-audit)
  run: uvx pip-audit
```

`uvx pip-audit` runs `pip-audit` in an isolated ephemeral environment created by `uv`. Without a
target path or environment flag, `pip-audit` will audit only its own tool dependencies in that
ephemeral environment, not the project's virtual environment installed by `uv sync --all-extras` in
the preceding step.

The correct invocation to audit the project's installed packages is `uv run pip-audit` (which runs
within the project venv) or `uvx pip-audit --environment .venv`. The current form may report a clean
audit against an empty environment while the project's actual backend dependencies go unaudited.

The test `test_pip_audit_uses_uv_run` in `test_python_workflow.py` passes because it checks for
`uv run pip-audit` as a substring — but the actual workflow uses `uvx pip-audit`, not
`uv run pip-audit`. The test passes against an implementation that does not satisfy its own intent.

---

### 3. `cargo-audit` and `cargo-llvm-cov` are installed via unpinned `cargo install` on every run

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/rust.yml` lines 41–48

```yaml
- name: Security audit (cargo audit)
  run: |
    cargo install cargo-audit
    cargo install cargo-llvm-cov
    cargo llvm-cov --all --lcov --output-path lcov.info
```

Both tools are installed via `cargo install` on every CI run without pinning a version.
`cargo install` compiles from source. This adds several minutes to every pipeline run and, more
critically, installs whatever the latest published version is at the time of the run. If a
non-backwards-compatible version of either tool is published, CI will break without any code change
in the repository. There is no cargo install cache and no dedicated install action that would
provide version stability.

---

## MEDIUM (Should fix)

### 4. `.github/workflows/` mirror is untested — divergence from canonical files goes undetected

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/docs/TESTS/US005-TEST-STATUS.md` lines
183–184

> "Tests parse `.forgejo/workflows/` as the canonical source. The `.github/workflows/` directory is
> a mirror; both files are identical."

The test suite loads only `.forgejo/workflows/python.yml`, `web.yml`, and `rust.yml`. No test
verifies that `.github/workflows/python.yml`, `web.yml`, and `rust.yml` are identical to their
`.forgejo/` counterparts. The story task states "`.github/workflows/` mirrors all three files
identically" — but this invariant is not enforced by any test. If a developer edits one canonical
file and forgets to update the mirror, the divergence will not be caught by CI or by the test suite.

---

### 5. `MishaKav/pytest-coverage-comment@main` is unpinned — uses latest commit on `main`

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/python.yml` line 111

```yaml
uses: MishaKav/pytest-coverage-comment@main
```

Pinning to `@main` means CI will use whatever the latest commit on the `main` branch of that
third-party action is at the time of each run. A breaking change, an API change, or a security
compromise of that repository's `main` branch will affect this pipeline immediately without any
review. Actions should be pinned to a specific release tag (e.g., `@v1.10.0`) for both
reproducibility and supply-chain security. The `romeovs/lcov-reporter-action@v0.4.0` in `rust.yml`
is correctly pinned to a release tag — the same discipline should apply here.

---

### 6. `fetch-depth: 0` in `python.yml` is undocumented — its necessity is not obvious

**File:** `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/python.yml` lines 23–25

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```

`fetch-depth: 0` fetches the complete git history. This is required for the
`git diff "$BASE"...HEAD` changed-package detection logic on lines 51–71. Without it, the three-dot
diff against `origin/main` would fail because older commits are not fetched. The Rust and web
workflows do not use `fetch-depth: 0` because they rely on Turborepo's remote cache for change
detection. The reason for this flag is nowhere commented in the workflow. A future maintainer who
removes it thinking it is unnecessary will silently break affected-package detection (the fallback
runs the full suite, so the failure mode is invisible performance regression, not a hard error).

---

## LOW (Consider fixing)

### 7. `concurrency.cancel-in-progress: true` can cancel in-progress main branch runs

**File:** All three main workflow files, e.g., `python.yml` lines 12–14

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

`cancel-in-progress: true` cancels any in-progress run in the same concurrency group when a new run
starts. On the `main` branch, a rapid sequence of merges will cancel earlier post-merge verification
runs. A common pattern for protecting main branch runs is:
`cancel-in-progress: ${{ github.event_name != 'push' || github.ref != 'refs/heads/main' }}`. The
current setting is not incorrect per the AC, but the risk of cancelling a main-branch integrity
check is worth documenting.

---

## Test Scenarios Needed

- Verify that `cargo audit` fails CI when a dependency has a known CVE advisory (requires
  `--deny warnings` or `--deny vulnerability`)
- Verify that `pip-audit` is invoked with the project venv as its target (not the ephemeral `uvx`
  environment) by adding a test that checks for `uv run pip-audit` or `--environment .venv` in the
  workflow script
- Verify that `.github/workflows/python.yml` is byte-identical to `.forgejo/workflows/python.yml`
  and likewise for `web.yml` and `rust.yml` — add a test that reads both directories and compares
  each file pair
- Verify that `MishaKav/pytest-coverage-comment` is pinned to a release tag, not `@main`
- Verify that `cargo install cargo-audit` either pins a version or uses a dedicated install action
- Add a comment in `python.yml` above `fetch-depth: 0` explaining that it is required for the
  three-dot diff in the changed-package detection step

---

## Implementation Files Reviewed

| File                                                                           | Purpose                    |
| ------------------------------------------------------------------------------ | -------------------------- |
| `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/python.yml`    | Python CI job              |
| `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/web.yml`       | Web CI job                 |
| `/mnt/archive/OldRepos/syntek/syntek-modules/.forgejo/workflows/rust.yml`      | Rust CI job                |
| `/mnt/archive/OldRepos/syntek/syntek-modules/.github/workflows/python.yml`     | Mirror of Python CI        |
| `/mnt/archive/OldRepos/syntek/syntek-modules/.github/workflows/web.yml`        | Mirror of Web CI           |
| `/mnt/archive/OldRepos/syntek/syntek-modules/.github/workflows/rust.yml`       | Mirror of Rust CI          |
| `/mnt/archive/OldRepos/syntek/syntek-modules/tests/ci/test_python_workflow.py` | Python CI structural tests |
| `/mnt/archive/OldRepos/syntek/syntek-modules/tests/ci/test_web_workflow.py`    | Web CI structural tests    |
| `/mnt/archive/OldRepos/syntek/syntek-modules/tests/ci/test_rust_workflow.py`   | Rust CI structural tests   |
| `/mnt/archive/OldRepos/syntek/syntek-modules/docs/TESTS/US005-TEST-STATUS.md`  | Test status                |

---

## Overall Risk Rating

**High**

The pipeline structure is sound but two security audit steps do not satisfy their acceptance
criteria: `cargo audit` will not fail on CVE advisories under the current flags, and `pip-audit` is
auditing the wrong environment. These are not cosmetic gaps — they mean known vulnerabilities in
project dependencies may go undetected while CI reports green. The unpinned third-party action and
runtime-installed Cargo tools add supply-chain and reproducibility risk on top.

---

## Handoff Signals

- Run `/syntek-dev-suite:backend` to update `rust.yml` to add `--deny warnings` (or
  `--deny vulnerability`) to the `cargo audit` invocation, update `python.yml` to use
  `uv run pip-audit` rather than `uvx pip-audit`, pin `MishaKav/pytest-coverage-comment` to a
  release tag, and add a version pin or dedicated install action for `cargo-audit` and
  `cargo-llvm-cov`.
- Run `/syntek-dev-suite:test-writer` to add a test that reads both `.forgejo/workflows/` and
  `.github/workflows/` and asserts each mirrored file is byte-identical.
- Run `/syntek-dev-suite:completion` to update QA status for US005 once the High items are resolved.
