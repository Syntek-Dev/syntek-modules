use serde_json::json;
use std::env;
use std::fs;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(|s| s.as_str()).unwrap_or("status");

    match command {
        "init" => {
            let project_path = args.get(2).ok_or("Project path required")?;
            init_fuzzing(project_path)?;
        }
        "status" => {
            let project_path = args.get(2).ok_or("Project path required")?;
            check_fuzzing_status(project_path)?;
        }
        _ => {
            eprintln!("Usage: fuzzer-tool [init|status] <project-path>");
            std::process::exit(1);
        }
    }

    Ok(())
}

fn init_fuzzing(project_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let fuzz_dir = Path::new(project_path).join("fuzz");

    if !fuzz_dir.exists() {
        fs::create_dir_all(&fuzz_dir)?;
        let fuzz_targets_dir = fuzz_dir.join("fuzz_targets");
        fs::create_dir_all(&fuzz_targets_dir)?;

        // Create a basic Cargo.toml for fuzzing
        let cargo_toml = r#"[package]
name = "fuzz"
version = "0.0.0"
edition = "2021"
publish = false

[dependencies]
libfuzzer-sys = "0.4"

[[bin]]
name = "fuzz_target_1"
path = "fuzz_targets/fuzz_target_1.rs"
"#;
        fs::write(fuzz_dir.join("Cargo.toml"), cargo_toml)?;

        // Create a basic fuzz target
        let fuzz_target = r#"#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    // Add your fuzzing logic here
});
"#;
        fs::write(fuzz_targets_dir.join("fuzz_target_1.rs"), fuzz_target)?;
    }

    let output = json!({
        "status": "initialized",
        "fuzz_directory": fuzz_dir.to_string_lossy(),
    });

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}

fn check_fuzzing_status(project_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let fuzz_dir = Path::new(project_path).join("fuzz");
    let has_fuzzing = fuzz_dir.exists();

    let output = json!({
        "has_fuzzing": has_fuzzing,
        "fuzz_directory": fuzz_dir.to_string_lossy(),
    });

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}
