use serde_json::json;
use std::env;
use std::process::Command;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let manifest_path = args.get(1);

    // Run cargo audit
    let mut cmd = Command::new("cargo");
    cmd.arg("audit");

    if let Some(path) = manifest_path {
        cmd.arg("--manifest-path").arg(path);
    }

    let output = cmd.output()?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    let result = json!({
        "status": if output.status.success() { "success" } else { "failed" },
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": output.status.code(),
    });

    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}
