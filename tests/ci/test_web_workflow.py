"""CI workflow validation tests — Web (TypeScript) layer (US005).

Asserts that the Forgejo web workflow (.forgejo/workflows/web.yml)
contains all three missing behaviours identified in US005:

  1. pnpm audit vulnerability scanning that fails on high/critical findings
  2. Turborepo --affected flag so only changed packages are tested
  3. Coverage upload and PR comment steps after the test/coverage step

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
# 1. Vulnerability scanning — pnpm audit
# ---------------------------------------------------------------------------


class TestPnpmAuditStep:
    """The web workflow must run pnpm audit and fail on high/critical CVEs.

    US005 acceptance criterion:
        Given `npm audit` finds a high/critical vulnerability,
        When CI runs,
        Then the pipeline fails with a clear vulnerability report.

    Note: this project uses pnpm, so the correct command is pnpm audit.
    """

    def test_audit_step_name_present(self, web_step_names: list[str]) -> None:
        """A step whose name references 'audit' must exist."""
        assert _any_name_contains(web_step_names, "audit"), (
            "No audit step found in web.yml — expected a step named "
            "something like 'Security audit (pnpm audit)'"
        )

    def test_pnpm_audit_command_present(self, web_run_scripts: list[str]) -> None:
        """A run script must invoke pnpm audit."""
        assert _any_script_contains(web_run_scripts, "pnpm audit"), (
            "pnpm audit is not invoked in any run script in web.yml"
        )

    def test_pnpm_audit_fails_on_high_severity(self, web_run_scripts: list[str]) -> None:
        """pnpm audit must be configured to fail on high/critical findings.

        The correct flag is --audit-level=high.
        """
        assert _any_script_contains(web_run_scripts, "--audit-level"), (
            "pnpm audit invocation is missing --audit-level flag in web.yml — "
            "the pipeline will not fail when high/critical CVEs are found"
        )

    def test_pnpm_audit_level_is_high_or_critical(self, web_run_scripts: list[str]) -> None:
        """--audit-level must be set to high or critical."""
        scripts_with_audit = [s for s in web_run_scripts if "--audit-level" in s]
        assert scripts_with_audit, "No run script in web.yml contains --audit-level"
        combined = " ".join(scripts_with_audit)
        assert "high" in combined or "critical" in combined, (
            "--audit-level flag is present but not set to 'high' or 'critical' in web.yml"
        )

    def test_pnpm_audit_level_equals_high(self, web_run_scripts: list[str]) -> None:
        """Prefer the canonical form --audit-level=high."""
        assert _any_script_contains(web_run_scripts, "--audit-level=high"), (
            "pnpm audit does not use --audit-level=high in web.yml — "
            "use the canonical flag form to match the US005 acceptance criterion"
        )


# ---------------------------------------------------------------------------
# 2. Turborepo --affected for web layer
# ---------------------------------------------------------------------------


class TestTurboAffectedWeb:
    """The web workflow must use Turborepo's --affected flag for test runs.

    US005 acceptance criterion:
        Given a Python change is made only in one backend package,
        When CI runs,
        Then only that package's tests run (not the full suite) using
        Turborepo change detection.

    The same principle applies to the web layer: only affected packages
    should be tested.  Currently web.yml runs 'pnpm test' (full suite).
    The fix is to add '--affected' to the turbo run test invocation.
    """

    def test_turbo_affected_flag_present_in_test_step(
        self, web_run_scripts: list[str]
    ) -> None:
        """The test run command must include the --affected flag."""
        assert _any_script_contains(web_run_scripts, "--affected"), (
            "No --affected flag found in web.yml run scripts — "
            "Turborepo will run tests across ALL packages instead of only "
            "those affected by the current change"
        )

    def test_turbo_run_test_with_affected(self, web_run_scripts: list[str]) -> None:
        """The specific command 'turbo run test --affected' must be present."""
        has_turbo_affected = (
            _any_script_contains(web_run_scripts, "turbo run test --affected")
            or _any_script_contains(web_run_scripts, "pnpm turbo test --affected")
            or _any_script_contains(web_run_scripts, "pnpm test -- --affected")
        )
        assert has_turbo_affected, (
            "web.yml does not invoke turbo run test --affected — "
            "the current 'pnpm test' runs the full suite unconditionally"
        )

    def test_pnpm_test_bare_not_sole_test_invocation(
        self, web_run_scripts: list[str]
    ) -> None:
        """The bare 'pnpm test' must not be the only test invocation.

        If an --affected invocation is also present that is fine.  But
        'pnpm test' alone without --affected means the full suite runs.
        """
        bare_pnpm_test = _any_script_contains(web_run_scripts, "pnpm test\n") or (
            "pnpm test" in " ".join(web_run_scripts)
            and not _any_script_contains(web_run_scripts, "--affected")
        )
        # Invert: we want to confirm affected IS present.  The test above
        # already covers this; this assertion is a belt-and-braces check.
        assert _any_script_contains(web_run_scripts, "--affected"), (
            "'pnpm test' is the sole test invocation in web.yml with no --affected — "
            "all packages are always tested regardless of what changed"
        )


# ---------------------------------------------------------------------------
# 3. Coverage reports as PR comments
# ---------------------------------------------------------------------------


class TestCoverageReportingWeb:
    """The web workflow must surface coverage as a PR comment.

    US005 acceptance criterion:
        Given the CI pipeline completes successfully,
        When the PR is reviewed,
        Then test coverage and audit reports are available as PR comments.

    Currently web.yml runs 'pnpm test -- --coverage' but does not upload
    the coverage artefact or post it as a PR comment.
    """

    def test_coverage_comment_step_name_distinct_from_run_step(
        self, web_steps: list[dict]
    ) -> None:
        """The coverage PR comment step must be distinct from the bare 'pnpm test -- --coverage' run.

        The existing 'Coverage report' step only runs pnpm test -- --coverage.
        What US005 requires is an *additional* step that posts coverage as a
        PR comment using a recognised action — not just a test run that happens
        to collect coverage.
        """
        known_comment_actions = (
            "davelosert/vitest-coverage-report-action",
            "romeovs/lcov-reporter-action",
            "orgoro/coverage",
            "codecov/codecov-action",
        )
        for step in web_steps:
            uses = step.get("uses", "")
            if any(action in uses for action in known_comment_actions):
                return  # a real PR-comment step exists
        assert False, (  # noqa: PT015
            "web.yml has no coverage PR comment step — the existing 'Coverage report' "
            "step only runs pnpm test --coverage but does not post to the PR. "
            "Add a step using one of: "
            + ", ".join(known_comment_actions)
        )

    def test_coverage_comment_step_uses_action(self, web_steps: list[dict]) -> None:
        """The coverage comment step must use a recognised Actions action."""
        known_comment_actions = (
            "davelosert/vitest-coverage-report-action",
            "romeovs/lcov-reporter-action",
            "orgoro/coverage",
            "codecov/codecov-action",
        )
        for step in web_steps:
            uses = step.get("uses", "")
            if any(action in uses for action in known_comment_actions):
                return
        assert False, (  # noqa: PT015
            "No recognised coverage-comment action found in web.yml steps — "
            f"expected one of: {', '.join(known_comment_actions)}"
        )

    def test_coverage_json_summary_exists_in_run(
        self, web_run_scripts: list[str]
    ) -> None:
        """The coverage step must produce a JSON summary Vitest can consume.

        Vitest with --coverage produces coverage-summary.json which actions
        like davelosert/vitest-coverage-report-action read.
        """
        has_json_reporter = (
            _any_script_contains(web_run_scripts, "--coverage.reporter=json-summary")
            or _any_script_contains(web_run_scripts, "json-summary")
            or _any_script_contains(web_run_scripts, "--reporter=json")
        )
        assert has_json_reporter, (
            "The coverage run in web.yml does not produce a JSON summary — "
            "add --coverage.reporter=json-summary to the Vitest invocation"
        )

    def test_coverage_step_runs_on_pull_request(
        self, forgejo_web_workflow: dict
    ) -> None:
        """The workflow must trigger on pull_request for PR comment posting."""
        # PyYAML (YAML 1.1) parses bare `on:` as boolean True — check both keys.
        triggers = forgejo_web_workflow.get("on") or forgejo_web_workflow.get(True, {})
        assert "pull_request" in triggers, (
            "web.yml does not trigger on pull_request — "
            "coverage PR comments cannot be posted"
        )

    def test_coverage_report_step_runs_if_pr(self, web_steps: list[dict]) -> None:
        """The coverage comment step should guard itself to PR event contexts.

        A common pattern is:
            if: github.event_name == 'pull_request'

        Without this guard the step will fail on push events where there is
        no PR to comment on.  This test also implicitly verifies that the
        coverage comment step exists — if no recognised action is found we fail.
        """
        known_comment_actions = (
            "davelosert/vitest-coverage-report-action",
            "romeovs/lcov-reporter-action",
            "orgoro/coverage",
            "codecov/codecov-action",
        )
        found = False
        for step in web_steps:
            uses = step.get("uses", "")
            if any(action in uses for action in known_comment_actions):
                found = True
                condition = step.get("if", "")
                assert "pull_request" in condition, (
                    f"Coverage comment step '{step.get('name', uses)}' has no "
                    "'if: github.event_name == pull_request' guard — it will fail "
                    "on push events where no PR exists"
                )
        assert found, (
            "No recognised coverage-comment action found in web.yml — "
            "the 'if: pull_request' guard cannot be verified without the action step"
        )
