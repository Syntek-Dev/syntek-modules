use anyhow::Result;
use std::process;

use crate::cli::TestArgs;
use crate::config;
use crate::process as proc;
use crate::ui;

pub async fn run(args: TestArgs) -> Result<()> {
    let root = config::find_root()?;
    let mut failed: u32 = 0;

    // Run all layers when no specific flag is set.
    let run_all = !args.python && !args.rust && !args.web && !args.mobile && !args.e2e;

    ui::header("syntek-modules — Test Suite");

    // -----------------------------------------------------------------------
    // Python / Django — pytest
    // -----------------------------------------------------------------------
    if run_all || args.python {
        ui::section("Layer: Python — pytest");

        let pytest = config::venv_bin(&root, "pytest");

        let pkg: Option<String> = args
            .python_package
            .as_deref()
            .map(|p| format!("packages/backend/{}", p));

        let marker = args.marker.clone().unwrap_or_default();
        let pattern = args.pattern.clone().unwrap_or_default();

        let mut a: Vec<&str> = Vec::new();
        if let Some(ref p) = pkg {
            a.push(p.as_str());
        }
        if args.marker.is_some() {
            a.extend_from_slice(&["-m", &marker]);
        }
        if args.pattern.is_some() {
            a.extend_from_slice(&["-k", &pattern]);
        }
        if args.coverage {
            a.extend_from_slice(&["--cov", "--cov-report=html"]);
        }

        if !proc::run(&pytest, &a, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // Rust — cargo test
    // -----------------------------------------------------------------------
    if run_all || args.rust {
        ui::section("Layer: Rust — cargo test");

        if !proc::run("cargo", &["test", "--all"], &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // TypeScript / web — pnpm test (Vitest via Turborepo)
    // -----------------------------------------------------------------------
    if run_all || args.web {
        ui::section("Layer: TypeScript — Vitest");

        let mut a: Vec<String> = Vec::new();
        if let Some(ref pkg) = args.web_package {
            a.extend(["--filter".to_string(), pkg.clone()]);
        }
        a.push("test".to_string());
        if args.watch {
            a.push("--".to_string());
            a.push("--watch".to_string());
        }
        if args.coverage {
            a.push("--".to_string());
            a.push("--coverage".to_string());
        }
        let refs: Vec<&str> = a.iter().map(String::as_str).collect();

        if !proc::run("pnpm", &refs, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // Mobile — pnpm test (Jest + RNTL)
    // -----------------------------------------------------------------------
    if run_all || args.mobile {
        ui::section("Layer: Mobile — Jest + RNTL");

        let mut a = vec!["--filter", "@syntek/mobile-*", "test"];
        if args.watch {
            a.extend_from_slice(&["--", "--watch"]);
        }
        if args.coverage {
            a.extend_from_slice(&["--", "--coverage"]);
        }

        if !proc::run("pnpm", &a, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // E2E — Playwright
    // -----------------------------------------------------------------------
    if args.e2e {
        ui::section("Layer: E2E — Playwright");

        if !proc::run("pnpm", &["test:e2e"], &root).await? {
            failed += 1;
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
