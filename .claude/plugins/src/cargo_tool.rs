use cargo_metadata::MetadataCommand;
use serde_json::json;
use std::env;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let manifest_path = args.get(1);

    let mut cmd = MetadataCommand::new();
    if let Some(path) = manifest_path {
        cmd.manifest_path(path);
    }

    let metadata = cmd.exec()?;

    let output = json!({
        "workspace_root": metadata.workspace_root,
        "packages": metadata.packages.iter().map(|p| {
            json!({
                "name": p.name,
                "version": p.version.to_string(),
                "edition": p.edition,
                "rust_version": p.rust_version.as_ref().map(|v| v.to_string()),
                "dependencies": p.dependencies.iter().map(|d| {
                    json!({
                        "name": d.name,
                        "version": d.req.to_string(),
                        "kind": format!("{:?}", d.kind),
                    })
                }).collect::<Vec<_>>(),
            })
        }).collect::<Vec<_>>(),
    });

    println!("{}", serde_json::to_string_pretty(&output)?);
    Ok(())
}
