"""Shared fixtures for CI workflow validation tests (US005).

Parses each Forgejo/GitHub Actions workflow YAML file once per session and
exposes the parsed structure as pytest fixtures.  Tests then make assertions
against that structure to verify the three missing pipeline behaviours:

  1. Dependency vulnerability scanning (pip-audit / cargo audit / pnpm audit)
  2. Affected-only test runs via Turborepo --affected flag
  3. Coverage reports surfaced as PR comments
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parents[2]

# Both Forgejo and GitHub Actions directories are kept in sync; we validate
# the Forgejo directory (the canonical CI source) throughout.
FORGEJO_DIR = ROOT / ".forgejo" / "workflows"
GITHUB_DIR = ROOT / ".github" / "workflows"


def _load_workflow(directory: Path, filename: str) -> dict[str, Any]:
    """Load and parse a single workflow YAML file."""
    path = directory / filename
    with open(path) as fh:
        data = yaml.safe_load(fh)
    return data  # type: ignore[return-value]


def _collect_step_names(workflow: dict[str, Any]) -> list[str]:
    """Return all step ``name`` values across every job in the workflow."""
    names: list[str] = []
    for job in workflow.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "name" in step:
                names.append(step["name"])
    return names


def _collect_step_run_scripts(workflow: dict[str, Any]) -> list[str]:
    """Return all ``run`` script bodies across every job in the workflow."""
    scripts: list[str] = []
    for job in workflow.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                scripts.append(step["run"])
    return scripts


def _collect_all_step_fields(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every step dict (with all fields) across every job."""
    steps: list[dict[str, Any]] = []
    for job in workflow.get("jobs", {}).values():
        steps.extend(job.get("steps", []))
    return steps


# ---------------------------------------------------------------------------
# Forgejo workflow fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def forgejo_python_workflow() -> dict[str, Any]:
    return _load_workflow(FORGEJO_DIR, "python.yml")


@pytest.fixture(scope="session")
def forgejo_web_workflow() -> dict[str, Any]:
    return _load_workflow(FORGEJO_DIR, "web.yml")


@pytest.fixture(scope="session")
def forgejo_rust_workflow() -> dict[str, Any]:
    return _load_workflow(FORGEJO_DIR, "rust.yml")


# Convenience: step names and run scripts extracted for each workflow


@pytest.fixture(scope="session")
def python_step_names(forgejo_python_workflow: dict[str, Any]) -> list[str]:
    return _collect_step_names(forgejo_python_workflow)


@pytest.fixture(scope="session")
def python_run_scripts(forgejo_python_workflow: dict[str, Any]) -> list[str]:
    return _collect_step_run_scripts(forgejo_python_workflow)


@pytest.fixture(scope="session")
def python_steps(forgejo_python_workflow: dict[str, Any]) -> list[dict[str, Any]]:
    return _collect_all_step_fields(forgejo_python_workflow)


@pytest.fixture(scope="session")
def web_step_names(forgejo_web_workflow: dict[str, Any]) -> list[str]:
    return _collect_step_names(forgejo_web_workflow)


@pytest.fixture(scope="session")
def web_run_scripts(forgejo_web_workflow: dict[str, Any]) -> list[str]:
    return _collect_step_run_scripts(forgejo_web_workflow)


@pytest.fixture(scope="session")
def web_steps(forgejo_web_workflow: dict[str, Any]) -> list[dict[str, Any]]:
    return _collect_all_step_fields(forgejo_web_workflow)


@pytest.fixture(scope="session")
def rust_step_names(forgejo_rust_workflow: dict[str, Any]) -> list[str]:
    return _collect_step_names(forgejo_rust_workflow)


@pytest.fixture(scope="session")
def rust_run_scripts(forgejo_rust_workflow: dict[str, Any]) -> list[str]:
    return _collect_step_run_scripts(forgejo_rust_workflow)


@pytest.fixture(scope="session")
def rust_steps(forgejo_rust_workflow: dict[str, Any]) -> list[dict[str, Any]]:
    return _collect_all_step_fields(forgejo_rust_workflow)
