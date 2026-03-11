use anyhow::Result;

use crate::cli::{Cli, Commands};

mod build;
mod check;
mod ci;
mod db;
mod format;
mod lint;
mod open;
mod test;
mod up;

pub async fn run(cli: Cli) -> Result<()> {
    match cli.command {
        Commands::Up(args) => up::run(args).await,
        Commands::Build(args) => build::run(args).await,
        Commands::Test(args) => test::run(args).await,
        Commands::Lint(args) => lint::run(args).await,
        Commands::Format(args) => format::run(args).await,
        Commands::Db { command } => db::run(command).await,
        Commands::Check(args) => check::run(args).await,
        Commands::Ci => ci::run().await,
        Commands::Open(args) => open::run(args).await,
    }
}
