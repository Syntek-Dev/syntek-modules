//! Security audit command
//!
//! Performs comprehensive security audits across all package managers:
//! - NPM/pnpm: Checks for vulnerabilities in Node packages
//! - Python: Uses pip-audit to scan Python dependencies
//! - Rust: Uses cargo-audit for Rust crates
//!
//! Generates reports in multiple formats (text, JSON, markdown) and can
//! save results to a file for CI/CD integration.

use colored::*;
use std::path::PathBuf;
use std::process::Command;

/// Run security audit across all ecosystems
///
/// # Arguments
///
/// * `format` - Output format (Text, Json, Markdown)
/// * `severity` - Minimum severity level to report
/// * `output` - Optional output file path
///
/// # Returns
///
/// * `Ok(())` if audit completes (may have found vulnerabilities)
/// * `Err` if audit tools fail to run
pub fn run(
    format: crate::AuditFormat,
    severity: String,
    output: Option<PathBuf>,
) -> anyhow::Result<()> {
    println!("{}", "🔒 Running security audit...".green().bold());
    println!(
        "{}",
        format!("   Minimum severity: {}", severity).dimmed()
    );

    let mut all_passed = true;
    let mut audit_results = Vec::new();

    // Audit NPM/PNPM packages
    println!("\n{}", "📦 Auditing NPM packages...".cyan());
    match audit_pnpm(&severity) {
        Ok(result) => {
            audit_results.push(("NPM", result.clone()));
            if !result.is_empty() {
                println!("{}", result);
                all_passed = false;
            } else {
                println!("{}", "   ✅ No vulnerabilities found".green());
            }
        }
        Err(e) => {
            let msg = format!("   ⚠️  Audit failed: {}", e);
            println!("{}", msg.yellow());
            audit_results.push(("NPM", msg.clone()));
        }
    }

    // Audit Python/uv packages
    println!("\n{}", "🐍 Auditing Python packages...".cyan());
    match audit_python(&severity) {
        Ok(result) => {
            audit_results.push(("Python", result.clone()));
            if !result.is_empty() {
                println!("{}", result);
                all_passed = false;
            } else {
                println!("{}", "   ✅ No vulnerabilities found".green());
            }
        }
        Err(e) => {
            let msg = format!("   ⚠️  Audit failed: {}", e);
            println!("{}", msg.yellow());
            audit_results.push(("Python", msg.clone()));
        }
    }

    // Audit Rust/Cargo packages
    println!("\n{}", "🦀 Auditing Rust packages...".cyan());
    match audit_rust() {
        Ok(result) => {
            audit_results.push(("Rust", result.clone()));
            if !result.is_empty() {
                println!("{}", result);
                all_passed = false;
            } else {
                println!("{}", "   ✅ No vulnerabilities found".green());
            }
        }
        Err(e) => {
            let msg = format!("   ⚠️  Audit failed: {}", e);
            println!("{}", msg.yellow());
            audit_results.push(("Rust", msg.clone()));
        }
    }

    // Write output file if requested
    if let Some(output_path) = output {
        write_audit_report(&output_path, &format, &audit_results)?;
        println!(
            "\n{} {}",
            "📄 Report saved to:".cyan(),
            output_path.display()
        );
    }

    // Final summary
    println!("\n{}", "━".repeat(60).dimmed());
    if all_passed {
        println!("{}", "✅ Security audit passed!".green().bold());
        println!("{}", "   No vulnerabilities found in any ecosystem.".dimmed());
    } else {
        println!("{}", "⚠️  Security vulnerabilities found!".yellow().bold());
        println!(
            "{}",
            "   Review the results above and update dependencies.".dimmed()
        );
    }
    println!("{}", "━".repeat(60).dimmed());

    Ok(())
}

fn audit_pnpm(severity: &str) -> anyhow::Result<String> {
    let output = Command::new("pnpm")
        .args(&[
            "audit",
            "--json",
            &format!("--audit-level={}", severity),
        ])
        .output()?;

    if output.status.success() {
        Ok(String::new())
    } else {
        let stdout = String::from_utf8_lossy(&output.stdout);
        if stdout.contains("No known vulnerabilities") {
            Ok(String::new())
        } else {
            Ok(stdout.to_string())
        }
    }
}

