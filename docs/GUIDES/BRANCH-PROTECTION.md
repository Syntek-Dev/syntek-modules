# Branch Protection Guide — syntek-modules

**Last Updated:** 08/03/2026 | **Audience:** Repository maintainers only\
**Language:** British English (en_GB)

---

## Overview

Branch protection rules are managed **exclusively by the repository owner** via the GitHub and
Forgejo web UIs. No scripts or automation tools are provided to modify these rules — this is
intentional to prevent accidental or unauthorised changes.

If you believe a rule needs updating, open an issue and tag a maintainer. Do not attempt to modify
protection rules directly.

---

## Table of Contents

- [Branch Flow](#branch-flow)
- [GitHub Branch Protection Rules](#github-branch-protection-rules)
- [Forgejo Branch Protection Rules](#forgejo-branch-protection-rules)
- [Required CI Checks](#required-ci-checks)
- [Applying or Updating Rules](#applying-or-updating-rules)

---

## Branch Flow

```text
us###/feature → testing → dev → staging → main
```

| Branch       | Purpose                            |
| ------------ | ---------------------------------- |
| `main`       | Production-ready code              |
| `staging`    | Client review and acceptance       |
| `dev`        | Integration testing                |
| `testing`    | QA verification                    |
| `us###/name` | Feature work — no protection rules |

---

## GitHub Branch Protection Rules

Rules are applied to four branches. All branches block direct pushes and force pushes.

### `testing`

| Rule                    | Setting                         |
| ----------------------- | ------------------------------- |
| Required reviewers      | 1                               |
| Dismiss stale reviews   | No                              |
| Required status checks  | `web`, `python`, `rust`         |
| Strict status checks    | Yes (branch must be up to date) |
| Enforce admins          | No                              |
| Linear history required | No                              |
| Allow force pushes      | No                              |
| Allow deletions         | No                              |

### `dev`

| Rule                    | Setting                 |
| ----------------------- | ----------------------- |
| Required reviewers      | 1                       |
| Dismiss stale reviews   | Yes                     |
| Required status checks  | `web`, `python`, `rust` |
| Strict status checks    | Yes                     |
| Enforce admins          | No                      |
| Linear history required | No                      |
| Allow force pushes      | No                      |
| Allow deletions         | No                      |

### `staging`

| Rule                    | Setting                 |
| ----------------------- | ----------------------- |
| Required reviewers      | 2                       |
| Dismiss stale reviews   | Yes                     |
| Required status checks  | `web`, `python`, `rust` |
| Strict status checks    | Yes                     |
| Enforce admins          | No                      |
| Linear history required | Yes                     |
| Allow force pushes      | No                      |
| Allow deletions         | No                      |

### `main`

| Rule                    | Setting                                 |
| ----------------------- | --------------------------------------- |
| Required reviewers      | 2                                       |
| Dismiss stale reviews   | Yes                                     |
| Required status checks  | `web`, `python`, `rust`, `drift-check`  |
| Strict status checks    | Yes                                     |
| Enforce admins          | **Yes** — no bypassing, even for admins |
| Linear history required | Yes                                     |
| Allow force pushes      | No                                      |
| Allow deletions         | No                                      |

---

## Forgejo Branch Protection Rules

Forgejo branch protection is configured via the web UI at `git.syntek-studio.com`.

Navigate to: **Repository → Settings → Branches → Add Protected Branch**

Apply the same rules as GitHub (see tables above) to the same four branches: `testing`, `dev`,
`staging`, and `main`.

> Forgejo's API for branch protection differs from GitHub's, so rules must be applied manually via
> the web UI rather than scripted.

---

## Required CI Checks

| Check         | Branches                    | Workflow file                         |
| ------------- | --------------------------- | ------------------------------------- |
| `web`         | testing, dev, staging, main | `.github/workflows/web.yml`           |
| `python`      | testing, dev, staging, main | `.github/workflows/python.yml`        |
| `rust`        | testing, dev, staging, main | `.github/workflows/rust.yml`          |
| `drift-check` | **main only**               | `.github/workflows/graphql-drift.yml` |

`drift-check` is path-scoped to GraphQL schema changes. It is only required on `main` to avoid
blocking non-GraphQL PRs on lower branches.

---

## Applying or Updating Rules

Branch protection rules are managed **manually** by a repository owner with admin access.

**GitHub:**

1. Go to **Repository → Settings → Branches** on GitHub.
2. Click **Edit** next to the branch you want to update.
3. Apply the settings from the tables above.
4. Click **Save changes**.

**Forgejo:**

1. Go to **Repository → Settings → Branches** on `git.syntek-studio.com`.
2. Add or edit the protected branch.
3. Apply the equivalent settings.

If you need to change a rule, open an issue explaining the reason. Maintainers will review and apply
the change.

---

## Related Guides

| Guide                   | Purpose                                 |
| ----------------------- | --------------------------------------- |
| `.claude/GIT-GUIDE.md`  | Commit and push workflow                |
| `CONTRIBUTING.md`       | Contribution guidelines and PR workflow |
| `docs/GUIDES/ISSUES.md` | How to report bugs and request features |
