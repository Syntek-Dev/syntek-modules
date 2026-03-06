use anyhow::Result;

use crate::cli::UpArgs;
use crate::config;
use crate::process;
use crate::ui;

pub async fn run(args: UpArgs) -> Result<()> {
    let root = config::find_root()?;

    ui::header("syntek-modules — Development Mode");

    if !config::venv_exists(&root) {
        ui::warn("No .venv found — run: uv venv && source .venv/bin/activate");
    }

    // If no specific flags are given, start everything available.
    let start_all = !args.frontend && !args.storybook && !args.rust;

    let mut children: Vec<tokio::process::Child> = Vec::new();

    // Frontend packages via Turborepo (pnpm dev)
    if start_all || args.frontend {
        if process::exists("pnpm") {
            ui::step("Starting frontend packages in watch mode (pnpm dev)...");
            children.push(process::spawn("pnpm", &["dev"], &root)?);
        } else {
            ui::warn("pnpm not found — install with: npm install -g pnpm@10");
        }
    }

    // Storybook for @syntek/ui
    if start_all || args.storybook {
        if process::exists("pnpm") {
            ui::step("Starting Storybook for @syntek/ui (http://localhost:6006)...");
            children.push(process::spawn(
                "pnpm",
                &["--filter", "@syntek/ui", "storybook"],
                &root,
            )?);
        }
    }

    // Rust watcher
    if start_all || args.rust {
        if process::exists("cargo-watch") {
            ui::step("Starting Rust watcher (cargo-watch)...");
            children.push(process::spawn(
                "cargo-watch",
                &["--why", "-x", "check"],
                &root,
            )?);
        } else {
            ui::warn("cargo-watch not installed — run: cargo install cargo-watch");
        }
    }

    if children.is_empty() {
        ui::warn("No services started. Try: syntek-dev up --frontend or syntek-dev up --storybook");
        return Ok(());
    }

    println!();
    println!("  Press Ctrl+C to stop all services.");

    // Block until Ctrl+C
    tokio::signal::ctrl_c().await?;

    println!();
    ui::step("Shutting down...");
    for mut child in children {
        let _ = child.kill().await;
    }
    ui::ok("Done.");

    Ok(())
}
