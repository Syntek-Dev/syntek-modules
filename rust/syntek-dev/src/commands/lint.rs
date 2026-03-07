use anyhow::Result;
use std::process;

use crate::cli::LintArgs;
use crate::config;
use crate::process as proc;
use crate::ui;

pub async fn run(args: LintArgs) -> Result<()> {
    let root = config::find_root()?;
    let mut failed: u32 = 0;

    // Run all linters when no specific flag is set.
    let run_all = !args.ruff && !args.pyright && !args.eslint && !args.clippy && !args.markdown;

    ui::header("syntek-modules — Lint");

    // -----------------------------------------------------------------------
    // ruff (Python lint + import sorting)
    // -----------------------------------------------------------------------
    if run_all || args.ruff {
        ui::section("ruff — Python lint");

        let target = args
            .package
            .as_deref()
            .map(|p| format!("packages/backend/{}", p))
            .unwrap_or_else(|| "packages/backend/".to_string());

        let ruff = config::venv_bin(&root, "ruff");

        let mut check_args: Vec<&str> = vec!["check", &target];
        if args.fix {
            check_args.push("--fix");
        }
        if !proc::run(&ruff, &check_args, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // basedpyright (Python type checking)
    // -----------------------------------------------------------------------
    if run_all || args.pyright {
        ui::section("basedpyright — Python type checking");

        let target = args
            .package
            .as_deref()
            .map(|p| format!("packages/backend/{}", p))
            .unwrap_or_else(|| "packages/backend/".to_string());

        // Prefer basedpyright, fall back to pyright
        let checker = if proc::exists("basedpyright") {
            "basedpyright"
        } else if proc::exists("pyright") {
            "pyright"
        } else {
            ui::warn("basedpyright not found — install with: npm install -g pyright");
            ""
        };

        if !checker.is_empty() && !proc::run(checker, &[&target], &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // ESLint (TypeScript / JS)
    // -----------------------------------------------------------------------
    if run_all || args.eslint {
        ui::section("ESLint — TypeScript / JS");

        let mut a: Vec<String> = Vec::new();

        if let Some(ref pkg) = args.package {
            a.extend(["--filter".to_string(), pkg.clone()]);
        }
        a.push("lint".to_string());
        if args.fix {
            a.push("--".to_string());
            a.push("--fix".to_string());
        }
        let refs: Vec<&str> = a.iter().map(String::as_str).collect();

        if !proc::run("pnpm", &refs, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // clippy (Rust)
    // -----------------------------------------------------------------------
    if run_all || args.clippy {
        ui::section("clippy — Rust");

        let extra = if args.fix {
            &["--fix", "--allow-dirty"][..]
        } else {
            &["--", "-D", "warnings"][..]
        };

        let mut a = vec!["clippy", "--all-targets", "--all-features"];
        a.extend_from_slice(extra);

        if !proc::run("cargo", &a, &root).await? {
            failed += 1;
        }
    }

    // -----------------------------------------------------------------------
    // markdownlint
    // -----------------------------------------------------------------------
    if run_all || args.markdown {
        ui::section("markdownlint — Markdown");

        if !proc::run("pnpm", &["lint:md"], &root).await? {
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
