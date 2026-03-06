use anyhow::Result;

use crate::cli::{OpenArgs, OpenTarget};
use crate::ui;

pub async fn run(args: OpenArgs) -> Result<()> {
    let (url, label) = match args.target {
        OpenTarget::Api => ("http://localhost:8000/graphql", "GraphQL playground"),
        OpenTarget::Frontend => ("http://localhost:3000", "Frontend dev server"),
        OpenTarget::Storybook => ("http://localhost:6006", "Storybook"),
        OpenTarget::Admin => ("http://localhost:8000/admin", "Django admin"),
    };

    ui::step(&format!("Opening {} at {}", label, url));

    if let Err(e) = open::that(url) {
        ui::warn(&format!("Could not open browser automatically: {}", e));
        ui::warn(&format!("Open manually: {}", url));
    }

    Ok(())
}
