use anyhow::Result;
use std::process;

use crate::cli::AuditArgs;
use crate::config;
use crate::process as proc;
use crate::ui;

pub async fn run(args: AuditArgs) -> Result<()> {
    let root = config::find_root()?;
    let mut failed: u32 = 0;

    // Run all layers when no specific flag is set.
    let run_all = !args.python && !args.rust && !args.js;

    ui::header("syntek-modules — Audit");

    // -----------------------------------------------------------------------
    // Python — pip-audit (CVE / vulnerability scan)
    // -----------------------------------------------------------------------
    if run_all || args.python {
        let has_uv = proc::exists("uv");

        ui::section("pip-audit — Python vulnerability scan");
        if has_uv {
            // `--with pip-audit` injects pip-audit into an ephemeral layer on
            // top of the project's managed environment — no permanent install needed.
            if !proc::run("uv", &["run", "--with", "pip-audit", "pip-audit"], &root).await? {
                failed += 1;
            }
        } else {
            ui::warn("uv not found — skipping Python audit");
        }

        if args.outdated {
            ui::section("uv pip list --outdated — Python packages");
            if has_uv {
                // `uv pip list --outdated` operates on the project's managed
                // venv without requiring pip to be installed inside it.
                // Non-zero exit only occurs on a uv error, not merely because
                // outdated packages exist, so treat as informational.
                if !proc::run("uv", &["pip", "list", "--outdated"], &root).await? {
                    ui::warn(
                        "Outdated Python dependencies detected — review and update pyproject.toml",
                    );
                }
            } else {
                ui::warn("uv not found — skipping Python outdated check");
            }
        }
    }

    // -----------------------------------------------------------------------
    // Rust — cargo audit (RustSec advisory database)
    // -----------------------------------------------------------------------
    if run_all || args.rust {
        let has_cargo = proc::exists("cargo");

        ui::section("cargo audit — Rust vulnerability scan");
        if has_cargo {
            if proc::exists("cargo-audit") || cargo_subcommand_exists("audit") {
                if !proc::run(
                    "cargo",
                    &["audit", "--deny", "unsound", "--deny", "yanked"],
                    &root,
                )
                .await?
                {
                    failed += 1;
                }
            } else {
                ui::warn("cargo-audit not installed — run: cargo install cargo-audit");
            }
        } else {
            ui::warn("cargo not found — skipping Rust audit");
        }

        if args.outdated {
            ui::section("cargo outdated — Rust packages");
            if has_cargo {
                if proc::exists("cargo-outdated") || cargo_subcommand_exists("outdated") {
                    // --exit-code 1 makes cargo-outdated exit non-zero when any
                    // crate has an update available, treating it as a soft failure.
                    if !proc::run("cargo", &["outdated", "--exit-code", "1"], &root).await? {
                        ui::warn(
                            "Outdated Rust dependencies detected — review and update Cargo.toml",
                        );
                        // Informational only: do not increment `failed` so that
                        // outdated packages do not block a `syntek-dev audit` run.
                    }
                } else {
                    ui::warn("cargo-outdated not installed — run: cargo install cargo-outdated");
                }
            } else {
                ui::warn("cargo not found — skipping Rust outdated check");
            }
        }
    }

    // -----------------------------------------------------------------------
    // JS / TS — pnpm audit (npm advisory database)
    // -----------------------------------------------------------------------
    if run_all || args.js {
        ui::section("pnpm audit — JS/TS vulnerability scan");
        // --audit-level=moderate surfaces moderate, high, and critical findings.
        // Exit code is non-zero when the threshold is met, so treat as failure.
        if !proc::run("pnpm", &["audit", "--audit-level=moderate"], &root).await? {
            failed += 1;
        }

        if args.outdated {
            ui::section("pnpm outdated — JS/TS packages");
            // pnpm outdated exits non-zero when outdated packages are found.
            // Treat as informational: warn but do not fail the overall audit.
            if !proc::run("pnpm", &["outdated"], &root).await? {
                ui::warn("Outdated JS/TS dependencies detected — review and update package.json");
            }
        }
    }

    // -----------------------------------------------------------------------
    // Summary
    // -----------------------------------------------------------------------
    if failed == 0 {
        ui::summary_pass();
    } else {
        ui::summary_fail(failed);
        process::exit(1);
    }

    Ok(())
}

/// Returns true if `cargo <subcommand>` is available as an installed subcommand.
/// This covers the case where the binary is named e.g. `cargo-audit` but is
/// invoked as `cargo audit` — which::which won't find "cargo audit" directly.
fn cargo_subcommand_exists(subcommand: &str) -> bool {
    let binary = format!("cargo-{subcommand}");
    which::which(&binary).is_ok()
}
