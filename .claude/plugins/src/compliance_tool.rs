use serde_json::json;
use std::env;
use std::fs;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let project_path = args.get(1).ok_or("Project path required")?;

    let report = generate_compliance_report(project_path)?;

    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn generate_compliance_report(project_path: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let cargo_toml_path = Path::new(project_path).join("Cargo.toml");

    if !cargo_toml_path.exists() {
        return Err("Cargo.toml not found".into());
    }

    let cargo_toml = fs::read_to_string(&cargo_toml_path)?;

    // Check for security-critical settings
    let has_zeroize = cargo_toml.contains("zeroize");
    let has_overflow_checks = cargo_toml.contains("overflow-checks");
    let has_panic_abort = cargo_toml.contains(r#"panic = "abort""#);

    // Scan for unsafe code
    let src_dir = Path::new(project_path).join("src");
    let unsafe_count = if src_dir.exists() {
        count_unsafe_blocks(&src_dir)?
    } else {
        0
    };

    let report = json!({
        "project_path": project_path,
        "compliance_checks": {
            "zeroize_dependency": has_zeroize,
            "overflow_checks_enabled": has_overflow_checks,
            "panic_abort_enabled": has_panic_abort,
        },
        "security_metrics": {
            "unsafe_blocks": unsafe_count,
        },
        "recommendations": generate_recommendations(has_zeroize, has_overflow_checks, has_panic_abort, unsafe_count),
    });

    Ok(report)
}

fn count_unsafe_blocks(dir: &Path) -> Result<usize, Box<dyn std::error::Error>> {
    let mut count = 0;

    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.is_file() && path.extension().map(|e| e == "rs").unwrap_or(false) {
            let contents = fs::read_to_string(&path)?;
            count += contents.matches("unsafe").count();
        } else if path.is_dir() {
            count += count_unsafe_blocks(&path)?;
        }
    }

    Ok(count)
}

fn generate_recommendations(has_zeroize: bool, has_overflow_checks: bool, has_panic_abort: bool, unsafe_count: usize) -> Vec<String> {
    let mut recommendations = Vec::new();

    if !has_zeroize {
        recommendations.push("Add 'zeroize' dependency for sensitive data handling".to_string());
    }

    if !has_overflow_checks {
        recommendations.push("Enable overflow-checks in release profile".to_string());
    }

    if !has_panic_abort {
        recommendations.push("Consider panic = 'abort' in release profile".to_string());
    }

    if unsafe_count > 10 {
        recommendations.push(format!("Review {} unsafe blocks for safety", unsafe_count));
    }

    if recommendations.is_empty() {
        recommendations.push("Project follows security best practices".to_string());
    }

    recommendations
}
