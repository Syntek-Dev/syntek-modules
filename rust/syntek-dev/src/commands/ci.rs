use anyhow::Result;
use std::process;

use crate::config;
use crate::process as proc;
use crate::ui;

/// Run the full CI pipeline locally, mirroring all GitHub/Forgejo workflows.
///
/// Workflows covered:
///   web.yml         — Prettier, ESLint, markdownlint, type-check, pnpm audit, test, coverage
///   graphql-drift.yml — GraphQL schema drift check
///   python.yml      — ruff check, ruff format, basedpyright, pip-audit, pytest
///   rust.yml        — cargo fmt, clippy, cargo test, cargo audit, cargo llvm-cov
pub async fn run() -> Result<()> {
    let root = config::find_root()?;
    let mut failed: Vec<&str> = Vec::new();
    let mut step: u32 = 0;
    let total: u32 = 18;

    ui::header("syntek-modules — CI (local)");

    // ===================================================================
    // web.yml — Prettier, ESLint, markdownlint, type-check, test, coverage
    // ===================================================================

    // 1. Prettier
    step += 1;
    ui::section(&format!("{step}/{total}  Prettier — format check"));
    if !proc::run("pnpm", &["format:check"], &root).await? {
        failed.push("prettier");
    }

    // 2. ESLint
    step += 1;
    ui::section(&format!("{step}/{total}  ESLint — TypeScript / JS"));
    if !proc::run("pnpm", &["lint"], &root).await? {
        failed.push("eslint");
    }

    // 3. Markdownlint
    step += 1;
    ui::section(&format!("{step}/{total}  Markdownlint"));
    if !proc::run("pnpm", &["lint:md"], &root).await? {
        failed.push("markdownlint");
    }

    // 4. TypeScript type-check
    step += 1;
    ui::section(&format!("{step}/{total}  TypeScript — type-check"));
    if !proc::run("pnpm", &["type-check"], &root).await? {
        failed.push("type-check");
    }

    // 5. pnpm security audit
    step += 1;
    ui::section(&format!("{step}/{total}  TypeScript — pnpm audit"));
    if !proc::run("pnpm", &["audit", "--audit-level=high"], &root).await? {
        failed.push("pnpm-audit");
    }

    // 6. TypeScript test
    step += 1;
    ui::section(&format!("{step}/{total}  TypeScript — test"));
    if !proc::run("pnpm", &["test"], &root).await? {
        failed.push("test");
    }

    // 7. TypeScript coverage (json-summary + json + text reporters, matches web.yml)
    step += 1;
    ui::section(&format!("{step}/{total}  TypeScript — coverage"));
    if !proc::run(
        "pnpm",
        &[
            "turbo",
            "run",
            "test",
            "--affected",
            "--",
            "--coverage",
            "--coverage.reporter=json-summary",
            "--coverage.reporter=json",
            "--coverage.reporter=text",
        ],
        &root,
    )
    .await?
    {
        failed.push("coverage");
    }

    // ===================================================================
    // graphql-drift.yml — schema drift check
    // ===================================================================

    // 8. GraphQL schema drift
    step += 1;
    ui::section(&format!("{step}/{total}  GraphQL — schema drift check"));
    if !proc::run(
        "pnpm",
        &["--filter", "@syntek/graphql", "codegen:check"],
        &root,
    )
    .await?
    {
        failed.push("graphql-drift");
    }

    // ===================================================================
    // python.yml — ruff, basedpyright, pytest
    // ===================================================================

    let has_uv = proc::exists("uv");

    // 8. ruff check
    step += 1;
    ui::section(&format!("{step}/{total}  Python — ruff check"));
    if has_uv {
        if !proc::run("uv", &["run", "ruff", "check", "packages/backend/"], &root).await? {
            failed.push("ruff-check");
        }
    } else {
        ui::warn("uv not found — skipping Python checks");
    }

    // 9. ruff format check
    step += 1;
    ui::section(&format!("{step}/{total}  Python — ruff format check"));
    if has_uv {
        if !proc::run(
            "uv",
            &["run", "ruff", "format", "--check", "packages/backend/"],
            &root,
        )
        .await?
        {
            failed.push("ruff-format");
        }
    } else {
        ui::warn("uv not found — skipping");
    }

    // 10. basedpyright
    step += 1;
    ui::section(&format!("{step}/{total}  Python — basedpyright"));
    if has_uv {
        if !proc::run("uv", &["run", "basedpyright", "packages/backend/"], &root).await? {
            failed.push("basedpyright");
        }
    } else {
        ui::warn("uv not found — skipping");
    }

    // 11. pip-audit
    step += 1;
    ui::section(&format!("{step}/{total}  Python — pip-audit"));
    if has_uv {
        if !proc::run("uvx", &["pip-audit"], &root).await? {
            failed.push("pip-audit");
        }
    } else {
        ui::warn("uv not found — skipping");
    }

    // 12. pytest (exit code 5 = no tests collected, tolerated early on)
    step += 1;
    ui::section(&format!("{step}/{total}  Python — pytest"));
    if has_uv {
        let status = tokio::process::Command::new("uv")
            .args([
                "run",
                "pytest",
                "packages/backend/",
                "-x",
                "-q",
                "--cov=packages/backend/",
                "--cov-report=xml:coverage.xml",
                "--cov-report=term-missing",
            ])
            .current_dir(&root)
            .status()
            .await?;
        match status.code() {
            Some(0) => {}
            Some(5) => {
                ui::warn("No tests collected — OK until backend packages have tests");
            }
            _ => {
                failed.push("pytest");
            }
        }
    } else {
        ui::warn("uv not found — skipping");
    }

    // ===================================================================
    // rust.yml — fmt, clippy, test, cargo audit
    // ===================================================================

    let has_cargo = proc::exists("cargo");

    // 15. cargo fmt
    step += 1;
    ui::section(&format!("{step}/{total}  Rust — cargo fmt check"));
    if has_cargo {
        if !proc::run("cargo", &["fmt", "--all", "--", "--check"], &root).await? {
            failed.push("cargo-fmt");
        }
    } else {
        ui::warn("cargo not found — skipping Rust checks");
    }

    // 16. clippy
    step += 1;
    ui::section(&format!("{step}/{total}  Rust — clippy"));
    if has_cargo {
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
    } else {
        ui::warn("cargo not found — skipping");
    }

    // 17. cargo test
    step += 1;
    ui::section(&format!("{step}/{total}  Rust — cargo test"));
    if has_cargo {
        if !proc::run("cargo", &["test", "--all"], &root).await? {
            failed.push("cargo-test");
        }
    } else {
        ui::warn("cargo not found — skipping");
    }

    // 17. cargo audit
    step += 1;
    ui::section(&format!("{step}/{total}  Rust — cargo audit"));
    if has_cargo {
        if !proc::run(
            "cargo",
            &["audit", "--deny", "unsound", "--deny", "yanked"],
            &root,
        )
        .await?
        {
            failed.push("cargo-audit");
        }
    } else {
        ui::warn("cargo not found — skipping");
    }

    // 18. cargo llvm-cov (matches rust.yml coverage step)
    step += 1;
    ui::section(&format!("{step}/{total}  Rust — coverage (cargo llvm-cov)"));
    if has_cargo {
        if !proc::run(
            "cargo",
            &["llvm-cov", "--all", "--lcov", "--output-path", "lcov.info"],
            &root,
        )
        .await?
        {
            failed.push("cargo-llvm-cov");
        }
    } else {
        ui::warn("cargo not found — skipping");
    }

    // ===================================================================
    // Summary
    // ===================================================================
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
