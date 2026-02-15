//! Init command implementation
//!
//! Handles `syntek init` command to initialize Syntek in a project.

use crate::config::loader::ConfigLoader;
use crate::utils::error::Result;
use clap::Args;
use colored::Colorize;
use std::path::Path;

/// Init command arguments
#[derive(Debug, Args)]
pub struct InitArgs {
    /// Project name
    #[arg(short, long)]
    pub name: Option<String>,

    /// Target project directory
    #[arg(long, default_value = ".")]
    pub project_dir: String,

    /// Force re-initialization (overwrite existing config)
    #[arg(short, long)]
    pub force: bool,
}

/// Execute init command
pub fn execute(args: InitArgs) -> Result<()> {
    println!("{}", "=== Syntek Initialization ===\n".bold().cyan());

    let project_dir = Path::new(&args.project_dir);

    // Check if configuration already exists
    let config_path = project_dir.join("syntek.toml");
    if config_path.exists() && !args.force {
        return Err(crate::utils::error::CliError::AlreadyInstalled(config_path));
    }

    // Determine project name
    let project_name = args.name.unwrap_or_else(|| {
        project_dir
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("my-project")
            .to_string()
    });

    println!("Initializing Syntek for project: {}", project_name.cyan());

    // Create default configuration
    let config = ConfigLoader::create_default(&project_name);

    // Save configuration
    ConfigLoader::save_to_project(project_dir, &config)?;

    println!(
        "{} Created configuration at {}",
        "✓".green().bold(),
        config_path.display()
    );

    // Create directory structure
    create_directory_structure(project_dir, &config)?;

    // Print next steps
    print_next_steps(&project_name);

    Ok(())
}

/// Create initial directory structure
fn create_directory_structure(
    project_dir: &Path,
    config: &crate::config::loader::ProjectConfig,
) -> Result<()> {
    println!("\n{}", "Creating directory structure...".bold());

    // Create backend directory
    let backend_dir = project_dir.join(&config.backend.directory);
    if !backend_dir.exists() {
        std::fs::create_dir_all(&backend_dir)?;
        println!("{} {}", "✓".green().bold(), backend_dir.display());
    }

    // Create web directory
    if !config.web.directory.is_empty() {
        let web_dir = project_dir.join(&config.web.directory);
        if !web_dir.exists() {
            std::fs::create_dir_all(&web_dir)?;
            println!("{} {}", "✓".green().bold(), web_dir.display());
        }
    }

    // Create mobile directory
    if !config.mobile.directory.is_empty() {
        let mobile_dir = project_dir.join(&config.mobile.directory);
        if !mobile_dir.exists() {
            std::fs::create_dir_all(&mobile_dir)?;
            println!("{} {}", "✓".green().bold(), mobile_dir.display());
        }
    }

    // Create shared directory
    if config.shared.enabled {
        let shared_dir = project_dir.join(&config.shared.directory);
        if !shared_dir.exists() {
            std::fs::create_dir_all(&shared_dir)?;
            println!("{} {}", "✓".green().bold(), shared_dir.display());
        }
    }

    // Create rust directory
    let rust_dir = project_dir.join("rust");
    if !rust_dir.exists() {
        std::fs::create_dir_all(&rust_dir)?;
        println!("{} {}", "✓".green().bold(), rust_dir.display());
    }

    // Create docs directory
    let docs_dir = project_dir.join("docs");
    if !docs_dir.exists() {
        std::fs::create_dir_all(&docs_dir)?;
        println!("{} {}", "✓".green().bold(), docs_dir.display());
    }

    // Create config directory
    let config_dir = project_dir.join("config");
    if !config_dir.exists() {
        std::fs::create_dir_all(&config_dir)?;
        println!("{} {}", "✓".green().bold(), config_dir.display());
    }

    Ok(())
}

/// Print next steps
fn print_next_steps(project_name: &str) {
    println!("\n{}", "=== Next Steps ===".bold().cyan());

    println!(
        r#"
1. Review configuration:
   Edit syntek.toml to customize your setup

2. Install authentication:
   syntek install auth --full

   Or choose a specific mode:
   syntek install auth --minimal    # Backend + GraphQL only
   syntek install auth --web-only   # Backend + GraphQL + Web
   syntek install auth --mobile-only # Backend + GraphQL + Mobile

3. Configure social authentication (optional):
   syntek install auth --social-auth --providers google,github

4. Verify installation:
   syntek verify auth

5. Start development:
   - Backend: cd backend && python manage.py runserver
   - Web: cd web/packages && pnpm dev
   - Mobile: cd mobile/packages && pnpm start

For more information, see:
- Documentation: ./docs/
- Syntek modules: https://github.com/yourusername/syntek-modules
"#
    );

    println!("{}", format!("Happy coding with {}! 🚀", project_name).green().bold());
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_init_creates_config() {
        let temp_dir = TempDir::new().unwrap();

        let args = InitArgs {
            name: Some("test-project".to_string()),
            project_dir: temp_dir.path().to_str().unwrap().to_string(),
            force: false,
        };

        let result = execute(args);
        assert!(result.is_ok());
        assert!(temp_dir.path().join("syntek.toml").exists());
    }

    #[test]
    fn test_init_fails_if_exists() {
        let temp_dir = TempDir::new().unwrap();

        // Create existing config
        let config_path = temp_dir.path().join("syntek.toml");
        std::fs::write(&config_path, "test").unwrap();

        let args = InitArgs {
            name: Some("test-project".to_string()),
            project_dir: temp_dir.path().to_str().unwrap().to_string(),
            force: false,
        };

        let result = execute(args);
        assert!(result.is_err());
    }
}
