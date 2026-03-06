use anyhow::Result;
use std::process;

use crate::cli::FormatArgs;
use crate::config;
use crate::process as proc;
use crate::ui;

pub async fn run(args: FormatArgs) -> Result<()> {
    let root = config::find_root()?;
    let mut failed: u32 = 0;

    // Format all layers when no specific flag is set.
    let run_all = !args.python && !args.ts && !args.rust;

    ui::header("syntek-modules — Format");

    // -----------------------------------------------------------------------
    // ruff format (Python)
    // -----------------------------------------------------------------------
    if run_all || args.python {
        ui::section("ruff format — Python");

        let ruff = config::venv_bin(&root, "ruff");

        let mut fmt_args: Vec<&str> = vec!["format", "packages/backend/"];
        if args.check {
            fmt_args.push("--check");
        }

        if !proc::run(&ruff, &fmt_args, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // prettier (TypeScript / JS / JSON / YAML / Markdown)
    // -----------------------------------------------------------------------
    if run_all || args.ts {
        ui::section("prettier — TypeScript / JS / JSON / YAML / Markdown");

        let flag = if args.check { "--check" } else { "--write" };

        if !proc::run("pnpm", &["prettier", flag, "."], &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // cargo fmt (Rust)
    // -----------------------------------------------------------------------
    if run_all || args.rust {
        ui::section("cargo fmt — Rust");

        let mut fmt_args: Vec<&str> = vec!["fmt", "--all"];
        if args.check {
            fmt_args.extend_from_slice(&["--", "--check"]);
        }

        if !proc::run("cargo", &fmt_args, &root).await? {
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
