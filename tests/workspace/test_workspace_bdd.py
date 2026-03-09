"""BDD integration tests — US001 workspace resolution acceptance criteria.

Each scenario maps directly to a Gherkin scenario in
features/workspace_resolution.feature and invokes real toolchain commands.

Red phase failures expected:
  - pnpm install: will fail until web/mobile packages have package.json files
  - uv pip install syntek-auth: will fail until syntek-auth pyproject.toml exists
  - dev.sh / test.sh: will fail until those scripts are created
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

ROOT = Path(__file__).parents[2]

scenarios("features/workspace_resolution.feature")

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Shared context fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def context() -> dict:
    return {"root": ROOT}


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------


@given("I have a fresh clone of the repository")
def fresh_clone(context: dict) -> None:
    assert context["root"].exists(), "Repository root not found"
    assert (context["root"] / ".git").exists(), "Not a git repository"


# ---------------------------------------------------------------------------
# pnpm scenario
# ---------------------------------------------------------------------------


@when("I run pnpm install from the root")
def run_pnpm_install(context: dict) -> None:
    result = subprocess.run(
        ["pnpm", "install", "--frozen-lockfile"],
        cwd=context["root"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    context["pnpm_result"] = result


@then("all TypeScript workspace packages are linked")
def ts_packages_linked(context: dict) -> None:
    result = context["pnpm_result"]
    assert result.returncode == 0, (
        f"pnpm install failed (exit {result.returncode}):\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# uv scenario
# ---------------------------------------------------------------------------


@when("I activate the uv virtual environment")
def activate_uv_venv(context: dict) -> None:
    context["venv"] = context["root"] / ".venv"


@when("I install syntek-auth with dev dependencies")
def install_syntek_auth(context: dict) -> None:
    package_path = context["root"] / "packages" / "backend" / "syntek-auth"
    assert package_path.is_dir(), (
        f"Package directory does not exist: {package_path} — "
        "scaffold syntek-auth before running this test"
    )
    result = subprocess.run(
        ["uv", "pip", "install", "-e", f"{package_path}[dev]"],
        cwd=context["root"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    context["uv_result"] = result


@then("the package installs without errors")
def uv_install_success(context: dict) -> None:
    result = context["uv_result"]
    assert result.returncode == 0, (
        f"uv pip install failed (exit {result.returncode}):\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# cargo scenario
# ---------------------------------------------------------------------------


@when("I run cargo build from the root")
def run_cargo_build(context: dict) -> None:
    result = subprocess.run(
        ["cargo", "build"],
        cwd=context["root"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    context["cargo_result"] = result


@then("all Rust crates compile without errors")
def cargo_build_success(context: dict) -> None:
    result = context["cargo_result"]
    assert result.returncode == 0, (
        f"cargo build failed (exit {result.returncode}):\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# syntek-dev CLI scenarios (shared When step — both scenarios reuse it)
# ---------------------------------------------------------------------------


@when("I query the syntek-dev CLI help")
def query_syntek_dev_help(context: dict) -> None:
    result = subprocess.run(
        ["syntek-dev", "--help"],
        cwd=context["root"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    context["cli_help"] = result


@then("the up subcommand is listed")
def cli_has_up_subcommand(context: dict) -> None:
    result = context["cli_help"]
    assert result.returncode == 0, f"syntek-dev --help failed:\n{result.stderr}"
    assert "up" in result.stdout, "syntek-dev 'up' subcommand not found in --help output"


@then("the test subcommand is listed")
def cli_has_test_subcommand(context: dict) -> None:
    result = context["cli_help"]
    assert result.returncode == 0, f"syntek-dev --help failed:\n{result.stderr}"
    assert "test" in result.stdout, "syntek-dev 'test' subcommand not found in --help output"
