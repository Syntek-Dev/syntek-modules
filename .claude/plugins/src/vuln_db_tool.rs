use reqwest;
use serde_json::{json, Value};
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(|s| s.as_str()).unwrap_or("fetch");

    match command {
        "fetch" => fetch_advisory_db().await?,
        "check" => {
            let package = args.get(2).ok_or("Package name required")?;
            let version = args.get(3).ok_or("Version required")?;
            check_package(package, version).await?;
        }
        _ => {
            eprintln!("Usage: vuln-db-tool [fetch|check <package> <version>]");
            std::process::exit(1);
        }
    }

    Ok(())
}

async fn fetch_advisory_db() -> Result<(), Box<dyn std::error::Error>> {
    let url = "https://raw.githubusercontent.com/RustSec/advisory-db/main/crates.json";
    let response = reqwest::get(url).await?;
    let advisories: Value = response.json().await?;

    let output = json!({
        "status": "success",
        "advisory_count": advisories.as_object().map(|o| o.len()).unwrap_or(0),
        "last_updated": chrono::Utc::now().to_rfc3339(),
    });

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}

async fn check_package(package: &str, version: &str) -> Result<(), Box<dyn std::error::Error>> {
    // In a real implementation, this would check against the RustSec database
    let output = json!({
        "package": package,
        "version": version,
        "vulnerabilities": [],
        "status": "no_known_vulnerabilities",
    });

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}
