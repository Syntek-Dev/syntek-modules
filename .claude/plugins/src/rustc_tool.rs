use serde_json::json;
use std::process::Command;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let output = Command::new("rustc")
        .arg("--version")
        .arg("--verbose")
        .output()?;

    let version_info = String::from_utf8_lossy(&output.stdout);

    let mut version = String::new();
    let mut commit_hash = String::new();
    let mut commit_date = String::new();
    let mut host = String::new();

    for line in version_info.lines() {
        if line.starts_with("rustc") {
            version = line.replace("rustc ", "");
        } else if line.starts_with("commit-hash:") {
            commit_hash = line.replace("commit-hash: ", "");
        } else if line.starts_with("commit-date:") {
            commit_date = line.replace("commit-date: ", "");
        } else if line.starts_with("host:") {
            host = line.replace("host: ", "");
        }
    }

    let output = json!({
        "version": version,
        "commit_hash": commit_hash,
        "commit_date": commit_date,
        "host": host,
    });

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}