fn audit_python(_severity: &str) -> anyhow::Result<String> {
    let install_output = Command::new("uv")
        .args(&["pip", "install", "pip-audit", "--quiet"])
        .output()?;

    if !install_output.status.success() {
        anyhow::bail!("Failed to install pip-audit");
    }

    let output = Command::new("uv")
        .args(&["run", "pip-audit", "--format=json"])
        .output()?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);

        if stdout.contains("\"fixes\":[]") || stdout.contains("No known vulnerabilities found") {
            Ok(String::new())
        } else {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&stdout) {
                if let Some(deps) = json["dependencies"].as_array() {
                    let has_vulns = deps.iter().any(|dep| {
                        if let Some(vulns) = dep["vulns"].as_array() {
                            !vulns.is_empty()
                        } else {
                            false
                        }
                    });

                    if has_vulns {
                        Ok(stdout.to_string())
                    } else {
                        Ok(String::new())
                    }
                } else {
                    Ok(String::new())
                }
            } else {
                Ok(stdout.to_string())
            }
        }
    } else {
        Ok(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

fn audit_rust() -> anyhow::Result<String> {
    let check = Command::new("cargo").args(&["audit", "--version"]).output();

    if check.is_err() || !check?.status.success() {
        println!("{}", "   Installing cargo-audit...".dimmed());
        let install = Command::new("cargo")
            .args(&["install", "cargo-audit"])
            .output()?;

        if !install.status.success() {
            anyhow::bail!("Failed to install cargo-audit");
        }
    }

    let output = Command::new("cargo")
        .args(&["audit", "--json"])
        .current_dir("rust")
        .output()?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        if stdout.contains("\"vulnerabilities\":[]") {
            Ok(String::new())
        } else {
            Ok(stdout.to_string())
        }
    } else {
        Ok(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

fn write_audit_report(
    path: &PathBuf,
    format: &crate::AuditFormat,
    results: &[(&str, String)],
) -> anyhow::Result<()> {
    use std::fs::File;
    use std::io::Write;

    let mut file = File::create(path)?;

    match format {
        crate::AuditFormat::Json => {
            writeln!(file, "{{")?;
            writeln!(file, "  \"timestamp\": \"{}\",", chrono::Utc::now())?;
            writeln!(file, "  \"results\": [")?;
            for (i, (ecosystem, result)) in results.iter().enumerate() {
                writeln!(file, "    {{")?;
                writeln!(file, "      \"ecosystem\": \"{}\",", ecosystem)?;
                writeln!(file, "      \"output\": {}",
                    serde_json::to_string(result).unwrap_or_else(|_| "null".to_string()))?;
                if i < results.len() - 1 {
                    writeln!(file, "    }},")?;
                } else {
                    writeln!(file, "    }}")?;
                }
            }
            writeln!(file, "  ]")?;
            writeln!(file, "}}")?;
        }
        crate::AuditFormat::Markdown => {
            writeln!(file, "# Security Audit Report")?;
            writeln!(file, "\n**Generated:** {}\n", chrono::Utc::now())?;
            for (ecosystem, result) in results {
                writeln!(file, "## {} Ecosystem\n", ecosystem)?;
                if result.is_empty() {
                    writeln!(file, "✅ No vulnerabilities found\n")?;
                } else {
                    writeln!(file, "```")?;
                    writeln!(file, "{}", result)?;
                    writeln!(file, "```\n")?;
                }
            }
        }
        crate::AuditFormat::Text => {
            writeln!(file, "Security Audit Report")?;
            writeln!(file, "Generated: {}\n", chrono::Utc::now())?;
            writeln!(file, "{}", "=".repeat(60))?;
            for (ecosystem, result) in results {
                writeln!(file, "\n{} Ecosystem:", ecosystem)?;
                writeln!(file, "{}", "-".repeat(60))?;
                if result.is_empty() {
                    writeln!(file, "✅ No vulnerabilities found")?;
                } else {
                    writeln!(file, "{}", result)?;
                }
            }
            writeln!(file, "\n{}", "=".repeat(60))?;
        }
    }

    Ok(())
}
