# Versioning Guide — syntek-modules

---

## Table of Contents

- [Version Increment Rules](#version-increment-rules)
- [Root-Level Version Files](#root-level-version-files)
- [Per-Module and Per-Package Versioning](#per-module-and-per-package-versioning)
- [Rust Workspace Version Inheritance](#rust-workspace-version-inheritance)
- [Lock Files](#lock-files)
- [Tooling](#tooling)

---

## Version Increment Rules

| Type  | When                                              | Example         |
| ----- | ------------------------------------------------- | --------------- |
| MAJOR | Breaking changes to any public API or interface   | `1.0.0 → 2.0.0` |
| MINOR | New features, new modules, backwards-compatible   | `1.0.0 → 1.1.0` |
| PATCH | Bug fixes, documentation updates, tooling changes | `1.0.0 → 1.0.1` |

---

## Root-Level Version Files

**ALL of the following files must be updated on every root version bump.** Missing any one of them
leaves the repository in an inconsistent state.

| File                 | What to update                                                                         |
| -------------------- | -------------------------------------------------------------------------------------- |
| `VERSION`            | Replace the plain semver string with the new version                                   |
| `VERSION-HISTORY.md` | Add one summary row to the table (date, version, one-line description)                 |
| `RELEASES.md`        | Add a full release notes section for the new version                                   |
| `CHANGELOG.md`       | Add a detailed changelog entry grouped by Added / Changed / Fixed / Removed / Security |
| `pyproject.toml`     | Update the `version` field in the `[project]` table                                    |
| `package.json`       | Update the `version` field                                                             |
| `Cargo.toml`         | Update the `version` field in the root `[workspace.package]` table                     |

After updating `Cargo.toml`, run `cargo build` (or `cargo build --release -p syntek-dev`) so that
`Cargo.lock` is regenerated. After updating `pyproject.toml`, run `uv sync` so that `uv.lock` is
regenerated. Both lock files must then be staged and included in the version bump commit.

---

## Per-Module and Per-Package Versioning

Each individual package or module has its own version, independent of the root workspace version.

| Layer   | Version file location                           |
| ------- | ----------------------------------------------- |
| Backend | `packages/backend/syntek-<name>/pyproject.toml` |
| Web     | `packages/web/<name>/package.json`              |
| Mobile  | `mobile/<name>/package.json`                    |
| Rust    | `rust/<name>/Cargo.toml` (see below)            |

Release notes for individual module releases go into the **root** `RELEASES.md` and `CHANGELOG.md`,
not into per-module files. `VERSION-HISTORY.md` is a summary table of root workspace version bumps
only — it does not track per-module versions.

---

## Rust Workspace Version Inheritance

All Rust crates in `rust/` use workspace version inheritance:

```toml
# rust/<crate>/Cargo.toml
[package]
version.workspace = true
```

This means the Rust crate version is always read from the root `Cargo.toml` `[workspace.package]`
table. Updating the root `Cargo.toml` version automatically applies to all crates. Do not set an
explicit `version` field in individual crate `Cargo.toml` files.

---

## Lock Files

Lock files are generated automatically — do not edit them by hand.

| Lock file    | Updated by                       | Must be committed |
| ------------ | -------------------------------- | ----------------- |
| `Cargo.lock` | `cargo build` / `cargo update`   | Yes               |
| `uv.lock`    | `uv sync` / `uv add` / `uv lock` | Yes               |

Both lock files must be staged and committed as part of every version bump commit. The Rust
workspace `Cargo.lock` is committed even though all crates are libraries, because this is a
development repository rather than a published library consumed by others.

---

## Tooling

Use the `/syntek-dev-suite:version` skill to manage version bumps. This skill automates the
multi-file update process described above and ensures no file is missed.

Manual version bumps are permitted but must touch every file listed in
[Root-Level Version Files](#root-level-version-files) plus the relevant lock files.
