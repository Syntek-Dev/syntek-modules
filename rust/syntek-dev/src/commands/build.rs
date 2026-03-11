use anyhow::Result;
use std::process;

use crate::cli::BuildArgs;
use crate::config;
use crate::process as proc;
use crate::ui;

pub async fn run(args: BuildArgs) -> Result<()> {
    let root = config::find_root()?;
    let mut failed: u32 = 0;

    // Build all layers when no specific flag is set.
    let run_all = !args.rust
        && args.rust_crate.is_none()
        && !args.python
        && args.python_package.is_none()
        && !args.web
        && args.web_package.is_none()
        && !args.mobile;

    ui::header("syntek-modules — Build");

    // -----------------------------------------------------------------------
    // cargo build --release (Rust)
    // -----------------------------------------------------------------------
    if run_all || args.rust || args.rust_crate.is_some() {
        ui::section("cargo build — Rust");

        let cargo_args: Vec<String> = if let Some(ref crate_name) = args.rust_crate {
            vec![
                "build".into(),
                "--release".into(),
                "-p".into(),
                crate_name.clone(),
            ]
        } else {
            vec!["build".into(), "--release".into(), "--all".into()]
        };

        let cargo_str: Vec<&str> = cargo_args.iter().map(String::as_str).collect();

        if !proc::run("cargo", &cargo_str, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // uv sync / uv build (Python)
    // -----------------------------------------------------------------------
    if run_all || args.python || args.python_package.is_some() {
        let uv = config::venv_bin(&root, "uv");

        if let Some(ref pkg) = args.python_package {
            ui::section(&format!("uv build — Python package: {pkg}"));

            if !proc::run(&uv, &["build", "--package", pkg], &root).await? {
                failed += 1;
            }
        } else {
            ui::section("uv sync — Python (dev install)");

            if !proc::run(&uv, &["sync", "--group", "dev"], &root).await? {
                failed += 1;
            }
        }
    }

    // -----------------------------------------------------------------------
    // pnpm turbo run build (web)
    // -----------------------------------------------------------------------
    if run_all || args.web || args.web_package.is_some() {
        if let Some(ref pkg) = args.web_package {
            ui::section(&format!("pnpm build — web package: {pkg}"));

            if !proc::run("pnpm", &["--filter", pkg, "build"], &root).await? {
                failed += 1;
            }
        } else {
            ui::section("turbo run build — web");

            if !proc::run("pnpm", &["turbo", "run", "build"], &root).await? {
                failed += 1;
            }
        }
    }

    // -----------------------------------------------------------------------
    // pnpm --filter @syntek/mobile-* build (mobile)
    // -----------------------------------------------------------------------
    if run_all || args.mobile {
        ui::section("pnpm build — mobile");

        if !proc::run("pnpm", &["--filter", "@syntek/mobile-*", "build"], &root).await? {
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
