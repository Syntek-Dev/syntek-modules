use anyhow::Result;
use std::process;

use crate::config;
use crate::process as proc;
use crate::ui;

/// Run the full CI pipeline locally, mirroring what GitHub/Forgejo workflows execute.
/// Runs each step sequentially and reports a summary at the end.
pub async fn run() -> Result<()> {
    let root = config::find_root()?;
    let mut failed: Vec<&str> = Vec::new();

    ui::header("syntek-modules — CI (local)");

    // -----------------------------------------------------------------------
    // 1. Prettier — format check (matches CI: pnpm format:check)
    // -----------------------------------------------------------------------
    ui::section("1/6  Prettier — format check");
    if !proc::run("pnpm", &["format:check"], &root).await? {
        failed.push("prettier");
    }

    // -----------------------------------------------------------------------
    // 2. ESLint (matches CI: pnpm lint)
    // -----------------------------------------------------------------------
    ui::section("2/6  ESLint — TypeScript / JS");
    if !proc::run("pnpm", &["lint"], &root).await? {
        failed.push("eslint");
    }

    // -----------------------------------------------------------------------
    // 3. Markdownlint (matches CI: pnpm lint:md)
    // -----------------------------------------------------------------------
    ui::section("3/6  Markdownlint");
    if !proc::run("pnpm", &["lint:md"], &root).await? {
        failed.push("markdownlint");
    }

    // -----------------------------------------------------------------------
    // 4. TypeScript type-check (matches CI: pnpm type-check)
    // -----------------------------------------------------------------------
    ui::section("4/6  TypeScript — type-check");
    if !proc::run("pnpm", &["type-check"], &root).await? {
        failed.push("type-check");
    }

    // -----------------------------------------------------------------------
    // 5. TypeScript tests (matches CI: pnpm test)
    // -----------------------------------------------------------------------
    ui::section("5/6  TypeScript — test");
    if !proc::run("pnpm", &["test"], &root).await? {
        failed.push("test");
    }

    // -----------------------------------------------------------------------
    // 6. Rust — fmt + clippy + test
    // -----------------------------------------------------------------------
    ui::section("6/6  Rust — fmt, clippy, test");

    if proc::exists("cargo") {
        if !proc::run("cargo", &["fmt", "--all", "--", "--check"], &root).await? {
            failed.push("cargo-fmt");
        }
        if !proc::run(
            "cargo",
            &[
                "clippy",
                "--all-targets",
                "--all-features",
                "--",
                "-D",
                "warnings",
            ],
            &root,
        )
        .await?
        {
            failed.push("clippy");
        }
        if !proc::run("cargo", &["test", "--all"], &root).await? {
            failed.push("cargo-test");
        }
    } else {
        ui::warn("cargo not found — skipping Rust checks");
    }

    // -----------------------------------------------------------------------
    // Summary
    // -----------------------------------------------------------------------
    if failed.is_empty() {
        ui::summary_pass();
        ui::step("Safe to push.");
    } else {
        println!();
        ui::error(&format!("Failed: {}", failed.join(", ")));
        ui::summary_fail(failed.len() as u32);
        process::exit(1);
    }

    Ok(())
}
