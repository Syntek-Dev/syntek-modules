use anyhow::Result;

use crate::cli::LintArgs;
use crate::commands::lint;

/// Quick check: runs all linters and type checkers but skips the test suite.
/// Identical to `syntek-dev lint` with all flags set.
pub async fn run(args: LintArgs) -> Result<()> {
    // If the user passed specific flags, respect them.
    // If no flags, run everything (same default as lint).
    lint::run(args).await
}
