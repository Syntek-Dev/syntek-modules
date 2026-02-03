//! Code coverage management command
//!
//! This module provides the `syntek coverage` command for generating, comparing,
//! and managing code coverage reports for the Python backend.
//!
//! # Features
//!
//! - Generate coverage reports (HTML, JSON, terminal)
//! - Create baseline coverage for CI/CD comparison
//! - Compare current coverage against baseline (fails if drops > 1%)
//! - Custom output paths for coverage data
//!
//! # Usage
//!
//! ```bash
//! syntek coverage                  # Generate report
//! syntek coverage --baseline       # Generate baseline
//! syntek coverage --compare        # Compare with baseline
//! syntek coverage --output foo.json # Custom output
//! ```
//!
//! Coverage data is used by GitHub Actions to enforce coverage thresholds.

use colored::*;
use crate::utils::exec;
use std::path::PathBuf;

/// Run the coverage command
///
/// # Arguments
///
/// * `generate_baseline` - Generate coverage baseline for comparison
/// * `compare` - Compare current coverage with baseline
/// * `output` - Optional custom output file path
///
/// # Returns
///
/// * `Ok(())` if coverage generation succeeds
/// * `Err` if tests fail or coverage drops below threshold
pub fn run(generate_baseline: bool, compare: bool, output: Option<PathBuf>) -> anyhow::Result<()> {
    println!("{}", "📊 Running coverage analysis...".green().bold());
    println!();

    if generate_baseline {
        generate_coverage_baseline()?;
    } else if compare {
        compare_coverage()?;
    } else {
        run_coverage_report(output)?;
    }

    Ok(())
}

fn generate_coverage_baseline() -> anyhow::Result<()> {
    println!("{}", "📈 Generating coverage baseline...".cyan());
    println!();

    // Run tests with coverage
    println!("{}", "🧪 Running tests with coverage...".dimmed());
    exec::run_command(
        "uv",
        &[
            "run",
            "pytest",
            "--cov=backend",
            "--cov-report=json",
            "--cov-report=html",
            "--cov-report=term",
        ],
    )?;

    // Extract coverage percentage
    let output = exec::run_command_output(
        "python3",
        &[
            "-c",
            "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.2f}\")",
        ],
    )?;

    let coverage = output.trim();

    println!();
    println!("{}", "━".repeat(60).dimmed());
    println!("{}", "✅ Coverage baseline generated!".green().bold());
    println!("{}", "━".repeat(60).dimmed());
    println!();
    println!("{} {}", "📈 Current coverage:".cyan(), format!("{}%", coverage).bold());
    println!();
    println!("{}", "📁 Reports generated:".cyan());
    println!("{}", "   - coverage.json (for CI/CD)".dimmed());
    println!("{}", "   - htmlcov/index.html (for viewing)".dimmed());
    println!();
    println!("{}", "🌐 View HTML report:".cyan());
    println!("{}", "   open htmlcov/index.html".dimmed());
    println!();
    println!("{}", "💡 Commit coverage.json as baseline:".cyan());
    println!("{}", "   mv coverage.json coverage-baseline.json".dimmed());
    println!("{}", "   git add coverage-baseline.json .coveragerc".dimmed());
    println!("{}", "   git commit -m 'chore: add coverage baseline'".dimmed());
    println!();

    Ok(())
}

fn compare_coverage() -> anyhow::Result<()> {
    println!("{}", "🔍 Comparing coverage with baseline...".cyan());
    println!();

    // Check if baseline exists
    if !std::path::Path::new("coverage-baseline.json").exists() {
        anyhow::bail!("No coverage baseline found. Run 'syntek coverage --baseline' first.");
    }

    // Run tests with coverage
    println!("{}", "🧪 Running tests with coverage...".dimmed());
    exec::run_command(
        "uv",
        &[
            "run",
            "pytest",
            "--cov=backend",
            "--cov-report=json",
            "--cov-report=term",
        ],
    )?;

    // Extract current coverage
    let current = exec::run_command_output(
        "python3",
        &[
            "-c",
            "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.2f}\")",
        ],
    )?.trim().to_string();

    // Extract baseline coverage
    let baseline = exec::run_command_output(
        "python3",
        &[
            "-c",
            "import json; data=json.load(open('coverage-baseline.json')); print(f\"{data['totals']['percent_covered']:.2f}\")",
        ],
    )?.trim().to_string();

    // Calculate difference
    let diff_output = exec::run_command_output(
        "python3",
        &[
            "-c",
            &format!("print({} - {})", current, baseline),
        ],
    )?;

    let diff: f64 = diff_output.trim().parse()?;

    println!();
    println!("{}", "━".repeat(60).dimmed());
    println!("{}", "📊 Coverage Comparison".cyan().bold());
    println!("{}", "━".repeat(60).dimmed());
    println!();
    println!("{} {}%", "📈 Baseline coverage:".dimmed(), baseline.bold());
    println!("{} {}%", "📊 Current coverage: ".dimmed(), current.bold());
    println!();

    if diff < -1.0 {
        println!("{} Coverage dropped by {:.2}%!", "❌".red(), -diff);
        println!("{}", "   This fails the coverage threshold.".red());
        anyhow::bail!("Coverage dropped below acceptable threshold");
    } else if diff > 0.0 {
        println!("{} Coverage improved by {:.2}%!", "✅".green(), diff);
    } else {
        println!("{} Coverage maintained", "✅".green());
    }

    println!();

    Ok(())
}

fn run_coverage_report(output: Option<PathBuf>) -> anyhow::Result<()> {
    println!("{}", "🧪 Running tests with coverage...".cyan());
    println!();

    let output_arg;
    let mut args = vec![
        "run",
        "pytest",
        "--cov=backend",
        "--cov-report=html",
        "--cov-report=term",
    ];

    if let Some(ref path) = output {
        output_arg = format!("json:{}", path.display());
        args.push("--cov-report");
        args.push(&output_arg);
    } else {
        args.push("--cov-report=json");
    }

    exec::run_command("uv", &args)?;

    // Extract coverage percentage
    let coverage_file = output.as_ref().map(|p| p.display().to_string())
        .unwrap_or_else(|| "coverage.json".to_string());

    let coverage = exec::run_command_output(
        "python3",
        &[
            "-c",
            &format!("import json; data=json.load(open('{}')); print(f\"{{data['totals']['percent_covered']:.2f}}\")", coverage_file),
        ],
    )?.trim().to_string();

    println!();
    println!("{}", "━".repeat(60).dimmed());
    println!("{}", "✅ Coverage report generated!".green().bold());
    println!("{}", "━".repeat(60).dimmed());
    println!();
    println!("{} {}%", "📊 Coverage:".cyan(), coverage.bold());
    println!();
    println!("{}", "📁 View HTML report:".cyan());
    println!("{}", "   open htmlcov/index.html".dimmed());
    println!();

    Ok(())
}
