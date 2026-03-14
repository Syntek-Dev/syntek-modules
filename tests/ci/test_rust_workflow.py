"""CI workflow validation tests — Rust layer (US005).

Asserts that the Forgejo Rust workflow (.forgejo/workflows/rust.yml)
contains all three missing behaviours identified in US005:

  1. cargo audit vulnerability scanning that fails on high/critical findings
  2. Coverage collection (llvm-cov or tarpaulin) and output to a consumable format
  3. Coverage upload and PR comment steps after the test step

Red phase: all tests below FAIL against the current workflow file because
none of these steps have been added yet.  They will go green once the
implementation is added as part of the US005 green phase.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _any_script_contains(scripts: list[str], fragment: str) -> bool:
    return any(fragment in script for script in scripts)


def _any_name_contains(names: list[str], fragment: str) -> bool:
    fragment_lower = fragment.lower()
    return any(fragment_lower in name.lower() for name in names)


# ---------------------------------------------------------------------------
# Baseline: confirm currently-present steps to document what IS there
# ---------------------------------------------------------------------------


class TestRustWorkflowBaseline:
    """Sanity-check that the workflow file parses and has the known good steps.

    These tests assert the existing steps that ARE present; they act as
    regression guards so refactoring does not silently remove them.
    """

    def test_workflow_has_jobs(self, forgejo_rust_workflow: dict) -> None:
        assert "jobs" in forgejo_rust_workflow, "rust.yml has no jobs section"

    def test_rust_job_exists(self, forgejo_rust_workflow: dict) -> None:
        assert "rust" in forgejo_rust_workflow["jobs"], (
            "rust.yml has no job named 'rust'"
        )

    def test_format_check_step_present(self, rust_step_names: list[str]) -> None:
        assert _any_name_contains(rust_step_names, "format"), (
            "'cargo fmt --check' step missing from rust.yml"
        )

    def test_clippy_step_present(self, rust_step_names: list[str]) -> None:
        assert _any_name_contains(rust_step_names, "clippy"), (
            "Clippy step missing from rust.yml"
        )

    def test_cargo_test_present(self, rust_run_scripts: list[str]) -> None:
        assert _any_script_contains(rust_run_scripts, "cargo test"), (
            "'cargo test' not present in rust.yml"
        )

    def test_rust_cache_action_used(self, rust_steps: list[dict]) -> None:
        uses_values = [step.get("uses", "") for step in rust_steps]
        assert any("rust-cache" in u for u in uses_values), (
            "Swatinem/rust-cache is not used in rust.yml"
        )


# ---------------------------------------------------------------------------
# 1. Vulnerability scanning — cargo audit
# ---------------------------------------------------------------------------


class TestCargoAuditStep:
    """The Rust workflow must run cargo audit and fail on high/critical CVEs.

    US005 acceptance criterion:
        Given `cargo audit` finds a high/critical vulnerability,
        When CI runs,
        Then the pipeline fails with a clear vulnerability report.
    """

    def test_cargo_audit_step_name_present(self, rust_step_names: list[str]) -> None:
        """A step whose name references 'audit' must exist in rust.yml."""
        assert _any_name_contains(rust_step_names, "audit"), (
            "No audit step found in rust.yml — expected a step named "
            "something like 'Security audit (cargo audit)'"
        )

    def test_cargo_audit_command_present(self, rust_run_scripts: list[str]) -> None:
        """A run script must invoke cargo audit."""
        assert _any_script_contains(rust_run_scripts, "cargo audit"), (
            "cargo audit is not invoked in any run script in rust.yml"
        )

    def test_cargo_audit_deny_flag_present(self, rust_run_scripts: list[str]) -> None:
        """cargo audit must use --deny to fail on vulnerability findings.

        The canonical form is: cargo audit --deny warnings
        or more targeted: cargo audit --deny vulnerable
        """
        assert _any_script_contains(rust_run_scripts, "--deny"), (
            "cargo audit invocation is missing --deny flag in rust.yml — "
            "vulnerabilities will be reported but the step will not fail"
        )

    def test_cargo_audit_denies_vulnerabilities(
        self, rust_run_scripts: list[str]
    ) -> None:
        """--deny must reference at least one advisory category to block merges.

        Accepted values: warnings, vulnerabilities, unmaintained, unsound, yanked.
        The workflow uses --deny warnings which blocks on all advisory categories
        including CVEs, unmaintained crates, unsound code, and yanked crates.
        """
        scripts_with_deny = [s for s in rust_run_scripts if "--deny" in s]
        assert scripts_with_deny, "No run script in rust.yml contains --deny"
        combined = " ".join(scripts_with_deny)
        accepted = ("warnings", "vulnerabilities", "unmaintained", "unsound", "yanked")
        assert any(term in combined for term in accepted), (
            "--deny flag present in rust.yml but not set to any recognised advisory "
            "category (warnings, vulnerabilities, unmaintained, unsound, yanked)"
        )

    def test_cargo_audit_install_or_action_step(self, rust_steps: list[dict]) -> None:
        """cargo audit must be installed via an action or cargo install before use."""
        # Accept either: an 'actions-rs/audit-check' action, a rustsec/audit-check,
        # or a run step that installs cargo-audit
        has_install = (
            _any_script_contains(
                [s.get("run", "") for s in rust_steps],
                "cargo install cargo-audit",
            )
            or any("audit" in step.get("uses", "") for step in rust_steps)
            or any("rustsec" in step.get("uses", "") for step in rust_steps)
        )
        assert has_install, (
            "cargo-audit is not installed or referenced via an action in rust.yml — "
            "add 'cargo install cargo-audit' or use actions-rs/audit-check"
        )


# ---------------------------------------------------------------------------
# 2. Coverage collection for Rust
# ---------------------------------------------------------------------------


class TestRustCoverage:
    """The Rust workflow must collect coverage data for PR comments.

    US005 acceptance criterion:
        Given the CI pipeline completes successfully,
        When the PR is reviewed,
        Then test coverage and audit reports are available as PR comments.

    cargo test alone produces no coverage data; llvm-cov or tarpaulin is
    required to generate an lcov or JSON summary.
    """

    def test_coverage_tool_invoked(self, rust_run_scripts: list[str]) -> None:
        """A coverage tool (llvm-cov or cargo-tarpaulin) must be invoked."""
        has_llvm_cov = _any_script_contains(rust_run_scripts, "llvm-cov")
        has_tarpaulin = _any_script_contains(rust_run_scripts, "tarpaulin")
        assert has_llvm_cov or has_tarpaulin, (
            "No coverage tool found in rust.yml — add 'cargo llvm-cov' or "
            "'cargo tarpaulin' to collect coverage data"
        )

    def test_coverage_produces_lcov_output(self, rust_run_scripts: list[str]) -> None:
        """Coverage must be output in lcov format for PR comment actions."""
        has_lcov = _any_script_contains(
            rust_run_scripts, "--lcov"
        ) or _any_script_contains(rust_run_scripts, "lcov")
        assert has_lcov, (
            "rust.yml coverage step does not produce lcov output — "
            "add --lcov flag to cargo llvm-cov invocation"
        )

    def test_coverage_step_name_present(self, rust_step_names: list[str]) -> None:
        """A step whose name references 'coverage' must exist in rust.yml."""
        assert _any_name_contains(rust_step_names, "coverage"), (
            "No coverage step found in rust.yml"
        )


# ---------------------------------------------------------------------------
# 3. Coverage PR comments
# ---------------------------------------------------------------------------


class TestRustCoveragePRComment:
    """The Rust workflow must post coverage as a PR comment."""

    def test_coverage_comment_step_uses_action(self, rust_steps: list[dict]) -> None:
        """A recognised coverage-comment action must be present in rust.yml."""
        known_comment_actions = (
            "romeovs/lcov-reporter-action",
            "orgoro/coverage",
            "codecov/codecov-action",
            "cargo-llvm-cov",
        )
        for step in rust_steps:
            uses = step.get("uses", "")
            if any(action in uses for action in known_comment_actions):
                return
        assert False, (  # noqa: PT015
            "No recognised coverage-comment action found in rust.yml steps — "
            f"expected one of: {', '.join(known_comment_actions)}"
        )

    def test_coverage_comment_step_name_present(
        self, rust_step_names: list[str]
    ) -> None:
        """A step that posts coverage as a PR comment must exist."""
        has_comment_step = (
            _any_name_contains(rust_step_names, "comment")
            or _any_name_contains(rust_step_names, "post coverage")
            or _any_name_contains(rust_step_names, "coverage report")
            or _any_name_contains(rust_step_names, "coverage summary")
        )
        assert has_comment_step, (
            "No coverage comment or upload step found in rust.yml — "
            "add a step using romeovs/lcov-reporter-action or codecov/codecov-action"
        )

    def test_coverage_step_runs_on_pull_request(
        self, forgejo_rust_workflow: dict
    ) -> None:
        """The workflow must trigger on pull_request for PR comment posting."""
        # PyYAML (YAML 1.1) parses bare `on:` as boolean True — check both keys.
        triggers = forgejo_rust_workflow.get("on") or forgejo_rust_workflow.get(
            True, {}
        )
        assert "pull_request" in triggers, (
            "rust.yml does not trigger on pull_request — "
            "coverage PR comments cannot be posted"
        )
