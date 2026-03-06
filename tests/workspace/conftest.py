"""Shared fixtures for workspace configuration tests (US001)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[2]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def pnpm_workspace(repo_root: Path) -> dict:
    with open(repo_root / "pnpm-workspace.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def root_pyproject(repo_root: Path) -> dict:
    with open(repo_root / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


@pytest.fixture(scope="session")
def root_cargo_toml(repo_root: Path) -> dict:
    with open(repo_root / "Cargo.toml", "rb") as f:
        return tomllib.load(f)


@pytest.fixture(scope="session")
def turbo_config(repo_root: Path) -> dict:
    with open(repo_root / "turbo.json") as f:
        return json.load(f)
