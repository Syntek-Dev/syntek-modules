use anyhow::{bail, Result};

use crate::cli::DbCommand;
use crate::config;
use crate::process as proc;
use crate::ui;

/// Resolve `manage.py` path, printing a helpful error if the sandbox is missing.
fn require_manage(root: &std::path::PathBuf) -> Result<String> {
    match config::sandbox_manage(root) {
        Some(p) => Ok(p.to_string_lossy().to_string()),
        None => bail!(
            "sandbox/manage.py not found.\n\n\
             The db commands require a sandbox Django project that has all backend\n\
             modules installed. Create sandbox/ with:\n\n\
             \x20 1. mkdir sandbox && cd sandbox\n\
             \x20 2. uv pip install -e '../packages/backend/syntek-auth[dev]' (repeat for each module)\n\
             \x20 3. Create a manage.py and settings.py that configure the modules\n\n\
             See docs/GUIDES/SANDBOX.md for the full setup guide (coming soon)."
        ),
    }
}

/// Build the Python binary path and manage.py path as a run-ready pair.
fn manage_cmd(root: &std::path::PathBuf, manage: &str) -> (String, String) {
    (config::venv_bin(root, "python"), manage.to_string())
}

pub async fn run(cmd: DbCommand) -> Result<()> {
    let root = config::find_root()?;

    match cmd {
        // -------------------------------------------------------------------
        // migrate
        // -------------------------------------------------------------------
        DbCommand::Migrate { module } => {
            ui::header("DB — migrate");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            let app_label = module.as_deref().unwrap_or("");
            let mut args: Vec<&str> = vec![&manage_path, "migrate"];
            if !app_label.is_empty() {
                args.push(app_label);
            }

            ui::step(&format!("Running: python {} migrate {}", manage_path, app_label));
            if !proc::run(&python, &args, &root).await? {
                bail!("Migration failed");
            }
            ui::ok("Migrations applied.");
        }

        // -------------------------------------------------------------------
        // makemigrations
        // -------------------------------------------------------------------
        DbCommand::Makemigrations { module } => {
            ui::header("DB — makemigrations");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            let app_label = module.as_deref().unwrap_or("");
            let mut args: Vec<&str> = vec![&manage_path, "makemigrations"];
            if !app_label.is_empty() {
                args.push(app_label);
            }

            ui::step(&format!("Generating migrations for: {}", if app_label.is_empty() { "all apps" } else { app_label }));
            if !proc::run(&python, &args, &root).await? {
                bail!("makemigrations failed");
            }
            ui::ok("Migrations generated.");
        }

        // -------------------------------------------------------------------
        // rollback
        // -------------------------------------------------------------------
        DbCommand::Rollback { module, to } => {
            ui::header("DB — rollback");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            let app_label = module.as_deref().unwrap_or_else(|| {
                eprintln!("Module name is required for rollback.");
                std::process::exit(1);
            });

            ui::step(&format!("Rolling back {} to {}", app_label, to));
            if !proc::run(&python, &[&manage_path, "migrate", app_label, &to], &root).await? {
                bail!("Rollback failed");
            }
            ui::ok("Rollback complete.");
        }

        // -------------------------------------------------------------------
        // status
        // -------------------------------------------------------------------
        DbCommand::Status { module } => {
            ui::header("DB — migration status");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            let app_label = module.as_deref().unwrap_or("");
            let mut args: Vec<&str> = vec![&manage_path, "showmigrations"];
            if !app_label.is_empty() {
                args.push(app_label);
            }

            proc::run(&python, &args, &root).await?;
        }

        // -------------------------------------------------------------------
        // seed (development mock data)
        // -------------------------------------------------------------------
        DbCommand::Seed => {
            ui::header("DB — seed (development data)");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            ui::step("Running seed_dev management command...");
            if !proc::run(&python, &[&manage_path, "seed_dev"], &root).await? {
                bail!(
                    "seed_dev command failed.\n\
                     Ensure each backend module provides a 'seed_dev' management command\n\
                     that uses factory_boy to populate development fixtures."
                );
            }
            ui::ok("Development data seeded.");
        }

        // -------------------------------------------------------------------
        // seed-test (test-specific mock data)
        // -------------------------------------------------------------------
        DbCommand::SeedTest { scenario } => {
            ui::header("DB — seed (test data)");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            let mut args: Vec<String> = vec![manage_path.clone(), "seed_test".to_string()];
            if let Some(s) = scenario {
                args.push(s);
            }
            let refs: Vec<&str> = args.iter().map(String::as_str).collect();

            ui::step("Running seed_test management command...");
            if !proc::run(&python, &refs, &root).await? {
                bail!("seed_test command failed.");
            }
            ui::ok("Test data seeded.");
        }

        // -------------------------------------------------------------------
        // reset (drop + recreate + migrate)
        // -------------------------------------------------------------------
        DbCommand::Reset => {
            ui::header("DB — reset");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            ui::step("Flushing database...");
            if !proc::run(&python, &[&manage_path, "flush", "--noinput"], &root).await? {
                bail!("flush failed");
            }

            ui::step("Applying migrations...");
            if !proc::run(&python, &[&manage_path, "migrate"], &root).await? {
                bail!("migrate failed after reset");
            }

            ui::ok("Database reset and re-migrated.");
        }

        // -------------------------------------------------------------------
        // shell (psql)
        // -------------------------------------------------------------------
        DbCommand::Shell => {
            ui::header("DB — psql shell");
            let manage = require_manage(&root)?;
            let (python, manage_path) = manage_cmd(&root, &manage);

            ui::step("Opening database shell (Ctrl+D or \\q to exit)...");
            proc::run(&python, &[&manage_path, "dbshell"], &root).await?;
        }
    }

    Ok(())
}
