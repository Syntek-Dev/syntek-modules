use anyhow::Result;
use clap::Parser;

mod cli;
mod commands;
mod config;
mod process;
mod ui;

use cli::Cli;

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    commands::run(cli).await
}
