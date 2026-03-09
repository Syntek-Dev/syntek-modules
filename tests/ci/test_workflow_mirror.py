"""CI workflow mirror validation tests (US005).

Asserts that the `.github/workflows/` directory mirrors all workflow files
from the canonical `.forgejo/workflows/` directory byte-for-byte.

This prevents silent divergence between the two directories when a developer
edits one but forgets to update the other.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).parents[2]
FORGEJO_DIR = ROOT / ".forgejo" / "workflows"
GITHUB_DIR = ROOT / ".github" / "workflows"

# Workflow files that must be mirrored (excludes GitHub-only files like codeql.yml)
MIRRORED_WORKFLOWS = [
    "python.yml",
    "web.yml",
    "rust.yml",
    "graphql-drift.yml",
]


class TestWorkflowMirrorSync:
    """The .github/workflows/ directory must mirror .forgejo/workflows/ exactly."""

    @pytest.mark.parametrize("filename", MIRRORED_WORKFLOWS)
    def test_mirror_file_exists(self, filename: str) -> None:
        """Each canonical workflow file must have a corresponding mirror."""
        assert (GITHUB_DIR / filename).exists(), (
            f".github/workflows/{filename} does not exist — "
            f"copy from .forgejo/workflows/{filename}"
        )

    @pytest.mark.parametrize("filename", MIRRORED_WORKFLOWS)
    def test_mirror_file_is_identical(self, filename: str) -> None:
        """Each mirrored file must be byte-identical to its canonical source."""
        forgejo_path = FORGEJO_DIR / filename
        github_path = GITHUB_DIR / filename

        if not forgejo_path.exists():
            pytest.skip(f".forgejo/workflows/{filename} does not exist")
        if not github_path.exists():
            pytest.skip(f".github/workflows/{filename} does not exist")

        forgejo_content = forgejo_path.read_bytes()
        github_content = github_path.read_bytes()

        assert forgejo_content == github_content, (
            f".github/workflows/{filename} has diverged from "
            f".forgejo/workflows/{filename} — update the mirror"
        )
