"""CI workflow validation tests — Python layer (US005).

Asserts that the Forgejo Python workflow (.forgejo/workflows/python.yml)
contains all three missing behaviours identified in US005:

  1. pip-audit vulnerability scanning that fails on high/critical findings
  2. Per-package affected-only pytest runs (not the entire packages/backend/ glob)
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
    """Return True if *any* run script in the workflow contains the fragment."""
    return any(fragment in script for script in scripts)


def _any_name_contains(names: list[str], fragment: str) -> bool:
    """Return True if *any* step name contains the fragment (case-insensitive)."""
    fragment_lower = fragment.lower()
    return any(fragment_lower in name.lower() for name in names)


# ---------------------------------------------------------------------------
# 1. Vulnerability scanning — pip-audit
# ---------------------------------------------------------------------------


class TestPipAuditStep:
    """The Python workflow must run pip-audit and fail on high/critical CVEs.

    US005 acceptance criterion:
        Given `pip-audit` finds a high/critical vulnerability,
        When CI runs,
        Then the pipeline fails with a clear vulnerability report.
    """

    def test_pip_audit_step_name_present(self, python_step_names: list[str]) -> None:
        """A step whose name references 'pip-audit' or 'audit' must exist."""
        assert _any_name_contains(python_step_names, "audit"), (
            "No audit step found in python.yml — expected a step named "
            "something like 'Security audit (pip-audit)'"
        )

    def test_pip_audit_command_present(self, python_run_scripts: list[str]) -> None:
        """A run script must invoke pip-audit via uv."""
        assert _any_script_contains(python_run_scripts, "pip-audit"), (
            "pip-audit is not invoked in any run script in python.yml"
        )

    def test_pip_audit_uses_uv_run(self, python_run_scripts: list[str]) -> None:
        """pip-audit must be invoked via uvx or uv run — not bare pip-audit.

        ``uvx pip-audit`` is the canonical form: it runs pip-audit in a temporary
        isolated environment managed by uv.  ``uv run pip-audit`` (using the
        project venv) is also acceptable.
        """
        has_uvx = _any_script_contains(python_run_scripts, "uvx pip-audit")
        has_uv_run = _any_script_contains(python_run_scripts, "uv run pip-audit")
        assert has_uvx or has_uv_run, (
            "pip-audit must be run via 'uvx pip-audit' or 'uv run pip-audit'"
        )

    def test_pip_audit_fails_on_high_severity(
        self, python_run_scripts: list[str]
    ) -> None:
        """pip-audit must be present so the step fails when vulnerabilities are found.

        pip-audit exits non-zero on any finding by default — no explicit --fail-on
        flag is required.  This test verifies pip-audit is actually invoked so
        the step will block the pipeline when high/critical CVEs are present.
        """
        assert _any_script_contains(python_run_scripts, "pip-audit"), (
            "pip-audit is not invoked in python.yml — high/critical CVEs will not "
            "block the pipeline"
        )

    def test_pip_audit_targets_high_and_critical(
        self, python_run_scripts: list[str]
    ) -> None:
        """pip-audit must be invoked without suppressing high/critical findings.

        pip-audit reports and fails on all severities by default.  The test
        verifies the command is present and does not use --ignore-vuln or
        severity-filtering flags that would suppress high/critical findings.
        """
        pip_audit_scripts = [s for s in python_run_scripts if "pip-audit" in s]
        assert pip_audit_scripts, "No run script contains pip-audit"
        combined = " ".join(pip_audit_scripts)
        assert "--ignore-vuln" not in combined, (
            "pip-audit invocation uses --ignore-vuln which may suppress "
            "high/critical findings — remove the flag or document each exemption"
        )


# ---------------------------------------------------------------------------
# 2. Per-package affected-only test runs
# ---------------------------------------------------------------------------


class TestPerPackagePytest:
    """The Python workflow must run tests per-affected-package, not the full suite.

    US005 acceptance criterion:
        Given a Python change is made only in one backend package,
        When CI runs,
        Then only that package's tests run (not the full suite).

    Currently the workflow runs:
        uv run pytest packages/backend/ -x -q
    which runs the full backend suite regardless of what changed.

    The fix requires either:
      a) A matrix strategy keyed on changed packages, or
      b) A per-package pytest invocation using the changed-files output, or
      c) Turborepo affected runs driving pytest per-package.

    We test for Turborepo --affected integration as specified in the story tasks.
    """

    def test_no_blanket_backend_pytest_run(self, python_run_scripts: list[str]) -> None:
        """The blanket 'pytest packages/backend/' must not be the only test invocation.

        If --affected or a matrix approach is present alongside the blanket run
        (e.g. as a fallback), that is acceptable; we check the blanket run is
        not the sole invocation by asserting that at least one script references
        a package-level or affected-only pattern.
        """
        blanket_run = _any_script_contains(
            python_run_scripts, "pytest packages/backend/"
        )
        affected_run = (
            _any_script_contains(python_run_scripts, "--affected")
            or _any_script_contains(python_run_scripts, "CHANGED_PACKAGES")
            or _any_script_contains(python_run_scripts, "changed_packages")
            or _any_script_contains(python_run_scripts, "packages/backend/$")
        )
        assert not (blanket_run and not affected_run), (
            "python.yml still runs 'pytest packages/backend/' across the full suite "
            "with no per-package or affected-only variant — add Turborepo --affected "
            "integration or a changed-files matrix"
        )

    def test_turbo_affected_or_changed_files_step_exists(
        self, python_step_names: list[str]
    ) -> None:
        """A step that detects changed packages or uses --affected must be present."""
        has_affected_step = (
            _any_name_contains(python_step_names, "affected")
            or _any_name_contains(python_step_names, "changed")
            or _any_name_contains(python_step_names, "matrix")
        )
        assert has_affected_step, (
            "No 'affected', 'changed', or 'matrix' step found in python.yml — "
            "per-package affected-only test runs are not configured"
        )

    def test_pytest_uses_per_package_path_or_affected(
        self, python_run_scripts: list[str]
    ) -> None:
        """The pytest invocation must reference a per-package path or affected flag."""
        has_specific_path = (
            _any_script_contains(python_run_scripts, "packages/backend/$PACKAGE")
            or _any_script_contains(python_run_scripts, "packages/backend/${")
            or _any_script_contains(python_run_scripts, "--affected")
            or _any_script_contains(python_run_scripts, "turbo run test")
        )
        assert has_specific_path, (
            "pytest is not invoked with a per-package path variable or --affected flag"
        )


# ---------------------------------------------------------------------------
# 3. Coverage reports as PR comments
# ---------------------------------------------------------------------------


class TestCoverageReporting:
    """The Python workflow must collect coverage and post it as a PR comment.

    US005 acceptance criterion:
        Given the CI pipeline completes successfully,
        When the PR is reviewed,
        Then test coverage and audit reports are available as PR comments.

    The existing workflow has no coverage flags on the pytest invocation and
    no step that uploads or comments coverage output.
    """

    def test_pytest_coverage_flag_present(self, python_run_scripts: list[str]) -> None:
        """pytest must be invoked with --cov to collect coverage data."""
        assert _any_script_contains(python_run_scripts, "--cov"), (
            "pytest is not invoked with --cov in python.yml — no coverage data "
            "will be produced for PR comments"
        )

    def test_coverage_xml_output_configured(
        self, python_run_scripts: list[str]
    ) -> None:
        """Coverage must be written to an XML or LCOV file consumable by comment actions."""
        has_xml = _any_script_contains(python_run_scripts, "--cov-report=xml")
        has_lcov = _any_script_contains(python_run_scripts, "--cov-report=lcov")
        assert has_xml or has_lcov, (
            "pytest --cov-report is not set to xml or lcov in python.yml — "
            "no machine-readable coverage file will be produced"
        )

    def test_coverage_comment_step_name_present(
        self, python_step_names: list[str]
    ) -> None:
        """A step that posts coverage as a PR comment must exist."""
        has_comment_step = (
            _any_name_contains(python_step_names, "comment")
            or _any_name_contains(python_step_names, "coverage report")
            or _any_name_contains(python_step_names, "post coverage")
            or _any_name_contains(python_step_names, "coverage summary")
        )
        assert has_comment_step, (
            "No step in python.yml posts coverage as a PR comment — "
            "add a step using an action such as 'py-cov-comment' or "
            "'MishaKav/pytest-coverage-comment'"
        )

    def test_coverage_comment_step_uses_action(self, python_steps: list[dict]) -> None:
        """The coverage comment step must use a recognised Actions action."""
        known_comment_actions = (
            "MishaKav/pytest-coverage-comment",
            "orgoro/coverage",
            "romeovs/lcov-reporter-action",
            "py-cov-comment",
        )
        for step in python_steps:
            uses = step.get("uses", "")
            if any(action in uses for action in known_comment_actions):
                return  # found at least one recognised action
        assert False, (  # noqa: PT015
            "No recognised coverage-comment action found in python.yml steps — "
            f"expected one of: {', '.join(known_comment_actions)}"
        )

    def test_coverage_step_runs_on_pull_request(
        self, forgejo_python_workflow: dict
    ) -> None:
        """The workflow must trigger on pull_request so coverage comments can be posted."""
        # PyYAML (YAML 1.1) parses bare `on:` as boolean True — check both keys.
        triggers = forgejo_python_workflow.get("on") or forgejo_python_workflow.get(
            True, {}
        )
        assert "pull_request" in triggers, (
            "python.yml does not trigger on pull_request — "
            "coverage PR comments cannot be posted"
        )
