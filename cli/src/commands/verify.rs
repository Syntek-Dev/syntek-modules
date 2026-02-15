//! Verify command implementation
//!
//! Handles `syntek verify auth` command to check installation integrity.

use crate::config::loader::ConfigLoader;
use crate::config::validator::ConfigValidator;
use crate::install::{BackendInstaller, FrontendInstaller, GraphQLInstaller, RustInstaller};
use crate::utils::error::Result;
use clap::Args;
use colored::Colorize;
use std::path::Path;

/// Verify command arguments
#[derive(Debug, Args)]
pub struct VerifyArgs {
    /// Module to verify (currently only "auth" supported)
    pub module: String,

    /// Target project directory
    #[arg(long, default_value = ".")]
    pub project_dir: String,

    /// Skip smoke tests (only check file existence)
    #[arg(long)]
    pub skip_tests: bool,

    /// Verbose output
    #[arg(short, long)]
    pub verbose: bool,
}

/// Execute verify command
pub fn execute(args: VerifyArgs) -> Result<()> {
    // Validate module name
    if args.module != "auth" {
        return Err(crate::utils::error::CliError::ValidationFailed(
            format!("Unknown module: {}. Currently only 'auth' is supported.", args.module),
        ));
    }

    println!("{}", "=== Syntek Authentication Verification ===\n".bold().cyan());

    let project_dir = Path::new(&args.project_dir);

    // Load project configuration
    println!("{}", "Loading project configuration...".bold());
    let config = ConfigLoader::load_from_project(project_dir)?;
    println!("{} Configuration loaded\n", "✓".green().bold());

    // Validate project structure
    println!("{}", "Validating project structure...".bold());
    let validation_result = ConfigValidator::validate_project(project_dir, &config);

    if !validation_result.warnings.is_empty() {
        for warning in &validation_result.warnings {
            println!("{}", warning);
        }
    }

    if !validation_result.errors.is_empty() {
        for error in &validation_result.errors {
            println!("{} {}", "✗".red().bold(), error);
        }
        return Err(crate::utils::error::CliError::ValidationFailed(
            "Project structure validation failed".to_string(),
        ));
    }

    println!("{} Project structure valid\n", "✓".green().bold());

    // Validate authentication installation
    println!("{}", "Validating authentication installation...".bold());
    let auth_validation = ConfigValidator::validate_auth_installation(project_dir, &config);

    if !auth_validation.is_ok() {
        for error in &auth_validation.errors {
            println!("{} {}", "✗".red().bold(), error);
        }
        return Err(crate::utils::error::CliError::ValidationFailed(
            "Authentication installation validation failed".to_string(),
        ));
    }

    println!("{} Authentication modules installed\n", "✓".green().bold());

    // Check security settings
    println!("{}", "Checking security settings...".bold());
    let security_validation = ConfigValidator::validate_security(project_dir);

    if !security_validation.warnings.is_empty() {
        for warning in &security_validation.warnings {
            println!("{}", warning);
        }
    }

    if !security_validation.errors.is_empty() {
        for error in &security_validation.errors {
            println!("{} {}", "✗".red().bold(), error);
        }
    } else {
        println!("{} Security settings validated\n", "✓".green().bold());
    }

    // Run smoke tests (unless skipped)
    if !args.skip_tests {
        println!("{}", "Running smoke tests...\n".bold());

        // Test backend installation
        if !config.modules.backend.is_empty() {
            BackendInstaller::verify_installation(project_dir, &config, &config.modules.backend)?;
        }

        // Test GraphQL installation
        if !config.modules.graphql.is_empty() {
            GraphQLInstaller::verify_installation(project_dir, &config, &config.modules.graphql)?;
        }

        // Test web installation
        if !config.modules.web.is_empty() {
            FrontendInstaller::verify_web_installation(project_dir, &config, &config.modules.web)?;
        }

        // Test mobile installation
        if !config.modules.mobile.is_empty() {
            FrontendInstaller::verify_mobile_installation(
                project_dir,
                &config,
                &config.modules.mobile,
            )?;
        }

        // Test Rust installation
        if !config.modules.rust.is_empty() {
            RustInstaller::verify_installation(project_dir, &config.modules.rust)?;
        }

        println!("\n{} All smoke tests passed", "✓".green().bold());
    }

    // Print summary
    print_verification_summary(&config, &validation_result, &security_validation);

    println!("\n{}", "Verification complete!".bold().green());

    Ok(())
}

/// Print verification summary
fn print_verification_summary(
    config: &crate::config::loader::ProjectConfig,
    validation: &crate::config::validator::ValidationResult,
    security: &crate::config::validator::ValidationResult,
) {
    println!("\n{}", "=== Verification Summary ===".bold().cyan());

    println!("\n{}", "Installed modules:".bold());
    println!("  Backend: {}", config.modules.backend.len());
    println!("  GraphQL: {}", config.modules.graphql.len());
    println!("  Web: {}", config.modules.web.len());
    println!("  Mobile: {}", config.modules.mobile.len());
    println!("  Rust: {}", config.modules.rust.len());

    println!("\n{}", "Validation results:".bold());
    println!("  Errors: {}", validation.errors.len());
    println!("  Warnings: {}", validation.warnings.len());

    println!("\n{}", "Security checks:".bold());
    println!("  Errors: {}", security.errors.len());
    println!("  Warnings: {}", security.warnings.len());

    if validation.errors.is_empty() && security.errors.is_empty() {
        println!("\n{}", "Status: All checks passed ✓".green().bold());
    } else {
        println!(
            "\n{}",
            "Status: Some checks failed. Review errors above.".red().bold()
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_verify_args_validation() {
        let args = VerifyArgs {
            module: "auth".to_string(),
            project_dir: ".".to_string(),
            skip_tests: false,
            verbose: false,
        };

        assert_eq!(args.module, "auth");
    }
}
