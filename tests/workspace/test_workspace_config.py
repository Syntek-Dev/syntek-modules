"""Unit tests — workspace configuration file structure (US001).

Verifies that pnpm-workspace.yaml, pyproject.toml, Cargo.toml, and turbo.json
declare the correct members and pipeline tasks required by the monorepo.

Red phase: all tests should pass once config files are correct. Tests for
packages that don't yet exist (syntek-auth etc.) will fail until scaffolded.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# pnpm workspace
# ---------------------------------------------------------------------------


class TestPnpmWorkspace:
    """pnpm-workspace.yaml declares the required package globs."""

    def test_web_packages_declared(self, pnpm_workspace: dict) -> None:
        assert "packages/web/*" in pnpm_workspace["packages"]

    def test_mobile_packages_declared(self, pnpm_workspace: dict) -> None:
        assert "mobile/*" in pnpm_workspace["packages"]

    def test_shared_packages_declared(self, pnpm_workspace: dict) -> None:
        assert "shared/*" in pnpm_workspace["packages"]


# ---------------------------------------------------------------------------
# uv workspace
# ---------------------------------------------------------------------------


class TestUvWorkspace:
    """pyproject.toml declares the uv workspace with correct members."""

    def test_uv_workspace_section_exists(self, root_pyproject: dict) -> None:
        assert "uv" in root_pyproject.get("tool", {})
        assert "workspace" in root_pyproject["tool"]["uv"]

    def test_backend_members_glob(self, root_pyproject: dict) -> None:
        members = root_pyproject["tool"]["uv"]["workspace"]["members"]
        assert "packages/backend/*" in members

    def test_python_version_constraint(self, root_pyproject: dict) -> None:
        requires_python = root_pyproject.get("project", {}).get("requires-python", "")
        assert "3.14" in requires_python, (
            f"requires-python must enforce >=3.14, got: '{requires_python}'"
        )

    def test_ruff_target_version_matches(self, root_pyproject: dict) -> None:
        target = root_pyproject["tool"]["ruff"].get("target-version", "")
        assert "py314" in target


# ---------------------------------------------------------------------------
# Cargo workspace
# ---------------------------------------------------------------------------


EXPECTED_RUST_CRATES = [
    "rust/syntek-crypto",
    "rust/syntek-pyo3",
    "rust/syntek-graphql-crypto",
    "rust/syntek-dev",
    "rust/syntek-manifest",
]


class TestCargoWorkspace:
    """Cargo.toml declares all Rust crates with correct workspace settings."""

    def test_workspace_resolver_v2(self, root_cargo_toml: dict) -> None:
        assert root_cargo_toml["workspace"]["resolver"] == "2"

    def test_edition_2024(self, root_cargo_toml: dict) -> None:
        assert root_cargo_toml["workspace"]["package"]["edition"] == "2024"

    @pytest.mark.parametrize("crate", EXPECTED_RUST_CRATES)
    def test_crate_member_declared(self, root_cargo_toml: dict, crate: str) -> None:
        members = root_cargo_toml["workspace"]["members"]
        assert crate in members, f"Rust crate not in workspace members: {crate}"

    def test_encryption_deps_declared(self, root_cargo_toml: dict) -> None:
        deps = root_cargo_toml["workspace"].get("dependencies", {})
        for dep in ("aes-gcm", "argon2", "hmac", "sha2", "zeroize"):
            assert dep in deps, f"Missing workspace dependency: {dep}"

    def test_release_profile_lto(self, root_cargo_toml: dict) -> None:
        assert root_cargo_toml["profile"]["release"]["lto"] is True


# ---------------------------------------------------------------------------
# Turborepo pipeline
# ---------------------------------------------------------------------------


REQUIRED_TURBO_TASKS = ["build", "test", "lint", "type-check", "dev"]


class TestTurboPipeline:
    """turbo.json defines all required pipeline tasks."""

    @pytest.mark.parametrize("task", REQUIRED_TURBO_TASKS)
    def test_task_declared(self, turbo_config: dict, task: str) -> None:
        assert task in turbo_config["tasks"], f"Missing turbo task: {task}"

    def test_build_depends_on_upstream(self, turbo_config: dict) -> None:
        assert "^build" in turbo_config["tasks"]["build"]["dependsOn"]

    def test_test_task_has_coverage_output(self, turbo_config: dict) -> None:
        outputs = turbo_config["tasks"]["test"].get("outputs", [])
        assert any("coverage" in o for o in outputs)

    def test_dev_is_persistent(self, turbo_config: dict) -> None:
        assert turbo_config["tasks"]["dev"]["persistent"] is True

    def test_dev_not_cached(self, turbo_config: dict) -> None:
        assert turbo_config["tasks"]["dev"]["cache"] is False


# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------


class TestDirectoryStructure:
    """Required top-level directories exist."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "packages/backend",
            "packages/web",
            "mobile",
            "rust",
            "shared",
            "docs",
        ],
    )
    def test_directory_exists(self, repo_root, rel_path: str) -> None:
        assert (repo_root / rel_path).is_dir(), f"Missing directory: {rel_path}"

    @pytest.mark.parametrize("crate_dir", EXPECTED_RUST_CRATES)
    def test_rust_crate_directory_exists(self, repo_root, crate_dir: str) -> None:
        assert (repo_root / crate_dir).is_dir(), f"Missing Rust crate dir: {crate_dir}"

    def test_rust_crate_has_cargo_toml(self, repo_root) -> None:
        for crate in EXPECTED_RUST_CRATES:
            assert (repo_root / crate / "Cargo.toml").exists(), (
                f"Missing Cargo.toml in {crate}"
            )
