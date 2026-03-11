# Versioning Guide — syntek-modules

---

## Table of Contents

- [Strategy Overview](#strategy-overview)
- [Version Increment Rules](#version-increment-rules)
- [Track 1 — Root Workspace Version](#track-1--root-workspace-version)
- [Track 2 — Per-Module Version](#track-2--per-module-version)
- [Rust Workspace Version Inheritance](#rust-workspace-version-inheritance)
- [When to Bump Which Track](#when-to-bump-which-track)
- [Inter-Module Dependency Constraints](#inter-module-dependency-constraints)
- [Lock Files](#lock-files)
- [Tooling](#tooling)

---

## Strategy Overview

syntek-modules uses a **formalised hybrid** versioning strategy. There are two independent tracks:

| Track              | What it versions                                                          | Who it serves                               |
| ------------------ | ------------------------------------------------------------------------- | ------------------------------------------- |
| **Root workspace** | The repository as a whole — dev tooling, Rust crates, milestone snapshots | CI, Forgejo releases, internal dev tracking |
| **Per-module**     | Each individually published package                                       | Consumers installing via `syntek add`       |

These two tracks are independent. A per-module bump does **not** require a root bump. A root bump
does **not** require per-module bumps.

**Key principle:** Consumers install individual packages (`syntek add syntek-auth`), not the whole
repository. A fix to `syntek-caldav` must not force a version change notification on `syntek-auth`.
Per-module versioning reflects this reality.

---

## Version Increment Rules

| Type  | When                                              | Example         |
| ----- | ------------------------------------------------- | --------------- |
| MAJOR | Breaking changes to any public API or interface   | `1.0.0 → 2.0.0` |
| MINOR | New features, new modules, backwards-compatible   | `1.0.0 → 1.1.0` |
| PATCH | Bug fixes, documentation updates, tooling changes | `1.0.0 → 1.0.1` |

These rules apply to **both** tracks independently.

---

## Track 1 — Root Workspace Version

The root version tracks the **repository as a whole**: dev tooling changes, Rust crate releases, and
significant multi-module milestones. It does not track every individual module release.

### Files to update on every root bump

**ALL of the following must be updated. Missing any one leaves the repository inconsistent.**

| File                 | What to update                                                               |
| -------------------- | ---------------------------------------------------------------------------- |
| `VERSION`            | Replace the plain semver string                                              |
| `VERSION-HISTORY.md` | Add one summary row (date, version, one-line description)                    |
| `RELEASES.md`        | Add a full release notes section for the new version                         |
| `CHANGELOG.md`       | Add a detailed entry grouped by Added / Changed / Fixed / Removed / Security |
| `pyproject.toml`     | Update the `version` field in `[project]`                                    |
| `package.json`       | Update the `version` field                                                   |
| `Cargo.toml`         | Update `version` in `[workspace.package]`                                    |

After updating `Cargo.toml`, run `cargo build` so `Cargo.lock` is regenerated. After updating
`pyproject.toml`, run `uv sync` so `uv.lock` is regenerated. Both lock files must be staged and
included in the version bump commit.

---

## Track 2 — Per-Module Version

Each published package has its own independent semver in its own version file. This is the version
consumers see in their lockfiles and dependency declarations.

### Version file locations

| Layer   | Version file                                    | Published as                           |
| ------- | ----------------------------------------------- | -------------------------------------- |
| Backend | `packages/backend/syntek-<name>/pyproject.toml` | `syntek-<name>` on Forgejo PyPI        |
| Web     | `packages/web/<name>/package.json`              | `@syntek/<name>` on Forgejo npm        |
| Mobile  | `mobile/<name>/package.json`                    | `@syntek/mobile-<name>` on Forgejo npm |
| Rust    | Workspace-inherited — see below                 | Forgejo Cargo registry                 |

### Files to update on every per-module bump

| File                                  | What to update                                                                     |
| ------------------------------------- | ---------------------------------------------------------------------------------- |
| Module version file (see table above) | Bump the `version` field                                                           |
| Root `CHANGELOG.md`                   | Add an entry under the current root version describing what changed in this module |

**Do not** create per-module `CHANGELOG.md`, `RELEASES.md`, or `VERSION-HISTORY.md` files. All
change history goes into the root files. The root `CHANGELOG.md` is the single source of truth for
what changed across all modules.

### Per-module bump workflow

```
1. Edit packages/backend/syntek-<name>/pyproject.toml  →  bump version field
2. Add entry to root CHANGELOG.md under the current root version heading
3. Run syntek-dev lint --fix && syntek-dev lint
4. Commit: "chore(syntek-<name>): bump X.Y.Z"
```

### Baseline version

All modules start at `0.1.0`. Do not back-fill version history. The current branch is the starting
point for each module's individual version history.

---

## Rust Workspace Version Inheritance

All Rust crates in `rust/` inherit the root workspace version:

```toml
# rust/<crate>/Cargo.toml
[package]
version.workspace = true
```

The three Rust crates (`syntek-crypto`, `syntek-pyo3`, `syntek-graphql-crypto`) form an inseparable
cryptographic chain — `syntek-graphql-crypto` depends on `syntek-pyo3` which depends on
`syntek-crypto`. They move together with the root workspace version.

**Do not** set an explicit `version` field in individual Rust crate `Cargo.toml` files. A Rust crate
release is always a root workspace version bump.

---

## When to Bump Which Track

| Situation                                              | Action                                                                                                                  |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| A single backend module changed (new feature, bug fix) | Per-module bump only. No root bump required.                                                                            |
| A single web or mobile package changed                 | Per-module bump only. No root bump required.                                                                            |
| A Rust crate changed                                   | Root workspace bump (Rust crates inherit the workspace version).                                                        |
| `syntek-dev` CLI changed                               | Root workspace bump (the CLI is workspace tooling).                                                                     |
| Multiple modules released as part of a sprint          | Per-module bump for each changed module. Optionally also a root bump to mark the milestone.                             |
| Breaking change to a module's public API               | Per-module MAJOR bump. If a root bump is also due, bump root to MAJOR.                                                  |
| Sprint milestone / release tag on Forgejo              | Root workspace bump.                                                                                                    |
| Documentation-only change in a module                  | Per-module PATCH bump if the docs are part of the published package (e.g. README). No bump if docs are only in `docs/`. |

---

## Inter-Module Dependency Constraints

When one Syntek module depends on another, declare the minimum compatible version explicitly in the
consuming module's `pyproject.toml`:

```toml
# packages/backend/syntek-permissions/pyproject.toml
dependencies = [
    "syntek-auth>=1.5.0",
]
```

Rules:

- Use `>=` minimum constraints, never pinned exact versions (`==`).
- Update the constraint whenever the dependency's public interface changes in a way that requires a
  minimum version.
- Document cross-module constraints in the root `CHANGELOG.md` when they change.

---

## Lock Files

Lock files are generated automatically — do not edit them by hand.

| Lock file    | Updated by                       | Must be committed |
| ------------ | -------------------------------- | ----------------- |
| `Cargo.lock` | `cargo build` / `cargo update`   | Yes               |
| `uv.lock`    | `uv sync` / `uv add` / `uv lock` | Yes               |

Both lock files must be staged and committed as part of every root version bump commit. Per-module
Python bumps should also include a refreshed `uv.lock` (run `uv sync` after editing
`pyproject.toml`).

---

## Tooling

Use the `/syntek-dev-suite:version` skill to manage version bumps. This skill handles both tracks:

### Root workspace bump

```
/syntek-dev-suite:version bump minor
/syntek-dev-suite:version bump patch
/syntek-dev-suite:version bump major
```

Updates `VERSION`, `VERSION-HISTORY.md`, `CHANGELOG.md`, `RELEASES.md`, `pyproject.toml`,
`package.json`, `Cargo.toml`, and regenerates lock files.

### Per-module bump

```
/syntek-dev-suite:version bump patch --module syntek-auth
/syntek-dev-suite:version bump minor --module syntek-security
/syntek-dev-suite:version bump major --module @syntek/ui
```

Updates only the specified module's version file and appends an entry to the root `CHANGELOG.md`.
Does not touch any other root files.

> **Note:** The `--module` flag requires `syntek-dev version bump --module <name>` support in the
> Rust CLI. Until that is implemented, the version agent bumps module files directly and appends the
> CHANGELOG entry manually.

### Status check

```
/syntek-dev-suite:version status
```

Shows the current root version, which modules have been modified since their last version bump, and
any files that are out of sync.

Manual version bumps are permitted but must touch every file listed in the relevant track above.
