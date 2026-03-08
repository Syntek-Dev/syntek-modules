#!/usr/bin/env bash
# =============================================================================
# setup-branch-protection.sh
#
# Applies branch protection rules to testing, dev, staging, and main via the
# GitHub API using the `gh` CLI.
#
# Usage:
#   chmod +x .github/setup-branch-protection.sh
#   gh auth login          # if not already authenticated
#   ./.github/setup-branch-protection.sh
#
# Requirements:
#   - gh CLI installed and authenticated (gh auth status)
#   - Repository admin permissions
#
# The REPO variable is auto-detected from `gh repo view`. Override if needed:
#   REPO=Syntek-Dev/syntek-modules ./.github/setup-branch-protection.sh
# =============================================================================

set -euo pipefail

REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"

echo "Applying branch protection rules to: ${REPO}"
echo ""

# -----------------------------------------------------------------------------
# Shared status checks — these are the CI job names from .github/workflows/
# drift-check is path-scoped (graphql changes only) so excluded from required
# checks on lower branches to avoid blocking non-graphql PRs.
# -----------------------------------------------------------------------------

CORE_CHECKS='[
  {"context": "web"},
  {"context": "python"},
  {"context": "rust"}
]'

ALL_CHECKS='[
  {"context": "web"},
  {"context": "python"},
  {"context": "rust"},
  {"context": "drift-check"}
]'

# -----------------------------------------------------------------------------
# testing
#   - 1 approving review required
#   - CI must pass (web, python, rust)
#   - No direct pushes
#   - Stale reviews not dismissed (active QA branch)
# -----------------------------------------------------------------------------
echo "→ Applying rules to: testing"
gh api \
  --method PUT \
  "repos/${REPO}/branches/testing/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "checks": ${CORE_CHECKS}
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "   ✓ testing"

# -----------------------------------------------------------------------------
# dev
#   - 1 approving review required
#   - CI must pass (web, python, rust)
#   - No direct pushes
#   - Stale reviews dismissed on new commits
# -----------------------------------------------------------------------------
echo "→ Applying rules to: dev"
gh api \
  --method PUT \
  "repos/${REPO}/branches/dev/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "checks": ${CORE_CHECKS}
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "   ✓ dev"

# -----------------------------------------------------------------------------
# staging
#   - 2 approving reviews required
#   - CI must pass (web, python, rust)
#   - No direct pushes
#   - Stale reviews dismissed
#   - Linear history required
# -----------------------------------------------------------------------------
echo "→ Applying rules to: staging"
gh api \
  --method PUT \
  "repos/${REPO}/branches/staging/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "checks": ${CORE_CHECKS}
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "   ✓ staging"

# -----------------------------------------------------------------------------
# main
#   - 2 approving reviews required
#   - All CI checks must pass (web, python, rust, drift-check)
#   - Enforce admins — no bypassing rules
#   - Stale reviews dismissed
#   - Linear history required
#   - No force pushes, no deletions
# -----------------------------------------------------------------------------
echo "→ Applying rules to: main"
gh api \
  --method PUT \
  "repos/${REPO}/branches/main/protection" \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "checks": ${ALL_CHECKS}
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "   ✓ main"

echo ""
echo "Branch protection rules applied successfully."
echo ""
echo "Summary:"
echo "  testing  — 1 reviewer, CI required, no direct push"
echo "  dev      — 1 reviewer, CI required, no direct push, dismiss stale reviews"
echo "  staging  — 2 reviewers, CI required, no direct push, linear history"
echo "  main     — 2 reviewers, all CI required, enforce admins, linear history"
